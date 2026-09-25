/*
 * SD VINTAGE : machine de caisse claire « vintage » pour l'Elektron Model:Cycles (OS 1.13).
 *
 * Interpretation clean-room (aucun code ni echantillon Elektron) : corps a deux modes
 * sinusoidaux accordes avec balayage de hauteur, bruit « snappy » filtre, puis la chaine
 * d'ampli d'origine du M:C (enveloppe DECAY/GATE, VCA, PUNCH) pour que ces reglages se
 * comportent exactement comme sur les 6 machines d'origine.
 *
 * Contrat (retro-ingenierie de l'OS 1.13, voir notes/14) :
 *   update(pmod, v, p) : 1 fois par bloc de 32 trames, avant render. pmod = note du trig
 *                        (demi-tons << 16), v = etat de voix (0x31c o), p = parametres piste
 *                        (mots 8.8 ; p+0x14 PITCH, +0x16 COLOR, +0x18 SHAPE, +0x1a SWEEP,
 *                        +0x1c CONTOUR, +0x1e PUNCH, +0x22 FINE, +0x24 DECAY).
 *   render(out, v)     : ecrit 32 echantillons int32 (Q31) dans out.
 *   v+0x38 != 0        : bloc de declenchement (nouvelle note).
 *   L'EMAC est en mode fractionnaire signe sature (MACSR = 0xa0) pendant ces appels.
 *
 * Etat propre a SD VINTAGE : v+0x70..v+0xab (zone des operateurs FM 0..1, inutilisee
 * par cette machine ; evite les champs remis a zero par 0x400a7d16 : 0x6c, 0xe4...).
 *
 * Compile par tools/gen_sdvintage.py (m68k-linux-gnu-gcc -mcpu=54418), valide dans le vrai
 * moteur emule par tools/emu/test_sdvintage.py.
 */
typedef signed char s8;
typedef short s16;
typedef int s32;
typedef unsigned int u32;

/* Q31 x Q31 -> Q31 (EMAC fractionnaire, sature). ACC0 est rendu vide, comme l'exige l'OS. */
static inline s32 qmul(s32 a, s32 b)
{
	s32 r;
	__asm__ volatile("mac.l %1,%2,%%acc0\n\tmovclr.l %%acc0,%0" : "=d"(r) : "r"(a), "r"(b));
	return r;
}
#define FW_TABLE(a) ((const s32 *)(a))
#define AMP_ENV(v) ((void (*)(char *))0x400a9252)(v)
#define VCA(o, v) ((void (*)(s32 *, char *))0x400a9430)(o, v)
#define PUNCH(o, v) ((void (*)(s32 *, char *))0x400a967a)(o, v)

/* Tables de l'OS 1.13 (lecture seule) */
#define SINE      FW_TABLE(0x8000eee4)   /* sinus 256+1 points, Q31 (SRAM, copie au boot) */
#define LUT_DECAY FW_TABLE(0x4012228c)   /* DECAY -> multiplicateur par bloc (negatif) */
#define LUT_ATK   FW_TABLE(0x4012268c)   /* DECAY -> attaque de l'enveloppe d'ampli */

#define V32(off)  (*(s32 *)(v + (off)))
#define U32(off)  (*(u32 *)(v + (off)))
#define P16(off)  (*(const s16 *)(p + (off)))

/* etat SD VINTAGE dans la voix */
#define S_PH1   0x70   /* phase mode 1 */
#define S_PH2   0x74   /* phase mode 2 */
#define S_INC   0x78   /* increment de phase courant (debut de bloc) */
#define S_INCT  0x7c   /* increment cible (fin de bloc) */
#define S_EB    0x80   /* enveloppe du corps, courante */
#define S_EBT   0x84   /* enveloppe du corps, cible */
#define S_ES    0x88   /* enveloppe du balayage */
#define S_RNG   0x8c   /* generateur de bruit */
#define S_HPY   0x90   /* passe-haut du bruit : sortie */
#define S_HPX   0x94   /* passe-haut du bruit : entree precedente */
#define S_LP1   0x98   /* passe-bas 1 */
#define S_LP2   0x9c   /* passe-bas 2 */
#define S_GB    0xa0   /* gain du corps */
#define S_GN    0xa4   /* gain du bruit */
#define S_GLP   0xa8   /* coefficient du passe-bas (SHAPE) */

