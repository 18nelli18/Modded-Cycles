/*
 * MODAL : le coeur du son, en virgule fixe, sans FPU.
 *
 * Reecriture de la Part de Rings (Emilie Gillet, Mutable Instruments, 2015, licence MIT : LICENSE-Rings) et de
 * ce qu'elle utilise de stmlib : resonateur modal (filtres passe-bande), cordes (Karplus-Strong, dispersion,
 * cordes sympathiques, accords), voix FM, excitateurs internes (impulsion filtree, bruit pince), reverbe, filtre
 * de note, limiteur. Memes calculs, dans le meme ordre, au meme rythme ; bloc de 32 trames (le Cycles) au lieu
 * de 24 ; reglages « eco » (notes/74) : la moitie des modes de Rings, 4 cordes au lieu de 8. Le synthe cache de
 * Rings (StringSynthPart, « easter egg ») n'y est pas.
 *
 * Ce fichier sert deux fois : compile pour le Cycles (modal.c, -mcpu=54418, l'EMAC) et pour l'ordinateur
 * (tools/emu/modal_host.c) avec la meme arithmetique a l'octet pres (modal_fix.h) ; la preuve
 * (tools/emu/test_modal_dsp.py) compare a Rings en flottant (tools/emu/rings_ref.cc).
 *
 * Formats : signaux 1,0 = 2^24 (UNIT) ; potards Q31 (0..1) ; hauteurs en demi-tons << 16 ; frequences
 * normalisees (f / 48 kHz) en Q31 ou en xf ; retards en echantillons, Q11.20.
 */
#ifndef MODAL_DSP_H
#define MODAL_DSP_H

#include "modal_fix.h"

#define MB          32                               /* trames par bloc */
#define UNIT        (1 << 24)
#define MAXPOLY     4
#define NSTRINGS    4                                /* eco : 4 cordes au lieu de 8 */
#define MAXMODES    32                               /* eco : 30 modes au plus ((64 / polyphonie - 4) / 2) ; modal_asm.S */
#define DLINE       2048                             /* kDelayLineSize */
#define SLINE       1024
#define RV_SIZE     32768

enum { MODEL_MODAL, MODEL_SYMPATHETIC, MODEL_STRING, MODEL_FM, MODEL_SYMPATHETIC_Q, MODEL_STRING_REVERB, MODEL_N };

#define Q31(x)      ((s32)((x) * 2147483648.0 + 0.5))

/* ---- tables en memoire (modal_init_tables) ---------------------------------------------------------------- */

static s16 m_sine[4097];                             /* lut_sine, Q15 */
static s32 m_soft[514];                              /* SoftLimit(x), x = 0..4 par pas de 1/128, en UNIT */

/* sin(2 pi i / 4096), par la serie de Taylor jusqu'a x^11 sur [0, pi/2] (erreur < 1e-7), puis les symetries */
static s32 m_ready;                                  /* entrees des tables deja calculees (MODAL_TABLES : fini) */
#define MODAL_TABLES (1025 + 514)

/* un morceau des tables (128 sinus ou 48 points du limiteur, moins de 10 000 instructions) : rend 1 quand tout est
 * pret. Calculees d'un coup a la premiere note, elles prendraient tout un bloc (le son craquerait). */
static int modal_init_step(void)
{
	int i, end;

	if (m_ready < 1025) {
		end = m_ready + 128 > 1025 ? 1025 : m_ready + 128;
		for (i = m_ready; i < end; i++) {
		s32 z = (s32)(1647099u * (u32)i);            /* x = pi/2 x i/1024 en Q30, soit x/2 en Q31 */
		s32 x2 = qmul(z, z), p, v;                   /* x^2 / 4 */
		/* sin(x) / x = 1 - x^2/6 (1 - x^2/20 (1 - x^2/42 (1 - x^2/72 (1 - x^2/110)))) */
		p = Q31ONE - qmul(x2, Q31(4.0 / 110));
		p = Q31ONE - qmul(qmul(x2, Q31(4.0 / 72)), p);
		p = Q31ONE - qmul(qmul(x2, Q31(4.0 / 42)), p);
		p = Q31ONE - qmul(qmul(x2, Q31(4.0 / 20)), p);
		p = Q31ONE - qmul(qmul(x2, Q31(4.0 / 6)), p);
		v = (qmul(z, p) + (1 << 14)) >> 15;          /* sin(x) / 2 en Q31 -> Q15 */
		if (v > 32767)
			v = 32767;
		m_sine[i] = (s16)v;
		m_sine[2048 - i] = (s16)v;
		m_sine[2048 + i] = (s16)-v;
		m_sine[(4096 - i) & 4095] = (s16)-v;
		}
		m_sine[0] = m_sine[2048] = m_sine[4096] = 0;
		m_ready = end;
		return 0;
	}
	end = m_ready + 48 > MODAL_TABLES ? MODAL_TABLES : m_ready + 48;
	for (i = m_ready - 1025; i < end - 1025; i++) {
		/* x (27 + x^2) / (27 + 9 x^2), x = i / 128 */
		xf x = xfrom(i, 7), x2 = xmul(x, x);
		xf n = xmul(x, xadd(XC(M_27), x2));
		xf d = xadd(XC(M_27), xmul(XC(M_9), x2));
		m_soft[i] = xto(xmul(n, xrecip(d)), 24);
	}
	m_ready = end;
	return m_ready == MODAL_TABLES;
}

static __attribute__((unused)) void modal_init_tables(void)    /* d'un coup (l'ordinateur, les bancs) */
{
	while (!modal_init_step())
		;
}

static __attribute__((noinline)) s32 softlimit_big(s32 a)  /* |x| >= 4 */
{
	xf v = xfrom(a, 24), v2 = xmul(v, v);
	return xto(xmul(xmul(v, xadd(XC(M_27), v2)), xrecip(xadd(XC(M_27), xmul(XC(M_9), v2)))), 24);
}

static inline s32 softlimit(s32 x)                    /* x en UNIT */
{
	s32 a = iabs(x), i, y;

	if (a >= 4 * UNIT) {
		y = softlimit_big(a);
	} else {
		i = a >> 17;
		y = m_soft[i] + qmul(m_soft[i + 1] - m_soft[i], shl(a, 14) & Q31ONE);
	}
	return x < 0 ? -y : y;
}

/* ---- petits elements ---------------------------------------------------------------------------------------- */

static u32 rng_next(u32 *s)                          /* stmlib Random::GetWord */
{
	*s = *s * 1664525u + 1013904223u;
	return *s;
}

static inline s32 rng_q31(u32 *s)                     /* 2 GetFloat() - 1, en Q31 */
{
	return (s32)(rng_next(s) ^ 0x80000000u);
}

/* oscillateur de cosinus lent (CosineOscillator des LFO de Rings), par accumulateur de phase : Next() rend
 * 0,5 + 0,5 cos(n theta), n = 0, 1, 2... ; value() le dernier rendu */
struct lfo {
	u32 ph, inc;
	s32 val;                                         /* Q31 */
};

static s32 cos_q31(u32 ph)                           /* 0,5 + 0,5 cos, Q31 */
{
	u32 p = ph + 0x40000000u;                        /* cos = sin(+ 1/4 de tour) */
	s32 i = p >> 20, f = (s32)((p << 11) & 0x7fffffffu);
	s32 a = m_sine[i], b = m_sine[i + 1];
	s32 s = shl(a, 16) + qmul(shl(b - a, 16), f);  /* Q31 */
	return (s >> 1) + 0x40000000;
}

static void lfo_init(struct lfo *l, u32 inc)
{
	l->ph = 0;
	l->inc = inc;
	l->val = cos_q31(0u - inc);
}

static s32 lfo_next(struct lfo *l)
{
	l->val = cos_q31(l->ph);
	l->ph += l->inc;
	return l->val;
}

/* filtre a variable d'etat (stmlib Svf), forme de Simper : v1 = bp, v2 = lp ; b = 1 - a1 */
struct svf {
	s32 b, a2, a3;                                   /* Q31 */
	s32 ic1, ic2;
};

/* coefficients depuis g et r = 1 / resonance */
static __attribute__((noinline)) void svf_set(struct svf *f, xf g, xf r, xf *a2x, xf *a3x)
{
	xf e = xmul(g, xadd(g, r));
	xf a1 = xrecip(xadd(xmk(1 << 30, 0), e));
	xf a2 = xmul(g, a1), a3 = xmul(g, a2);
	f->b = xto(xmul(e, a1), 31);
	f->a2 = xto(a2, 31);
	f->a3 = xto(a3, 31);
	if (a2x) {
		*a2x = a2;
		*a3x = a3;
	}
}

/* tangentes de stmlib (OnePole::tan), f en Q31 (<= 0,5) -> g */
static __attribute__((noinline)) xf tan_dirty(s32 f)
{
	s32 t = qmul(f, f);                              /* Q31 */
	s32 p = M_PI27 + qmul(t, M_TD_A27);              /* Q27 */
	xf fx = xfrom(f, 31);
	return xmul(fx, xfrom(p, 27));
}


static __attribute__((noinline)) xf tan_accurate(s32 f)
{
	s32 t = qmul(f, f), p;                          /* Q31 */
	p = M_TA_D21 + shl(qmul(t, M_TA_E19), 2);       /* Q21 */
	p = M_TA_C21 + qmul(t, p);
	p = M_TA_B21 + qmul(t, p);
	p = M_TA_A21 + qmul(t, p);
	p = (M_PI27 >> 6) + qmul(t, p);
	return xmul(xfrom(f, 31), xfrom(p, 21));
}

static void svf_reset(struct svf *f)
{
	f->ic1 = f->ic2 = 0;
}

#ifdef MODAL_ASM
void modal_svf_lp(struct svf *f, s32 *x, s32 p2, s32 p3);          /* svf_lp_block sur MB trames : modal_asm.S */
#endif

/* Process<LOW_PASS> sur un bloc, en place ; p2, p3 : une impulsion a la 1re trame (a2 x P, a3 x P), que le
 * format des signaux ne pourrait pas porter en entree */
static void svf_lp_block(struct svf *f, s32 *x, int n, s32 p2, s32 p3)
{
#ifdef MODAL_ASM
	if (n == MB) {                                   /* modal_asm.S */
		modal_svf_lp(f, x, p2, p3);
		return;
	}
#endif
	{
	s32 b = -f->b, a2 = f->a2, a3 = f->a3, ic1 = f->ic1, ic2 = f->ic2;
	int k;

	for (k = 0; k < n; k++) {
		s32 v3 = x[k] - ic2;
		s32 t1 = qmac2(b, ic1, a2, v3);
		s32 t2 = qmac2(a2, ic1, a3, v3);
		if (k == 0) {
			t1 += p2;
			t2 += p3;
		}
		ic1 += shl(t1, 1);
		ic2 += t2;
		x[k] = ic2;
		ic2 += t2;
	}
	f->ic1 = ic1;
	f->ic2 = ic2;
	}
}

static inline s32 svf_lp(struct svf *f, s32 x)
{
	s32 v3 = x - f->ic2;
	s32 t1 = qmac2(-f->b, f->ic1, f->a2, v3);
	s32 t2 = qmac2(f->a2, f->ic1, f->a3, v3);
	s32 lp = f->ic2 + t2;
	f->ic1 += shl(t1, 1);
	f->ic2 = lp + t2;
	return lp;
}

static inline s32 svf_lpr(struct svf *f, s32 x)     /* svf_lp, produits arrondis */
{
	s32 v3 = x - f->ic2;
	s32 t1 = qmac2r(-f->b, f->ic1, f->a2, v3);
	s32 t2 = qmac2r(f->a2, f->ic1, f->a3, v3);
	s32 lp = f->ic2 + t2;
	f->ic1 += shl(t1, 1);
	f->ic2 = lp + t2;
	return lp;
}

struct dcblock {
	s32 x, y, pole;
	u32 f;                                           /* partie fractionnaire de y, en 2^-31 LSB */
};

static void dc_init(struct dcblock *d, s32 pole)
{
	d->x = d->y = 0;
	d->f = 0;
	d->pole = pole;
}

/* DCBlocker de stmlib : y = y pole + x - x1. Le pole est a 2e-4 de 1 : arrondi a chaque echantillon, y pole
 * redonnerait y sous 0,5 / (1 - pole) LSB (2 400 LSB), et un reste continu ne s'eteindrait jamais (il entrerait sans
 * fin dans les cordes). La partie fractionnaire de y pole (les bits sous le LSB, le produit entier modulo 2^31) est
 * donc gardee d'un echantillon a l'autre : le filtre suit l'arithmetique exacte. */
static inline s32 dc_one(struct dcblock *d, s32 x)
{
	s32 hi = qmul(d->y, d->pole);                    /* plancher de y pole */
	u32 f = d->f + (((u32)d->y * (u32)d->pole) & 0x7fffffffu);
	s32 y = hi + (s32)(f >> 31) + x - d->x;
	d->f = f & 0x7fffffffu;
	d->x = x;
	d->y = y;
	return y;
}

static s32 b2mb(s32 b)                               /* b (2 - b), Q31, b dans [0, 1] */
{
	s32 r = shl(qmul(b, 0x40000000 - (b >> 2)), 2);  /* b (1 - b/2) en Q30, x 4 */
	return r < 0 ? Q31ONE : r;
}

/* Tampons de calcul, en variables et non sur la pile : la boucle des voix tourne dans l'interruption audio, sur la
 * pile de la tache interrompue, dont on ne connait pas la marge (MACRO et ACID restent sous 350 o). Jamais deux
 * calculs a la fois : l'interruption n'est pas reentrante. */
static struct {
	s32 x[MB + 1], ck[MB], y0[MB], y1[MB];           /* x : modal_asm.S (+1 : lu, inutilise, par modal_modes) */
	s32 zero[MB];                                    /* entree nulle (modal_str_read) */
	s32 so[MB + 1], sa[MB + 1];                      /* modal_modes : sommes des amp ic1 / 2, modes pairs, impairs */
	s32 amp[2 * MAXMODES];                           /* position qui bouge : amplitude au debut, pas (modal_modes_lin) */
} sc;

/* ---- resonateur modal (rings/dsp/resonator.cc) --------------------------------------------------------------- */

#define MODE_EPS 64                                   /* 2^-18 : -108 dB */

/* Un mode : le passe-bande d'etat variable de Rings (stmlib Svf, forme trapezoidale, Process<BAND_PASS>), avec ses
 * etats ic1 et ic2 tenus dans deux accumulateurs de l'EMAC pendant le bloc (8 bits sous le LSB) :
 *   v3 = x - ic2 ; ic1 += 2 (-b ic1 + a2 v3) ; ic2 += 2 (a2 ic1 + a3 v3)
 * et la sortie v1 = (ic1 + ic1') / 2 : pour une amplitude fixe, la somme sur les modes de amp ic1 / 2 a chaque
 * echantillon (sc.so, sc.sa), puis o[k] = s[k] + s[k + 1] une fois pour tous les modes (notes/74 §5.2). */
