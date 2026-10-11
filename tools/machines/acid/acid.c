/*
 * Acid : machine ajoutee du Model:Cycles (OS 1.13), une basse facon 303 (notes/51). Moteur en virgule fixe.
 *
 * Contrat de la boucle des voix (notes/14) : update(pmod, v, p) puis render(out, v), une fois par bloc de 32
 * trames a 48 kHz. pmod = note du trig (demi-tons << 16) ; v = voix du Cycles (0x31c o) ; p = parametres de la
 * piste (mots 8.8 : +0x14 PITCH, +0x16 COLOR, +0x18 SHAPE, +0x1a SWEEP, +0x1c CONTOUR, +0x1e PUNCH, +0x22 FINE,
 * +0x24 DECAY) ; v+0x34 / v+0x38 : trig de ce bloc / du bloc precedent ; out : 32 x int32 (Q31).
 *
 * Potards : COLOR = filtre facon DJ (0..63 passe-bas 20 Hz -> 20 kHz, 64 ouvert, 64..127 passe-haut 10 Hz ->
 * 20 kHz, lu en 8.8 pour des balayages sans marches) ; SHAPE = dent de scie -> carre (fondu continu) ; SWEEP =
 * resonance (auto-oscillation en haut de course) ; CONTOUR = enveloppe du filtre, bipolaire (64 : rien,
 * +-6 octaves) ; DECAY = duree de l'enveloppe du filtre (30 ms .. 2 s) et chaine d'ampli d'origine, reglee comme
 * TONE (enveloppe 0x400a9252, VCA 0x400a9430, PUNCH 0x400a967a), comme MACRO ; PUNCH = accent (plus d'attaque
 * dans le filtre, d'enveloppe et de resonance, decroissance du filtre bornee a ~200 ms, +3,5 dB) ; PITCH, FINE
 * et les touches : la note, comme les machines d'origine.
 *
 * Filtre : celui d'Open303 (Robin Schmidt, licence MIT, LICENSE-Open303) : echelle a 4 poles passe-bas, un pole
 * par etage (TPT, sans retard), contre-reaction globale k * y4 passée dans un passe-haut a 150 Hz, coefficients
 * pris dans une table a 1/16 d'octave (200 Hz -> 16,6 kHz, stable sans suréchantillonnage) puis interpolés.
 * Passe-haut : melange des étages (y0 - 4 y1 + 6 y2 - 4 y3 + y4), sans multiplication. Oscillateur : notre dent
 * de scie a polyBLEP ; carre = scie - scie decalee d'une demi-periode, d'ou le fondu scie - m * scie decalee.
 *
 * Formats : signaux Q27 (marge +-16), coefficients Q31 ; qmul = multiplication fractionnaire de l'EMAC, saturee
 * (MACSR = 0xa0 pendant la boucle des voix). Compile avec HOST pour l'ordinateur : meme calcul en entiers
 * (tools/emu/acid_ref.c, la reference de la preuve tools/emu/test_acid.py). Tables : acid_tables.h et
 * acid303_tables.h (le filtre), ecrites par tools/gen_acid.py.
 *
 * Etat : un par piste (BSS de la charge utile, mis a zero au demarrage), remis a zero a la premiere note apres un
 * changement de machine (marque en v+0x2c, effacee par la remise a zero de la voix 0x400a7ab8). Une voix muette
 * (enveloppe d'ampli eteinte, pas de trig) n'est pas calculee.
 */
typedef signed char s8;
typedef short s16;
typedef int s32;
typedef unsigned int u32;

#include "acid_tables.h"
#include "acid303_tables.h"

#define Q31MAX 0x7fffffff

#ifdef HOST
/* l'EMAC en mode fractionnaire : chaque produit entre dans l'accumulateur tronque a 8 bits sous le LSB du resultat
 * (unite 2^-62 : produit >> 23), la lecture tronque (>> 8) puis sature (OMC), comme tools/emu/emac.py */
