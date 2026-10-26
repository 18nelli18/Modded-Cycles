/*
 * Fonctions de DigitalOscillator (Braids, pichenettes/eurorack, code MIT d'Emilie Gillet) reecrites pour le ColdFire
 * du Model:Cycles (notes/81) : les memes calculs, entier pour entier, dans le meme ordre la ou il compte, pour le meme
 * son au bit pres (tools/emu/test_macro.py compare MACRO a Braids compile depuis ses sources d'origine). Ce qui
 * change : l'etat reste en registres le temps d'un rendu au lieu d'etre relu et reecrit a chaque echantillon, et les
 * boucles vont par partiel plutot que par echantillon. Inclus a la fin d'une copie de braids/digital_oscillator.cc,
 * dont les definitions d'origine sont mises hors compilation (tools/gen_macro.py, FAST) : ses tables y sont visibles.
 */

extern "C" {
void macro_sine_acc(int32_t* acc, int n, uint32_t* phase, uint32_t inc, int32_t amp, int shift,
                    const int16_t* table);
struct macro_cymbal_state {
  uint32_t inc[7];
  int32_t f0, damp0, f1, damp1, xfade;
  uint32_t phase, rng, p[6];
  int32_t lp0, bp0, lp1, bp1;
};
void macro_cymbal(int16_t* buffer, int n, macro_cymbal_state* st);
struct macro_drum_args {
  void* a;
  int32_t fade_increment, f, nmg, hg;
  uint32_t rng;
  int32_t dual;
};
void macro_drum_render(int16_t* buffer, int n, macro_drum_args* g);
struct macro_fluted_state {
  int32_t bi, bf, ji, jf, nfc, pole, lcg, bri;
  int32_t dcx, dcy, lp;
  uint32_t rng, dp;
  const uint16_t* env;
  int8_t* bore;
  int8_t* jet;
  const int16_t* jet_lut;
};
void macro_fluted(int16_t* buffer, int n, macro_fluted_state* st);
}

namespace braids {

using namespace stmlib;

/* echantillons par rendu, au plus : MACRO rend par 24 (96 kHz) ou 12 (48 kHz) */
static const size_t kFastMax = 32;

/* Svf::Process (braids/svf.h) sur des copies locales : f et damp calcules une fois (dirty_, comme le 1er appel),
 * lp et bp en registres, rendus a la fin. Sans « punch » : SNARE et CYMBAL remettent leurs filtres a zero (Init,
 * punch_ = 0) a chaque changement de modele (init_, DigitalOscillator::Render) et ne le reglent jamais. */
struct FastSvf {
  Svf& s;
  int32_t f, damp, lp, bp;
  const int mode;