struct mode {
	s32 b, a2, a3, ic1, ic2;                         /* cet ordre : modal_asm.S */
};
struct plucker;

#ifdef MODAL_ASM
void modal_modes(struct mode *md, int n, const s32 *x, s32 *so, s32 *sa, const s32 *amp, int quiet);
void modal_modes_lin(struct mode *md, int n, const s32 *x, s32 *ob, s32 *ab, const s32 *amp);
typedef char modal_maxmodes_32[MAXMODES == 32 ? 1 : -1];  /* modal_modes_lin lit le pas a amp + 32 mots */
void modal_str_read(const s32 *ph, s32 f, const s32 *in, s32 *hb, int n);
void modal_str_damp(s32 *hb, s32 *dk);
void modal_str_write(const s32 *hb, s32 *pw, s32 *out, const s32 *dpp, int n);
void modal_str_read_ap(const s32 *ph, s32 f, s32 *hb, int n, s32 *ap);
void modal_str_read_mv(const s32 *pw, s32 *st, const s32 *in, s32 *hb, int n);
void modal_str_damp_mv(s32 *hb, s32 *dk);
void modal_str_write_mv(const s32 *hb, s32 *pw, s32 *out, s32 *dpp, int n);
void modal_dc_in(struct dcblock *d, s32 *hb, const s32 *in);
#endif

struct resonator {
	struct mode md[MAXMODES];
	/* la 1re passe de reso_compute (frequences des partiels, tangentes), gardee tant que frequence et structure ne
	 * changent pas : BRIGHTNESS et DAMPING ne refont que les facteurs de qualite */
	s32 kv1, ks, knum, kfresh;
	xf kf;
	s32 kpq[MAXMODES], kpfm[MAXMODES], kpfe[MAXMODES], kgm[MAXMODES], kge[MAXMODES];
	s32 amp[MAXMODES];                               /* amplitudes (position fixe), Q31 */
	s32 resolution, nmodes;
	xf frequency;
	s32 structure, brightness, damping, position, prev_position;
	/* entrees du dernier ComputeFilters */
	xf cf;
	s32 cs, cb, cd, valid, amp_pos;
};

static void reso_init(struct resonator *r, int resolution)
{
	int i;

	for (i = 0; i < MAXMODES; i++)
		r->md[i].ic1 = r->md[i].ic2 = 0;
	r->frequency = XC(M_F220);
	r->structure = Q31(0.25);
	r->brightness = Q31(0.5);
	r->damping = Q31(0.3);
	r->position = M_0999;
	r->prev_position = 0;
	resolution -= resolution & 1;
	r->resolution = resolution > MAXMODES ? MAXMODES : resolution;
	r->valid = 0;
	r->kv1 = 0;
	r->amp_pos = -1;
}

/* CosineOscillator<APPROXIMATE>(position) : la constante c (Q29) ; Next() rend 0,5 + y0, y0' = c y0 - y1 */
static s32 amp_coef(s32 pos)
{
	s32 f = pos - 0x20000000, c;                     /* position - 0,25 */
	int sign = 1;

	if (f < 0)
		f = -f;
	else if (f > 0x40000000)
		f -= 0x40000000;
	else
		sign = -1;
	c = shl(qmul(f, 0x40000000 - f), 3);             /* 16 f (1 - 2 f) */
	return sign < 0 ? -c : c;
}

static void reso_amps(s32 *amp, s32 pos, int n)
{
	s32 c = amp_coef(pos), y1 = c, y0 = 0x40000000, t;   /* y1 = c / 4 en Q31 */
	int i;

	for (i = 0; i < n; i++) {
		t = y0;
		y0 = shl(qmul(c, y0), 2) - y1;
		y1 = t;
		t += 0x40000000;
		amp[i] = t < 0 ? Q31ONE : t;                 /* 1,0 : sature */
	}
}

/* tan_fast de stmlib (OnePole::tan<FREQUENCY_FAST>), f en Q31 (<= 0,5) -> g, en valeurs positives */
static inline __attribute__((always_inline)) xf tan_fast(s32 f)
{
	s32 t = qmul(f, f);
	s32 in = M_TF_A26 + shl(qmul(t, M_TF_B25), 1);  /* Q26 */
	s32 p = M_PI27 + shl(qmul(t, in), 1);           /* Q27 */
	return xmulp(xfromp(f, 31), xfromp(p, 27));
}

/* svf_set en ligne pour un mode (g, r = 1 / resonance), en valeurs positives ; b = e / (1 + e) = 1 - a1 (un produit
 * de moins, 2 LSB au plus d'ecart avec e a1) */
static inline __attribute__((always_inline)) void mode_set(struct mode *m, xf g, xf rq)
{
	xf a1 = xrecipp(xaddp(xmk(1 << 30, 0), xmulp(g, xaddp(g, rq))));
	xf a2 = xmulp(g, a1);

	m->b = Q31ONE - xtop(a1, 31);
	m->a2 = xtop(a2, 31);
	m->a3 = xtop(xmulp(g, a2), 31);
}

/* ComputeFilters de Rings, refait quand ses entrees changent. 1re passe (frequence ou structure changee) : les
 * frequences des partiels, leur nombre sous 0,49 (num) ; 2e : les facteurs de qualite et les coefficients des seuls
 * modes calcules (reso_process en fait (num + 1) & ~1). Les memes valeurs pour ceux-la que la boucle unique de Rings. */
static int reso_compute(struct resonator *r)
{
	s32 q_loss, rate, ba, br, i, n, num;
	xf q;

	if (r->valid && r->cf.m == r->frequency.m && r->cf.e == r->frequency.e && r->cs == r->structure
	    && r->cb == r->brightness && r->cd == r->damping)
		return r->nmodes;
	if (!r->kv1 || r->kf.m != r->frequency.m || r->kf.e != r->frequency.e || r->ks != r->structure) {
		s32 stiffness = interp(M_STIFF, r->structure, 8), stretch = 1 << 24;   /* Q29, Q24 */
		xf harmonic = r->frequency;
		num = 0;
		for (i = 0; i < r->resolution; i++) {
			xf pf = xmulp(harmonic, xfromp(stretch, 24));
			if (pf.e > M_049_E || (pf.e == M_049_E && pf.m >= M_049_M)) {     /* pf >= 0,49 (pf > 0) */
				r->kpq[i] = M_049Q;
				pf = XC(M_049);
			} else {
				r->kpq[i] = xtop(pf, 31);
				num = i + 1;
			}
			r->kpfm[i] = pf.m;
			r->kpfe[i] = pf.e;
			stretch += stiffness >> 5;
			stiffness = qmul(stiffness, stiffness < 0 ? Q31(0.93) : Q31(0.98));
			harmonic = xaddp(harmonic, r->frequency);
		}
		r->knum = num;
		r->kf = r->frequency;
		r->ks = r->structure;
		r->kv1 = 1;
		r->kfresh = 1;                           /* tangentes a refaire */
	}
	num = r->knum;
	n = (num + 1) & ~1;
	if (n > r->resolution)
		n = r->resolution;
	q = xmul(XC(M_500), xfrom(interp(M_DEC4, r->damping, 8), 17));
	ba = Q31ONE - r->structure;
	ba = qmul(ba, ba);
	ba = qmul(ba, ba);
	ba = qmul(ba, ba);
	br = qmul(r->brightness, Q31ONE - qmul(ba, Q31(0.2)));
	q_loss = qmul(b2mb(br), Q31(0.85)) + Q31(0.15);
	rate = qmul(b2mb(r->structure), Q31(0.1));
	for (i = 0; i < n; i++) {
		xf g;
		if (r->kfresh) {
			g = tan_fast(r->kpq[i]);
			r->kgm[i] = g.m;
			r->kge[i] = g.e;
		} else {
			g = xmk(r->kgm[i], r->kge[i]);
		}
		mode_set(&r->md[i], g, xrecipp(xaddp(xmk(1 << 30, 0), xmulp(xmk(r->kpfm[i], r->kpfe[i]), q))));
		q_loss += qmul(rate, Q31ONE - q_loss);
		q = xmulp(q, xfromp(q_loss, 31));
	}
	r->kfresh = 0;
	r->cf = r->frequency;
	r->cs = r->structure;
	r->cb = r->brightness;
	r->cd = r->damping;
	r->valid = 1;
	r->nmodes = num;
	return num;
}

#ifndef MODAL_ASM
#ifdef __mcoldfire__
#error "MODAL : les modes du resonateur sont en assembleur sur le ColdFire (modal_asm.S, -DMODAL_ASM)"
#endif
/* modal_modes et modal_modes_lin en C : les memes produits dans les memes accumulateurs (des sommes exactes, que
 * l'ordre ne change pas), lus aux memes moments. */
static void mode_fix(struct mode *m, const s32 *x, s32 *s, s32 amp)
{
	acc_t a = acc_ld(m->ic1), c = acc_ld(m->ic2);
	s32 nb = -m->b, r1, r2, v3;
	int k;

	for (k = 0; k < MB; k++) {
		r1 = acc_rd(a);
		r2 = acc_rd(c);
		s[k] = (s32)((u32)s[k] + (u32)acc_rd(empr(amp, r1)));
		v3 = (s32)((u32)x[k] - (u32)r2);
		a += emp1(nb, r1) + emp1(m->a2, v3);
		c += emp1(m->a2, r1) + emp1(m->a3, v3);
	}
	r1 = acc_rd(a);
	s[MB] = (s32)((u32)s[MB] + (u32)acc_rd(empr(amp, r1)));
	m->ic1 = r1;
	m->ic2 = acc_rd(c);
}

/* amplitude a + (k + 1) da a l'echantillon k : o[k] += (a ic1[k] + a ic1[k + 1]) / 2 */
static void mode_lin(struct mode *m, const s32 *x, s32 *o, s32 a, s32 da)
{
	acc_t s1 = acc_ld(m->ic1), c = acc_ld(m->ic2);
	s32 nb = -m->b, r1, r2, v3, prev = 0;
	int k;

	for (k = 0; k <= MB; k++) {
		r1 = acc_rd(s1);
		if (k > 0)
			o[k - 1] = (s32)((u32)o[k - 1] + (u32)acc_rd(empr(a, prev) + empr(a, r1)));
		if (k == MB)
			break;
		prev = r1;
		a += da;
		r2 = acc_rd(c);
		v3 = (s32)((u32)x[k] - (u32)r2);
		s1 += emp1(nb, r1) + emp1(m->a2, v3);
		c += emp1(m->a2, r1) + emp1(m->a3, v3);
	}
	m->ic1 = r1;
	m->ic2 = acc_rd(c);
}
#endif

/* Position fixe : une table d'amplitudes, comme Rings. Position qui bouge (SWEEP tourne ou module) : Rings refait
 * la recurrence des amplitudes a chaque echantillon pour chaque mode ; ici, les amplitudes du debut et de la fin du
 * bloc, et l'interpolation lineaire entre les deux, une addition par echantillon (l'ecart est de l'ordre du carre du
 * pas de la position sur un bloc : negligeable pour une position qui bouge lentement). */
static void reso_process(struct resonator *r, const s32 *in, s32 *out, s32 *aux)
{
	int num = reso_compute(r), n = (num + 1) & ~1, i, k, quiet = 1;
	s32 *x = sc.x, *so = sc.so, *sa = sc.sa, *a0 = sc.amp, *da = sc.amp + MAXMODES;
	s32 inc = (r->position - r->prev_position) / MB, p0 = r->prev_position + inc, pstart = r->prev_position;

	r->prev_position += MB * inc;
	for (k = 0; k < MB; k++) {
		x[k] = in[k] >> 3;
		out[k] = aux[k] = 0;
		if (x[k] > 2 || x[k] < -2)
			quiet = 0;
	}
	if (!n)
		return;
	if (inc) {
		reso_amps(a0, pstart, n);                    /* amplitudes au debut et a la fin du bloc */
		reso_amps(da, r->prev_position, n);
		for (i = 0; i < n; i++)
			da[i] = (da[i] - a0[i]) >> 5;
		r->amp_pos = -1;
#ifdef MODAL_ASM
		modal_modes_lin(r->md, n, x, out, aux, a0);  /* modal_asm.S */
#else
		for (i = 0; i < n; i++)
			mode_lin(&r->md[i], x, (i & 1) ? aux : out, a0[i], da[i]);
#endif
		return;
	}
	if (r->amp_pos != p0) {
		reso_amps(r->amp, p0, MAXMODES);
		r->amp_pos = p0;
	}
	for (k = 0; k <= MB; k++)
		so[k] = sa[k] = 0;
#ifdef MODAL_ASM
	modal_modes(r->md, n, x, so, sa, r->amp, quiet); /* modal_asm.S */
#else
	for (i = 0; i < n; i++) {                        /* mode eteint, sans entree : sa part est sous -108 dB, on */
		struct mode *m = &r->md[i];              /* ne le calcule plus (Rings le calcule) */
		if (quiet && iabs(m->ic1) < MODE_EPS && iabs(m->ic2) < MODE_EPS)
			continue;
		mode_fix(m, x, (i & 1) ? sa : so, r->amp[i]);
	}
#endif
	for (k = 0; k < MB; k++) {
		out[k] = (s32)((u32)so[k] + (u32)so[k + 1]);
		aux[k] = (s32)((u32)sa[k] + (u32)sa[k + 1]);
	}
}

/* ---- corde (rings/dsp/string.cc) --------------------------------------------------------------------------- */

/* La ligne a retard est doublee (chaque echantillon ecrit a wp et a wp + DLINE) : les lectures a moins de DLINE
 * echantillons se font sans masque. */
struct mstring {
	s32 frequency;                                   /* Q31 */
	s32 dispersion;                                  /* Q30 */
	s32 brightness, damping, position;              /* Q31 */
	s32 delay;                                       /* Q11.20 */
	s32 clamped_position, prev_dispersion, prev_damp_comp;
	s32 enable_dispersion;
	s32 dispersion_noise, curved_bridge;            /* UNIT */
	s32 src_phase;                                   /* Q29 */
	s32 out0, out1, aux0, aux1;
	s32 wp, swp, fill, sfill;
	s32 fx1, fx2, fbr, fdmp;                         /* DampingFilter */
	struct svf iir;
	struct dcblock dc;
	/* calculs par bloc, gardes tant que frequence, amortissement et brillance ne changent pas */
	s32 kf, kd, kb, kvalid;
	s32 kdisp_valid, kdisp, ksp, kna, kbc, kac, kapg;  /* disp_coefs, gardes tant que la dispersion ne change pas */
	s32 k_delay, k_unit, k_ratio, k_dcoef, k_bright, k_nfilt, k_dcomp, k_nk;
	s32 line[2 * DLINE];
	s32 stretch[SLINE];
};