#define ONE      0x7fffffff
#define NORM     66052          /* 0..0x7f00 (8.8) -> Q31 */
#define INC440   39370534       /* 2^32 * 440 / 48000 */
#define TUNE     (-(5 << 16))     /* corps : note 60 + PITCH 64 -> G3 (196 Hz) */
#define RATIO_M1 0x4f5c28f6     /* 2e mode = 1.62 x fondamental (0.62 en Q31) */
#define MODE2    0x46666666     /* niveau du 2e mode : 0.55 */
#define A_HP     0x7834793e     /* passe-haut 1 pole ~480 Hz */
#define NOISE_G  0x60000000     /* niveau du bruit filtre (x 0.75 puis << 2) */

/* SHAPE -> coefficient du passe-bas 1 pole (1.2 kHz -> 14 kHz), 17 points, interpolee */
static const s32 lp_tab[17] = {
	0x129b499f, 0x157332b1, 0x18ad3dd8, 0x1c522d1b, 0x2069f7b5, 0x24fb1c69,
	0x2a09c596, 0x2f96bf14, 0x359e44d6, 0x3c16bc04, 0x42ef772f, 0x4a0fb888,
	0x51563894, 0x58998735, 0x5fa99fd7, 0x6652f47d, 0x6c62fabb,
};

static inline s32 clamp_param(s32 x)
{
	return x < 0 ? 0 : (x > 0x7f00 ? 0x7f00 : x);
}

/* 2^(n/12) en increment de phase ; n = demi-tons << 16, relatif a la4 (440 Hz) */
__attribute__((optimize("Os"))) static s32 note_inc(s32 n)
{
	s32 o = qmul(n, 0x0aaaaaab);             /* / 12 -> octaves << 16 */
	s32 e = o >> 16;
	s32 x = (o & 0xffff) << 15;              /* fraction d'octave, Q31 */
	s32 y = qmul(0x09e79bdb, x) + 0x1d0c5fa9;
	y = qmul(y, x) + 0x5903d9d4;
	y = qmul(y, x);                          /* 2^x - 1, Q31 */
	s32 inc = qmul((1 << 30) + (y >> 1), INC440) << 1;
	if (e >= 0)
		inc <<= e;
	else
		inc >>= -e;
	return inc;
}

/* -Os : code de controle (1 fois par bloc), doit tenir dans la cave de 1025 o */
__attribute__((optimize("Os"))) void sdv_update(s32 pmod, char *v, const char *p)
{
	s32 dec = (s8)p[0x24];
	s32 sweep = clamp_param(P16(0x1a)), contour = clamp_param(P16(0x1c));
	s32 color = clamp_param(P16(0x16)), shape = clamp_param(P16(0x18));
	s32 n, inc0, d, es, idx;

	if (dec < 0) dec = 0;
	if (dec > 127) dec = 127;
	/* enveloppe d'ampli d'origine (DECAY), comme SNARE */
	V32(0x250) = LUT_DECAY[dec];

	if (V32(0x38)) {                         /* declenchement */
		V32(0x274) = V32(0x278) = 0x01f10e1d; /* constantes de l'etage PUNCH (identiques SNARE) */
		V32(0x280) = V32(0x284) = 0x001f7c5c;
		V32(0x290) = V32(0x294) = ONE;
		V32(0x27c) = 0x83e21c3a;
		V32(0x288) = 0x803ef8b8;
		V32(0x248) = LUT_ATK[dec];
		if (P16(0x1e)) {
			V32(0x29c) = 0x40000000; V32(0x2a0) = ONE; V32(0x2a4) = 0x40000000;
			V32(0x48) = 1; V32(0x2b8) = 0x80000000;
		} else {
			V32(0x29c) = ONE; V32(0x2a0) = 0x20000000; V32(0x2a4) = ONE;
			V32(0x48) = 0; V32(0x2b8) = 0xc028db9c;
		}
		U32(S_PH1) = 0;
		U32(S_PH2) = 0x40000000;             /* 2e mode decale d'un quart : attaque moins « clic » */
		V32(S_EB) = V32(S_EBT) = ONE;
		V32(S_ES) = ONE;
		V32(S_HPY) = V32(S_HPX) = V32(S_LP1) = V32(S_LP2) = 0;
		if (!V32(S_RNG))
			V32(S_RNG) = 0x2545f491;
	} else {
		/* CONTOUR -> duree du corps : LUT DECAY indices 14..69 (~12 ms .. ~650 ms) */
		idx = 14 + (((contour >> 8) * 7) >> 4);
		V32(S_EBT) = qmul(V32(S_EBT), -LUT_DECAY[idx]);
		/* SWEEP -> duree du balayage : indices 8..23 (~4 .. ~45 ms) */
		idx = 8 + ((sweep >> 8) >> 3);
		V32(S_ES) = qmul(V32(S_ES), -LUT_DECAY[idx]);
	}

	/* hauteur : meme convention que les machines d'origine (PITCH 64 + note du trig) */
	n = ((s32)P16(0x14) << 8) + (((s32)P16(0x22) - 0x4000) << 3) - (64 << 16) + pmod;
	if (n < 0) n = 0;
	if (n > (127 << 16)) n = 127 << 16;
	inc0 = note_inc(n + TUNE - (69 << 16));

	/* SWEEP -> profondeur : f = f0 * (1 + 2.2 * sweep^2 * env) */
	d = qmul(sweep * NORM, sweep * NORM);
	d = qmul(d, 0x46666666);                 /* 0.55 = 2.2 / 4 (Q29) */
	es = qmul(d, V32(S_ES));
	es = qmul(inc0, es);
	if (es > ((0x7fffffff - inc0) >> 2))
		V32(S_INCT) = 0x7fffffff;
	else
		V32(S_INCT) = inc0 + (es << 2);
	if (V32(0x38))
		V32(S_INC) = V32(S_INCT);

	/* COLOR -> « snappy » : bruit plus fort, corps un peu moins */
	color *= NORM;
	V32(S_GN) = color;
	V32(S_GB) = ONE - qmul(qmul(color, color), 0x39999999);   /* 1 - 0.45 c^2 */

	/* SHAPE -> brillance du bruit */
	idx = shape >> 11;
	V32(S_GLP) = lp_tab[idx] + qmul(lp_tab[idx + 1] - lp_tab[idx], (shape & 0x7ff) << 20);
}