  explicit FastSvf(Svf& svf) : s(svf), mode(svf.mode_) {
    if (s.dirty_) {
      s.f_ = Interpolate824(lut_svf_cutoff, s.frequency_ << 17);
      s.damp_ = Interpolate824(lut_svf_damp, s.resonance_ << 17);
      s.dirty_ = false;
    }
    f = s.f_;
    damp = s.damp_;
    lp = s.lp_;
    bp = s.bp_;
  }
  ~FastSvf() {
    s.lp_ = lp;
    s.bp_ = bp;
  }
  inline int32_t Process(int32_t in) {
    int32_t notch = in - (bp * damp >> 15);
    lp += f * bp >> 15;
    CLIP(lp)
    int32_t hp = notch - lp;
    bp += f * hp >> 15;
    CLIP(bp)
    return mode == SVF_MODE_BP ? bp : (mode == SVF_MODE_HP ? hp : lp);
  }
};

void DigitalOscillator::RenderSnare(
    const uint8_t* sync,
    int16_t* buffer,
    size_t size) {
  if (init_) {
    pulse_[0].Init();
    pulse_[0].set_delay(0);
    pulse_[0].set_decay(1536);

    pulse_[1].Init();
    pulse_[1].set_delay(1e-3 * 48000);
    pulse_[1].set_decay(3072);

    pulse_[2].Init();
    pulse_[2].set_delay(1e-3 * 48000);
    pulse_[2].set_decay(1200);

    pulse_[3].Init();
    pulse_[3].set_delay(0);

    svf_[0].Init();

    svf_[1].Init();

    svf_[2].Init();
    svf_[2].set_resonance(2000);
    svf_[2].set_mode(SVF_MODE_BP);

    init_ = false;
  }

  if (strike_) {
    int32_t decay = 49152 - pitch_;
    decay += parameter_[1] < 16384 ? 0 : parameter_[1] - 16384;
    if (decay > 65535) {
      decay = 65535;
    }
    svf_[0].set_resonance(29000 + (decay >> 5));
    svf_[1].set_resonance(26500 + (decay >> 5));
    pulse_[3].set_decay(4092 + (decay >> 14));

    pulse_[0].Trigger(15 * 32768);
    pulse_[1].Trigger(-1 * 32768);
    pulse_[2].Trigger(13107);
    int32_t snappy = parameter_[1];
    if (snappy >= 14336) {
      snappy = 14336;
    }
    pulse_[3].Trigger(512 + (snappy << 1));
    strike_ = false;
  }

  svf_[0].set_frequency(pitch_ + (12 << 7));
  svf_[1].set_frequency(pitch_ + (24 << 7));
  svf_[2].set_frequency(pitch_ + (60 << 7));

  int32_t g_1 = 22000 - (parameter_[0] >> 1);
  int32_t g_2 = 22000 + (parameter_[0] >> 1);

  FastSvf s0(svf_[0]), s1(svf_[1]), s2(svf_[2]);
  while (size) {
    int32_t excitation_1 = 0;
    excitation_1 += pulse_[0].Process();
    excitation_1 += pulse_[1].Process();
    excitation_1 += !pulse_[1].done() ? 2621 : 0;

    int32_t excitation_2 = 0;
    excitation_2 += pulse_[2].Process();
    excitation_2 += !pulse_[2].done() ? 13107 : 0;

    int32_t noise_sample = Random::GetSample() * pulse_[3].Process() >> 15;

    int32_t sd = 0;
    sd += (s0.Process(excitation_1) + (excitation_1 >> 4)) * g_1 >> 15;
    sd += (s1.Process(excitation_2) + (excitation_2 >> 4)) * g_2 >> 15;
    sd += s2.Process(noise_sample);
    CLIP(sd);

    *buffer++ = sd;
    *buffer++ = sd;
    size -= 2;
  }
}

void DigitalOscillator::RenderCymbal(
    const uint8_t* sync,
    int16_t* buffer,
    size_t size) {
  if (init_) {
    svf_[0].Init();
    svf_[0].set_mode(SVF_MODE_BP);
    svf_[0].set_resonance(12000);
    svf_[1].Init();
    svf_[1].set_mode(SVF_MODE_HP);
    svf_[1].set_resonance(2000);
    init_ = false;
  }

  HatState* hat = &state_.hat;

  uint32_t increments[7];
  int32_t note = (40 << 7) + (pitch_ >> 1);
  increments[0] = ComputePhaseIncrement(note);

  uint32_t root = increments[0] >> 10;
  increments[1] = root * 24273 >> 4;
  increments[2] = root * 12561 >> 4;
  increments[3] = root * 18417 >> 4;
  increments[4] = root * 22452 >> 4;
  increments[5] = root * 31858 >> 4;
  increments[6] = increments[0] * 24;

  int32_t xfade = parameter_[1];
  svf_[0].set_frequency(parameter_[0] >> 1);
  svf_[1].set_frequency(parameter_[0] >> 1);

  FastSvf s0(svf_[0]), s1(svf_[1]);                     /* f et damp (dirty_) ; lp et bp rendus a la fin */
  macro_cymbal_state st;                                  /* macro_asm.S : la boucle d'origine, exacte */
  for (size_t i = 0; i < 7; ++i) {
    st.inc[i] = increments[i];
  }
  st.f0 = s0.f;
  st.damp0 = s0.damp;
  st.f1 = s1.f;
  st.damp1 = s1.damp;
  st.xfade = xfade;
  st.phase = phase_;
  st.rng = hat->rng_state;
  for (size_t i = 0; i < 6; ++i) {
    st.p[i] = hat->phase[i];
  }
  st.lp0 = s0.lp;
  st.bp0 = s0.bp;
  st.lp1 = s1.lp;
  st.bp1 = s1.bp;
  macro_cymbal(buffer, size, &st);
  phase_ = st.phase;
  hat->rng_state = st.rng;
  for (size_t i = 0; i < 6; ++i) {
    hat->phase[i] = st.p[i];
  }
  s0.lp = st.lp0;
  s0.bp = st.bp0;
  s1.lp = st.lp1;
  s1.bp = st.bp1;
}

/* STRUCK BELL : 11 partiels inharmoniques, calcules a 48 kHz (un echantillon sur deux, comme Braids). Une boucle par
 * partiel : sa phase, son pas et son amplitude (fixe le temps d'un rendu) restent en registres. */
void DigitalOscillator::RenderStruckBell(
    const uint8_t* sync,
    int16_t* buffer,
    size_t size) {
  size_t first_partial = state_.add.current_partial;
  size_t last_partial = std::min(
      state_.add.current_partial + 3,
      kNumBellPartials);
  state_.add.current_partial = (first_partial + 3) % kNumBellPartials;

  bool strike_was = strike_;
  if (strike_) {
    for (size_t i = 0; i < kNumBellPartials; ++i) {
      state_.add.partial_amplitude[i] = kBellPartialAmplitudes[i];
      state_.add.partial_phase[i] = (1L << 30);
    }
    strike_ = false;
    first_partial = 0;
    last_partial = kNumBellPartials;
  }

  /* d'origine, 3 partiels recalcules a chaque rendu, a tour de role. Quand pitch_ et parameter_[1] n'ont pas bouge
   * depuis que les 11 l'ont ete (4 rendus), le calcul redonnerait les memes valeurs : saute. La cle et le compte dans
   * lp_noise[0] et [1], inutilises ici, mis a zero par Init au changement de modele. */
  int32_t key = (static_cast<int32_t>(pitch_) << 16) ^ static_cast<uint16_t>(parameter_[1]) ^ 0x5a5a;
  if (strike_was || state_.add.lp_noise[0] != key) {
    state_.add.lp_noise[0] = key;
    state_.add.lp_noise[1] = 0;
  }
  if (state_.add.lp_noise[1] < 4) {
    ++state_.add.lp_noise[1];
    for (size_t i = first_partial; i < last_partial; ++i) {
      int16_t partial_pitch = pitch_ + kBellPartials[i];
      if (i & 1) {
        partial_pitch += parameter_[1] >> 7;
      } else {
        partial_pitch -= parameter_[1] >> 7;
      }
      state_.add.partial_phase_increment[i] = \
          ComputePhaseIncrement(partial_pitch) << 1;
    }
  }

  if (parameter_[0] < 32000) {
    int16_t balance = (32767 - parameter_[0]) >> 8;       /* (le meme pour les 11 partiels) */
    balance = balance * balance >> 7;
    for (size_t i = 0; i < kNumBellPartials; ++i) {
      int32_t decay_long = kBellPartialDecayLong[i];
      int32_t decay_short = kBellPartialDecayShort[i];
      int32_t decay = decay_long - ((decay_long - decay_short) * balance >> 7);
      state_.add.partial_amplitude[i] = \
          state_.add.partial_amplitude[i] * decay >> 16;
    }
  }

  const size_t n = size >> 1;
  int32_t acc[kFastMax];
  for (size_t k = 0; k < n; ++k) {
    acc[k] = 0;
  }
  for (size_t i = 0; i < kNumBellPartials; ++i) {         /* macro_asm.S */
    macro_sine_acc(acc, n, &state_.add.partial_phase[i], state_.add.partial_phase_increment[i],
                   state_.add.partial_amplitude[i], 17, wav_sine);
  }
  int16_t previous_sample = state_.add.previous_sample;
  for (size_t k = 0; k < n; ++k) {
    int32_t out = acc[k];
    CLIP(out)
    *buffer++ = (out + previous_sample) >> 1;
    *buffer++ = out;
    previous_sample = out;
  }
  state_.add.previous_sample = previous_sample;
}

/* STRUCK DRUM : 6 partiels et un bruit filtre (3 passe-bas), a 48 kHz (un echantillon sur deux, comme Braids). Le
 * bruit et le fondu d'abord, puis une boucle par partiel, puis le melange. */
void DigitalOscillator::RenderStruckDrum(
    const uint8_t* sync,
    int16_t* buffer,
    size_t size) {

  if (strike_) {
    bool reset_phase = state_.add.partial_amplitude[0] < 1024;
    for (size_t i = 0; i < kNumDrumPartials; ++i) {
      state_.add.target_partial_amplitude[i] = kDrumPartialAmplitude[i];
      if (reset_phase) {
        state_.add.partial_phase[i] = (1L << 30);
      }
    }
    strike_ = false;
  } else {
    if (parameter_[0] < 32000) {
      int16_t balance = (32767 - parameter_[0]) >> 8;     /* (le meme pour les 6 partiels) */
      balance = balance * balance >> 7;
      for (size_t i = 0; i < kNumDrumPartials; ++i) {
        int32_t decay_long = kDrumPartialDecayLong[i];
        int32_t decay_short = kDrumPartialDecayShort[i];
        int32_t decay = decay_long - ((decay_long - decay_short) * balance >> 7);
        state_.add.target_partial_amplitude[i] = \
            state_.add.partial_amplitude[i] * decay >> 16;
      }
    }
  }

  /* les pas des partiels ne dependent que de pitch_ : recalcules seulement quand elle change (d'origine, a chaque
   * rendu ; memes valeurs). La cle dans current_partial, inutilise ici, mis a zero par Init au changement de modele */
  if (state_.add.current_partial != static_cast<size_t>(pitch_) + 1) {
    for (size_t i = 0; i < kNumDrumPartials; ++i) {
      int16_t partial_pitch = pitch_ + kDrumPartials[i];
      state_.add.partial_phase_increment[i] = i && kDrumPartials[i] == kDrumPartials[i - 1]
          ? state_.add.partial_phase_increment[i - 1]      /* meme hauteur que le precedent : meme pas */
          : ComputePhaseIncrement(partial_pitch) << 1;
    }
    state_.add.current_partial = static_cast<size_t>(pitch_) + 1;
  }

  int32_t cutoff = (pitch_ - 12 * 128) + (parameter_[1] >> 2);
  if (cutoff < 0) {
    cutoff = 0;
  } else if (cutoff > 32767) {
    cutoff = 32767;
  }
  int32_t f = Interpolate824(lut_svf_cutoff, cutoff << 16);
  int32_t lp_state_0 = state_.add.lp_noise[0];
  int32_t lp_state_1 = state_.add.lp_noise[1];
  int32_t lp_state_2 = state_.add.lp_noise[2];
  int32_t harmonics_gain = parameter_[1] < 12888 ? (parameter_[1] + 4096) : 16384;
  int32_t noise_mode_gain = parameter_[1] < 16384 ? 0 : parameter_[1] - 16384;
  noise_mode_gain = noise_mode_gain * 12888 >> 14;

  /* le bruit, les 6 partiels et le melange : macro_asm.S, en un appel (les memes calculs) */
  static_assert(__builtin_offsetof(AdditiveState, partial_phase_increment) == 44, "add");
  static_assert(__builtin_offsetof(AdditiveState, previous_sample) == 176, "add");
  static_assert(__builtin_offsetof(AdditiveState, lp_noise) == 182, "add");   /* (alignement de 2 octets du m68k) */
  AdditiveState* a = &state_.add;
  a->lp_noise[0] = lp_state_0;
  a->lp_noise[1] = lp_state_1;
  a->lp_noise[2] = lp_state_2;
  macro_drum_args g = { a, static_cast<int32_t>(65536 / size), f, noise_mode_gain, harmonics_gain, Random::state(),
                        a->partial_phase[0] == a->partial_phase[1]
                            && a->partial_phase_increment[0] == a->partial_phase_increment[1] };
  macro_drum_render(buffer, (size + 1) >> 1, &g);           /* (size + 1) / 2 : la boucle d'origine */
  Random::Seed(g.rng);
  for (size_t i = 0; i < kNumBellPartials; ++i) {
    AdditiveState* a = &state_.add;
    a->partial_amplitude[i] = a->target_partial_amplitude[i];
  }
}

void DigitalOscillator::RenderFluted(
    const uint8_t* sync,
    int16_t* buffer,
    size_t size) {
  uint16_t delay_ptr = state_.phy.delay_ptr;
  uint16_t excitation_ptr = state_.phy.excitation_ptr;

  int32_t lp_state = state_.phy.lp_state;
  int32_t dc_blocking_x0 = state_.phy.filter_state[0];
  int32_t dc_blocking_y0 = state_.phy.filter_state[1];

  int8_t* dl_b = delay_lines_.fluted.bore;
  int8_t* dl_j = delay_lines_.fluted.jet;

  if (strike_) {
    excitation_ptr = 0;
    memset(dl_b, 0, sizeof(delay_lines_.fluted.bore));
    memset(dl_j, 0, sizeof(delay_lines_.fluted.jet));
    lp_state = 0;
    strike_ = false;
  }

  uint32_t bore_delay = (delay_ << 1) - (2 << 16);
  uint32_t jet_delay = (bore_delay >> 8) * (48 + (parameter_[1]  >> 10));
  bore_delay -= jet_delay;
  while (bore_delay > ((kWGFBoreLength - 1) << 16)
         || jet_delay > ((kWGJetLength - 1) << 16)) {
    bore_delay >>= 1;
    jet_delay >>= 1;
  }
  uint16_t breath_intensity = 2100 - (parameter_[0] >> 4);
  uint16_t filter_coefficient = lut_flute_body_filter[pitch_ >> 7];

  macro_fluted_state st;                                  /* macro_asm.S : la boucle d'origine, exacte */
  st.bi = bore_delay >> 16;
  st.bf = bore_delay & 0xffff;
  st.ji = jet_delay >> 16;
  st.jf = jet_delay & 0xffff;
  st.nfc = -filter_coefficient;
  st.pole = kDCBlockingPole;
  st.lcg = 1664525;
  st.bri = breath_intensity;
  st.dcx = dc_blocking_x0;
  st.dcy = dc_blocking_y0;
  st.lp = lp_state;
  st.rng = Random::state();
  st.dp = delay_ptr;
  st.env = lut_blowing_envelope + excitation_ptr;
  st.bore = dl_b;
  st.jet = dl_j;
  st.jet_lut = lut_blowing_jet;
  macro_fluted(buffer, size, &st);
  Random::Seed(st.rng);
  phase_ += phase_increment_ * size;                      /* phase_ += phase_increment_, a chaque echantillon */
  delay_ptr = st.dp;
  excitation_ptr = st.env - lut_blowing_envelope;
  lp_state = st.lp;
  dc_blocking_x0 = st.dcx;
  dc_blocking_y0 = st.dcy;

  if (excitation_ptr >= LUT_BLOWING_ENVELOPE_SIZE - 32) {
    excitation_ptr = LUT_BLOWING_ENVELOPE_SIZE - 32;
  }
  state_.phy.delay_ptr = delay_ptr;
  state_.phy.excitation_ptr = excitation_ptr;
  state_.phy.lp_state = lp_state;
  state_.phy.filter_state[0] = dc_blocking_x0;
  state_.phy.filter_state[1] = dc_blocking_y0;
}

}  // namespace braids