static void str_init(struct mstring *s, int dispersion)
{
	s->enable_dispersion = dispersion;
	s->wp = s->swp = 0;
	s->fill = s->sfill = 0;
	s->fx1 = s->fx2 = s->fbr = s->fdmp = 0;
	svf_reset(&s->iir);
	s->iir.b = s->iir.a2 = s->iir.a3 = 0;
	s->frequency = M_F220Q;
	s->dispersion = 0x10000000;                      /* 0,25 */
	s->brightness = Q31(0.5);
	s->damping = Q31(0.3);
	s->position = Q31(0.8);
	s->delay = M_D220;                               /* 1 / (220 / 48000) */
	s->clamped_position = 0;
	s->prev_dispersion = 0;
	s->dispersion_noise = 0;
	s->curved_bridge = 0;
	s->prev_damp_comp = 0;
	s->out0 = s->out1 = s->aux0 = s->aux1 = 0;
	s->src_phase = 0;
	s->kvalid = 0;
	s->kdisp_valid = 0;
	dc_init(&s->dc, M_POLE20);
}

/* DampingFilter de Rings : y = damping (h0 x1 + h1 (x + x2)), h0 = (1 + b) / 2, h1 = (1 - b) / 4. Ici
 * damping x h0 et damping x h1 d'abord (arrondis), puis une seule somme : le chemin rapide en assembleur
 * (modal_asm.S) tient ainsi dans les registres du ColdFire ; un LSB d'ecart avec un produit apres la somme. */
static inline s32 fir_h0(s32 fdmp, s32 fbr)
{
	return qmulr(fdmp, 0x40000000 + (fbr >> 1));
}

static inline s32 fir_h1(s32 fdmp, s32 fbr)
{
	return qmulr(fdmp, 0x20000000 - (fbr >> 2));
}

static inline s32 fir_damp(s32 fdmp, s32 fbr, s32 x1, s32 x0x2)
{
	return qmac2r(fir_h0(fdmp, fbr), x1, fir_h1(fdmp, fbr), x0x2);
}

/* ReadHermite : t = wp + partie entiere du retard (sans masque : t + 2 < 2 DLINE) */
static inline s32 hermite(const s32 *p, s32 f)
{
	s32 xm1 = p[-1], x0 = p[0], x1 = p[1], x2 = p[2];
	s32 c = (x1 - xm1) >> 1, v = x0 - x1, w = c + v;
	s32 a = w + v + ((x2 - x0) >> 1), bn = w + a;
	return qmulr(qmulr(qmulr(a, f) - bn, f) + c, f) + x0;
}

static inline s32 rd_hermite(const s32 *line, s32 wp, s32 delay)  /* avec masque */
{
	s32 t = wp + (delay >> 20) + DLINE, f = shl(delay, 11) & Q31ONE;
	s32 xm1 = line[(t - 1) & (DLINE - 1)], x0 = line[t & (DLINE - 1)];
	s32 x1 = line[(t + 1) & (DLINE - 1)], x2 = line[(t + 2) & (DLINE - 1)];
	s32 c = (x1 - xm1) >> 1, v = x0 - x1, w = c + v;
	s32 a = w + v + ((x2 - x0) >> 1), bn = w + a;
	return qmulr(qmulr(qmulr(a, f) - bn, f) + c, f) + x0;
}

static inline s32 rd_linear(const s32 *line, s32 mask, s32 wp, s32 delay)
{
	s32 i = wp + (delay >> 20), f = shl(delay, 11) & Q31ONE;
	s32 a = line[i & mask], b = line[(i + 1) & mask];
	return a + qmul(b - a, f);
}

/* les termes de la dispersion (par echantillon dans Rings, ici seulement quand elle change) */
struct dispk {
	s32 disp, sp, na, bc, ac, apg;
};

/* le gain du passe-tout de l'etirement : -0,618 disp / (0,15 + |disp|), Q31 ; disp en Q30. En virgule fixe (1 / den
 * par une division 32/32 et une iteration de Newton, comme xrecip) : il se refait a chaque echantillon quand la
 * dispersion bouge, comme dans Rings */
static s32 disp_apg(s32 disp)
{
	s32 a = iabs(disp), den = a + 161061274, m, z, t, r;  /* 0,15 en Q30 */
	int n;

	if (!disp)
		return 0;
	n = __builtin_clz((u32)den) - 1;                 /* den dans [0,15, 1,15] : n de 1 a 3 */
	m = shl(den, n);                                 /* [2^30, 2^31) */
	z = (s32)((0xffffffffu / (u32)(m >> 15)) << 13); /* 1 / m en Q30 */
	t = (s32)(0x80000000u - (u32)shl(qmul(m, z), 1));
	z = shl(qmul(z, t), 1);
	r = shl(qmul(shl(a, n), z), 2);                  /* a / den en Q31 (a 2^n <= den 2^n < 2^31) */
	r = qmul(r, Q31(0.618));
	return disp > 0 ? -r : r;
}

static __attribute__((noinline)) void disp_coefs(struct dispk *k, s32 disp)    /* disp en Q30 */
{
	s32 na, bc;

	k->disp = disp;
	k->sp = disp <= 0 ? 0 : qmul(b2mb(disp >= 0x40000000 ? Q31ONE : shl(disp, 1)), Q31(0.475));
	na = disp > 0x30000000 ? (disp >= 0x40000000 ? Q31ONE : shl(disp - 0x30000000, 3)) : 0;
	k->na = qmul(qmul(na, na), Q31(0.025));
	bc = disp < 0 ? shl(-disp, 1) : 0;               /* Q31 */
	k->ac = bc;
	k->bc = qmul(qmul(bc, bc), Q31(0.01));
	k->apg = disp_apg(disp);
}

/* les calculs par bloc de String::ProcessInternal */
static __attribute__((noinline)) void str_block(struct mstring *s)
{
	s32 delay, src_ratio, lf, dcoef, bright, nfilt, dcut, df, b16;
	xf fx = xfrom(s->frequency, 31), dx, rt60, base;
	int unit;

	dx = xrecip(fx);
	delay = xto(dx, 20);
	if (delay < (4 << 20))
		delay = 4 << 20;
	else if (delay > ((DLINE - 4) << 20))
		delay = (DLINE - 4) << 20;
	unit = delay < ((DLINE - 4) << 20) || xcmp(xfrom(delay, 20), dx) >= 0;
	src_ratio = 1 << 29;                             /* Q29 */
	if (!unit) {
		src_ratio = xto(xmul(xfrom(delay, 20), fx), 29);
		if (src_ratio >= (M_09999Q30 >> 1))
			unit = 1;
	}
	if (unit)
		src_ratio = 1 << 29;
	lf = b2mb(s->damping);
	rt60 = xmul(XC(M_RT60S), xs2r(qmul(lf, 96 << 16)));
	/* -120 x delay / src_ratio / rt60 */
	base = unit ? xfrom(delay, 20) : xrecip(fx);
	base = xmul(xmul(base, xrecip(rt60)), XC(M_M120));
	b16 = xto(base, 16);
	if (b16 < -127 * 65536)
		b16 = -127 * 65536;
	dcoef = xto(xs2r(b16), 31);
	bright = qmul(s->brightness, s->brightness);
	nfilt = xto(xs2r(qmul(s->brightness - Q31ONE, 48 << 16)), 31);
	dcut = (24 << 16) + qmul(qmul(s->damping, s->damping), 48 << 16) + qmul(bright, 24 << 16);
	if (dcut > (84 << 16))
		dcut = 84 << 16;
	df = xto(xmin(xmul(fx, xs2r(dcut)), XC(M_0499)), 31);
	if (s->damping >= M_095) {
		s32 dd = s->damping - M_095;
		s32 ti = dd >= Q31ONE / 20 ? Q31ONE : dd * 20;   /* 20 (d - 0,95) : 1,0 au plus, sans deborder */
		dcoef += qmul(ti, Q31ONE - dcoef);
		bright += qmul(ti, Q31ONE - bright);
		df += qmul(ti, M_04999 - df);
		dcut += qmul(ti, (128 << 16) - dcut);
	}
	svf_set(&s->iir, tan_accurate(df), xmk(1 << 30, 1), 0, 0);
	s->k_dcomp = Q31ONE - interp(M_SVFSHIFT, dcut, 15);
	s->k_nk = xto(xrecip(xadd(XC(M_02), xfrom(nfilt, 31))), 28);   /* 1 / (0,2 + nf), Q28 */
	s->k_delay = delay;
	s->k_unit = unit;
	s->k_ratio = src_ratio;
	s->k_dcoef = dcoef;
	s->k_bright = bright;
	s->k_nfilt = nfilt;
	s->kf = s->frequency;
	s->kd = s->damping;
	s->kb = s->brightness;
	s->kvalid = 1;
}

