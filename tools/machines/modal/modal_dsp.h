/*
 * MODAL : le coeur du son, en virgule fixe, sans FPU.
 *
 * Reecriture de la Part de Rings (Emilie Gillet, Mutable Instruments, 2015, licence MIT : LICENSE-Rings) et de
 * ce qu'elle utilise de stmlib : resonateur modal (filtres passe-bande), cordes (Karplus-Strong, dispersion,
 * cordes sympathiques, accords), voix FM, excitateurs internes (impulsion filtree, bruit pince), reverbe, filtre
 * de note, limiteur. Memes calculs, dans le meme ordre, au meme rythme ; reglages « eco » (notes/74) : la moitie
 * des modes de Rings, 4 cordes au lieu de 8. Le synthe cache de Rings (StringSynthPart, « easter egg ») n'y est pas.
 * Calcule a 24 kHz, par blocs de 16 trames (notes/81, modal_cfg.h) : ce qui compte en echantillons est recale pour
 * garder ses durees en secondes et ses frequences en hertz (tools/emu/test_modal_dsp.py, SR24), et la passerelle
 * (modal.c) remonte la sortie a 48 kHz.
 *
 * Ce fichier sert deux fois : compile pour le Cycles (modal.c, -mcpu=54418, l'EMAC) et pour l'ordinateur
 * (tools/emu/modal_host.c) avec la meme arithmetique a l'octet pres (modal_fix.h) ; la preuve
 * (tools/emu/test_modal_dsp.py) compare a Rings en flottant (tools/emu/rings_ref.cc).
 *
 * Formats : signaux 1,0 = 2^24 (UNIT) ; potards Q31 (0..1) ; hauteurs en demi-tons << 16 ; frequences
 * normalisees (f / 24 kHz) en Q31 ou en xf ; retards en echantillons, Q11.20.
 */
#ifndef MODAL_DSP_H
#define MODAL_DSP_H

#include "modal_fix.h"
#include "modal_cfg.h"                               /* MB, DLINE, SLINE (avec modal_asm.S) */

#define UNIT        (1 << 24)
#define MAXPOLY     4
#define NSTRINGS    4                                /* eco : 4 cordes au lieu de 8 */
#define MAXMODES    32                               /* eco : 30 modes au plus ((64 / polyphonie - 4) / 2) ; modal_asm.S */

/* les numeros de Rings (ResonatorModel) ; ni la voix FM (3) ni la corde et reverbe (5) : choix de Maxime (22/10/2026) */
enum { MODEL_MODAL = 0, MODEL_SYMPATHETIC = 1, MODEL_STRING = 2, MODEL_SYMPATHETIC_Q = 4 };

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

#ifdef MODAL_ASM
s32 modal_softbig(s32 a);                            /* pour modal_lim (modal_asm.S) */
s32 modal_softbig(s32 a)
{
	return softlimit_big(a);
}
void modal_lim(const s32 *oa, s32 *w, s32 *peak, const s32 *k);   /* modal_asm.S */
#endif

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

/* MB tirages d'un coup : s <- A s + C, A = 1664525^16, C = 1013904223 (1664525^15 + ... + 1), modulo 2^32 */
#define M_LCG16A    0x77520441u
#define M_LCG16C    0x83c6b450u
typedef char modal_lcg16[MB == 16 ? 1 : -1];

static u32 rng_next(u32 *s)                          /* stmlib Random::GetWord */
{
	*s = *s * 1664525u + 1013904223u;
	return *s;
}

