/*
 * Ce que le Modded Cycles OS change au calcul de Braids (pichenettes/eurorack, code MIT d'Emilie Gillet), dans le
 * firmware comme dans la reference de tools/emu/test_macro.py (notes/81) : inclus a la fin d'une copie de
 * braids/digital_oscillator.cc (tools/gen_macro.py, SEMANTIC_INC).
 *
 * HARMONICS en 48 kHz natifs (g_native48) : Braids calcule ses 12 harmoniques a 48 kHz, une interpolation de table de
 * sinus chacune, en coupe au-dessus de 12 kHz et lisse leurs amplitudes a chaque echantillon. Ici :
 *   - sin(k phi) et cos(k phi) par rotations : (s, c) <- (s cos phi + c sin phi, c cos phi - s sin phi), sur l'EMAC
 *     (produits Q31 de MODAL, modal_fix.h : tronques a 2^-39, sommes, puis a 2^-31) ; sin phi et cos phi par la table
 *     de Braids. Ecart a la table : moins de -69 dB ;
 *   - les harmoniques jusqu'a 9,75 kHz a 24 kHz (deux fois moins de calcul), remontees a 48 kHz par un filtre
 *     demi-bande de 43 coefficients (+-0,006 dB jusqu'a 9,75 kHz, -63 dB des 14,25 kHz, la ou tombent les images) ;
 *     celles au-dela (une ou deux, les notes aigues) a 48 kHz, chacune par la table de sinus, retardees comme le
 *     filtre (20 echantillons) : la meme coupure a 12 kHz que Braids, sans image ;
 *   - les amplitudes lissees une fois par rendu (n/256 de l'ecart pour n echantillons a 48 kHz, le rythme de Braids ;
 *     comme chez lui, en montant,
 *     arretees a moins de 256 de leur cible : les harmoniques tres faibles restent muettes), fixes le temps d'un rendu
 *     (la passerelle en fait un par bloc de 64, macro.cc NATIVE = 3) ;
 *   - les gains (24 divisions) recalcules seulement quand TIMBRE ou COLOR changent, la coupure quand la note change.
 * Sans g_native48 (96 kHz) : la fonction d'origine, RenderHarmonics96. La boucle des harmoniques : harm_rot ci-dessous,
 * ou son double en assembleur (macro_asm.S, macro_harm_rot) dans le firmware (MODDED_CYCLES_FAST), au bit pres.
 */