/* s->frequency etc. deja poses ; ajoute la corde a out / aux */
static void str_process(struct mstring *s, const s32 *in, s32 *out, s32 *aux, u32 *rng)
{
	s32 delay, clamped, nfilt, nk, src_ratio, swp0;
	s32 d_inc, p_inc, disp_inc, dc_inc, dmp_inc, br_inc;
	s32 dv, pv, dispv, dcv, fx1, fx2, fbr, fdmp, wp, out0, aux0, out1, aux1;
	s32 ib, ia2, ia3, ic1, ic2;
	s32 *line = s->line;
	int k;

	if (!s->kvalid || s->kf != s->frequency || s->kd != s->damping || s->kb != s->brightness)
		str_block(s);
	delay = s->k_delay;
	src_ratio = s->k_ratio;
	nfilt = s->k_nfilt;
	nk = s->k_nk;
	if (s->k_unit)
		s->src_phase = 1 << 29;
	clamped = 0x40000000 - qmul(Q31(0.98), iabs(s->position - 0x40000000));
	d_inc = (delay - s->delay) / MB;
	p_inc = (clamped - s->clamped_position) / MB;
	disp_inc = (s->dispersion - s->prev_dispersion) / MB;
	dc_inc = (s->k_dcomp - s->prev_damp_comp) / MB;
	dmp_inc = (s->k_dcoef - s->fdmp) / MB;
	br_inc = (s->k_bright - s->fbr) / MB;

	/* Effacement paresseux (Rings efface tout a l'initialisation : ici, ce serait un bloc entier a chaque changement
	 * de modele, verrouillable par pas) : seulement ce qui sera lu, jusqu'a delay + 3 en arriere (x 1,25 avec la
	 * dispersion, qui allonge le retard), et les places que ce bloc ecrit (lues juste avant quand le retard est
	 * court). La ligne de l'allpass (stretch), lue a 0,6 retard au plus, de meme. */
	swp0 = s->swp;
	if (s->fill < DLINE) {
		int need = (delay > s->delay ? delay : s->delay) >> 20;
		if (s->enable_dispersion)
			need += need >> 2;
		need += 8 + MB;
		if (need > DLINE - MB - 8)
			need = DLINE;
		for (k = s->fill; k < need; k++) {
			s32 j = (s->wp + k) & (DLINE - 1);
			line[j] = line[j + DLINE] = 0;
		}
		if (need > s->fill)
			s->fill = need;
		if (s->fill < DLINE)
			for (k = 0; k < MB; k++) {
				s32 j = (s->wp - k) & (DLINE - 1);
				line[j] = line[j + DLINE] = 0;
			}
	}
	if (s->enable_dispersion && s->sfill < SLINE) {
		int need = ((delay > s->delay ? delay : s->delay) >> 20) * 5 / 8 + 8 + MB;
		if (need > SLINE - MB - 8)
			need = SLINE;
		for (k = s->sfill; k < need; k++)
			s->stretch[(s->swp + k) & (SLINE - 1)] = 0;
		if (need > s->sfill)
			s->sfill = need;
	}

	dv = s->delay;
	pv = s->clamped_position;
	dispv = s->prev_dispersion;
	dcv = s->prev_damp_comp;
	fx1 = s->fx1;
	fx2 = s->fx2;
	fbr = s->fbr;
	fdmp = s->fdmp;
	wp = s->wp;
	ib = -s->iir.b;
	ia2 = s->iir.a2;
	ia3 = s->iir.a3;
	ic1 = s->iir.ic1;
	ic2 = s->iir.ic2;
	if (src_ratio == (1 << 29) && !s->enable_dispersion && delay >= ((MB + 8) << 20) && s->delay >= ((MB + 8) << 20)) {
		/* le cas courant (pas de dispersion ni de surechantillonnage, retard de plus d'un bloc : rien de ce
		 * qu'on lit n'est ecrit dans ce bloc), en trois passes legeres : lectures, filtres, ecritures */
		s32 *hb = sc.x;
		s32 dvk = dv, dck = dcv, w = wp;
#ifdef MODAL_ASM
		if (!d_inc && !dc_inc) {                     /* passe 1, retard fixe : modal_asm.S */
			s32 d = qmul(dv, dcv) - (1 << 20), f = shl(d, 11) & Q31ONE;
			int n1 = wp + 1 < MB ? wp + 1 : MB;  /* w de wp a 0, puis de DLINE - 1 vers le bas */
			modal_str_read(&line[wp + (d >> 20)], f, in, hb, n1);
			modal_str_read(&line[DLINE - 1 + (d >> 20)], f, in + n1, hb + n1, MB - n1);
		} else {                                     /* passe 1, retard qui bouge : modal_asm.S */
			s32 st[4];
			int n1 = wp + 1 < MB ? wp + 1 : MB;
			st[0] = dv;
			st[1] = dcv;
			st[2] = d_inc;
			st[3] = dc_inc;
			modal_str_read_mv(&line[wp], st, in, hb, n1);
			modal_str_read_mv(&line[DLINE - 1], st, in + n1, hb + n1, MB - n1);
		}
		if (0)
#endif
		for (k = 0; k < MB; k++) {                   /* passe 1 : ReadHermite */
			s32 d;
			dvk += d_inc;
			dck += dc_inc;
			d = qmul(dvk, dck) - (1 << 20);
			hb[k] = hermite(&line[w + (d >> 20)], shl(d, 11) & Q31ONE) + in[k];
			w = (w - 1) & (DLINE - 1);
		}
#ifdef MODAL_ASM
		if (!br_inc && !dmp_inc) {                   /* passe 2, reglages fixes : modal_asm.S */
			s32 dk[9];
			dk[0] = fx1;
			dk[1] = fx2;
			dk[2] = fir_h0(fdmp, fbr);
			dk[3] = fir_h1(fdmp, fbr);
			dk[4] = ib;
			dk[5] = ia2;
			dk[6] = ia3;
			dk[7] = ic1;
			dk[8] = ic2;
			modal_str_damp(hb, dk);
			fx1 = dk[0];
			fx2 = dk[1];
			ic1 = dk[7];
			ic2 = dk[8];
		} else {                                     /* passe 2, reglages qui bougent : modal_asm.S */
			s32 dk[11];
			dk[0] = fx1;
			dk[1] = fx2;
			dk[2] = fbr;
			dk[3] = fdmp;
			dk[4] = br_inc;
			dk[5] = dmp_inc;
			dk[6] = ib;
			dk[7] = ia2;
			dk[8] = ia3;
			dk[9] = ic1;
			dk[10] = ic2;
			modal_str_damp_mv(hb, dk);
			fx1 = dk[0];
			fx2 = dk[1];
			fbr = dk[2];
			fdmp = dk[3];
			ic1 = dk[9];
			ic2 = dk[10];
		}
		if (0)
#endif
		for (k = 0; k < MB; k++) {                   /* passe 2 : amortissement (FIR puis IIR) */
			s32 sv = hb[k], y, v3, t1, t2;
			y = fir_damp(fdmp, fbr, fx1, sv + fx2);
			fx2 = fx1;
			fx1 = sv;
			fbr += br_inc;
			fdmp += dmp_inc;
			v3 = y - ic2;
			t1 = qmac2r(ib, ic1, ia2, v3);
			t2 = qmac2r(ia2, ic1, ia3, v3);
			hb[k] = ic2 + t2;
			ic1 += shl(t1, 1);
			ic2 = hb[k] + t2;
		}
		out1 = s->out0;
		aux1 = s->aux0;
		out0 = out1;
		aux0 = aux1;
#ifdef MODAL_ASM
		if (!d_inc && aux == out + MB) {             /* passe 3, retard fixe : modal_asm.S */
			s32 dpp[3], a30 = aux[MB - 2], a31 = aux[MB - 1], pv0 = pv;
			int n1 = wp < MB ? wp : MB;          /* ecritures en wp..1 : la lecture qui suit reste dans la ligne */
			dpp[0] = dv;
			dpp[1] = pv;
			dpp[2] = p_inc;
			modal_str_write(hb, &line[wp], out, dpp, n1);
			if (n1 < MB) {                       /* l'echantillon qui ecrit en 0 : la lecture repart de DLINE - 1 */
				s32 comb, i;
				pv = (s32)((u32)pv0 + (u32)p_inc * (u32)(n1 + 1));
				comb = qmul(dv, pv);
				line[0] = line[DLINE] = hb[n1];
				i = DLINE - 1 + (comb >> 20);
				out[n1] += hb[n1];
				aux[n1] += line[i] + qmul(line[i + 1] - line[i], shl(comb, 11) & Q31ONE);
				dpp[1] = pv;
				modal_str_write(hb + n1 + 1, &line[DLINE - 1], out + n1 + 1, dpp, MB - n1 - 1);
			}
			pv = (s32)((u32)pv0 + (u32)p_inc * MB);
			dcv += MB * dc_inc;
			wp = (wp - MB) & (DLINE - 1);
			out1 = hb[MB - 2];
			out0 = hb[MB - 1];
			aux1 = aux[MB - 2] - a30;            /* ce que la corde a ajoute aux 2 derniers echantillons */
			aux0 = aux[MB - 1] - a31;
		} else if (aux == out + MB) {                /* passe 3, retard qui bouge : modal_asm.S */
			s32 dpp[4], a30 = aux[MB - 2], a31 = aux[MB - 1];
			int n1 = wp < MB ? wp : MB;
			dpp[0] = dv;
			dpp[1] = pv;
			dpp[2] = p_inc;
			dpp[3] = d_inc;
			modal_str_write_mv(hb, &line[wp], out, dpp, n1);
			if (n1 < MB) {                       /* l'echantillon qui ecrit en 0 : la lecture repart de DLINE - 1 */
				s32 comb, i;
				dpp[0] += d_inc;
				dpp[1] += p_inc;
				comb = qmul(dpp[0], dpp[1]);
				line[0] = line[DLINE] = hb[n1];
				i = DLINE - 1 + (comb >> 20);
				out[n1] += hb[n1];
				aux[n1] += line[i] + qmul(line[i + 1] - line[i], shl(comb, 11) & Q31ONE);
				modal_str_write_mv(hb + n1 + 1, &line[DLINE - 1], out + n1 + 1, dpp, MB - n1 - 1);
			}
			dv = dpp[0];
			pv = dpp[1];
			dcv += MB * dc_inc;
			wp = (wp - MB) & (DLINE - 1);
			out1 = hb[MB - 2];
			out0 = hb[MB - 1];
			aux1 = aux[MB - 2] - a30;
			aux0 = aux[MB - 1] - a31;
		} else
#endif
		for (k = 0; k < MB; k++) {                   /* passe 3 : ecriture, lecture du peigne */
			s32 comb, i;
			dv += d_inc;
			pv += p_inc;
			dcv += dc_inc;
			comb = qmul(dv, pv);
			line[wp] = line[wp + DLINE] = hb[k];
			wp = (wp - 1) & (DLINE - 1);
			i = wp + (comb >> 20);
			out1 = out0;
			aux1 = aux0;
			out0 = hb[k];
			aux0 = line[i] + qmul(line[i + 1] - line[i], shl(comb, 11) & Q31ONE);
			out[k] += out0;
			aux[k] += aux0;
		}
		s->out0 = out0;
		s->aux0 = aux0;
		s->out1 = out1;
		s->aux1 = aux1;
	} else if (src_ratio == (1 << 29) && s->enable_dispersion && !d_inc && !dc_inc && !disp_inc && !br_inc
		   && !dmp_inc) {
		/* dispersion, reglages fixes (le cas courant) : la boucle d'en dessous, specialisee (constantes hors de la
		 * boucle, lectures directes dans la ligne doublee : line[x] = line[x + DLINE]) ; memes calculs */
		struct dispk dk;
		s32 dn = s->dispersion_noise, cb = s->curved_bridge, swp = s->swp;
		s32 *st = s->stretch;
		u32 rs = *rng;
		s32 d0 = qmul(dv, dcv) - (1 << 20), h0 = fir_h0(fdmp, fbr), h1 = fir_h1(fdmp, fbr);
		s32 sp, apg, ac, na, bc, fm, a30 = aux[MB - 2], a31 = aux[MB - 1];
		if (!s->kdisp_valid || s->kdisp != dispv) {
			disp_coefs(&dk, dispv);
			s->kdisp = dispv;
			s->ksp = dk.sp;
			s->kna = dk.na;
			s->kbc = dk.bc;
			s->kac = dk.ac;
			s->kapg = dk.apg;
			s->kdisp_valid = 1;
		}
		sp = s->ksp;
		apg = s->kapg;
		ac = s->kac;
		na = s->kna;
		bc = s->kbc;
		fm = na | bc;
#ifdef MODAL_ASM
		/* sans modulation du retard (fm nul) ni melange de l'anti-continu (ac nul), le retard est fixe sur le bloc :
		 * les memes calculs en passes (modal_asm.S) : le bruit de dispersion et l'anti-continu avancent a part (leur
		 * etat seul sert, aux blocs suivants), la lecture (et le passe-tout de l'etirement), puis les passes 2 et 3
		 * de la corde sans dispersion. Le retard lu doit depasser le bloc : rien de ce qu'on lit n'y est ecrit. */
		if (!fm && !ac && aux == out + MB) {
			s32 apd = qmul(d0, sp), md = d0 - apd, D = d0, f, *hb = sc.x, ap[4];
			int allpass = apd >= (4 << 20) && md >= (4 << 20), n1 = wp + 1 < MB ? wp + 1 : MB;
			if (allpass)
				D = md;
			if (D >= ((MB + 8) << 20)) {
				for (k = 0; k < MB; k++) {
					rs = rs * 1664525u + 1013904223u;
					dn += qmul(nfilt, qmul((s32)(rs ^ 0x80000000u) >> 4, nk) - dn);
				}
				f = shl(D, 11) & Q31ONE;
				if (allpass) {
					ap[0] = (s32)(unsigned long)st;
					ap[1] = swp;
					ap[2] = apd >> 20;
					ap[3] = apg;
					modal_str_read_ap(&line[wp + (D >> 20)], f, hb, n1, ap);
					modal_str_read_ap(&line[DLINE - 1 + (D >> 20)], f, hb + n1, MB - n1, ap);
					swp = ap[1];
				} else {
					modal_str_read(&line[wp + (D >> 20)], f, sc.zero, hb, n1);
					modal_str_read(&line[DLINE - 1 + (D >> 20)], f, sc.zero, hb + n1, MB - n1);
				}
				{
					s32 value = iabs(hb[MB - 1]) - M_0025U;
					cb = value > 0 ? (hb[MB - 1] > 0 ? 2 * value : -3 * value) : 0;
				}
				modal_dc_in(&s->dc, hb, in);
				{
					s32 dk2[9], dpp[3], pv0 = pv;
					int n3 = wp < MB ? wp : MB;
					dk2[0] = fx1;
					dk2[1] = fx2;
					dk2[2] = h0;
					dk2[3] = h1;
					dk2[4] = ib;
					dk2[5] = ia2;
					dk2[6] = ia3;
					dk2[7] = ic1;
					dk2[8] = ic2;
					modal_str_damp(hb, dk2);
					fx1 = dk2[0];
					fx2 = dk2[1];
					ic1 = dk2[7];
					ic2 = dk2[8];
					dpp[0] = dv;
					dpp[1] = pv;
					dpp[2] = p_inc;
					modal_str_write(hb, &line[wp], out, dpp, n3);
					if (n3 < MB) {               /* l'echantillon qui ecrit en 0 : la lecture repart de DLINE - 1 */
						s32 comb, i;
						pv = (s32)((u32)pv0 + (u32)p_inc * (u32)(n3 + 1));
						comb = qmul(dv, pv);
						line[0] = line[DLINE] = hb[n3];
						i = DLINE - 1 + (comb >> 20);
						out[n3] += hb[n3];
						aux[n3] += line[i] + qmul(line[i + 1] - line[i], shl(comb, 11) & Q31ONE);
						dpp[1] = pv;
						modal_str_write(hb + n3 + 1, &line[DLINE - 1], out + n3 + 1, dpp, MB - n3 - 1);
					}
					pv = (s32)((u32)pv0 + (u32)p_inc * MB);
					wp = (wp - MB) & (DLINE - 1);
				}
				goto disp_done;
			}
		}
#endif
		for (k = 0; k < MB; k++) {
			s32 d, sv, v3, t1, t2, apd, md, value, noise, *p;
			pv += p_inc;
			rs = rs * 1664525u + 1013904223u;
			noise = qmul((s32)(rs ^ 0x80000000u) >> 4, nk);   /* Q27 x Q28 -> UNIT */
			dn += qmul(nfilt, noise - dn);
			d = d0;
			if (fm)
				d = shl(qmul(d, (1 << 30) + shl(qmul(dn, na), 6) - shl(qmul(cb, bc), 6)), 1);
			apd = qmul(d, sp);
			md = d - apd;
			if (apd >= (4 << 20) && md >= (4 << 20)) {
				s32 rd, wr, i = wp + (md >> 20);
				if (i > 2 * DLINE - 3)
					i -= DLINE;
				sv = hermite(&line[i], shl(md, 11) & Q31ONE);
				rd = st[(swp + (apd >> 20)) & (SLINE - 1)];
				wr = sv + qmulr(apg, rd);
				st[swp] = wr;
				swp = (swp - 1) & (SLINE - 1);
				sv = rd - qmulr(wr, apg);
			} else {
				s32 i = wp + (d >> 20);
				if (i > 2 * DLINE - 3)
					i -= DLINE;
				sv = hermite(&line[i], shl(d, 11) & Q31ONE);
			}
			{
				s32 sac = dc_one(&s->dc, sv);          /* DCBlocker */
				if (ac)
					sv += qmul(ac, sac - sv);
			}
			value = iabs(sv) - M_0025U;
			cb = value > 0 ? (sv > 0 ? 2 * value : -3 * value) : 0;
			sv += in[k];
			{
				s32 y = qmac2r(h0, fx1, h1, sv + fx2);
				fx2 = fx1;
				fx1 = sv;
				v3 = y - ic2;
			}
			t1 = qmac2r(ib, ic1, ia2, v3);
			t2 = qmac2r(ia2, ic1, ia3, v3);
			sv = ic2 + t2;
			ic1 += shl(t1, 1);
			ic2 = sv + t2;
			line[wp] = line[wp + DLINE] = sv;
			wp = (wp - 1) & (DLINE - 1);
			out[k] += sv;
			{
				s32 comb = qmul(dv, pv);
				p = &line[wp + (comb >> 20)];
				aux[k] += p[0] + qmul(p[1] - p[0], shl(comb, 11) & Q31ONE);
			}
		}
#ifdef MODAL_ASM
	disp_done:
#endif
		*rng = rs;
		s->dispersion_noise = dn;
		s->curved_bridge = cb;
		s->swp = swp;
		s->out1 = line[(wp + 2) & (DLINE - 1)];         /* les deux derniers echantillons ecrits */
		s->out0 = line[(wp + 1) & (DLINE - 1)];
		s->aux1 = aux[MB - 2] - a30;                     /* ce que la corde a ajoute aux 2 derniers */
		s->aux0 = aux[MB - 1] - a31;
	} else if (src_ratio == (1 << 29) && s->enable_dispersion) {
		/* dispersion (STRING, STRING + REVERB), sans surechantillonnage */
		struct dispk dk;
		s32 dn = s->dispersion_noise, cb = s->curved_bridge, swp = s->swp;
		s32 *st = s->stretch;
		u32 rs = *rng;
		disp_coefs(&dk, dispv);
		out1 = s->out1;
		aux1 = s->aux1;
		out0 = s->out0;
		aux0 = s->aux0;
		for (k = 0; k < MB; k++) {
			s32 d, comb, sv, y, v3, t1, t2, apd, md, sac, value, noise;
			dv += d_inc;
			pv += p_inc;
			dcv += dc_inc;
			comb = qmul(dv, pv);
			d = qmul(dv, dcv) - (1 << 20);
			rs = rs * 1664525u + 1013904223u;
			noise = qmul((s32)(rs ^ 0x80000000u) >> 4, nk);   /* Q27 x Q28 -> UNIT */
			dn += qmul(nfilt, noise - dn);
			if (disp_inc) {
				dispv += disp_inc;
				disp_coefs(&dk, dispv);
			}
			if (dk.na | dk.bc)
				d = shl(qmul(d, (1 << 30) + shl(qmul(dn, dk.na), 6) - shl(qmul(cb, dk.bc), 6)), 1);
			apd = qmul(d, dk.sp);
			md = d - apd;
			if (apd >= (4 << 20) && md >= (4 << 20)) {
				s32 rd, wr;
				sv = (md >> 20) < DLINE - 4 ? hermite(&line[wp + (md >> 20)], shl(md, 11) & Q31ONE)
					: rd_hermite(line, wp, md);
				rd = st[(swp + (apd >> 20)) & (SLINE - 1)];
				wr = sv + qmulr(dk.apg, rd);
				st[swp] = wr;
				swp = (swp - 1) & (SLINE - 1);
				sv = rd - qmulr(wr, dk.apg);
			} else {
				sv = (d >> 20) < DLINE - 4 ? hermite(&line[wp + (d >> 20)], shl(d, 11) & Q31ONE)
					: rd_hermite(line, wp, d);
			}
			sac = dc_one(&s->dc, sv);                          /* DCBlocker */
			if (dk.ac)
				sv += qmul(dk.ac, sac - sv);
			value = iabs(sv) - M_0025U;
			cb = value > 0 ? (sv > 0 ? 2 * value : -3 * value) : 0;
			sv += in[k];
			y = fir_damp(fdmp, fbr, fx1, sv + fx2);
			fx2 = fx1;
			fx1 = sv;
			fbr += br_inc;
			fdmp += dmp_inc;
			v3 = y - ic2;
			t1 = qmac2r(ib, ic1, ia2, v3);
			t2 = qmac2r(ia2, ic1, ia3, v3);
			sv = ic2 + t2;
			ic1 += shl(t1, 1);
			ic2 = sv + t2;
			line[wp] = line[wp + DLINE] = sv;
			wp = (wp - 1) & (DLINE - 1);
			out1 = out0;
			aux1 = aux0;
			out0 = sv;
			aux0 = rd_linear(line, DLINE - 1, wp, comb);
			out[k] += out0;
			aux[k] += aux0;
		}
		*rng = rs;
		s->dispersion_noise = dn;
		s->curved_bridge = cb;
		s->swp = swp;
		s->out0 = out0;
		s->aux0 = aux0;
		s->out1 = out1;
		s->aux1 = aux1;
	} else if (src_ratio == (1 << 29) && !s->enable_dispersion) {
		/* reglages qui bougent */
		out0 = s->out0;
		aux0 = s->aux0;
		out1 = s->out1;
		aux1 = s->aux1;
		for (k = 0; k < MB; k++) {
			s32 d, comb, sv, y, v3, t1, t2;
			dv += d_inc;
			pv += p_inc;
			dcv += dc_inc;
			comb = qmul(dv, pv);
			d = qmul(dv, dcv) - (1 << 20);
			sv = hermite(&line[wp + (d >> 20)], shl(d, 11) & Q31ONE) + in[k];
			y = fir_damp(fdmp, fbr, fx1, sv + fx2);
			fx2 = fx1;
			fx1 = sv;
			fbr += br_inc;
			fdmp += dmp_inc;
			v3 = y - ic2;
			t1 = qmac2r(ib, ic1, ia2, v3);
			t2 = qmac2r(ia2, ic1, ia3, v3);
			sv = ic2 + t2;
			ic1 += shl(t1, 1);
			ic2 = sv + t2;
			line[wp] = line[wp + DLINE] = sv;
			wp = (wp - 1) & (DLINE - 1);
			out1 = out0;
			aux1 = aux0;
			out0 = sv;
			{
				const s32 *p = &line[wp + (comb >> 20)];
				aux0 = p[0] + qmul(p[1] - p[0], shl(comb, 11) & Q31ONE);
			}
			out[k] += out0;
			aux[k] += aux0;
		}
		s->out0 = out0;
		s->aux0 = aux0;
		s->out1 = out1;
		s->aux1 = aux1;
	} else {
		struct dispk dk;
		dk.disp = dispv + 1;                             /* a calculer au 1er echantillon */
		for (k = 0; k < MB; k++) {
			s32 o, a;
			s->src_phase += src_ratio;
			if (s->src_phase > (1 << 29)) {
				s32 d, comb, sv;
				s->src_phase -= 1 << 29;
				dv += d_inc;
				pv += p_inc;
				dcv += dc_inc;
				d = dv;
				comb = qmul(d, pv);
				d = qmul(d, dcv);
				d -= 1 << 20;
				if (s->enable_dispersion) {
					s32 noise, fm, apd, md, sac, value;
					noise = qmul(rng_q31(rng) >> 4, nk);         /* Q27 x Q28 -> UNIT */
					s->dispersion_noise += qmul(nfilt, noise - s->dispersion_noise);
					dispv += disp_inc;
					if (disp_inc || dispv != dk.disp)
						disp_coefs(&dk, dispv);
					fm = (1 << 30) + shl(qmul(s->dispersion_noise, dk.na), 6)
						- shl(qmul(s->curved_bridge, dk.bc), 6);
					d = shl(qmul(d, fm), 1);
					apd = qmul(d, dk.sp);
					md = d - apd;
					if (apd >= (4 << 20) && md >= (4 << 20)) {
						s32 rd, wr, j = apd >> 20;
						sv = rd_hermite(line, wp, md);
						rd = s->stretch[(s->swp + j) & (SLINE - 1)];
						wr = sv + qmulr(dk.apg, rd);
						s->stretch[s->swp] = wr;
						s->swp = (s->swp - 1) & (SLINE - 1);
						sv = rd - qmulr(wr, dk.apg);
					} else {
						sv = rd_hermite(line, wp, d);
					}
					sac = dc_one(&s->dc, sv);
					sv += qmul(dk.ac, sac - sv);
					value = iabs(sv) - M_0025U;
					s->curved_bridge = value > 0 ? (sv > 0 ? 2 * value : -3 * value) : 0;
				} else {
					sv = rd_hermite(line, wp, d);
				}
				sv += in[k];
				{
					s32 y = fir_damp(fdmp, fbr, fx1, sv + fx2);
					fx2 = fx1;
					fx1 = sv;
					fbr += br_inc;
					fdmp += dmp_inc;
					sv = y;
				}
				{
					s32 v3 = sv - ic2, t1 = qmac2r(ib, ic1, ia2, v3), t2 = qmac2r(ia2, ic1, ia3, v3);
					sv = ic2 + t2;
					ic1 += shl(t1, 1);
					ic2 = sv + t2;
				}
				line[wp] = line[wp + DLINE] = sv;
				wp = (wp - 1) & (DLINE - 1);
				s->out1 = s->out0;
				s->aux1 = s->aux0;
				s->out0 = sv;
				s->aux0 = rd_linear(line, DLINE - 1, wp, comb);
			}
			if (src_ratio == (1 << 29)) {
				o = s->out0;
				a = s->aux0;
			} else {
				s32 f = shl(s->src_phase, 2);            /* Q31 */
				o = s->out1 + qmul(s->out0 - s->out1, f);
				a = s->aux1 + qmul(s->aux0 - s->aux1, f);
			}
			out[k] += o;
			aux[k] += a;
		}
	}
	s->delay = dv;
	s->clamped_position = pv;
	s->prev_dispersion = dispv;
	s->prev_damp_comp = dcv;
	s->fx1 = fx1;
	s->fx2 = fx2;
	s->fbr = fbr;
	s->fdmp = fdmp;
	s->wp = wp;
	s->iir.ic1 = ic1;
	s->iir.ic2 = ic2;
	if (s->fill < DLINE) {
		s->fill += MB;
		if (s->fill > DLINE)
			s->fill = DLINE;
	}
	if (s->sfill < SLINE) {
		s->sfill += (swp0 - s->swp) & (SLINE - 1);
		if (s->sfill > SLINE)
			s->sfill = SLINE;
	}
}