static inline s32 rng_q31(u32 *s)                     /* 2 GetFloat() - 1, en Q31 */
{
	return (s32)(rng_next(s) ^ 0x80000000u);
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

/* tanf(pi f) de stmlib (OnePole::tan<FREQUENCY_EXACT>, f borne a 0,497), f en Q31 (notes/81 : a 24 kHz, les modes
 * et les filtres montent jusqu'a 0,49, ou les approximations de Rings, faites pour 48 kHz, ne tiennent plus).
 * sin(x) / cos(x) par leurs series jusqu'a x^11 sur [0, pi/4] (x = pi f), et tan(pi f) = 1 / tan(pi (1/2 - f))
 * au-dela : environ 1e-9 d'ecart. */
static __attribute__((noinline)) xf tan_exact(s32 f)
{
	s32 z, z2, ps, pc, sn, cs;
	int inv;

	if (f > M_0497Q)
		f = M_0497Q;
	inv = f > 0x20000000;
	if (inv)
		f = 0x40000000 - f;
	z = shl(qmul(f, Q31(3.14159265358979 / 4)), 1);   /* x / 2, Q31 (<= pi / 8) */
	z2 = qmul(z, z);                                   /* x^2 / 4 */
	/* sin(x) / x = 1 - x^2/6 (1 - x^2/20 (1 - x^2/42 (1 - x^2/72 (1 - x^2/110)))) */
	ps = Q31ONE - qmul(z2, Q31(4.0 / 110));
	ps = Q31ONE - qmul(qmul(z2, Q31(4.0 / 72)), ps);
	ps = Q31ONE - qmul(qmul(z2, Q31(4.0 / 42)), ps);
	ps = Q31ONE - qmul(qmul(z2, Q31(4.0 / 20)), ps);
	ps = Q31ONE - qmul(qmul(z2, Q31(4.0 / 6)), ps);
	sn = qmul(z, ps);                                  /* sin(x) / 2, Q31 */
	/* cos(x) = 1 - x^2/2 (1 - x^2/12 (1 - x^2/30 (1 - x^2/56 (1 - x^2/90)))) */
	pc = Q31ONE - qmul(z2, Q31(4.0 / 90));
	pc = Q31ONE - qmul(qmul(z2, Q31(4.0 / 56)), pc);
	pc = Q31ONE - qmul(qmul(z2, Q31(4.0 / 30)), pc);
	pc = Q31ONE - qmul(qmul(z2, Q31(4.0 / 12)), pc);
	cs = Q31ONE - shl(qmul(z2, pc), 1);                /* cos(x), Q31 */
	if (!sn)
		return xfrom(0, 0);
	return inv ? xmul(xfrom(cs, 31), xrecip(xfrom(sn, 30)))
		   : xmul(xfrom(sn, 30), xrecip(xfrom(cs, 31)));
}

/* cos(pi f), Q31, f dans [0, 1/2] (Q31) : la table des sinus (sin(2 pi (f / 2 + 1/4))) */
static s32 cospi_q31(s32 f)
{
	s32 i = 1024 + (f >> 20), fr = shl(f, 11) & Q31ONE;
	s32 a = m_sine[i], b = m_sine[i + 1];
	return shl(a, 16) + qmul(shl(b - a, 16), fr);
}

/* le facteur de qualite des filtres d'excitation et du pincement (notes/81) : q0 jusqu'a la coupure 0,6, puis vers
 * 0,7071 a 0,998 (q0 + d t, d = 0,7071 - q0, t = (f - 0,6) / 0,398 borne a [0, 1]) ; rend 1 / q */
static __attribute__((noinline)) xf q_fade_r(s32 fq, xf q0, xf d, xf r0)
{
	s32 t;

	if (fq <= M_06Q)
		return r0;
	t = shl(qmul(fq - M_06Q, M_R0398), 2);           /* (f - 0,6) / 0,398, M_R0398 en Q29 */
	if (t < 0 || t > Q31ONE)
		t = Q31ONE;
	return xrecip(xadd(q0, xmul(d, xfrom(t, 31))));
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
	s32 nc[MB];                                      /* le peigne d'une corde sans peigne, jamais lu (str_process) */
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
typedef char modal_mb_shift[(1 << MB_SHIFT) == MB ? 1 : -1];
void modal_str_read(const s32 *ph, s32 f, const s32 *in, s32 *hb, int n);
void modal_str_damp(s32 *hb, s32 *dk, int n);
void modal_str_write(const s32 *hb, s32 *pw, s32 *out, const s32 *dpp, int n);
void modal_str_read_ap(const s32 *ph, s32 f, s32 *hb, int n, s32 *ap);
void modal_str_read_mv(const s32 *pw, s32 *st, const s32 *in, s32 *hb, int n);
void modal_str_read_nz(s32 *line, s32 *hb, const s32 *in, int n, s32 *k);
void modal_str_run(s32 *pw, const s32 *pr, const s32 *in, s32 *out, int n, s32 *k);
void modal_str_comb(const s32 *pb, s32 *aux, int n, s32 *cp);
void modal_str_read_cb(s32 *line, s32 *hb, const s32 *in, int n, s32 *k);
void modal_str_damp_mv(s32 *hb, s32 *dk);
void modal_str_write_mv(const s32 *hb, s32 *pw, s32 *out, s32 *dpp, int n);
#endif

struct resonator {
	struct mode md[MAXMODES];
	/* la 1re passe de reso_compute (frequences des partiels, tangentes), gardee tant que frequence et structure ne
	 * changent pas : BRIGHTNESS et DAMPING ne refont que les facteurs de qualite */
	s32 kv1, ks, knum, kfresh;
	xf kf;
	s32 kpq[MAXMODES], kpfm[MAXMODES], kpfe[MAXMODES], kgm[MAXMODES], kge[MAXMODES], kcos[MAXMODES];
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
 * modes calcules (reso_process en fait (num + 1) & ~1). Les memes valeurs pour ceux-la que la boucle unique de Rings.
 * A 24 kHz (notes/81) : tangente exacte, et le facteur de qualite multiplie par cos(pi f), pour que chaque mode
 * garde sa duree en secondes jusqu'a la moitie de la frequence d'echantillonnage. */
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
			r->kcos[i] = cospi_q31(r->kpq[i]);
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
	q = xmul(XC(M_QMODE), xfrom(interp(M_DEC4, r->damping, 8), 17));
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
			g = tan_exact(r->kpq[i]);
			r->kgm[i] = g.m;
			r->kge[i] = g.e;
		} else {
			g = xmk(r->kgm[i], r->kge[i]);
		}
		mode_set(&r->md[i], g, xrecipp(xmulp(xaddp(xmk(1 << 30, 0), xmulp(xmk(r->kpfm[i], r->kpfe[i]), q)),
						     xfromp(r->kcos[i], 31))));
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
/* noinline : en ligne dans modal_process, GCC y tient moins bien les registres (2 a 10 % de plus, 22/10/2026) */
static __attribute__((noinline)) void reso_process(struct resonator *r, const s32 *in, s32 *out, s32 *aux)
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
			da[i] = (da[i] - a0[i]) >> MB_SHIFT;
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
	/* le chemin court (str_fast, notes/81) : rien ne bouge que la position et le retard ; ce qu'il lit, prepare par
	 * str_plan. kver : compte les str_block ; kf_full : la frequence du dernier ; lite : glissade (str_delay) */
	s32 fast, fdisp, fdi, ff, fh0, fh1, fap, fapj, fver, fmode, fd0;
	s32 kver, kf_full, lite;
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
	s->fast = 0;
	s->kver = 0;
	s->kf_full = 0;
	s->lite = 0;
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

/* La lecture de la ligne d'une corde : lineaire (Read de stmlib, a la place du ReadHermite de Rings : le choix du
 * budget de 13 %, notes/81), le produit arrondi (la boucle ne doit pas deriver vers le bas). p = &line[wp + partie
 * entiere du retard], sans masque (p + 1 < line + 2 DLINE) ; f : la partie fractionnaire, Q31. */
static inline s32 rd_lin(const s32 *p, s32 f)
{
	return p[0] + qmulr(p[1] - p[0], f);
}

static inline s32 rd_linear(const s32 *line, s32 mask, s32 wp, s32 delay)
{
	s32 i = wp + (delay >> 20), f = shl(delay, 11) & Q31ONE;
	s32 a = line[i & mask], b = line[(i + 1) & mask];
	return a + qmul(b - a, f);
}

static inline s32 rd_linm(const s32 *line, s32 wp, s32 delay)  /* rd_lin avec masque */
{
	s32 t = wp + (delay >> 20), f = shl(delay, 11) & Q31ONE;
	s32 x0 = line[t & (DLINE - 1)], x1 = line[(t + 1) & (DLINE - 1)];
	return x0 + qmulr(x1 - x0, f);
}


/* le facteur du retard de la dispersion (Q30), au moins 1/2 : le chevalet courbe ne peut pas raccourcir la corde
 * de plus de moitie (un plancher que le son n'atteint pas ; le chemin en assembleur s'y fie, notes/81) */
static inline s32 disp_fm(s32 m)
{
	return m < (1 << 29) ? 1 << 29 : m;
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
	nfilt = b2mb(nfilt);                             /* 24 kHz : deux pas de 48 kHz par pas (notes/81) */
	dcut = (24 << 16) + qmul(qmul(s->damping, s->damping), 48 << 16) + qmul(bright, 24 << 16);
	if (dcut > (84 << 16))
		dcut = 84 << 16;
	df = xto(xmin(xscale(xmul(fx, xs2r(dcut)), -1), XC(M_0499)), 31);   /* la coupure de 48 kHz (notes/81) */
	if (s->damping >= M_095) {
		s32 dd = s->damping - M_095;
		s32 ti = dd >= Q31ONE / 20 ? Q31ONE : dd * 20;   /* 20 (d - 0,95) : 1,0 au plus, sans deborder */
		dcoef += qmul(ti, Q31ONE - dcoef);
		bright += qmul(ti, Q31ONE - bright);
		df += qmul(ti, M_04999 - df);
		dcut += qmul(ti, (128 << 16) - dcut);
	}
	svf_set(&s->iir, xscale(tan_accurate(df), 1), xmk(1 << 30, 1), 0, 0);   /* son prototype de 48 kHz : 2 g48 */
	s->k_dcomp = Q31ONE - interp(M_SVFSHIFT, dcut, 15);
	s->k_nk = xto(xrecip(xadd(XC(M_02), xfrom(nfilt, 31))), 28);   /* 1 / (0,2 + nf), Q28 */
	s->k_delay = delay;
	s->k_unit = unit;
	s->k_ratio = src_ratio;
	s->k_dcoef = dcoef;
	s->k_bright = 0x60000000 + (bright >> 2);       /* 3/4 + b/4 : la courbe du FIR de 48 kHz (notes/81) */
	s->k_nfilt = nfilt;
	s->kf = s->frequency;
	s->kd = s->damping;
	s->kb = s->brightness;
	s->kvalid = 1;
	s->kf_full = s->frequency;
	s->kver++;
}

/* La glissade des cordes sympathiques (notes/81) : tant que la frequence glisse, seul le retard la suit (Rings
 * refait tout a chaque bloc ; les autres coefficients changent a peine sur ces quelques dizaines de millisecondes),
 * et str_block refait tout des qu'elle s'arrete. Rend 0 hors de ce que couvre le chemin simple (retard borne,
 * surechantillonnage) : alors str_block. */
static int str_delay(struct mstring *s)
{
	s32 delay = xto(xrecip(xfrom(s->frequency, 31)), 20);

	if (delay < (4 << 20) || delay >= ((DLINE - 4) << 20) || s->k_ratio != (1 << 29))
		return 0;
	s->k_delay = delay;
	s->kf = s->frequency;
	return 1;
}

/* la glissade ne refait que le retard tant qu'elle reste a moins de 1 / 2^LITE_SHIFT de la frequence du dernier
 * str_block */
#ifndef LITE_SHIFT
#define LITE_SHIFT  5
#endif

/* les calculs par bloc de String::ProcessInternal, quand leurs entrees changent */
static void str_params(struct mstring *s)
{
	if (!s->kvalid || s->kd != s->damping || s->kb != s->brightness)
		str_block(s);
	else if (s->kf != s->frequency) {
		if (!s->lite || iabs(s->frequency - s->kf_full) > (s->kf_full >> LITE_SHIFT) || !str_delay(s))
			str_block(s);
	} else if (s->kf_full != s->kf) {
		str_block(s);                            /* la glissade s'est arretee */
	}
}

/* La passe 3 d'une corde sans peigne (les cordes sympathiques, notes/81) : la ligne et out seulement, n echantillons */
static void str_wout(const s32 *hb, s32 *line, s32 wp, s32 *out, int n)
{
	int k;

	for (k = 0; k < n; k++) {
		line[wp] = line[wp + DLINE] = hb[k];
		wp = (wp - 1) & (DLINE - 1);
		out[k] += hb[k];
	}
}

#ifdef MODAL_ASM
/* Le chemin court d'une corde (notes/81) : quand plus rien ne bouge (frequence, amortissement, brillance, dispersion
 * et les rampes de str_process arrivees au bout ; ligne et etirement effaces jusqu'au bout ; ni surechantillonnage,
 * ni modulation du retard, ni anti-continu), str_process ferait exactement ceci : ses passes en assembleur, avec ce
 * que str_plan a prepare. Seuls la position (le peigne de aux) et, sans dispersion, le retard (la glissade des cordes
 * sympathiques) peuvent bouger. Les passes vont par morceaux de c echantillons, c la partie entiere du retard la
 * plus courte du bloc (MB au plus) : rien de ce qu'un morceau lit n'est ecrit par lui (les notes aigues). */
static __attribute__((noinline)) void str_fast(struct mstring *s, const s32 *in, s32 *out, s32 p_inc, s32 d_inc,
						u32 *rng, int comb)
{
	s32 *hb = sc.x, *line = s->line, *aux = out + MB, wp = s->wp;
	s32 a30 = aux[MB - 2], a31 = aux[MB - 1], dk[9], dpp[4], st[4], di = s->fdi, ff = s->ff;
	int k0, c, cs;

	if (s->enable_dispersion) {
		if (s->fmode != 2)                       /* le bruit de dispersion ne sert pas : ses tirages d'un coup */
			*rng = *rng * M_LCG16A + M_LCG16C;
		cs = di;
	} else {
		s32 d = qmul(s->delay, s->prev_damp_comp) - (1 << 20);
		s32 d1 = qmul(s->delay + MB * d_inc, s->prev_damp_comp) - (1 << 20);
		di = d >> 20;
		ff = shl(d, 11) & Q31ONE;
		cs = (d < d1 ? d : d1) >> 20;
	}
	cs = cs > MB ? MB : (cs < 1 ? 1 : cs);         /* 1 : lu avant d'etre ecrit, comme dans la boucle de str_process */
	if (cs == MB && !d_inc && !s->fap && !s->fmode) {
		/* le cas courant : une boucle (modal_str_run) puis le peigne a part (modal_str_comb) ; quand sa lecture
		 * tombe sur la place que l'echantillon suivant va ecrire (comb >> 20 nul : POSITION a un bout, une corde
		 * aigue), l'ancien contenu de cette place, garde avant la boucle */
		s32 pv0 = s->clamped_position;
		{
			s32 kk[11], old[MB];
			int n1 = wp + 1 < MB ? wp + 1 : MB, n3 = wp < MB ? wp : MB, k;
			int whole = !comb || (qmul(s->delay, pv0 + p_inc) >= (1 << 20)
					      && qmul(s->delay, pv0 + MB * p_inc) >= (1 << 20));
			if (!whole)
				for (k = 1; k < MB; k++)
					old[k] = line[(wp - k) & (DLINE - 1)];
			kk[0] = ff;
			kk[1] = s->fh0;
			kk[2] = s->fh1;
			kk[3] = -s->iir.b;
			kk[4] = s->iir.a2;
			kk[5] = s->iir.a3;
			kk[6] = s->fx1;
			kk[7] = s->fx2;
			kk[8] = s->iir.ic1;
			kk[9] = s->iir.ic2;
			modal_str_run(&line[wp], &line[wp + di], in, out, n1, kk);
			modal_str_run(&line[DLINE - 1], &line[DLINE - 1 + di], in + n1, out + n1, MB - n1, kk);
			s->fx1 = kk[6];
			s->fx2 = kk[7];
			s->iir.ic1 = kk[8];
			s->iir.ic2 = kk[9];
			if (comb && whole) {
				kk[0] = s->delay;
				kk[1] = pv0;
				kk[2] = p_inc;
				modal_str_comb(n3 ? &line[wp - 1] : line, aux, n3, kk);
				modal_str_comb(&line[DLINE - 1], aux + n3, MB - n3, kk);
			} else if (comb) {
				s32 pv = pv0;
				for (k = 0; k < MB; k++) {
					s32 cb, i, b = (wp - k - 1) & (DLINE - 1), x0, x1;
					pv += p_inc;
					cb = qmul(s->delay, pv);
					i = cb >> 20;
					x0 = !i && k < MB - 1 ? old[k + 1] : line[b + i];
					x1 = line[b + i + 1];
					aux[k] += x0 + qmul(x1 - x0, shl(cb, 11) & Q31ONE);
				}
			}
			if (comb) {
				s->aux1 = aux[MB - 2] - a30;
				s->aux0 = aux[MB - 1] - a31;
			} else {
				s->aux1 = s->aux0 = 0;
			}
			s->clamped_position = pv0 + MB * p_inc;
			wp = (wp - MB) & (DLINE - 1);
			s->wp = wp;
			s->out1 = line[(wp + 2) & (DLINE - 1)];
			s->out0 = line[(wp + 1) & (DLINE - 1)];
			return;
		}
	}
	dk[0] = s->fx1;
	dk[1] = s->fx2;
	dk[2] = s->fh0;
	dk[3] = s->fh1;
	dk[4] = -s->iir.b;
	dk[5] = s->iir.a2;
	dk[6] = s->iir.a3;
	dk[7] = s->iir.ic1;
	dk[8] = s->iir.ic2;
	dpp[0] = st[0] = s->delay;
	dpp[1] = s->clamped_position;
	dpp[2] = p_inc;
	dpp[3] = st[2] = d_inc;
	st[1] = s->prev_damp_comp;
	st[3] = 0;
	for (k0 = 0; k0 < MB; k0 += c) {
		int n1, n3;
		c = MB - k0 < cs ? MB - k0 : cs;
		n1 = wp + 1 < c ? wp + 1 : c;            /* w de wp a 0, puis de DLINE - 1 vers le bas */
		n3 = wp < c ? wp : c;
		if (s->fmode == 2) {                     /* 1 : la lecture ; le bruit module le retard (str_process) */
			s32 kk[12];
			kk[0] = s->fd0;
			kk[1] = s->ksp;
			kk[2] = s->kapg;
			kk[3] = s->kna;
			kk[4] = s->k_nfilt;
			kk[5] = s->k_nk;
			kk[6] = s->dispersion_noise;
			kk[7] = (s32)*rng;
			kk[8] = wp;
			kk[9] = s->swp;
			kk[10] = 1664525;
			kk[11] = (s32)(unsigned long)s->stretch;
			modal_str_read_nz(line, hb + k0, in + k0, n1, kk);
			kk[8] = DLINE - 1;
			modal_str_read_nz(line, hb + k0 + n1, in + k0 + n1, c - n1, kk);
			s->dispersion_noise = kk[6];
			*rng = (u32)kk[7];
			s->swp = kk[9];
		} else if (s->fmode == 3) {              /* le chevalet courbe module le retard (str_process) */
			s32 kk[10];
			kk[0] = s->fd0;
			kk[1] = s->kbc;
			kk[2] = s->kac;
			kk[3] = s->curved_bridge;
			kk[4] = s->dc.x;
			kk[5] = s->dc.y;
			kk[6] = s->dc.pole;
			kk[7] = (s32)s->dc.f;
			kk[8] = wp;
			kk[9] = M_0025U;
			modal_str_read_cb(line, hb + k0, in + k0, n1, kk);
			kk[8] = DLINE - 1;
			modal_str_read_cb(line, hb + k0 + n1, in + k0 + n1, c - n1, kk);
			s->curved_bridge = kk[3];
			s->dc.x = kk[4];
			s->dc.y = kk[5];
			s->dc.f = (u32)kk[7];
		} else if (s->fap) {
			s32 ap[4], k;
			ap[0] = (s32)(unsigned long)s->stretch;
			ap[1] = s->swp;
			ap[2] = s->fapj;
			ap[3] = s->kapg;
			modal_str_read_ap(&line[wp + di], ff, hb + k0, n1, ap);
			modal_str_read_ap(&line[DLINE - 1 + di], ff, hb + k0 + n1, c - n1, ap);
			s->swp = ap[1];
			for (k = k0; k < k0 + c; k++)
				hb[k] += in[k];
		} else if (!d_inc) {
			modal_str_read(&line[wp + di], ff, in + k0, hb + k0, n1);
			modal_str_read(&line[DLINE - 1 + di], ff, in + k0 + n1, hb + k0 + n1, c - n1);
		} else {
			modal_str_read_mv(&line[wp], st, in + k0, hb + k0, n1);
			modal_str_read_mv(&line[DLINE - 1], st, in + k0 + n1, hb + k0 + n1, c - n1);
		}
		modal_str_damp(hb + k0, dk, c);          /* 2 */
		if (!comb) {                             /* 3 : sans peigne, ni aux ni position */
			str_wout(hb + k0, line, wp, out + k0, c);
		} else if (!d_inc) {
			modal_str_write(hb + k0, &line[wp], out + k0, dpp, n3);
			dpp[1] += n3 * p_inc;
			if (n3 < c) {                    /* l'echantillon qui ecrit en 0 : la lecture repart de DLINE - 1 */
				s32 cb, i, j = k0 + n3;
				dpp[1] += p_inc;
				cb = qmul(dpp[0], dpp[1]);
				line[0] = line[DLINE] = hb[j];
				i = DLINE - 1 + (cb >> 20);
				out[j] += hb[j];
				aux[j] += line[i] + qmul(line[i + 1] - line[i], shl(cb, 11) & Q31ONE);
				modal_str_write(hb + j + 1, &line[DLINE - 1], out + j + 1, dpp, c - n3 - 1);
				dpp[1] += (c - n3 - 1) * p_inc;
			}
		} else {
			modal_str_write_mv(hb + k0, &line[wp], out + k0, dpp, n3);
			if (n3 < c) {
				s32 cb, i, j = k0 + n3;
				dpp[0] += d_inc;
				dpp[1] += p_inc;
				cb = qmul(dpp[0], dpp[1]);
				line[0] = line[DLINE] = hb[j];
				i = DLINE - 1 + (cb >> 20);
				out[j] += hb[j];
				aux[j] += line[i] + qmul(line[i + 1] - line[i], shl(cb, 11) & Q31ONE);
				modal_str_write_mv(hb + j + 1, &line[DLINE - 1], out + j + 1, dpp, c - n3 - 1);
			}
		}
		wp = (wp - c) & (DLINE - 1);
	}
	s->fx1 = dk[0];
	s->fx2 = dk[1];
	s->iir.ic1 = dk[7];
	s->iir.ic2 = dk[8];
	s->delay += MB * d_inc;
	s->clamped_position += MB * p_inc;
	s->wp = wp;
	s->out1 = hb[MB - 2];
	s->out0 = hb[MB - 1];
	if (comb) {
		s->aux1 = aux[MB - 2] - a30;
		s->aux0 = aux[MB - 1] - a31;
	} else {
		s->aux1 = s->aux0 = 0;
	}
}

/* a la fin du chemin complet : le bloc suivant peut-il prendre str_fast (s'il garde frequence, amortissement,
 * brillance et dispersion) ? Les memes conditions que les chemins en assembleur de str_process. */
static void str_plan(struct mstring *s)
{
	s32 d0, D;

	s->fast = 0;
	if (s->k_ratio != (1 << 29) || s->fill < DLINE || (s->k_dcomp - s->prev_damp_comp) / MB
	    || (s->k_dcoef - s->fdmp) / MB || (s->k_bright - s->fbr) / MB)
		return;
	d0 = qmul(s->delay, s->prev_damp_comp) - (1 << 20);
	D = d0;
	s->fap = 0;
	s->fmode = 0;
	s->fd0 = d0;
	if (s->enable_dispersion) {
		s32 apd, md;
		if ((s->k_delay - s->delay) / MB || (s->dispersion - s->prev_dispersion) / MB || !s->kdisp_valid
		    || s->kdisp != s->prev_dispersion)
			return;
		if (s->kna | s->kbc | s->kac) {          /* le retard module, a chaque echantillon : les lectures de */
			if (s->kna && !s->kbc && !s->kac && d0 >= ((MB * 9 / 4) << 20) && s->sfill >= SLINE)
				s->fmode = 2;            /* str_process (modal_str_read_nz, _cb), les memes conditions */
			else if (s->kac && s->kbc && !s->kna && !s->ksp && d0 >= ((2 * MB) << 20))
				s->fmode = 3;
			else
				return;
			s->fdi = MB;                     /* des morceaux de MB : le retard lu depasse toujours le bloc */
			goto plan;
		}
		apd = qmul(d0, s->ksp);
		md = d0 - apd;
		if (apd >= (4 << 20) && md >= (4 << 20)) {
			if (s->sfill < SLINE)                /* l'etirement avance : son effacement aussi */
				return;
			s->fap = 1;
			s->fapj = apd >> 20;
			D = md;
		} else {                                 /* sans passe-tout, l'etirement ne bouge pas : rien a effacer */
			int need = ((s->k_delay > s->delay ? s->k_delay : s->delay) >> 20) * 5 / 8 + 8 + MB;
			if (need > SLINE - MB - 8)
				need = SLINE;
			if (s->sfill < need)
				return;
		}
	}
	s->fdi = D >> 20;
	s->ff = shl(D, 11) & Q31ONE;
plan:
	s->fh0 = fir_h0(s->fdmp, s->fbr);
	s->fh1 = fir_h1(s->fdmp, s->fbr);
	s->fdisp = s->dispersion;
	s->fver = s->kver;
	s->fast = 1;
}
#endif

/* str_process, le chemin complet (str_params deja fait) */
static __attribute__((noinline)) void str_process_full(struct mstring *s, const s32 *in, s32 *out, s32 *aux, u32 *rng)
{
	s32 delay, clamped, nfilt, nk, src_ratio, swp0;
	s32 d_inc, p_inc, disp_inc, dc_inc, dmp_inc, br_inc;
	s32 dv, pv, dispv, dcv, fx1, fx2, fbr, fdmp, wp, out0, aux0, out1, aux1;
	s32 ib, ia2, ia3, ic1, ic2;
	s32 *line = s->line;
	int k, plain, wcomb = aux != 0;

	if (!wcomb)
		aux = sc.nc;                             /* les C qui suivent y ecrivent un peigne que personne ne lit */
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
	plain = !s->enable_dispersion;
	if (!plain && src_ratio == (1 << 29) && !disp_inc) {
		/* une corde avec dispersion qui n'en fait rien sur ce bloc (ni modulation du retard, ni anti-continu, ni
		 * passe-tout de l'etirement) : le chemin sans dispersion, ses MB tirages aleatoires d'un coup (notes/81) */
		if (!s->kdisp_valid || s->kdisp != dispv) {
			struct dispk dk0;
			disp_coefs(&dk0, dispv);
			s->kdisp = dispv;
			s->ksp = dk0.sp;
			s->kna = dk0.na;
			s->kbc = dk0.bc;
			s->kac = dk0.ac;
			s->kapg = dk0.apg;
			s->kdisp_valid = 1;
		}
		if (!(s->kna | s->kbc | s->kac)) {
			s32 d0 = qmul(dv + d_inc, dcv + dc_inc) - (1 << 20), d1 = qmul(dv + MB * d_inc, dcv + MB * dc_inc) - (1 << 20);
			if (qmul(d0 > d1 ? d0 : d1, s->ksp) < (4 << 20))
				plain = 2;
		}
	}
	if (src_ratio == (1 << 29) && plain && delay >= ((MB + 8) << 20) && s->delay >= ((MB + 8) << 20)) {
		/* le cas courant (pas de dispersion ni de surechantillonnage, retard de plus d'un bloc : rien de ce
		 * qu'on lit n'est ecrit dans ce bloc), en trois passes legeres : lectures, filtres, ecritures */
		s32 *hb = sc.x;
		s32 dvk = dv, dck = dcv, w = wp;
		if (plain == 2)
			*rng = *rng * M_LCG16A + M_LCG16C;
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
		for (k = 0; k < MB; k++) {                   /* passe 1 : la lecture */
			s32 d;
			dvk += d_inc;
			dck += dc_inc;
			d = qmul(dvk, dck) - (1 << 20);
			hb[k] = rd_lin(&line[w + (d >> 20)], shl(d, 11) & Q31ONE) + in[k];
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
			modal_str_damp(hb, dk, MB);
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
		if (!wcomb) {                                /* passe 3 sans peigne */
			str_wout(hb, line, wp, out, MB);
			dv += MB * d_inc;
			pv += MB * p_inc;
			dcv += MB * dc_inc;
			wp = (wp - MB) & (DLINE - 1);
			out1 = hb[MB - 2];
			out0 = hb[MB - 1];
			aux1 = aux0 = 0;
		} else
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
		/* En passes (modal_asm.S), quand rien de ce qu'on lit n'est ecrit par ce bloc (le retard lu le plus court
		 * depasse le bloc) : la lecture, puis les passes 2 et 3 de la corde sans dispersion. La lecture :
		 * - sans modulation du retard (fm nul) ni anti-continu (ac nul) : le retard est fixe sur le bloc, le bruit de
		 *   dispersion ne sert pas (ses MB tirages d'un coup) : modal_str_read (ou _ap, le passe-tout de l'etirement) ;
		 * - dispersion au-dela de 0,75 (na) : le bruit module le retard, a chaque echantillon : modal_str_read_nz
		 *   (le retard reste au-dessus de 0,875 d0, la lecture principale de 0,46 d0) ;
		 * - dispersion negative (ac, bc) : le chevalet courbe module le retard, a chaque echantillon :
		 *   modal_str_read_cb (le retard reste au-dessus de d0 / 2, disp_fm). */
		if (aux == out + MB) {
			s32 apd = qmul(d0, sp), md = d0 - apd, D = d0, *hb = sc.x;
			int mode = 0, n1 = wp + 1 < MB ? wp + 1 : MB;
			if (!fm && !ac) {
				if (apd >= (4 << 20) && md >= (4 << 20))
					D = md;
				mode = D >= (MB << 20);
			} else if (na && !bc && !ac) {
				mode = d0 >= ((MB * 9 / 4) << 20) ? 2 : 0;
			} else if (ac && bc && !na && !sp) {
				mode = d0 >= ((2 * MB) << 20) ? 3 : 0;
			}
			if (mode == 1) {
				s32 f = shl(D, 11) & Q31ONE, ap[4];
				rs = rs * M_LCG16A + M_LCG16C;       /* MB tirages d'un coup (le pincement les partage) */
				if (D != d0) {
					ap[0] = (s32)(unsigned long)st;
					ap[1] = swp;
					ap[2] = apd >> 20;
					ap[3] = apg;
					modal_str_read_ap(&line[wp + (D >> 20)], f, hb, n1, ap);
					modal_str_read_ap(&line[DLINE - 1 + (D >> 20)], f, hb + n1, MB - n1, ap);
					swp = ap[1];
					for (k = 0; k < MB; k++)
						hb[k] += in[k];
				} else {
					modal_str_read(&line[wp + (D >> 20)], f, in, hb, n1);
					modal_str_read(&line[DLINE - 1 + (D >> 20)], f, in + n1, hb + n1, MB - n1);
				}
			} else if (mode == 2) {
				s32 kk[12];
				kk[0] = d0;
				kk[1] = sp;
				kk[2] = apg;
				kk[3] = na;
				kk[4] = nfilt;
				kk[5] = nk;
				kk[6] = dn;
				kk[7] = (s32)rs;
				kk[8] = wp;
				kk[9] = swp;
				kk[10] = 1664525;
				kk[11] = (s32)(unsigned long)st;
				modal_str_read_nz(line, hb, in, n1, kk);
				kk[8] = DLINE - 1;
				modal_str_read_nz(line, hb + n1, in + n1, MB - n1, kk);
				dn = kk[6];
				rs = (u32)kk[7];
				swp = kk[9];
			} else if (mode == 3) {
				s32 kk[10];
				rs = rs * M_LCG16A + M_LCG16C;       /* sans na, le bruit ne sert pas */
				kk[0] = d0;
				kk[1] = bc;
				kk[2] = ac;
				kk[3] = cb;
				kk[4] = s->dc.x;
				kk[5] = s->dc.y;
				kk[6] = s->dc.pole;
				kk[7] = (s32)s->dc.f;
				kk[8] = wp;
				kk[9] = M_0025U;
				modal_str_read_cb(line, hb, in, n1, kk);
				kk[8] = DLINE - 1;
				modal_str_read_cb(line, hb + n1, in + n1, MB - n1, kk);
				cb = kk[3];
				s->dc.x = kk[4];
				s->dc.y = kk[5];
				s->dc.f = (u32)kk[7];
			}
			if (mode) {
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
				modal_str_damp(hb, dk2, MB);
				fx1 = dk2[0];
				fx2 = dk2[1];
				ic1 = dk2[7];
				ic2 = dk2[8];
				dpp[0] = dv;
				dpp[1] = pv;
				dpp[2] = p_inc;
				modal_str_write(hb, &line[wp], out, dpp, n3);
				if (n3 < MB) {                       /* l'echantillon qui ecrit en 0 : la lecture repart de DLINE - 1 */
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
				goto disp_done;
			}
		}
#endif
		for (k = 0; k < MB; k++) {
			s32 d, sv, v3, t1, t2, apd, md, value, noise, *p;
			pv += p_inc;
			rs = rs * 1664525u + 1013904223u;
			if (na) {                                /* le bruit de dispersion ne sert qu'avec na (notes/81) */
				noise = qmul((s32)(rs ^ 0x80000000u) >> 4, nk);   /* Q27 x Q28 -> UNIT */
				dn += qmul(nfilt, noise - dn);
			}
			d = d0;
			if (fm)
				d = shl(qmul(d, disp_fm((1 << 30) + shl(qmul(dn, na), 6) - shl(qmul(cb, bc), 6))), 1);
			apd = qmul(d, sp);
			md = d - apd;
			if (apd >= (4 << 20) && md >= (4 << 20)) {
				s32 rd, wr, i = wp + (md >> 20);
				if (i > 2 * DLINE - 3)
					i -= DLINE;
				sv = rd_lin(&line[i], shl(md, 11) & Q31ONE);
				rd = st[(swp + (apd >> 20)) & (SLINE - 1)];
				wr = sv + qmulr(apg, rd);
				st[swp] = wr;
				swp = (swp - 1) & (SLINE - 1);
				sv = rd - qmulr(wr, apg);
			} else {
				s32 i = wp + (d >> 20);
				if (i > 2 * DLINE - 3)
					i -= DLINE;
				sv = rd_lin(&line[i], shl(d, 11) & Q31ONE);
			}
			if (ac) {                                /* l'anti-continu et le chevalet courbe : avec ac seulement */
				s32 sac = dc_one(&s->dc, sv);          /* DCBlocker */
				sv += qmul(ac, sac - sv);
				value = iabs(sv) - M_0025U;
				cb = value > 0 ? (sv > 0 ? 2 * value : -3 * value) : 0;
			}
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
			if (disp_inc) {
				dispv += disp_inc;
				disp_coefs(&dk, dispv);
			}
			if (dk.na) {
				noise = qmul((s32)(rs ^ 0x80000000u) >> 4, nk);   /* Q27 x Q28 -> UNIT */
				dn += qmul(nfilt, noise - dn);
			}
			if (dk.na | dk.bc)
				d = shl(qmul(d, disp_fm((1 << 30) + shl(qmul(dn, dk.na), 6) - shl(qmul(cb, dk.bc), 6))), 1);
			apd = qmul(d, dk.sp);
			md = d - apd;
			if (apd >= (4 << 20) && md >= (4 << 20)) {
				s32 rd, wr;
				sv = (md >> 20) < DLINE - 4 ? rd_lin(&line[wp + (md >> 20)], shl(md, 11) & Q31ONE)
					: rd_linm(line, wp, md);
				rd = st[(swp + (apd >> 20)) & (SLINE - 1)];
				wr = sv + qmulr(dk.apg, rd);
				st[swp] = wr;
				swp = (swp - 1) & (SLINE - 1);
				sv = rd - qmulr(wr, dk.apg);
			} else {
				sv = (d >> 20) < DLINE - 4 ? rd_lin(&line[wp + (d >> 20)], shl(d, 11) & Q31ONE)
					: rd_linm(line, wp, d);
			}
			if (dk.ac) {
				sac = dc_one(&s->dc, sv);                  /* DCBlocker */
				sv += qmul(dk.ac, sac - sv);
				value = iabs(sv) - M_0025U;
				cb = value > 0 ? (sv > 0 ? 2 * value : -3 * value) : 0;
			}
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
			sv = rd_lin(&line[wp + (d >> 20)], shl(d, 11) & Q31ONE) + in[k];
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
			if (aux != sc.nc) {
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
					dispv += disp_inc;
					if (disp_inc || dispv != dk.disp)
						disp_coefs(&dk, dispv);
					if (dk.na)                           /* avec na seulement (notes/81) */
						s->dispersion_noise += qmul(nfilt, noise - s->dispersion_noise);
					fm = disp_fm((1 << 30) + shl(qmul(s->dispersion_noise, dk.na), 6)
						     - shl(qmul(s->curved_bridge, dk.bc), 6));
					d = shl(qmul(d, fm), 1);
					apd = qmul(d, dk.sp);
					md = d - apd;
					if (apd >= (4 << 20) && md >= (4 << 20)) {
						s32 rd, wr, j = apd >> 20;
						sv = rd_linm(line, wp, md);
						rd = s->stretch[(s->swp + j) & (SLINE - 1)];
						wr = sv + qmulr(dk.apg, rd);
						s->stretch[s->swp] = wr;
						s->swp = (s->swp - 1) & (SLINE - 1);
						sv = rd - qmulr(wr, dk.apg);
					} else {
						sv = rd_linm(line, wp, d);
					}
					if (dk.ac) {
						sac = dc_one(&s->dc, sv);
						sv += qmul(dk.ac, sac - sv);
						value = iabs(sv) - M_0025U;
						s->curved_bridge = value > 0 ? (sv > 0 ? 2 * value : -3 * value) : 0;
					}
				} else {
					sv = rd_linm(line, wp, d);
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
#ifdef MODAL_ASM
	str_plan(s);
#endif
}

/* s->frequency etc. deja poses ; ajoute la corde a out / aux. aux nul : sans peigne (les cordes sympathiques, notes/81) :
 * la sortie aux de la corde, la seule qui depende de sa position, n'est pas calculee. Le chemin court (str_fast) sans
 * entrer dans le complet : moins de code relu a chaque bloc. */
static __attribute__((noinline)) void str_process(struct mstring *s, const s32 *in, s32 *out, s32 *aux, u32 *rng)
{
	str_params(s);
#ifdef MODAL_ASM
	if (s->fast && s->fver == s->kver && s->fdisp == s->dispersion && (aux == out + MB || !aux)) {
		s32 clamped = 0x40000000 - qmul(Q31(0.98), iabs(s->position - 0x40000000));
		str_fast(s, in, out, (clamped - s->clamped_position) / MB,
			 s->enable_dispersion ? 0 : (s->k_delay - s->delay) / MB, rng, aux != 0);
		return;
	}
#endif
	str_process_full(s, in, out, aux, rng);
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
	while (xcmp(period, XC(M_PLCAP)) >= 0)
		period = xscale(period, -1);
	p->period = xto(period, 20);
	p->gain = qmul(Q31ONE - position, Q31(0.8));
	{
		s32 cq = xto(xmin(cutoff, XC(M_0998)), 31);
		svf_set(&p->svf, tan_exact(cq), q_fade_r(cq, xmk(1 << 30, 0), XC(M_QD100), xmk(1 << 30, 0)), 0, 0);
	}
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
			in = qmul(rng_q31(rng) >> 7, Q31(0.70710678));   /* la meme densite par hertz (notes/81) */
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

/* ---- filtre de note (rings/dsp/note_filter.h) -------------------------------------------------------------- */

struct note_filter {
	s32 prev[4], note, stable;                       /* demi-tons << 16 */
	s32 coef, stable_coef;                           /* Q31 */
	s32 line[16], wp;
	s32 pend;                                        /* pas de coef et stable_coef en retard (nf_process) */
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
	n->pend = 0;
}

static void nf_process(struct note_filter *n, s32 note, int strum)
{
	if (iabs(note - n->note) > M_NF_JUMP || strum) {
		int i;
		n->stable = n->note = note;
		n->coef = M_NF_FAST;
		n->stable_coef = M_NF_SLOW;
		n->pend = 0;
		for (i = 0; i < 4; i++)
			n->prev[i] = note;
	} else {
		s32 s[4], t, med;
		int i, j;
		n->prev[0] = n->prev[1];
		n->prev[1] = n->prev[2];
		n->prev[2] = n->prev[3];
		n->prev[3] = note;
		if (n->prev[0] == note && n->prev[1] == note && n->prev[2] == note) {
			if (n->note == note && n->stable == note) {
				/* la note et sa version stable ne bougent pas : seuls coef et stable_coef avancent, et ils ne
				 * servent qu'au prochain changement de note. Leurs pas sont faits a ce moment-la (notes/81). */
				n->pend++;
				n->line[n->wp] = note;
				n->wp = (n->wp - 1) & 15;
				return;
			}
			med = note;                      /* quatre valeurs egales : la mediane sans le tri */
		} else {
			for (i = 0; i < 4; i++)
				s[i] = n->prev[i];
			for (i = 1; i < 4; i++)
				for (j = i; j > 0 && s[j - 1] > s[j]; j--) {
					t = s[j];
					s[j] = s[j - 1];
					s[j - 1] = t;
				}
			med = (s[1] + s[2]) >> 1;
		}
		for (; n->pend > 0; n->pend--) {         /* les pas en retard ; arrives au point fixe, ils n'y changent rien */
			s32 c = n->coef + qmul(M_NF_LAG, M_NF_SLOW - n->coef);
			s32 sc = n->stable_coef + qmul(M_NF_LAG, M_NF_LAG - n->stable_coef);
			if (c == n->coef && sc == n->stable_coef) {
				n->pend = 0;
				break;
			}
			n->coef = c;
			n->stable_coef = sc;
		}
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
	s32 peak, lz, ln;                                /* limiteur : peak (UNIT), 1 / m (Q30) et n de lim_gain ; cet ordre */
	s32 rin_zero;                                    /* rin nul a l'entree de la voix (pas d'entree) */
	s32 exc_idle[MAXPOLY];                           /* blocs d'excitation muette d'une voix inactive (exc_quiet) */
	s32 rin[MB], sym[MB], ob[MB], ab[MB], nb[MB];
	/* le bloc court des cordes (modal_fast, notes/81) : ce que le dernier bloc complet a vu */
	s32 fk_valid, fk_st, fk_b, fk_d, fk_p, fk_tonic, fk_fm, fk_chord, fk_active, fk_note;
	struct mstring str[NSTRINGS];
};

static const s32 PING[8] = { 1, 0, 2, 1, 0, 2, 1, 0 };
/* modal_pluck lit nb a 4 MB mots de rin */
typedef char modal_nb_at_rin[(__builtin_offsetof(struct modal_part, nb) - __builtin_offsetof(struct modal_part, rin)
			      == 4 * MB * sizeof(s32)) ? 1 : -1];

static void modal_part_init(struct modal_part *p)
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
	p->peak = UNIT >> 1;
	p->ln = -1;
	p->fk_valid = 0;
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
	if (m != MODEL_SYMPATHETIC && m != MODEL_STRING && m != MODEL_SYMPATHETIC_Q)
		m = MODEL_MODAL;
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
		for (i = 0; i < NSTRINGS; i++)
			str_init(&p->str[i], p->model == MODEL_STRING);
		for (i = 0; i < p->poly; i++)
			pl_init(&p->pl[i]);
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

/* La chaine d'excitation d'une voix sans entree (filtre d'excitation, pincement, filtre anti-continu) qui est
 * restee sous -108 dB pendant EXC_IDLE blocs n'est plus calculee, jusqu'a sa prochaine note (ou une entree) : elle ne
 * sort plus que des restes sous 2^-18 (l'arrondi par defaut du peigne du pincement la laisse osciller sur un LSB au
 * lieu de s'eteindre). Rings la calcule ; la corde ou le resonateur de la voix, eux, continuent de resonner. Depuis
 * notes/81, la voix active aussi, entre deux notes. */
#define EXC_IDLE 8

static int exc_quiet(struct modal_part *p, int v, const s32 *x)
{
	int k;

	if (!p->rin_zero) {                              /* une entree : jamais muette */
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

static inline int exc_skip(const struct modal_part *p, int v, int strum)
{
	return p->exc_idle[v] >= EXC_IDLE && p->rin_zero && !(strum && v == p->active);
}

/* les cordes d'une voix des modeles sympathiques : 3 pour une voix (la corde jouee et deux cordes sympathiques),
 * 1 pour plusieurs (Rings : 8, 4, 2 pour 1, 2, 4 voix ; eco, notes/74 : 4, 2, 1 ; le budget de 13 %, notes/81 :
 * une corde sympathique coute presque 2 % du processeur) */
static inline int sym_strings(const struct modal_part *p)
{
	return p->poly == 1 ? 3 : 1;
}

/* ob, ab : les deux sorties de la voix (ab = ob + MB : str_fast) */
static void render_string(struct modal_part *p, int voice, const struct modal_perf *ps,
			  const struct modal_patch *pa, xf frequency, xf fc, s32 *ob, s32 *ab)
{
	s32 freqs[NSTRINGS], dispersion, st = pa->structure;
	int ns = 1, i;

	if (p->model == MODEL_SYMPATHETIC || p->model == MODEL_SYMPATHETIC_Q) {
		struct vcache *vc = &p->vc[voice];
		s32 tonic = ps->tonic + ps->fm, note = ps->tonic + p->note[voice] + ps->fm;
		int chord = p->model == MODEL_SYMPATHETIC ? -1 : ps->chord;
		ns = sym_strings(p);
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
	if (!exc_skip(p, voice, ps->strum)) {            /* sinon : rin reste a zero (exc_quiet) */
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
		ob[i] = ab[i] = 0;
	dispersion = st < Q31(0.24) ? shl(qmul(st - Q31(0.24), Q31(4.166 / 8)), 2)
		: (st > Q31(0.26) ? qmul(st - Q31(0.26), Q31(1.35135 / 2)) : 0);       /* Q30 */
	for (i = 0; i < ns; i++) {
		int idx = voice + i * p->poly;
		struct mstring *s = &p->str[idx];
		s32 brightness = pa->brightness, damping = pa->damping;
		s32 glide = Q31ONE, sidx = i * (Q31ONE / ns);
		const s32 *input = p->rin;
		int sym = i > 0 && ps->internal_exciter;
		/* Les cordes sympathiques (excitees par la 1re) n'ont pas de peigne (notes/81) : leur position, et le LFO de
		 * Rings qui la fait bouger, ne servent plus a rien. */
		if (sym) {
			brightness = b2mb(brightness);
			brightness = b2mb(brightness);
			damping = Q31(0.7) + qmul(pa->damping, Q31(0.27));
			if (!p->gvalid || p->gbright != pa->brightness) {
				p->glide = xto(xs2r(qmul(brightness - Q31ONE, 36 << 16)), 31);
				p->gbright = pa->brightness;
				p->gvalid = 1;
			}
			glide = p->glide;
			input = p->sym;
		}
		s->dispersion = dispersion;
		s->lite = glide != Q31ONE;
		if (glide == Q31ONE)
			s->frequency = freqs[i];
		else
			s->frequency += qmul(glide, freqs[i] - s->frequency);
		s->brightness = brightness;
		s->position = pa->position;
		s->damping = damping + qmul(sidx, Q31(0.95) - damping);
		str_process(s, input, ob, sym ? (s32 *)0 : ab, &p->rng);
		if (i == 0 && ns > 1) {                  /* l'entree des autres cordes de la voix */
			s32 g = M_SYMG[ns];
			int k;
			for (k = 0; k < MB; k++)
				p->sym[k] = qmul(g, ob[k] - ab[k]);
		}
	}
}

/* le gain du limiteur au-dessus de 1,0 : 0,8 / peak (peak en UNIT, > UNIT), en Q31. peak = m 2^-n (m dans
 * [2^30, 2^31), Q30) ; 1 / m par une division 32/32 puis une iteration de Newton (~30 bits justes), sans le flottant
 * maison : il change a chaque echantillon. Quand peak descend (relachement, err <= 0 : de 4e-5 par echantillon au
 * plus) et garde son n, l'iteration repart du 1 / m de l'echantillon d'avant, sans la division (notes/81) : l'ecart
 * relatif de depart est sous 4e-5, son carre sous 2e-9. lz, ln : ce 1 / m (Q30) et son n (-1 : a refaire). */
static inline s32 lim_gain(s32 peak, s32 *lz, s32 *ln, int rel)
{
	int n = __builtin_clz((u32)peak) - 1;            /* 1..6 : peak dans (2^24, 2^31) */
	s32 m = shl(peak, n), z, t;                      /* [2^30, 2^31) : m / 2^30 dans [1, 2) */

	if (rel && n == *ln)
		z = *lz;
	else
		z = (s32)((0xffffffffu / (u32)(m >> 15)) << 13); /* 1 / m en Q30, 16 bits justes */
	t = (s32)(0x80000000u - (u32)shl(qmul(m, z), 1));
	z = shl(qmul(z, t), 1);                          /* 1 / m, Q30 */
	*lz = z;
	*ln = n;
	z = qmul(z, Q31(0.8));                           /* 0,8 / m, Q30 */
	return n >= 5 ? shl(z, n - 5) : z >> (5 - n);    /* 0,8 / peak = (0,8 / m) 2^(n - 6) */
}

/* le limiteur de Rings, sur les deux sorties (UNIT), en place ; pg : le gain du modele ; lim : peak, lz, ln */
static __attribute__((unused)) void modal_limiter(s32 *out, s32 *aux, s32 *lim, s32 pg)
{
	s32 peak = lim[0], g;
	int k;

	for (k = 0; k < MB; k++) {
		s32 l = shl(qmul(out[k], pg), 1), r = shl(qmul(aux[k], pg), 1);
		s32 pk = iabs(l), t = iabs(r), err;
		if (t > pk)
			pk = t;
		t = iabs(r - l);
		if (t > pk)
			pk = t;
		err = pk - peak;
		peak += qmul(err > 0 ? M_LIM_ATK : M_LIM_DEC, err);
		if (peak <= UNIT) {
			g = Q31(0.8);
			lim[2] = -1;
		} else {
			g = lim_gain(peak, &lim[1], &lim[2], err <= 0);
		}
		out[k] = softlimit(qmul(l, g));
		aux[k] = softlimit(qmul(r, g));
	}
	lim[0] = peak;
}

/* Les modeles a cordes quand rien n'a change depuis le bloc complet precedent (potards, notes, voix active, ni strum,
 * ni entree, l'excitateur interne) : les memes calculs que modal_process et render_string pour ce cas, sans refaire
 * ce qui ne bouge pas (notes/81). Seules les glissades des cordes sympathiques avancent. */
static void modal_fast(struct modal_part *p, s32 *out, s32 *aux)
{
	int v, i, k, ns = p->model == MODEL_STRING ? 1 : sym_strings(p);

	for (v = 0; v < p->poly; v++) {
		s32 *ob = p->poly == 1 ? out : p->ob, *ab = p->poly == 1 ? aux : p->ab;
		const struct vcache *vc = &p->vc[v];
		p->rin_zero = 1;
		for (k = 0; k < MB; k++)
			p->rin[k] = 0;
		if (!exc_skip(p, v, 0)) {
			struct svf *e = &p->exc[v];
			if (e->ic1 || e->ic2)
				svf_lp_block(e, p->rin, MB, 0, 0);
#ifdef MODAL_ASM
			if (!p->pl[v].remaining)
				modal_pluck(&p->pl[v], p->rin, &p->dcb[v]);
			else
#endif
			{
				pl_process(&p->pl[v], p->nb, &p->rng);
				for (k = 0; k < MB; k++)
					p->rin[k] = dc_one(&p->dcb[v], p->rin[k] + p->nb[k]);
			}
			exc_quiet(p, v, p->rin);
		}
		for (k = 0; k < MB; k++)
			ob[k] = ab[k] = 0;
		for (i = 0; i < ns; i++) {
			struct mstring *s = &p->str[v + i * p->poly];
			const s32 *input = p->rin;
			if (i > 0) {                             /* sympathique : sans peigne */
				if (p->glide == Q31ONE)
					s->frequency = vc->freqs[i];
				else
					s->frequency += qmul(p->glide, vc->freqs[i] - s->frequency);
				input = p->sym;
			}
			str_process(s, input, ob, i > 0 ? (s32 *)0 : ab, &p->rng);
			if (i == 0 && ns > 1)
				for (k = 0; k < MB; k++)
					p->sym[k] = qmul(M_SYMG[ns], ob[k] - ab[k]);
		}
		if (p->poly > 1) {
			s32 *d = (v & 1) ? aux : out;
			if (v < 2)
				for (k = 0; k < MB; k++)
					d[k] = p->ob[k] - p->ab[k];
			else
				for (k = 0; k < MB; k++)
					d[k] += p->ob[k] - p->ab[k];
		}
	}
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
	if (p->fk_valid && !ps->strum && !in && ps->internal_exciter && !p->dirty && p->fk_st == pa->structure
	    && p->fk_b == pa->brightness && p->fk_d == pa->damping && p->fk_p == pa->position && p->fk_tonic == ps->tonic
	    && p->fk_fm == ps->fm && p->fk_chord == ps->chord && p->fk_active == p->active && p->fk_note == p->nf.note) {
		modal_fast(p, out, aux);
		goto limit;
	}
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
				fc = xmul(XC(M_EXTFC), xs2r(qmul(cutoff - Q31ONE, 108 << 16)));
			if (!act)
				fc = XC(M_FCIDLE);
			fc = xmin(fc, XC(M_0998));
			fcq = xto(fc, 31);
			svf_set(&p->exc[v], tan_exact(fcq), ps->internal_exciter
				? q_fade_r(fcq, XC(M_Q150), XC(M_QD150), XC(M_R150))
				: q_fade_r(fcq, XC(M_Q080), XC(M_QD080), XC(M_R080)), &a2x, &a3x);
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
			if (!exc_skip(p, v, ps->strum)) {
				svf_lp_block(&p->exc[v], p->rin, MB, p2, p3);
				exc_quiet(p, v, p->rin);
			}
			r->frequency = frequency;
			r->structure = pa->structure;
			r->brightness = qmul(pa->brightness, pa->brightness);
			r->position = pa->position;
			r->damping = pa->damping;
			reso_process(r, p->rin, p->poly == 1 ? out : p->ob, p->poly == 1 ? aux : p->ab);
		} else {
			render_string(p, v, ps, pa, frequency, fc, p->poly == 1 ? out : p->ob, p->poly == 1 ? aux : p->ab);
		}
		if (p->poly > 1) {                       /* une voix sur deux de chaque cote : les deux 1res posent */
			s32 *d = (v & 1) ? aux : out;
			const s32 *ob = p->ob, *ab = p->ab;
			if (v < 2)
				for (k = 0; k < MB; k++)
					d[k] = ob[k] - ab[k];
			else
				for (k = 0; k < MB; k++)
					d[k] += ob[k] - ab[k];
		}
	}
	/* ce que le bloc court reprendra (modal_fast) */
	p->fk_valid = p->model != MODEL_MODAL && !in && ps->internal_exciter;
	p->fk_st = pa->structure;
	p->fk_b = pa->brightness;
	p->fk_d = pa->damping;
	p->fk_p = pa->position;
	p->fk_tonic = ps->tonic;
	p->fk_fm = ps->fm;
	p->fk_chord = ps->chord;
	p->fk_active = p->active;
	p->fk_note = p->nf.note;
limit:
	/* le limiteur ; sur le ColdFire, la passerelle le fait avec sa difference (modal_lim, modal_asm.S) */
#ifndef MODAL_ASM
	modal_limiter(out, aux, &p->peak, M_GAINS[p->model]);
#endif
	return;
}

#endif