namespace braids {

/* la phase calculee du demi-bande (k = 0, 2, ..., 20 sur 43, Kaiser beta 6,2), en Q15, paires (x[m - j], x[m - 21 + j]) ;
 * somme de 2 x 32768 : gain 1 ; l'autre phase : x[m - 10] */
static const int16_t kHalfband24[11] = {
  12, -50, 126, -262, 482, -824, 1344, -2156, 3545, -6560, 20727
};

/* l'EMAC (modal_fix.h) : un produit Q31 tronque a 2^-39 ; lecture : a 2^-31, saturee */
static inline int64_t hp_emp(int32_t a, int32_t b) {
  return (static_cast<int64_t>(a) * b) >> 23;
}
static inline int32_t hp_rd(int64_t a) {
  a >>= 8;
  return a > 0x7fffffffLL ? 0x7fffffff : (a < -0x80000000LL ? static_cast<int32_t>(0x80000000) : static_cast<int32_t>(a));
}

#ifdef MODDED_CYCLES_FAST
/* macro_asm.S lit HarmonicsState a ces decalages */
static_assert(__builtin_offsetof(HarmonicsState, hist) == 144, "hist");
static_assert(__builtin_offsetof(HarmonicsState, pos) == 232, "pos");
static_assert(__builtin_offsetof(HarmonicsState, delay) == 236, "delay");
static_assert(__builtin_offsetof(HarmonicsState, dpos) == 316, "dpos");
extern "C" void macro_harm_rot(int32_t* out, int n, uint32_t phase, uint32_t inc, const int32_t* amp, int k,
                               const int16_t* table);
extern "C" void macro_harm_out(int16_t* buffer, int n, const int32_t* lo, const int32_t* hi, HarmonicsState* h);
extern "C" void macro_sine_acc(int32_t* acc, int n, uint32_t* phase, uint32_t inc, int32_t amp, int shift,
                               const int16_t* table);
#define HARM_ROT macro_harm_rot
#define HARM_OUT macro_harm_out
#define SINE_ACC macro_sine_acc
#else
/* un sinus de la table, amplitude fixe : pour k = 0..n-1 : *phase += inc ;
 * acc[k] += Interpolate824(table, *phase) * amp >> shift (n pair) */
static void sine_acc(int32_t* acc, int n, uint32_t* phase, uint32_t inc, int32_t amp, int shift,
                     const int16_t* table) {
  uint32_t p = *phase;
  for (int k = 0; k < n; ++k) {
    p += inc;
    acc[k] += Interpolate824(table, p) * amp >> shift;
  }
  *phase = p;
}
/* k harmoniques, n echantillons : pour chaque echantillon, phase += inc, puis
 *   S = I(phase) << 16, C = I(phase + 2^30) << 16 (Q31), s = I(phase) << 15, c = I(phase + 2^30) << 15 (Q30) ;
 *   pour j = 0..k-1 : o += amp[j] s ; (s, c) <- (rd(s C + c S), rd(c C + (-s) S)) ;
 *   out = rd(o) >> 15   (I = Interpolate824 de la table, rd : lecture de l'EMAC) */
static void harm_rot(int32_t* out, int n, uint32_t phase, uint32_t inc, const int32_t* amp, int k,
                     const int16_t* table) {
  for (int t = 0; t < n; ++t) {
    phase += inc;
    int32_t sq = Interpolate824(table, phase), cq = Interpolate824(table, phase + 0x40000000);
    int32_t S = sq << 16, C = cq << 16, s = sq << 15, c = cq << 15;
    int64_t o = 0;
    for (int j = 0; j < k; ++j) {
      o += hp_emp(amp[j], s);
      int32_t s2 = hp_rd(hp_emp(s, C) + hp_emp(c, S));
      int32_t c2 = hp_rd(hp_emp(c, C) + hp_emp(-s, S));
      s = s2;
      c = c2;
    }
    out[t] = hp_rd(o) >> 15;
  }
}
/* la phase calculee du demi-bande sur x[0..21] (le plus ancien d'abord) : sortie bornee a +-32767 */
static int32_t hb24(const int16_t* x) {
  int32_t a = 16384;
  for (int j = 0; j < 11; ++j) {
    a += kHalfband24[j] * (x[21 - j] + x[j]);
  }
  a >>= 15;
  CLIP(a)
  return a;
}
/* la sortie : chaque echantillon a 24 kHz (lo) dans l'historique, remonte a 48 kHz (hb24, puis celui d'il y a 10),
 * plus les harmoniques a 48 kHz (hi) retardees de 20 ; 2 echantillons « a 96 kHz » par echantillon a 48 kHz (la
 * passerelle prend le 2e) */
static void harm_out(int16_t* buffer, int n, const int32_t* lo, const int32_t* hi, HarmonicsState* h) {
  int16_t* hist = h->hist;                               /* les 22 derniers, ecrits deux fois : hist[pos..pos+21] */
  int32_t pos = h->pos, dpos = h->dpos;
  for (int t = 0; t < n; ++t) {
    int32_t out = lo[t];
    CLIP(out)
    pos = pos == 21 ? 0 : pos + 1;
    hist[pos + 21] = hist[pos - 1 + (pos ? 0 : 22)] = out;
    const int16_t* x = hist + pos;                         /* x[0] le plus ancien, x[21] le dernier */
    int32_t y[2] = { hb24(x), x[11] };                     /* 48 kHz : interpole, puis l'echantillon d'il y a 10 */
    for (int k = 0; k < 2; ++k) {
      int32_t d = h->delay[dpos];                          /* les harmoniques a 48 kHz, 20 echantillons plus tot */
      h->delay[dpos] = hi[2 * t + k];
      dpos = dpos == 19 ? 0 : dpos + 1;
      int32_t v = y[k] + d;
      CLIP(v)
      *buffer++ = v;
      *buffer++ = v;
    }
  }
  h->pos = pos;
  h->dpos = dpos;
}
#define HARM_ROT harm_rot
#define HARM_OUT harm_out
#define SINE_ACC sine_acc
#endif

void DigitalOscillator::RenderHarmonics(
    const uint8_t* sync,
    int16_t* buffer,
    size_t size) {
  if (!g_native48) {
    RenderHarmonics96(sync, buffer, size);
    return;
  }
  HarmonicsState* h = &state_.hrm;
  const uint32_t inc48 = phase_increment_ << 1;          /* 48 kHz : un echantillon pour 2 a 96 kHz */
  const uint32_t inc24 = phase_increment_ << 2;          /* 24 kHz */

  if (!h->valid || h->key0 != parameter_[0] || h->key1 != parameter_[1]) {
    /* les gains (24 divisions) ne dependent que de TIMBRE et COLOR */
    int32_t peak = (kNumAdditiveHarmonics * parameter_[0]) >> 7;
    int32_t second_peak = (peak >> 1) + kNumAdditiveHarmonics * 128;
    int32_t second_peak_amount = parameter_[1] * parameter_[1] >> 15;

    int32_t sqrtsqrt_width = parameter_[1] < 16384
        ? parameter_[1] >> 6 : 511 - (parameter_[1] >> 6);
    int32_t sqrt_width = sqrtsqrt_width * sqrtsqrt_width >> 10;
    int32_t width = sqrt_width * sqrt_width + 4;
    int32_t total = 0;
    for (size_t i = 0; i < kNumAdditiveHarmonics; ++i) {
      int32_t x = i << 8;
      int32_t d, g;

      d = (x - peak);
      g = 32768 * 128 / (128 + d * d / width);

      d = (x - second_peak);
      g += second_peak_amount * 128 / (128 + d * d / width);
      total += g;
      h->gain[i] = g;
    }

    int32_t attenuation = 2147483647 / total;
    for (size_t i = 0; i < kNumAdditiveHarmonics; ++i) {
      h->gain[i] = h->gain[i] * attenuation >> 16;
    }
    h->key0 = parameter_[0];
    h->key1 = parameter_[1];
    h->valid = 1;
    h->key_inc = ~inc48;                                 /* les cibles sont a refaire */
  }
  if (h->key_inc != inc48) {                             /* la coupure a 12 kHz, comme Braids */
    for (size_t i = 0; i < kNumAdditiveHarmonics; ++i) {
      h->target[i] = (inc48 >> 16) * (i + 1) > 0x4000 ? 0 : h->gain[i];
    }
    h->key_inc = inc48;
  }

  const int n = size >> 2, n48 = 2 * n;                  /* echantillons a 24 kHz, a 48 kHz */
  int32_t lo[16], hi[32];
  int32_t amp_lo[kNumAdditiveHarmonics + 1];            /* + 1 : lue, inutilisee */
  int k_lo = 0;
  bool hi_first = true;
  const uint32_t phase = phase_;
  for (size_t i = 0; i < kNumAdditiveHarmonics; ++i) {
    int32_t amp = h->amplitude[i];                       /* le lissage de Braids, une fois par rendu : */
    const int32_t d = h->target[i] - amp;                /* (cible - amplitude) >> 8 par echantillon, qui en */
    if (d < 0 || d >= 256) {                             /* montant s'arrete a moins de 256 de la cible ; */
      amp += (d * n48) >> 8;                             /* n48 echantillons a 48 kHz par rendu */
    }
    h->amplitude[i] = amp;
    const uint32_t rank = i + 1;
    if ((inc24 >> 16) * rank <= 0x6800 && k_lo == static_cast<int>(i)) {   /* jusqu'a 9,75 kHz : a 24 kHz */
      amp_lo[i] = amp >= 32768 ? 0x7fffffff : (amp << 16);
      k_lo = i + 1;
    } else if (amp && (inc48 >> 16) * rank < 0x8000) {  /* au-dela : a 48 kHz, tant qu'elle sonne ; une ou deux */
      if (hi_first) {                                    /* harmoniques, chacune par la table */
        for (int t = 0; t < n48; ++t) {
          hi[t] = 0;
        }
        hi_first = false;
      }
      uint32_t p = phase * rank;
      SINE_ACC(hi, n48, &p, inc48 * rank, amp, 15, wav_sine);
    }
  }
  amp_lo[k_lo] = 0;
  bool lo_first = k_lo == 0;
  if (!lo_first) {
    HARM_ROT(lo, n, phase, inc24, amp_lo, k_lo, wav_sine);
  }
  phase_ = phase + n * inc24;

  static const int32_t zeros[32] = { 0 };               /* pas d'harmonique dans ce groupe */
  HARM_OUT(buffer, n, lo_first ? zeros : lo, hi_first ? zeros : hi, h);
}

}  // namespace braids