/* ---- pincement (rings/dsp/plucker.h) ----------------------------------------------------------------------- */

struct plucker {
	struct svf svf;
	s32 comb[256];
	s32 wp, remaining, period, gain, level;          /* period Q11.20 */
};

static void pl_init(struct plucker *p)
{
	int i;

	svf_set(&p->svf, tan_dirty(M_001), XC(M_R100), 0, 0);
	svf_reset(&p->svf);
	for (i = 0; i < 256; i++)
		p->comb[i] = 0;
	p->wp = 0;
	p->remaining = 0;
	p->period = 0;
	p->gain = 0;
	p->level = Q31ONE;
}

static void pl_trigger(struct plucker *p, xf frequency, xf cutoff, s32 position, s32 level)
{
	p->level = level;
	s32 ratio = qmul(position, Q31(0.9)) + Q31(0.05);
	xf period = xmul(xrecip(frequency), xfrom(ratio, 31));
	p->remaining = xto(period, 0);
	while (xcmp(period, XC(M_255)) >= 0)
		period = xscale(period, -1);
	p->period = xto(period, 20);
	p->gain = qmul(Q31ONE - position, Q31(0.8));
	svf_set(&p->svf, tan_dirty(xto(xmin(cutoff, XC(M_0499)), 31)), xmk(1 << 30, 0), 0, 0);
}

#ifdef MODAL_ASM
/* pl_process sans bouffee de bruit (remaining nul), puis rin[k] = dc_one(dc, rin[k] + nb[k]) : modal_asm.S.
 * nb = rin + 4 MB (struct modal_part). */
void modal_pluck(struct plucker *p, s32 *rin, struct dcblock *dc);
#endif

static void pl_process(struct plucker *p, s32 *out, u32 *rng)
{
	int k;

	for (k = 0; k < MB; k++) {
		s32 in = 0;
		if (p->remaining) {
			in = rng_q31(rng) >> 7;
			if (p->level != Q31ONE)
				in = qmul(in, p->level);
			p->remaining--;
		}
		out[k] = in + qmul(p->gain, rd_linear(p->comb, 255, p->wp, p->period));
		p->comb[p->wp] = out[k];
		p->wp = (p->wp - 1) & 255;
	}
	svf_lp_block(&p->svf, out, MB, 0, 0);
}

/* ---- voix FM (rings/dsp/fm_voice.cc, follower.h) ------------------------------------------------------------ */

struct naive {
	s32 f, lp, bp;
};

static inline s32 naive_hp(struct naive *n, s32 in)  /* NaiveSvf Process<HIGH_PASS>, amortissement 2 */
{
	s32 hp;
	n->lp += qmul(n->f, n->bp);
	hp = in - shl(n->bp, 1) - n->lp;
	n->bp += qmul(n->f, hp);
	return hp;
}

struct follower {
	struct naive lm, mh;
	s32 det[3], centroid;                            /* UNIT, Q31 */
};

struct fmvoice {
	xf carrier;                                      /* frequence */
	s32 ratio, brightness, damping, feedback_amount;
	u32 prev_car, prev_mod;                          /* increments, Q32 */
	s32 prev_bright, prev_damp, prev_fb;             /* Q31, Q30 */
	s32 amp_env, bright_env;                         /* UNIT */
	s32 gain;                                        /* Q27 */
	s32 fm_amount;                                   /* Q28 */
	u32 car_phase, mod_phase;
	s32 prev_sample;                                 /* UNIT */
	struct follower fol;
	s32 kd, kvalid, k_amp, k_bright;                 /* decroissances, gardees tant que DAMPING ne change pas */
};

static void fm_init(struct fmvoice *v)
{
	u32 inc = M_INC220;

	v->carrier = XC(M_F220);
	v->ratio = Q31(0.5);
	v->brightness = Q31(0.5);
	v->damping = Q31(0.5);
	v->feedback_amount = 0;
	v->prev_car = inc;
	v->prev_mod = inc;
	v->prev_bright = v->brightness;
	v->prev_damp = v->damping;
	v->prev_fb = 0;
	v->amp_env = v->bright_env = 0;
	v->car_phase = v->mod_phase = 0;
	v->gain = 0;
	v->fm_amount = 0;
	v->prev_sample = 0;
	v->fol.lm.f = M_FOL_LM;
	v->fol.mh.f = M_FOL_MH;
	v->fol.lm.lp = v->fol.lm.bp = v->fol.mh.lp = v->fol.mh.bp = 0;
	v->fol.det[0] = v->fol.det[1] = v->fol.det[2] = 0;
	v->fol.centroid = 0;
	v->kvalid = 0;
}

static inline s32 sine_fm(u32 phase, s32 fm)         /* fm en tours, Q28 ; rend UNIT */
{
	s32 i, f, a, b;
	phase += (u32)fm << 4;
	i = phase >> 20;
	f = (s32)((phase << 11) & 0x7fffffffu);
	a = m_sine[i];
	b = m_sine[i + 1];
	return shl(a, 9) + qmul(shl(b - a, 9), f);
}

/* 1 - 0,001^(1 / rt60) : x = ln(1000) / rt60, x - x^2/2 + x^3/6 */
static s32 decay_coef(xf rt60)
{
	s32 x = xto(xmul(XC(M_LN1000), xrecip(rt60)), 31);
	s32 x2 = qmul(x, x);
	return x - (x2 >> 1) + qmul(qmul(x2, x), Q31(1.0 / 6));
}