static inline s32 sine(u32 ph)
{
	const s32 *t = SINE + (ph >> 24);
	return t[0] + qmul(t[1] - t[0], (s32)((ph & 0xffffff) << 7));
}

void sdv_render(s32 *out, char *v)
{
	u32 ph1 = U32(S_PH1), ph2 = U32(S_PH2), rng = U32(S_RNG);
	s32 inc = V32(S_INC), dinc = (V32(S_INCT) - inc) >> 5;
	s32 eb = V32(S_EB), deb = (V32(S_EBT) - eb) >> 5;
	s32 hpy = V32(S_HPY), hpx = V32(S_HPX), lp1 = V32(S_LP1), lp2 = V32(S_LP2);
	s32 gb = V32(S_GB), gn = qmul(V32(S_GN), NOISE_G), glp = V32(S_GLP);
	int i;

	for (i = 0; i < 32; i++) {
		s32 body, x;
		/* corps : 2 modes accordes, le 2e s'eteint deux fois plus vite */
		ph1 += inc;
		ph2 += inc + qmul(inc, RATIO_M1);
		body = (sine(ph1) >> 1) + (qmul(sine(ph2), qmul(eb, MODE2)) >> 1);
		body = qmul(qmul(body, eb), gb);
		/* bruit blanc -> passe-haut 480 Hz -> 2 passe-bas 1 pole (SHAPE) */
		rng = rng * 1664525u + 1013904223u;
		x = (s32)rng >> 2;
		hpy = qmul(A_HP, hpy + x - hpx);
		hpx = x;
		lp1 += qmul(glp, hpy - lp1);
		lp2 += qmul(glp, lp1 - lp2);
		out[i] = body + (qmul(lp2, gn) << 2);
		inc += dinc;
		eb += deb;
	}
	U32(S_PH1) = ph1; U32(S_PH2) = ph2; U32(S_RNG) = rng;
	V32(S_INC) = V32(S_INCT);
	V32(S_EB) = V32(S_EBT);
	V32(S_HPY) = hpy; V32(S_HPX) = hpx; V32(S_LP1) = lp1; V32(S_LP2) = lp2;

	/* chaine d'ampli d'origine : enveloppe DECAY/GATE, VCA, PUNCH */
	AMP_ENV(v);
	VCA(out, v);
	PUNCH(out, v);
}