#include <stdint.h>
static inline int64_t prod(s32 a, s32 b) { return ((int64_t)a * b) >> 23; }
static inline s32 rd(int64_t acc)
{
	acc >>= 8;
	return acc > Q31MAX ? Q31MAX : acc < -(int64_t)Q31MAX - 1 ? (s32)0x80000000 : (s32)acc;
}
static inline s32 qmul(s32 a, s32 b) { return rd(prod(a, b)); }
static inline s32 qmac2(s32 a, s32 b, s32 c, s32 d) { return rd(prod(a, b) + prod(c, d)); }
#else
/* ACC0 rendu vide, comme l'exige l'OS (movclr) */
static inline s32 qmul(s32 a, s32 b)
{
	s32 r;
	__asm__ volatile("mac.l %1,%2,%%acc0\n\tmovclr.l %%acc0,%0" : "=d"(r) : "r"(a), "r"(b));
	return r;
}
static inline s32 qmac2(s32 a, s32 b, s32 c, s32 d)
{
	s32 r;
	__asm__ volatile("mac.l %1,%2,%%acc0\n\tmac.l %3,%4,%%acc0\n\tmovclr.l %%acc0,%0"
			 : "=d"(r) : "r"(a), "r"(b), "r"(c), "r"(d));
	return r;
}
#endif

#define V32(o) (*(s32 *)(v + (o)))
#define P16(o) (*(const s16 *)(p + (o)))

#ifdef HOST
void host_amp(s32 *out, char *v);                 /* la reference : rien (sortie avant la chaine d'ampli) */
#define AMP_DECAY(d) (0)
#else
#define CYC_VOICE0   0x42308828
#define CYC_VSTRIDE  0x31c
#define AMP_ENV(v)   ((void (*)(char *))0x400a9252)(v)
#define VCA(o, v)    ((void (*)(s32 *, char *))0x400a9430)(o, v)
#define PUNCH(o, v)  ((void (*)(s32 *, char *))0x400a967a)(o, v)
#define AMP_DECAY(d) (((const s32 *)0x4011d84c)[d])   /* DECAY -> multiplicateur par bloc (celui de TONE) */
#endif
#define MARK_OFF   0x2c
#define MARK       0x41434431                       /* 'ACD1' */
#define IDLE_LEVEL (1 << 14)                        /* enveloppe d'ampli sous -102 dB : voix muette */

#define OUT_GAIN 751619277                          /* 0,35, comme avant l'echange du filtre */
#define OUT_ACC  1127428915                         /* 0,525 : accent +3,5 dB */

enum { BYPASS, LP, HP };

struct acid {
	u32 ph, dt, invdt;
	s32 m, xg, fenv;
	s32 y0, y1, y2, y3, y4;                         /* etats de l'echelle et de sa sortie, Q27 */
	s32 f1, fh;                                     /* passe-haut de la contre-reaction (150 Hz) */
	s32 n1, n2, n3, n4;                             /* echelle du passe-haut (cascade TPT) */
	s32 mode, b, k, g, og;
};

#ifdef HOST
static struct acid tracks[1];
static inline struct acid *track_of(const char *v) { (void)v; return &tracks[0]; }
#else
static struct acid tracks[6];
static inline struct acid *track_of(const char *v) { return &tracks[((u32)v - CYC_VOICE0) / CYC_VSTRIDE]; }
#endif

static inline s32 knob(s16 x) { s32 k = x >> 8; return k < 0 ? 0 : k > 127 ? 127 : k; }
static inline u32 mag(s32 x) { return x < 0 ? -(u32)x : (u32)x; }
static inline s32 shl_sat(s32 x, int sh)
{
	s32 lim = Q31MAX >> sh;
	return x > lim ? Q31MAX : x < -lim ? -Q31MAX : x << sh;
}

/* 17 points sur la course d'un potard (0..32767), interpolés (comme Open303) */
static inline s32 lut17(const s32 *t, s32 x)
{
	s32 i = x >> 11;
	return t[i] + qmul(t[i + 1] - t[i], (x & 0x7ff) << 20);
}

/* dent de scie a bande limitee (polyBLEP), Q27 dans [-1, 1) */
static inline s32 saw(u32 ph, u32 dt, u32 invdt)
{
	s32 x = (s32)(ph >> 4) - (1 << 27);
	if (ph < dt) {
		s32 w = (s32)(~(ph * invdt) >> 1);      /* 1 - t */
		x += qmul(w, w) >> 4;
	} else if (-ph < dt) {
		s32 w = (s32)(~((-ph) * invdt) >> 1);   /* 1 - r */
		x -= qmul(w, w) >> 4;
	}
	return x;
}