/* in_zero : l'entree de ce bloc est muette (la Part le sait : seule la voix active la recoit) */
static void fm_process(struct fmvoice *v, const s32 *in, s32 *out, s32 *aux, int in_zero)
{
	s32 d = v->damping, env_amount, amp_decay, bright_decay, ratio, feedback, pfb;
	xf modf;
	u32 car_inc, mod_inc;
	s32 ci, mi, bi, fi;
	s32 amp_env = v->amp_env, bright_env = v->bright_env, fm_amount = v->fm_amount, gain_ = v->gain;
	s32 prev_sample = v->prev_sample, prev_bright = v->prev_bright, prev_fb = v->prev_fb;
	u32 mod_phase = v->mod_phase, car_phase = v->car_phase, prev_car = v->prev_car, prev_mod = v->prev_mod;
	s32 bv = 0, fmin = 0, fmax = 0, dlt = 0, mfb = 0;
	struct follower *fo = &v->fol;
	int k, quiet;

	env_amount = d < M_09 ? (1 << 30) : shl(qmul(Q31ONE - d, Q31(10.0 / 16)), 3);   /* Q30 */
	if (!v->kvalid || v->kd != d) {
		v->k_amp = decay_coef(xmul(XC(M_RT60FM), xs2r(qmul(d, 96 << 16))));
		v->k_bright = decay_coef(xmul(XC(M_RT60FM), xs2r(qmul(d, 84 << 16))));
		v->kd = d;
		v->kvalid = 1;
	}
	amp_decay = v->k_amp;
	bright_decay = v->k_bright;
	ratio = interp(M_FMQ, v->ratio, 7);
	modf = xmul(v->carrier, xs2r(ratio));
	if (xcmp(modf, xmk(1 << 30, -1)) > 0)
		modf = xmk(1 << 30, -1);
	feedback = v->feedback_amount - 0x40000000;     /* (fb - 0,5) x 2, Q30 */
	car_inc = (u32)xto(v->carrier, 32);
	mod_inc = (u32)xto(modf, 32);
	if (xcmp(v->carrier, xmk(1 << 30, -1)) >= 0)
		car_inc = 0x80000000u;
	if (xcmp(modf, xmk(1 << 30, -1)) >= 0)
		mod_inc = 0x80000000u;
	ci = ((s32)(car_inc - prev_car)) / MB;
	mi = ((s32)(mod_inc - prev_mod)) / MB;
	bi = (v->brightness - prev_bright) / MB;
	fi = (feedback - prev_fb) / MB;
	pfb = feedback < 0 ? qmul(feedback, feedback) : 0;   /* fb^2 en Q29, soit 0,5 fb^2 en Q30 */
	if (!bi) {
		bv = qmul(prev_bright, prev_bright);
		fmin = bv < 0x40000000 ? 0 : bv - 0x40000000;
		fmax = bv < 0x40000000 ? bv : 0x40000000;
		dlt = Q31(0.005 / 8) + qmul(fmax, Q31(0.015 / 4));
	}
	if (!fi)
		mfb = prev_fb > 0 ? qmul(prev_fb, prev_fb) : 0;
	/* suiveur au repos (entree nulle, filtres et detecteurs a zero) : ses bandes restent nulles */
	quiet = in_zero && !(fo->lm.lp | fo->lm.bp | fo->mh.lp | fo->mh.bp | fo->det[0] | fo->det[1] | fo->det[2]);

	/* Suiveur au repos, brillance et retour fixes : les enveloppes (amplitude, brillance, quantite de FM, gain) ne
	 * dependent pas des oscillateurs. Deux boucles : les enveloppes, puis les oscillateurs ; les memes calculs. */
	if (quiet && !bi && !fi) {
		s32 *fa = sc.ck, *ga = sc.y0;
		for (k = 0; k < MB; k++) {
			s32 e = -fo->centroid, err, fenv, fma, gain;
			fo->centroid += qmul(e, e > 0 ? Q31(0.05) : Q31(0.001));
			err = -amp_env;
			amp_env += qmul(err > 0 ? Q31(0.05) : amp_decay, err);
			err = -bright_env;
			bright_env += qmul(err > 0 ? Q31(0.01) : bright_decay, err);
			fenv = (UNIT >> 1) + shl(qmul(env_amount, bright_env - (UNIT >> 1)), 1);
			fma = (fmin >> 1) + shl(qmul(fmax, fenv), 6);
			err = fma - fm_amount;
			if (err > dlt)
				err = dlt;
			else if (err < -dlt)
				err = -dlt;
			fm_amount += err;
			gain = UNIT + shl(qmul(env_amount, amp_env - UNIT), 1);
			gain_ += qmul(Q31(0.005) + shl(qmul(Q31(0.045 / 8), fm_amount), 6), shl(gain, 3) - gain_);
			fa[k] = fm_amount;
			ga[k] = gain_;
		}
		for (k = 0; k < MB; k++) {
			s32 mod, car;
			prev_mod += mi;
			prev_car += ci;
			mod_phase += (u32)shl(qmul((s32)(prev_mod >> 1), (1 << 30) + shl(qmul(prev_sample, pfb), 7)), 2);
			car_phase += prev_car;
			mod = sine_fm(mod_phase, shl(qmul(mfb, prev_sample), 4));
			car = sine_fm(car_phase, shl(qmul(fa[k], mod), 7));
			prev_sample += qmul(Q31(0.1), car - prev_sample);
			out[k] = shl(qmul(car + (mod >> 1), ga[k]), 4);
			aux[k] = shl(qmul(mod >> 1, ga[k]), 4);
		}
		k = MB;
	} else
	for (k = 0; k < MB; k++) {
		s32 ae, be, fenv, fma, err, mod, car, gain;
		if (quiet) {
			s32 e = -fo->centroid;
			fo->centroid += qmul(e, e > 0 ? Q31(0.05) : Q31(0.001));
			ae = 0;
			be = 0;
		} else {
			s32 b2 = naive_hp(&fo->mh, in[k]);
			s32 b1 = naive_hp(&fo->lm, fo->mh.lp);
			s32 b0 = fo->lm.lp, er, w, tot, e;
			er = iabs(b0) - fo->det[0];
			fo->det[0] += qmul(er > 0 ? M_FOL_ATT[0] : M_FOL_DEC[0], er);
			er = iabs(b1) - fo->det[1];
			fo->det[1] += qmul(er > 0 ? M_FOL_ATT[1] : M_FOL_DEC[1], er);
			er = iabs(b2) - fo->det[2];
			fo->det[2] += qmul(er > 0 ? M_FOL_ATT[2] : M_FOL_DEC[2], er);
			tot = fo->det[0] + fo->det[1] + fo->det[2];
			w = (fo->det[1] >> 1) + fo->det[2];
			e = w ? xto(xmul(xfrom(w, 24), xrecip(xadd(xfrom(tot, 24), XC(M_0001)))), 31) : 0;
			e -= fo->centroid;
			fo->centroid += qmul(e, e > 0 ? Q31(0.05) : Q31(0.001));
			ae = tot;
			/* be x 2 ae (2 - ae) */
			be = qmul(fo->centroid, shl(qmul(ae, (2 * UNIT) - ae), 8));
		}
		err = ae - amp_env;
		amp_env += qmul(err > 0 ? Q31(0.05) : amp_decay, err);
		err = be - bright_env;
		bright_env += qmul(err > 0 ? Q31(0.01) : bright_decay, err);

		if (bi) {
			prev_bright += bi;
			bv = qmul(prev_bright, prev_bright);         /* Q31 */
			fmin = bv < 0x40000000 ? 0 : bv - 0x40000000; /* 2 bv - 1, Q30 */
			fmax = bv < 0x40000000 ? bv : 0x40000000;     /* 2 bv, Q30 */
			dlt = Q31(0.005 / 8) + qmul(fmax, Q31(0.015 / 4));    /* Q28 */
		}
		fenv = (UNIT >> 1) + shl(qmul(env_amount, bright_env - (UNIT >> 1)), 1);   /* UNIT */
		fma = (fmin >> 1) + shl(qmul(fmax, fenv), 6);         /* (min + max env) x 2, Q28 */
		err = fma - fm_amount;
		if (err > dlt)
			err = dlt;
		else if (err < -dlt)
			err = -dlt;
		fm_amount += err;

		prev_mod += mi;
		prev_car += ci;
		mod_phase += (u32)shl(qmul((s32)(prev_mod >> 1), (1 << 30) + shl(qmul(prev_sample, pfb), 7)), 2);
		car_phase += prev_car;
		if (fi) {
			prev_fb += fi;
			mfb = prev_fb > 0 ? qmul(prev_fb, prev_fb) : 0;     /* 0,25 fb^2 en Q31 */
		}
		mod = sine_fm(mod_phase, shl(qmul(mfb, prev_sample), 4));
		car = sine_fm(car_phase, shl(qmul(fm_amount, mod), 7));
		prev_sample += qmul(Q31(0.1), car - prev_sample);
		gain = UNIT + shl(qmul(env_amount, amp_env - UNIT), 1);
		gain_ += qmul(Q31(0.005) + shl(qmul(Q31(0.045 / 8), fm_amount), 6), shl(gain, 3) - gain_);
		out[k] = shl(qmul(car + (mod >> 1), gain_), 4);
		aux[k] = shl(qmul(mod >> 1, gain_), 4);
	}
	v->amp_env = amp_env;
	v->bright_env = bright_env;
	v->fm_amount = fm_amount;
	v->gain = gain_;
	v->prev_sample = prev_sample;
	v->mod_phase = mod_phase;
	v->car_phase = car_phase;
	v->prev_car = car_inc;
	v->prev_mod = mod_inc;
	v->prev_bright = v->brightness;
	v->prev_fb = feedback;
}

/* ---- reverbe (rings/dsp/fx/reverb.h, fx_engine.h, 16 bits) -------------------------------------------------- */

struct reverb {
	s16 *buf;
	s32 wp;
	struct lfo lfo[2];
	s32 amount, input_gain, time, diffusion, lp;    /* Q31 */
	s32 lp1, lp2;                                    /* UNIT */
	s32 cleared;                                     /* demi-mots deja effaces : par morceaux, RV_CHUNK par bloc */
};

#define RV_CHUNK 2048                                /* 4 Ko par bloc : 16 blocs (11 ms) pour toute la reverbe */


static void rv_init(struct reverb *r, s16 *buf)
{
	r->buf = buf;
	r->wp = 0;
	lfo_init(&r->lfo[0], M_RV_LFO1);
	lfo_init(&r->lfo[1], M_RV_LFO2);
	r->lp = Q31(0.7);
	r->diffusion = Q31(0.625);
	r->lp1 = r->lp2 = 0;
	r->cleared = 0;
}

/* un morceau de l'effacement (Rings efface les 64 Ko d'un coup : ici, plus d'un bloc) ; rend 1 quand c'est fini */
static int rv_clear_step(struct reverb *r)
{
	u32 *b = (u32 *)(r->buf + r->cleared);
	int i;

	if (r->cleared >= RV_SIZE)
		return 1;
	for (i = 0; i < RV_CHUNK / 2; i++)
		b[i] = 0;
	r->cleared += RV_CHUNK;
	return r->cleared >= RV_SIZE;
}

/* Compress de fx_engine : trunc(v x 32768) vers zero, sature a 16 bits ; sans branche : pour v < 0,
 * -((-v) >> 9) = (v + 511) >> 9 */
static inline s32 rv_c(s32 v)
{
	s32 t = (v + ((v >> 31) & 511)) >> 9;

	if ((u32)(t + 32768) > 65535u)
		t = (t >> 31) ^ 32767;
	return t;
}

/* les lignes de la reverbe dans le tampon : debut (RV_BASE) et derniere case (debut + longueur - 1) */
#define RV_AP1   0
#define RV_AP1T  149
#define RV_AP2   151
#define RV_AP2T  364
#define RV_AP3   366
#define RV_AP3T  684
#define RV_AP4   686
#define RV_AP4T  1212
#define RV_D1A   1214
#define RV_D1AT  3395
#define RV_D1B   3397
#define RV_D1BT  6086
#define RV_DEL1  6088
#define RV_D2A   10590
#define RV_D2AT  13114
#define RV_D2B   13116
#define RV_D2BT  15312
#define RV_DEL2  15314
#define RV_TAP(o) buf[(w + (o)) & (RV_SIZE - 1)]
#define RV_GET(o) shl(RV_TAP(o), 9)                  /* Decompress : / 32768, en UNIT */

/* l'Interpolate de fx_engine sur une ligne modulee par un LFO : decalage (Q16) -> case et fraction */
static inline void rv_mod(s32 v, s32 center, s32 depth, s32 *idx, s32 *frac)
{
	s32 off = (center << 16) + qmul(v, depth << 16);

	*idx = off >> 16;
	*frac = shl(off, 15) & Q31ONE;
}

/* La reverbe etage par etage sur tout le bloc : chaque ligne fait plus de 32 echantillons (la plus courte, 150), donc
 * rien de ce qu'un etage lit n'a ete ecrit dans ce bloc, et chaque boucle de retour passe par une ligne : les memes
 * calculs que l'ecriture echantillon par echantillon d'en dessous, dans un autre ordre, qui donnent les memes
 * nombres. Chaque prise avance d'une case par echantillon : un pointeur, sans masque, quand aucune ne repasse par le
 * debut du tampon dans le bloc (sinon : rv_process, echantillon par echantillon). */
#define RV_P(o) (buf + (((w0 + (o)) & (RV_SIZE - 1))))  /* la case de l'echantillon -1 : k lit RV_P(o)[-1 - k] */

#ifdef MODAL_ASM
void modal_rv_ap(s16 *head, const s16 *tail, s32 *v, s32 k1, s32 k2);      /* rv_ap sur MB : modal_asm.S */
void modal_rv_tail(s16 *head, const s32 *v, s32 *out, s32 amount);         /* rv_tail : modal_asm.S */
#define rv_ap(h, t, v, k1, k2, n) modal_rv_ap(h, t, v, k1, k2)
#define rv_tail modal_rv_tail
#else
/* un passe-tout de fx_engine sur n echantillons : prev = tail ; v += k1 prev ; head = Compress(v) ; v = k2 v + prev */
static void rv_ap(s16 *head, const s16 *tail, s32 *v, s32 k1, s32 k2, int n)
{
	int k;

	for (k = 0; k < n; k++) {
		s32 prev = shl(*--tail, 9), x = v[k] + qmul(prev, k1);
		*--head = (s16)rv_c(x);
		v[k] = qmul(x, k2) + prev;
	}
}

/* la sortie d'une branche : la ligne de retour ecrite, et le melange a la sortie */
static void rv_tail(s16 *head, const s32 *v, s32 *out, s32 amount)
{
	int k;

	for (k = 0; k < MB; k++) {
		*--head = (s16)rv_c(v[k]);
		out[k] += qmul(shl(v[k], 1) - out[k], amount);
	}
}
#endif

/* l'entree d'une branche du reservoir : la ligne modulee lue (deux segments : avant et apres le pas des LFO en ks),
 * le gain de reverberation, le passe-bas ; rend l'etat du passe-bas */
#ifdef MODAL_ASM
/* rv_branch sur les echantillons k0..k0 + n - 1 d'un meme segment : pa = RV_P(ligne) - k0 ; rend lp. modal_asm.S */
s32 modal_rv_in(const s16 *pa, s32 f, const s32 *apout, s32 *v, int n, s32 lp, s32 klp, s32 krt);
#endif

static s32 rv_branch(s16 *buf, s32 w0, const s32 *apout, s32 *v, s32 base, s32 ks, const s32 *mi, const s32 *mf,
		     s32 lp, s32 klp, s32 krt)
{
	int k;

#ifdef MODAL_ASM
	if (ks > 0)
		lp = modal_rv_in(RV_P(base + mi[0]), mf[0], apout, v, ks, lp, klp, krt);
	return modal_rv_in(RV_P(base + mi[1]) - ks, mf[1], apout + ks, v + ks, MB - ks, lp, klp, krt);
#endif
	for (k = 0; k < MB; k++) {
		int seg = k >= ks;
		const s16 *pa = RV_P(base + mi[seg]) - 1 - k;
		s32 a = shl(pa[0], 9), b = shl(pa[1], 9);
		s32 x = a + qmul(b - a, mf[seg]), acc = apout[k] + qmul(x, krt);
		lp += qmul(klp, acc - lp);
		v[k] = lp;
	}
	return lp;
}

