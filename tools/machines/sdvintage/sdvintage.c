/*
 * SD VINTAGE : machine de caisse claire « vintage » pour l'Elektron Model:Cycles (OS 1.13).
 *
 * Version 2 (29/09/2026) : recalee sur le vrai SD VINTAGE du Syntakt, mesure dans son moteur audio
 * emule (tools/emu/stengine.py, notes/16). Toujours clean-room : aucun code ni echantillon Elektron,
 * seulement des constantes ajustees sur des mesures (hauteur, balayage, durees, spectre).
 *
 * Les machines « FM » du Syntakt ont la disposition de celles du Cycles (notes/16 §4) ; les potards
 * prennent donc le sens de ceux du Syntakt :
 *   PITCH   = TUNE : corps accorde sur la note (note 60 -> 261,6 Hz)
 *   COLOR   = INHM : rapport du 2e mode du corps (x2 .. x2,8), un peu plus d'amas aigu
 *   SHAPE   = FCMP : force de l'amas aigu (les « modes » de la caisse), non monotone comme l'original
 *   SWEEP   = SWEP : balayage de la hauteur fondamentale (profondeur et duree)
 *   CONTOUR = MENV : niveau et duree du 2e mode (enveloppe de modulation)
 *   DECAY, PUNCH, GATE : chaine d'ampli d'origine du M:C, dont le Syntakt partage les tables
 *
 * Structure : corps sinusoidal (+ 2e mode) avec balayage, amas de bruit passe-bande 1,5 - 4,6 kHz
 * (2 poles de chaque cote), puis enveloppe d'ampli, VCA, PUNCH. Le DECAY lit la table d'origine a
 * l'index qui redonne les durees mesurees du Syntakt (dec_idx).
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
 * Etat propre a SD VINTAGE : v+0x70..v+0xbf (zone de l'operateur FM 0, inutilisee par cette
 * machine ; la remise a zero 0x400a7d16 n'y efface que 0x6c, avant cette zone).
 *
 * Compile par tools/gen_sdvintage.py (-mcpu=54418), valide dans le vrai moteur emule par
 * tools/emu/test_sdvintage.py et compare au Syntakt par tools/emu/compare_sdvintage.py.
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
#define S_PH1   0x70   /* phase du fondamental */
#define S_PH2   0x74   /* phase du 2e mode */
#define S_INC   0x78   /* increment de phase courant (debut de bloc) */
#define S_INCT  0x7c   /* increment cible (fin de bloc) */
#define S_EB    0x80   /* decroissance propre du corps, courante */
#define S_EBT   0x84   /* decroissance propre du corps, cible */
#define S_ES    0x88   /* enveloppe du balayage */
#define S_RNG   0x8c   /* generateur de bruit */
#define S_NX    0x90   /* bruit : entree precedente du 1er passe-haut */
#define S_H1    0x94   /* passe-haut 1 */
#define S_H2    0x98   /* passe-haut 2 */
#define S_LP1   0x9c   /* passe-bas 1 */
#define S_LP2   0xa0   /* passe-bas 2 */
#define S_GN    0xa4   /* gain de l'amas (SHAPE, COLOR) */
#define S_R2    0xa8   /* 2e mode : rapport - 2 (COLOR), Q31 */
#define S_E2    0xac   /* enveloppe du 2e mode, courante (x niveau) */
#define S_E2T   0xb0   /* enveloppe du 2e mode, cible */
#define S_E2E   0xb4   /* enveloppe du 2e mode, sans le niveau */

#define ONE      0x7fffffff
#define NORM     66052          /* 0..0x7f00 (8.8) -> Q31 */
#define INC440   39370534       /* 2^32 * 440 / 48000 */
#define BODY_MUL 0x7e4dfe3f     /* corps : tau 50 ms par bloc a DECAY 0, allonge avec DECAY (aucun a 127), comme le Syntakt */
#define A_HP     0x692e488f     /* passe-haut 1 pole ~1,5 kHz */
#define G_LP     0x2f5c28f6     /* passe-bas 1 pole (g = 0,37, ~3,7 kHz) : pente et centre mesures */
#define NOISE_G  0x56c8b439     /* niveau de l'amas (x GN_TAB, puis << 4) : -3,2 dB / corps, comme le Syntakt */

/* DECAY (0..127, pas de 16) -> index de la table d'origine : durees du Syntakt mesurees (notes/16 §6) */
static const unsigned char dec_idx[9] = { 25, 35, 41, 45, 49, 53, 59, 68, 78 };

/* SWEEP -> profondeur du balayage D/2 (Q31), D = 1,04 (SWEEP/127)^1,4 : 9 points, pas de 16 */
static const s32 dh_tab[9] = {
	0x00000000, 0x03a9566e, 0x09a9a617, 0x110bcf47, 0x197fff91,
	0x22d9d50b, 0x2cfc29ad, 0x37d20908, 0x428f5c29,
};
/* SHAPE -> gain de l'amas / 2 (Q31) : -7 / -9,9 / -3,2 / -2,5 dB a 0 / 64 / 110 / 127 (mesures) */
static const s32 gn_tab[9] = {
	0x2952661e, 0x26034783, 0x22f7ff4b, 0x202b1ec1, 0x1d97a691,
	0x26b2fd2c, 0x329bc68e, 0x409c144a, 0x455f0efe,
};

static inline s32 clamp_param(s32 x)
{
	return x < 0 ? 0 : (x > 0x7f00 ? 0x7f00 : x);
}