void acid_update(s32 pmod, char *v, const char *p)
{
	struct acid *a = track_of(v);
	s32 acc = P16(0x1e) != 0, dec = knob(P16(0x24));
	s32 col8 = P16(0x16), sweep = knob(P16(0x1a)), cont = knob(P16(0x1c));
	s32 n, oct, r, i, fr, idx, amt, mod;
	u32 d;

	if (V32(MARK_OFF) != MARK) {                    /* 1re note sur cette machine */
		char *z = (char *)a;
		for (u32 k = 0; k < sizeof *a; k++)
			z[k] = 0;
		V32(MARK_OFF) = MARK;
	}
	/* chaine d'ampli d'origine, reglee comme TONE (0x400aa7b8), comme MACRO */
	V32(0x250) = AMP_DECAY(dec);
	if (V32(0x38)) {
		V32(0x274) = V32(0x278) = 0x012c0f26;
		V32(0x280) = V32(0x284) = 0x001f7c5c;
		V32(0x290) = V32(0x294) = 0x7fffffff;
		V32(0x27c) = 0x82581e4b;
		V32(0x288) = 0x803ef8b8;
		if (acc) {
			V32(0x29c) = 0x20000000; V32(0x2a0) = 0x60000000; V32(0x2a4) = 0x20000000;
			V32(0x48) = 1;
		} else {
			V32(0x29c) = 0x7fffffff; V32(0x2a0) = 0x20000000; V32(0x2a4) = 0x20000000;
			V32(0x48) = 0;
		}
		a->fenv = Q31MAX;
	}

	/* note = PITCH - 64 + note du trig + FINE (+-2 demi-tons), comme toutes les machines ; 440 Hz a 69 */
	n = ((s32)P16(0x14) << 8) + (((s32)P16(0x22) - 0x4000) << 3) - (64 << 16) + pmod;
	n = n < 0 ? 0 : n > (127 << 16) ? (127 << 16) : n;
	oct = n / (12 << 16);
	r = n - oct * (12 << 16);
	i = r >> 12;
	fr = r & 0xfff;
	d = (PITCH_TAB[i] + (((PITCH_TAB[i + 1] - PITCH_TAB[i]) * (u32)fr) >> 12)) << oct;
	a->dt = d;
	a->invdt = 0xffffffffu / d;

	a->m = knob(P16(0x18)) * 16909320;              /* SHAPE / 127, Q31 */
	a->xg = acc ? 1932735283 : 1073741824;          /* attaque du filtre : 0,9 / 0,5 */
	a->og = acc ? OUT_ACC : OUT_GAIN;

	/* coupure en pas de table (1/16 d'octave au-dessus de 10 Hz) Q8 : 10 octaves = 40832 ; + 6 octaves d'enveloppe */
	amt = (cont - 64) * 32768 / 63;
	if (acc)
		amt = amt * 13 / 8;
	mod = (24576 * amt) >> 15;
	mod = (mod * (a->fenv >> 16)) >> 15;
	a->fenv = qmul(a->fenv, FDEC_TAB[acc && dec > FDEC_ACCENT_MAX ? FDEC_ACCENT_MAX : dec]);
	col8 = col8 < 0 ? 0 : col8 > (127 << 8) ? (127 << 8) : col8;
	if (col8 < (64 << 8)) {
		a->mode = LP;
		idx = col8 * 40832 / (63 << 8) + 4096 + mod;
	} else if (col8 > (64 << 8)) {
		a->mode = HP;
		/* depuis 10 Hz (notes/51 §3.2) */
		idx = (col8 - (64 << 8)) * 44928 / (63 << 8) + mod;
	} else {
		a->mode = BYPASS;
		return;
	}
	/* notre coupure (1/16 d'octave au-dessus de 10 Hz, Q8 : 256 par pas) dans le pas des tables d'Open303 :
	 * 175 coefficients couvrent 10 Hz -> 16,6 kHz, stabilité vérifiée sans suréchantillonnage */
	s32 lc = idx * 256;
	lc = lc < 0 ? 0 : lc > ((ACID_NCUT - 1) << 16) - 1 ? ((ACID_NCUT - 1) << 16) - 1 : lc;
	i = lc >> 16;
	fr = (lc & 0xffff) << 15;
	a->b = ACID_B0[i] + qmul(ACID_B0[i + 1] - ACID_B0[i], fr);
	r = lut17(ACID_RES, sweep << 8);
	if (acc) {                                      /* accent : resonance +10 % */
		r = r + r / 10 > Q31MAX ? Q31MAX : r + r / 10;
	}
	{
		s32 kf = ACID_KF[i] + qmul(ACID_KF[i + 1] - ACID_KF[i], fr);
		a->k = qmul(kf, r);                         /* k / 128, cf. le decalage dans la contre-reaction */
		/* gain du filtre d'Open303 : ((k/17 - 1) r + 1)(1 + r)/16, compresse dans le fait des etages */
		s32 t = qmul(qmul(kf, ACID_K17) - (1 << 28), r) + (1 << 28);
		a->g = qmul(t, (r >> 1) + (1 << 30));
	}
}