/* rend 1 si le bloc a ete calcule ainsi (aucune prise ne repasse par le debut du tampon) */
static int rv_block(struct reverb *r, s32 *left, s32 *right)
{
	const s32 kap = r->diffusion, nkap = -r->diffusion;
	s16 *buf = r->buf;
	s32 w0 = r->wp, ks = (w0 - 1) & 31, mi1[2], mf1[2], mi2[2], mf2[2], k;
	s32 *v = sc.ck, *apout = sc.y0;
	static const s16 taps[] = { RV_AP1, RV_AP1T, RV_AP2, RV_AP2T, RV_AP3, RV_AP3T, RV_AP4, RV_AP4T, RV_D1A, RV_D1AT,
				    RV_D1B, RV_D1BT, RV_DEL1, RV_D2A, RV_D2AT, RV_D2B, RV_D2BT, RV_DEL2 };
	struct lfo l0 = r->lfo[0], l1 = r->lfo[1];

	rv_mod(l1.val, 6261, 50, &mi1[0], &mf1[0]);
	rv_mod(l0.val, 4460, 40, &mi2[0], &mf2[0]);
	{
		s32 v0 = lfo_next(&l0), v1 = lfo_next(&l1);
		rv_mod(v1, 6261, 50, &mi1[1], &mf1[1]);
		rv_mod(v0, 4460, 40, &mi2[1], &mf2[1]);
	}
	for (k = 0; k < (s32)(sizeof(taps) / sizeof(taps[0])); k++)
		if (((w0 + taps[k]) & (RV_SIZE - 1)) < MB)
			return 0;
	for (k = 0; k < 2; k++)
		if (((w0 + RV_DEL2 + mi1[k]) & (RV_SIZE - 1)) < MB || ((w0 + RV_DEL1 + mi2[k]) & (RV_SIZE - 1)) < MB)
			return 0;
	r->lfo[0] = l0;
	r->lfo[1] = l1;
	for (k = 0; k < MB; k++)
		v[k] = qmul(left[k] + right[k], r->input_gain);
	rv_ap(RV_P(RV_AP1), RV_P(RV_AP1T), v, kap, nkap, MB);
	rv_ap(RV_P(RV_AP2), RV_P(RV_AP2T), v, kap, nkap, MB);
	rv_ap(RV_P(RV_AP3), RV_P(RV_AP3T), v, kap, nkap, MB);
	rv_ap(RV_P(RV_AP4), RV_P(RV_AP4T), v, kap, nkap, MB);
	for (k = 0; k < MB; k++)
		apout[k] = v[k];
	r->lp1 = rv_branch(buf, w0, apout, v, RV_DEL2, ks, mi1, mf1, r->lp1, r->lp, r->time);
	rv_ap(RV_P(RV_D1A), RV_P(RV_D1AT), v, nkap, kap, MB);
	rv_ap(RV_P(RV_D1B), RV_P(RV_D1BT), v, kap, nkap, MB);
	rv_tail(RV_P(RV_DEL1), v, left, r->amount);
	r->lp2 = rv_branch(buf, w0, apout, v, RV_DEL1, ks, mi2, mf2, r->lp2, r->lp, r->time);
	rv_ap(RV_P(RV_D2A), RV_P(RV_D2AT), v, kap, nkap, MB);
	rv_ap(RV_P(RV_D2B), RV_P(RV_D2BT), v, nkap, kap, MB);
	rv_tail(RV_P(RV_DEL2), v, right, r->amount);
	r->wp = (w0 - MB) & (RV_SIZE - 1);
	return 1;
}

/* Reverb de Rings (rings/dsp/fx/reverb.h sur fx_engine.h, 16 bits) : les memes calculs dans le meme ordre que
 * l'ecriture directe, avec les debuts de lignes en constantes et les decalages des LFO calcules quand ils changent
 * (un pas de LFO par bloc, quand wp & 31 passe a 0). */
static void rv_process(struct reverb *r, s32 *left, s32 *right)
{
	const s32 kap = r->diffusion, nkap = -r->diffusion, klp = r->lp, krt = r->time, amount = r->amount;
	const s32 gain = r->input_gain;
	s16 *buf = r->buf;
	s32 lp1 = r->lp1, lp2 = r->lp2, w = r->wp, i1, f1, i2, f2;
	int k, ks;

	if (r->cleared < RV_SIZE) {
		/* pas encore effacee : le son passe sec, mais le pointeur d'ecriture et les LFO avancent comme dans Rings
		 * (un pas de LFO par bloc : wp & 31 vaut 0 une fois sur 32), pour garder ensuite la meme modulation */
		r->wp = (r->wp - MB) & (RV_SIZE - 1);
		lfo_next(&r->lfo[0]);
		lfo_next(&r->lfo[1]);
		return;
	}
	if (rv_block(r, left, right))
		return;
	ks = (w - 1) & 31;                               /* l'echantillon ou wp & 31 vaut 0 : les LFO avancent */
	rv_mod(r->lfo[1].val, 6261, 50, &i1, &f1);
	rv_mod(r->lfo[0].val, 4460, 40, &i2, &f2);
	for (k = 0; k < MB; k++) {
		s32 acc, prev, apout, x, a, b;
		w = (w - 1) & (RV_SIZE - 1);
		if (k == ks) {
			s32 v0 = lfo_next(&r->lfo[0]), v1 = lfo_next(&r->lfo[1]);
			rv_mod(v1, 6261, 50, &i1, &f1);
			rv_mod(v0, 4460, 40, &i2, &f2);
		}
		acc = qmul(left[k] + right[k], gain);
		prev = RV_GET(RV_AP1T);
		acc += qmul(prev, kap);
		RV_TAP(RV_AP1) = (s16)rv_c(acc);
		acc = qmul(acc, nkap) + prev;
		prev = RV_GET(RV_AP2T);
		acc += qmul(prev, kap);
		RV_TAP(RV_AP2) = (s16)rv_c(acc);
		acc = qmul(acc, nkap) + prev;
		prev = RV_GET(RV_AP3T);
		acc += qmul(prev, kap);
		RV_TAP(RV_AP3) = (s16)rv_c(acc);
		acc = qmul(acc, nkap) + prev;
		prev = RV_GET(RV_AP4T);
		acc += qmul(prev, kap);
		RV_TAP(RV_AP4) = (s16)rv_c(acc);
		acc = qmul(acc, nkap) + prev;
		apout = acc;
		/* branche 1 */
		a = RV_GET(RV_DEL2 + i1);
		b = RV_GET(RV_DEL2 + i1 + 1);
		x = a + qmul(b - a, f1);
		acc = apout + qmul(x, krt);
		lp1 += qmul(klp, acc - lp1);
		acc = lp1;
		prev = RV_GET(RV_D1AT);
		acc += qmul(prev, nkap);
		RV_TAP(RV_D1A) = (s16)rv_c(acc);
		acc = qmul(acc, kap) + prev;
		prev = RV_GET(RV_D1BT);
		acc += qmul(prev, kap);
		RV_TAP(RV_D1B) = (s16)rv_c(acc);
		acc = qmul(acc, nkap) + prev;
		RV_TAP(RV_DEL1) = (s16)rv_c(acc);
		left[k] += qmul(shl(acc, 1) - left[k], amount);
		/* branche 2 */
		a = RV_GET(RV_DEL1 + i2);
		b = RV_GET(RV_DEL1 + i2 + 1);
		x = a + qmul(b - a, f2);
		acc = apout + qmul(x, krt);
		lp2 += qmul(klp, acc - lp2);
		acc = lp2;
		prev = RV_GET(RV_D2AT);
		acc += qmul(prev, kap);
		RV_TAP(RV_D2A) = (s16)rv_c(acc);
		acc = qmul(acc, nkap) + prev;
		prev = RV_GET(RV_D2BT);
		acc += qmul(prev, nkap);
		RV_TAP(RV_D2B) = (s16)rv_c(acc);
		acc = qmul(acc, kap) + prev;
		RV_TAP(RV_DEL2) = (s16)rv_c(acc);
		right[k] += qmul(shl(acc, 1) - right[k], amount);
	}
	r->wp = w;
	r->lp1 = lp1;
	r->lp2 = lp2;
}

/* ---- filtre de note (rings/dsp/note_filter.h) -------------------------------------------------------------- */

struct note_filter {
	s32 prev[4], note, stable;                       /* demi-tons << 16 */
	s32 coef, stable_coef;                           /* Q31 */
	s32 line[16], wp;
};

static void nf_init(struct note_filter *n)
{
	int i;

	n->stable = n->note = 69 << 16;
	n->coef = M_NF_FAST;
	n->stable_coef = M_NF_SLOW;
	for (i = 0; i < 4; i++)
		n->prev[i] = n->note;
	for (i = 0; i < 16; i++)
		n->line[i] = 0;
	n->wp = 0;
}

static void nf_process(struct note_filter *n, s32 note, int strum)
{
	if (iabs(note - n->note) > M_NF_JUMP || strum) {
		int i;
		n->stable = n->note = note;
		n->coef = M_NF_FAST;
		n->stable_coef = M_NF_SLOW;
		for (i = 0; i < 4; i++)
			n->prev[i] = note;
	} else {
		s32 s[4], t, med;
		int i, j;
		n->prev[0] = n->prev[1];
		n->prev[1] = n->prev[2];
		n->prev[2] = n->prev[3];
		n->prev[3] = note;
		for (i = 0; i < 4; i++)
			s[i] = n->prev[i];
		for (i = 1; i < 4; i++)
			for (j = i; j > 0 && s[j - 1] > s[j]; j--) {
				t = s[j];
				s[j] = s[j - 1];
				s[j - 1] = t;
			}
		med = (s[1] + s[2]) >> 1;
		n->note += qmul(n->coef, med - n->note);
		n->stable += qmul(n->stable_coef, n->note - n->stable);
		n->coef += qmul(M_NF_LAG, M_NF_SLOW - n->coef);
		n->stable_coef += qmul(M_NF_LAG, M_NF_LAG - n->stable_coef);
		n->line[n->wp] = n->stable;
		n->wp = (n->wp - 1) & 15;
	}
}

static inline s32 nf_stable(const struct note_filter *n)
{
	return n->line[(n->wp + M_NF_DELAY) & 15];
}

/* ---- la Part (rings/dsp/part.cc) --------------------------------------------------------------------------- */

struct modal_perf {
	s32 strum, internal_exciter, chord;
	s32 note, tonic, fm;                             /* demi-tons << 16 */
	s32 level;                                       /* force de la frappe (la velocite), Q31 ; Q31ONE : Rings */
};

struct modal_patch {
	s32 structure, brightness, damping, position;    /* Q31 */
};

/* les calculs par bloc d'une voix (hauteur, filtre d'excitation, notes des cordes), gardes tant que leurs entrees ne
 * changent pas : les memes valeurs, sans les refaire */
struct vcache {
	s32 valid, note, cut, act, ie;
	xf frequency, fc, a2x, a3x;
	s32 fcq;
	s32 svalid, stonic, snote, sst, schord, sns;     /* render_string : notes des cordes */
	s32 freqs[NSTRINGS];
};

struct modal_part {
	s32 model, poly, dirty, active;
	struct vcache vc[MAXPOLY];
	s32 gvalid, gbright, glide;                      /* render_string : la glissade des cordes sympathiques */
	u32 step;
	s32 note[MAXPOLY];
	u32 rng;
	struct note_filter nf;
	struct svf exc[MAXPOLY];
	struct dcblock dcb[MAXPOLY];
	struct plucker pl[MAXPOLY];
	struct resonator reso[MAXPOLY];
	struct fmvoice fm[MAXPOLY];
	struct lfo slfo[NSTRINGS];
	struct reverb rv;
	s32 peak;                                        /* limiteur, UNIT */
	s32 rin_zero;                                    /* rin nul a l'entree de la voix (pas d'entree) */
	s32 exc_idle[MAXPOLY];                           /* blocs d'excitation muette d'une voix inactive (exc_quiet) */
	s32 rin[MB], sym[MB], ob[MB], ab[MB], nb[MB];
	struct mstring str[NSTRINGS];
};

static const s32 PING[8] = { 1, 0, 2, 1, 0, 2, 1, 0 };
/* modal_pluck lit nb a 4 MB mots de rin */
typedef char modal_nb_at_rin[(__builtin_offsetof(struct modal_part, nb) - __builtin_offsetof(struct modal_part, rin)
			      == 4 * MB * sizeof(s32)) ? 1 : -1];

static void modal_part_init(struct modal_part *p, s16 *reverb_buffer)
{
	int i;

	p->active = 0;
	for (i = 0; i < MAXPOLY; i++) {
		p->note[i] = 0;
		p->exc_idle[i] = 0;
		p->vc[i].valid = p->vc[i].svalid = 0;
	}
	p->gvalid = 0;
	p->poly = 1;
	p->model = MODEL_MODAL;
	p->dirty = 1;
	p->step = 0;
	p->rng = 0x21;
	for (i = 0; i < MAXPOLY; i++) {
		svf_set(&p->exc[i], tan_dirty(M_001), XC(M_R100), 0, 0);
		svf_reset(&p->exc[i]);
		pl_init(&p->pl[i]);
		dc_init(&p->dcb[i], M_POLE10);
	}
	rv_init(&p->rv, reverb_buffer);
	p->peak = UNIT >> 1;
	nf_init(&p->nf);
}

static void modal_set_poly(struct modal_part *p, int n)
{
	int old = p->poly, i;

	p->poly = n > MAXPOLY ? MAXPOLY : n;
	for (i = old; i < p->poly; i++)
		p->note[i] = p->note[0] + i * M_005;
	p->dirty = 1;
}

static void modal_set_model(struct modal_part *p, int m)
{
	if (m != p->model) {
		p->model = m;
		p->dirty = 1;
	}
}

static void configure(struct modal_part *p)
{
	int i;

	if (!p->dirty)
		return;
	switch (p->model) {
	case MODEL_MODAL:
		for (i = 0; i < p->poly; i++)
			reso_init(&p->reso[i], (64 / p->poly - 4) / 2);   /* eco : la moitie des modes de Rings */
		break;
	case MODEL_SYMPATHETIC:
	case MODEL_STRING:
	case MODEL_SYMPATHETIC_Q:
	case MODEL_STRING_REVERB:
		for (i = 0; i < NSTRINGS; i++) {
			str_init(&p->str[i], p->model == MODEL_STRING || p->model == MODEL_STRING_REVERB);
			lfo_init(&p->slfo[i], M_SLFO[i]);
		}
		for (i = 0; i < p->poly; i++)
			pl_init(&p->pl[i]);
		break;
	case MODEL_FM:
		for (i = 0; i < p->poly; i++)
			fm_init(&p->fm[i]);
		break;
	}
	if (p->active >= p->poly)
		p->active = 0;
	for (i = 0; i < MAXPOLY; i++)
		p->exc_idle[i] = 0;
	p->dirty = 0;
}

static s32 squash(s32 x)                             /* Q31, x dans [0, 1) */
{
	s32 y;
	if (x < 0x40000000) {
		y = shl(x, 1);
		y = qmul(y, y);
		y = qmul(y, y);
		y = qmul(y, y);
		y = qmul(y, y);
		return y >> 1;
	}
	y = (s32)(0u - (u32)shl(x, 1));                 /* 2 - 2 x : 2^32 - 2 x 2^31 */
	if (y < 0)
		y = Q31ONE;
	y = qmul(y, y);
	y = qmul(y, y);
	y = qmul(y, y);
	y = qmul(y, y);
	return Q31ONE - (y >> 1);
}