/* table de 9 points (pas de 0x1000 en 8.8), interpolee */
static inline s32 lut9(const s32 *t, s32 x)
{
	s32 i = x >> 12;
	return t[i] + qmul(t[i + 1] - t[i], (x & 0xfff) << 19);
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
	s32 n, inc0, d, c, es, bm;

	if (dec < 0) dec = 0;
	if (dec > 127) dec = 127;
	bm = dec << 24;                          /* DECAY / 128, Q31 */
	bm = BODY_MUL + qmul(ONE - BODY_MUL, bm);
	/* enveloppe d'ampli d'origine ; le Syntakt a les memes tables, lues a un autre index */
	dec = dec_idx[dec >> 4] + (((dec_idx[(dec >> 4) + 1] - dec_idx[dec >> 4]) * (dec & 15)) >> 4);
	V32(0x250) = LUT_DECAY[dec];
	c = contour * NORM;

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
		U32(S_PH1) = U32(S_PH2) = 0;
		V32(S_EB) = V32(S_EBT) = V32(S_ES) = V32(S_E2E) = ONE;
		V32(S_NX) = V32(S_H1) = V32(S_H2) = V32(S_LP1) = V32(S_LP2) = 0;
		if (!V32(S_RNG))
			V32(S_RNG) = 0x2545f491;
	} else {
		V32(S_EBT) = qmul(V32(S_EBT), bm);
		/* CONTOUR -> duree du 2e mode : tau 15 ms (0) .. 6 ms (127) */
		V32(S_E2E) = qmul(V32(S_E2E), 0x7a6f88a2 - qmul(c, 0x07e0f7c6));
		/* SWEEP -> duree du balayage : 18 ms jusqu'a 74, puis jusqu'a 49 ms a 127 */
		d = sweep - 0x4a00;
		V32(S_ES) = qmul(V32(S_ES), d > 0 ? 0x7b5891f1 + qmul(d * NORM, 0x0703ae5f) : 0x7b5891f1);
	}
	/* CONTOUR -> niveau du 2e mode : 0,45 (0) .. 0,20 (127) ; ecart x2 sur 0-20 ms, comme MENV */
	V32(S_E2T) = qmul(V32(S_E2E), 0x39999999 - qmul(c, 0x20000000));
	if (V32(0x38))
		V32(S_E2) = V32(S_E2T);

	/* hauteur : meme convention que les machines d'origine (PITCH 64 + note du trig) */
	n = ((s32)P16(0x14) << 8) + (((s32)P16(0x22) - 0x4000) << 3) - (64 << 16) + pmod;
	if (n < 0) n = 0;
	if (n > (127 << 16)) n = 127 << 16;
	inc0 = note_inc(n - (69 << 16));

	/* SWEEP -> f = f0 (1 + D env) */
	es = qmul(inc0, qmul(lut9(dh_tab, sweep), V32(S_ES)));
	if (es > ((0x7fffffff - inc0) >> 1))
		V32(S_INCT) = 0x7fffffff;
	else
		V32(S_INCT) = inc0 + (es << 1);
	if (V32(0x38))
		V32(S_INC) = V32(S_INCT);

	/* COLOR -> 2e mode x2 .. x2,8, et amas +1,6 dB ; SHAPE -> force de l'amas */
	color *= NORM;
	V32(S_R2) = qmul(color, 0x66666666);
	V32(S_GN) = qmul(lut9(gn_tab, shape), 0x66666666 + qmul(color, 0x19999999));   /* x0,8 .. x1 */
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
	s32 e2 = V32(S_E2), de2 = (V32(S_E2T) - e2) >> 5;
	s32 eb = V32(S_EB), deb = (V32(S_EBT) - eb) >> 5;
	s32 nx = V32(S_NX), h1 = V32(S_H1), h2 = V32(S_H2), lp1 = V32(S_LP1), lp2 = V32(S_LP2);
	s32 gn = qmul(V32(S_GN), NOISE_G), r2 = V32(S_R2);
	int i;

	for (i = 0; i < 32; i++) {
		s32 body, x, h1o;
		/* corps : fondamental + 2e mode (x2 .. x2,8), qui s'eteint vite */
		ph1 += inc;
		ph2 += (inc << 1) + qmul(inc, r2);
		body = qmul((sine(ph1) >> 1) + qmul(sine(ph2) >> 1, e2), eb);
		/* amas aigu : bruit blanc -> 2 passe-haut 1,5 kHz -> 2 passe-bas ~4,6 kHz */
		rng = rng * 1664525u + 1013904223u;
		x = (s32)rng >> 2;
		h1o = h1;
		h1 = qmul(A_HP, h1 + x - nx);
		nx = x;
		h2 = qmul(A_HP, h2 + h1 - h1o);
		lp1 += qmul(G_LP, h2 - lp1);
		lp2 += qmul(G_LP, lp1 - lp2);
		out[i] = (body >> 1) + (qmul(lp2, gn) << 4);
		inc += dinc;
		e2 += de2;
		eb += deb;
	}
	U32(S_PH1) = ph1; U32(S_PH2) = ph2; U32(S_RNG) = rng;
	V32(S_INC) = V32(S_INCT);
	V32(S_E2) = V32(S_E2T);
	V32(S_EB) = V32(S_EBT);
	V32(S_NX) = nx; V32(S_H1) = h1; V32(S_H2) = h2; V32(S_LP1) = lp1; V32(S_LP2) = lp2;

	/* chaine d'ampli d'origine : enveloppe DECAY/GATE, VCA, PUNCH */
	AMP_ENV(v);
	VCA(out, v);
	PUNCH(out, v);
}