/* Genou de sortie du filtre d'Open303 (acid_out, ramene a notre echelle) : lineaire jusqu'a 1/2, puis
 * 1 (l'echelle d'Open303 rend le tiers de la notre : fois 32, borne avec l'EMAC sature). x : le gain du filtre
 * fois y4, Q27 ; rend Q31. */

void acid_render(s32 *out, char *v)
{
	struct acid *a = track_of(v);
	u32 ph = a->ph, dt = a->dt, invdt = a->invdt;
	s32 m = a->m, xg = a->xg, og = a->og, mode = a->mode;
	s32 y0 = a->y0, y1 = a->y1, y2 = a->y2, y3 = a->y3, y4 = a->y4;
	s32 f1 = a->f1, fh = a->fh;
	s32 n1 = a->n1, n2 = a->n2, n3 = a->n3, n4 = a->n4;
	s32 b = a->b, k = a->k, g = a->g;
	int sh = 4;

	if (!V32(0x34) && !V32(0x38) && mag(V32(0x230)) < IDLE_LEVEL && mag(V32(0x234)) < IDLE_LEVEL) {
		for (int j = 0; j < 32; j++)            /* voix muette : pas calculee */
			out[j] = 0;
		return;
	}
	for (int j = 0; j < 32; j++) {
		s32 x = saw(ph, dt, invdt);
		s32 o;
		x = qmul(x - qmul(m, saw(ph + 0x80000000u, dt, invdt)), xg);   /* scie - m * scie decalee */
		ph += dt;
		if (mode == BYPASS) {
			o = x;
		} else if (mode == LP) {
			s32 fb = qmul(k, y4) << 7;          /* k / 128 dans la table : fois 128 ici */
			fh = qmac2(ACID_HPF_B, fb - f1, ACID_HPF_A, fh);
			f1 = fb;
			y0 = x - fh;
			y1 += qmul(b << 1, y0 - y1 + y2);
			y2 += qmul(b, y1 - (y2 << 1) + y3);
			y3 += qmul(b, y2 - (y3 << 1) + y4);
			y4 += qmul(b, y3 - (y4 << 1));
			/* echelle de sortie d'Open303 : y4 x g, renforce d'un facteur 32 (l'echelle de son y4 est
			 * 32 fois plus petite que la notre), borne avec l'EMAC sature, og par-dessus */
			out[j] = qmul(og, shl_sat(qmul(g, y4), 5));
			continue;
		} else {
			/* passe-haut : cascade TPT en serie avec les memes coefficients, melange binomial (1 - t)^4 ;
			 * contre-reaction sur y4 sans le passe-haut 150 Hz (stable, k < 1 dans les tables) */
			s32 fb = qmul(k, n4);
			s32 u = x - fb;
			s32 w = qmul(b, u - n1);  s32 t1 = n1 + w;  n1 = t1 + w;
			w = qmul(b, t1 - n2);     s32 t2 = n2 + w; n2 = t2 + w;
			w = qmul(b, t2 - n3);     s32 t3 = n3 + w; n3 = t3 + w;
			w = qmul(b, t3 - n4);     s32 t4 = n4 + w; n4 = t4 + w;
			o = u - (t1 << 2) + (t2 << 2) + (t2 << 1) - (t3 << 2) + t4;
		}
		out[j] = shl_sat(qmul(o, og), sh);
	}
	a->ph = ph;
	a->y0 = y0; a->y1 = y1; a->y2 = y2; a->y3 = y3; a->y4 = y4;
	a->f1 = f1; a->fh = fh;
	a->n1 = n1; a->n2 = n2; a->n3 = n3; a->n4 = n4;
#ifdef HOST
	host_amp(out, v);
#else
	AMP_ENV(v);
	VCA(out, v);
	PUNCH(out, v);
#endif
}