static void sym_notes(struct modal_part *p, s32 tonic, s32 note, s32 parameter, int chord, s32 *dest, int ns)
{
	s32 notes[9];
	int nd, first, i;

	if (chord >= 0) {                                /* eco : la table de Rings pour 4, 2 puis 1 corde par voix */
		const s32 *c = p->poly == 1 ? &M_CHORDS[chord * 4] : &M_CHORDS[44 + chord * 2];
		for (i = 0; i < ns; i++)
			dest[i] = c[i] + note;
		return;
	}
	notes[0] = tonic;
	notes[1] = note - (12 << 16);
	notes[2] = note - M_FIFTH;
	notes[3] = note;
	notes[4] = note + M_FIFTH;
	notes[5] = note + (12 << 16);
	notes[6] = note + (12 << 16) + M_FIFTH;
	notes[7] = note + (24 << 16);
	notes[8] = note + (24 << 16);
	nd = (ns - 1) >> 1;
	first = ns - nd;
	for (i = 0; i < first; i++) {
		s32 n, ni, nfrac, a, b;
		if (i == 0) {
			ni = 3;
			nfrac = 0;
		} else {
			n = qmul(parameter, 7 << 24);          /* parameter x 7, Q24 */
			parameter += qmul(Q31ONE - parameter, Q31(0.2));
			ni = n >> 24;
			nfrac = shl(n, 7) & Q31ONE;
		}
		nfrac = squash(nfrac);
		a = notes[ni];
		b = notes[ni + 1];
		dest[i] = a + qmulr(b - a, nfrac);           /* arrondi, comme le float32 de Rings */
		if (i + first < ns)
			dest[i + first] = dest[i] + M_DETUNE[i & 3];
	}
}

/* La chaine d'excitation d'une voix inactive (son entree est nulle : filtre d'excitation, pincement, filtre
 * anti-continu) qui est restee sous -108 dB pendant EXC_IDLE blocs n'est plus calculee, jusqu'a ce que la voix
 * redevienne active : elle ne sort plus que des restes sous 2^-18 (l'arrondi par defaut du peigne du pincement la
 * laisse osciller sur un LSB au lieu de s'eteindre). Rings la calcule ; la corde ou le resonateur de la voix,
 * eux, continuent de resonner. */
#define EXC_IDLE 8

static int exc_quiet(struct modal_part *p, int v, const s32 *x)
{
	int k;

	if (v == p->active) {
		p->exc_idle[v] = 0;
		return 0;
	}
	for (k = 0; k < MB; k++)
		if (x[k] > MODE_EPS || x[k] < -MODE_EPS) {
			p->exc_idle[v] = 0;
			return 0;
		}
	if (p->exc_idle[v] < EXC_IDLE)
		p->exc_idle[v]++;
	return 1;
}

static inline int exc_skip(const struct modal_part *p, int v)
{
	return v != p->active && p->exc_idle[v] >= EXC_IDLE;
}

static void render_string(struct modal_part *p, int voice, const struct modal_perf *ps,
			  const struct modal_patch *pa, xf frequency, xf fc)
{
	s32 freqs[NSTRINGS], dispersion, st = pa->structure;
	int ns = 1, i;

	if (p->model == MODEL_SYMPATHETIC || p->model == MODEL_SYMPATHETIC_Q) {
		struct vcache *vc = &p->vc[voice];
		s32 tonic = ps->tonic + ps->fm, note = ps->tonic + p->note[voice] + ps->fm;
		int chord = p->model == MODEL_SYMPATHETIC ? -1 : ps->chord;
		ns = MAXPOLY / p->poly;                      /* eco : 4, 2, 1 cordes par voix (Rings : 8, 4, 2) */
		if (!vc->svalid || vc->stonic != tonic || vc->snote != note || vc->sst != st || vc->schord != chord
		    || vc->sns != ns) {
			s32 notes[NSTRINGS];
			sym_notes(p, tonic, note, st, chord, notes, ns);
			for (i = 0; i < ns; i++)
				vc->freqs[i] = xto(xmul(xs2r(notes[i] - (69 << 16)), XC(M_A3)), 31);
			vc->svalid = 1;
			vc->stonic = tonic;
			vc->snote = note;
			vc->sst = st;
			vc->schord = chord;
			vc->sns = ns;
		}
		for (i = 0; i < ns; i++)
			freqs[i] = vc->freqs[i];
	} else {
		freqs[0] = xto(frequency, 31);
	}
	if (!exc_skip(p, voice)) {                       /* sinon : rin reste a zero (exc_quiet) */
		struct svf *e = &p->exc[voice];
		if (voice == p->active && !p->rin_zero) {
			s32 g = M_SQRTG[ns];
			for (i = 0; i < MB; i++)
				p->rin[i] = qmul(p->rin[i], g);
		}
		if (!p->rin_zero || e->ic1 || e->ic2)        /* entree et etat nuls : sa sortie est nulle */
			svf_lp_block(e, p->rin, MB, 0, 0);
		if (ps->internal_exciter) {
			if (voice == p->active && ps->strum)
				pl_trigger(&p->pl[voice], frequency, xscale(fc, 3), pa->position, ps->level);
#ifdef MODAL_ASM
			if (!p->pl[voice].remaining) {
				modal_pluck(&p->pl[voice], p->rin, &p->dcb[voice]);   /* modal_asm.S */
				goto done;
			}
#endif
			pl_process(&p->pl[voice], p->nb, &p->rng);
			for (i = 0; i < MB; i++)
				p->rin[i] += p->nb[i];
		}
		for (i = 0; i < MB; i++)
			p->rin[i] = dc_one(&p->dcb[voice], p->rin[i]);
#ifdef MODAL_ASM
	done:
#endif
		exc_quiet(p, voice, p->rin);
	}
	for (i = 0; i < MB; i++)
		p->ob[i] = p->ab[i] = 0;
	dispersion = st < Q31(0.24) ? shl(qmul(st - Q31(0.24), Q31(4.166 / 8)), 2)
		: (st > Q31(0.26) ? qmul(st - Q31(0.26), Q31(1.35135 / 2)) : 0);       /* Q30 */
	for (i = 0; i < ns; i++) {
		int idx = voice + i * p->poly;
		struct mstring *s = &p->str[idx];
		s32 lfo = lfo_next(&p->slfo[idx]);
		s32 brightness = pa->brightness, damping = pa->damping, position = pa->position;
		s32 glide = Q31ONE, sidx = i * (Q31ONE / ns);
		const s32 *input = p->rin;
		if (p->model == MODEL_STRING_REVERB)
			damping = b2mb(damping);
		if (i > 0 && ps->internal_exciter) {
			s32 amount;
			brightness = b2mb(brightness);
			brightness = b2mb(brightness);
			damping = Q31(0.7) + qmul(pa->damping, Q31(0.27));
			amount = qmul(0x40000000 - iabs(0x40000000 - pa->position), Q31(0.9));
			position = pa->position + qmul(lfo, amount);
			if (!p->gvalid || p->gbright != pa->brightness) {
				p->glide = xto(xs2r(qmul(brightness - Q31ONE, 36 << 16)), 31);
				p->gbright = pa->brightness;
				p->gvalid = 1;
			}
			glide = p->glide;
			input = p->sym;
		}
		s->dispersion = dispersion;
		if (glide == Q31ONE)
			s->frequency = freqs[i];
		else
			s->frequency += qmul(glide, freqs[i] - s->frequency);
		s->brightness = brightness;
		s->position = position;
		s->damping = damping + qmul(sidx, Q31(0.95) - damping);
		str_process(s, input, p->ob, p->ab, &p->rng);
		if (i == 0) {
			s32 g = M_SYMG[ns];
			int k;
			for (k = 0; k < MB; k++)
				p->sym[k] = qmul(g, p->ob[k] - p->ab[k]);
		}
	}
}

/* le gain du limiteur au-dessus de 1,0 : 0,8 / peak (peak en UNIT, > UNIT), en Q31. L'inverse de xrecip (une
 * division 32/32 puis une iteration de Newton, ~30 bits justes), sans le flottant maison : il change a chaque
 * echantillon. */
static inline s32 lim_gain(s32 peak)
{
	int n = __builtin_clz((u32)peak) - 1;            /* 1..6 : peak dans (2^24, 2^31) */
	s32 m = shl(peak, n), z, t;                      /* [2^30, 2^31) : m / 2^30 dans [1, 2) */

	z = (s32)((0xffffffffu / (u32)(m >> 15)) << 13); /* 1 / m en Q30, 16 bits justes */
	t = (s32)(0x80000000u - (u32)shl(qmul(m, z), 1));
	z = qmul(shl(qmul(z, t), 1), Q31(0.8));         /* 0,8 / m, Q30 */
	return n >= 5 ? shl(z, n - 5) : z >> (5 - n);    /* 0,8 / peak = (0,8 / m) 2^(n - 6) */
}

/* in : l'entree (UNIT), ou NULL sans entree ; out, aux : les deux sorties de Rings, apres le limiteur (UNIT) */
static void modal_process(struct modal_part *p, const struct modal_perf *ps, const struct modal_patch *pa,
			  const s32 *in, s32 *out, s32 *aux)
{
	s32 cutoff;
	int v, k, in_zero = 1;

	if (in)                                          /* l'entree de la piste ; NULL : pas d'entree (MODAL, pour */
		for (k = 0; k < MB; k++)                 /* l'instant : l'excitateur interne seulement) */
			if (in[k])
				in_zero = 0;
	rv_clear_step(&p->rv);                           /* la reverbe s'efface par morceaux apres l'initialisation */
	configure(p);
	nf_process(&p->nf, ps->note, ps->strum);
	if (ps->strum) {
		p->note[p->active] = nf_stable(&p->nf);
		if (p->poly > 1 && (p->poly & 1)) {
			p->active = PING[p->step & 7];
			p->step = (p->step + 1) & 7;
		} else {
			p->active = (p->active + 1) % p->poly;
		}
	}
	p->note[p->active] = p->nf.note;
	for (k = 0; k < MB; k++)
		out[k] = aux[k] = 0;
	cutoff = b2mb(pa->brightness);
	for (v = 0; v < p->poly; v++) {
		s32 note = p->note[v] + ps->tonic + ps->fm, fcq;
		struct vcache *vc = &p->vc[v];
		xf frequency, fc, a2x, a3x;
		int act = v == p->active;
		if (!vc->valid || vc->note != note || vc->cut != cutoff || vc->act != act
		    || vc->ie != ps->internal_exciter) {
			frequency = xmul(xs2r(note - (69 << 16)), XC(M_A3));
			if (ps->internal_exciter)
				fc = xmul(frequency, xs2r(qmul(cutoff - 0x40000000, 96 << 16)));
			else
				fc = xmul(XC(M_04), xs2r(qmul(cutoff - Q31ONE, 108 << 16)));
			if (!act)
				fc = XC(M_FCIDLE);
			fc = xmin(fc, XC(M_0499));
			fcq = xto(fc, 31);
			svf_set(&p->exc[v], tan_dirty(fcq), ps->internal_exciter ? XC(M_R150) : XC(M_R080), &a2x, &a3x);
			vc->valid = 1;
			vc->note = note;
			vc->cut = cutoff;
			vc->act = act;
			vc->ie = ps->internal_exciter;
			vc->frequency = frequency;
			vc->fc = fc;
			vc->fcq = fcq;
			vc->a2x = a2x;
			vc->a3x = a3x;
		} else {
			frequency = vc->frequency;
			fc = vc->fc;
			fcq = vc->fcq;
			a2x = vc->a2x;
			a3x = vc->a3x;
		}
		{
			s32 *ri = p->rin;
			p->rin_zero = !(v == p->active && !in_zero);
			if (!p->rin_zero)
				for (k = 0; k < MB; k++)
					ri[k] = in[k];
			else
				for (k = 0; k < MB; k++)
					ri[k] = 0;
		}
		if (p->model == MODEL_MODAL) {
			s32 p2 = 0, p3 = 0;
			struct resonator *r = &p->reso[v];
			if (ps->internal_exciter && v == p->active && ps->strum) {
				xf pulse = xscale(xmul(xs2r(qmul(qmul(fcq, fcq), 24 << 16)), xrecip(fc)), -2);
				if (ps->level != Q31ONE)
					pulse = xmul(pulse, xfrom(ps->level, 31));
				p2 = xto(xmul(a2x, pulse), 24);
				p3 = xto(xmul(a3x, pulse), 24);
			}
			if (!exc_skip(p, v)) {
				svf_lp_block(&p->exc[v], p->rin, MB, p2, p3);
				exc_quiet(p, v, p->rin);
			}
			r->frequency = frequency;
			r->structure = pa->structure;
			r->brightness = qmul(pa->brightness, pa->brightness);
			r->position = pa->position;
			r->damping = pa->damping;
			reso_process(r, p->rin, p->ob, p->ab);
		} else if (p->model == MODEL_FM) {
			struct fmvoice *f = &p->fm[v];
			if (ps->internal_exciter && v == p->active && ps->strum) {
				f->amp_env = ps->level == Q31ONE ? UNIT : qmul(UNIT, ps->level);
				f->bright_env = f->amp_env;
			}
			f->carrier = frequency;
			f->ratio = pa->structure;
			f->brightness = pa->brightness;
			f->feedback_amount = pa->position;
			f->damping = pa->damping;
			fm_process(f, p->rin, p->ob, p->ab, in_zero || v != p->active);
		} else {
			render_string(p, v, ps, pa, frequency, fc);
		}
		if (p->poly == 1) {
			for (k = 0; k < MB; k++) {
				out[k] += p->ob[k];
				aux[k] += p->ab[k];
			}
		} else {
			s32 *d = (v & 1) ? aux : out;
			const s32 *ob = p->ob, *ab = p->ab;
			for (k = 0; k < MB; k++)
				d[k] += ob[k] - ab[k];
		}
	}
	if (p->model == MODEL_STRING_REVERB) {
		s32 pos = pa->position;
		for (k = 0; k < MB; k++) {
			s32 l = out[k], r = aux[k];
			out[k] = qmul(l, pos) + qmul(r, Q31ONE - pos);
			aux[k] = qmul(r, pos) + qmul(l, Q31ONE - pos);
		}
		p->rv.amount = Q31(0.1) + qmul(pa->damping, Q31(0.5));
		p->rv.diffusion = Q31(0.625);
		p->rv.time = Q31(0.35) + qmul(pa->damping, Q31(0.63));
		p->rv.input_gain = Q31(0.2);
		p->rv.lp = Q31(0.3) + qmul(pa->brightness, Q31(0.6));
		rv_process(&p->rv, out, aux);
		for (k = 0; k < MB; k++)
			aux[k] = -aux[k];
	}
	/* limiteur */
	{
		s32 pg = M_GAINS[p->model], peak = p->peak, g = Q31(0.8);
		for (k = 0; k < MB; k++) {
			s32 l = shl(qmul(out[k], pg), 1), r = shl(qmul(aux[k], pg), 1);
			s32 pk = iabs(l), t = iabs(r), err;
			if (t > pk)
				pk = t;
			t = iabs(r - l);
			if (t > pk)
				pk = t;
			err = pk - peak;
			peak += qmul(err > 0 ? Q31(0.05) : M_LIM_DEC, err);
			g = peak <= UNIT ? Q31(0.8) : lim_gain(peak);
			out[k] = softlimit(qmul(l, g));
			aux[k] = softlimit(qmul(r, g));
		}
		p->peak = peak;
	}
}

#endif
