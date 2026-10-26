/*
 * MODAL : l'arithmetique du coeur (modal_dsp.h), sans FPU.
 *
 * - qmul, qmac2, qmac3 : produits Q31 par l'EMAC du ColdFire (mode fractionnaire signe sature, MACSR = 0xa0
 *   pendant la boucle des voix), et pour l'ordinateur la meme arithmetique a l'octet pres (tools/emu/emac.py) :
 *   chaque produit tronque a 2^-39, somme, decalage de 31, saturation a 32 bits.
 * - xf : un flottant maison pour les calculs par bloc (coefficients des filtres, hauteurs, durees), qui ont la
 *   dynamique des flottants de Rings : mantisse signee |m| dans [2^30, 2^31) (ou 0), valeur m x 2^(e - 30).
 *   Produit par l'EMAC, normalisation par ff1 (__builtin_clz), inverse par une division 32/32 et une iteration de
 *   Newton : environ 30 bits justes.
 * - xs2r : SemitonesToRatio de stmlib (dsp/units.h), avec la meme troncature de la fraction en 1/256 de demi-ton.
 */
#ifndef MODAL_FIX_H
#define MODAL_FIX_H

typedef signed char s8;
typedef short s16;
typedef unsigned short u16;
typedef int s32;
typedef unsigned int u32;

#define Q31ONE 0x7fffffff

#include "modal_tables.h"

#ifdef __mcoldfire__
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
static inline s32 qmac3(s32 a, s32 b, s32 c, s32 d, s32 e, s32 f)
{
	s32 r;
	__asm__ volatile("mac.l %1,%2,%%acc0\n\tmac.l %3,%4,%%acc0\n\tmac.l %5,%6,%%acc0\n\tmovclr.l %%acc0,%0"
			 : "=d"(r) : "r"(a), "r"(b), "r"(c), "r"(d), "r"(e), "r"(f));
	return r;
}
/* arrondis au plus pres : un produit de plus, 2^15 x 2^15 = 1/2 du dernier bit (les boucles des cordes ne
 * doivent pas deriver vers le bas, comme le ferait la troncature) */
#define RND 0x8000
static inline s32 qmulr(s32 a, s32 b)
{
	s32 r;
	__asm__ volatile("mac.l %1,%2,%%acc0\n\tmac.l %3,%3,%%acc0\n\tmovclr.l %%acc0,%0"
			 : "=d"(r) : "r"(a), "r"(b), "r"(RND));
	return r;
}
static inline s32 qmac2r(s32 a, s32 b, s32 c, s32 d)
{
	s32 r;
	__asm__ volatile("mac.l %1,%2,%%acc0\n\tmac.l %3,%4,%%acc0\n\tmac.l %5,%5,%%acc0\n\tmovclr.l %%acc0,%0"
			 : "=d"(r) : "r"(a), "r"(b), "r"(c), "r"(d), "r"(RND));
	return r;
}
#else
static inline s32 emac_sat(long long a)
{
	return a > 0x7fffffffLL ? 0x7fffffff : (a < -0x80000000LL ? (s32)0x80000000 : (s32)a);
}
static inline s32 qmul(s32 a, s32 b)
{
	return emac_sat((((long long)a * b) >> 23) >> 8);
}
static inline s32 qmac2(s32 a, s32 b, s32 c, s32 d)
{
	return emac_sat(((((long long)a * b) >> 23) + (((long long)c * d) >> 23)) >> 8);
}
static inline s32 qmac3(s32 a, s32 b, s32 c, s32 d, s32 e, s32 f)
{
	return emac_sat(((((long long)a * b) >> 23) + (((long long)c * d) >> 23) + (((long long)e * f) >> 23)) >> 8);
}
static inline s32 qmulr(s32 a, s32 b)
{
	return emac_sat(((((long long)a * b) >> 23) + 128) >> 8);
}
static inline s32 qmac2r(s32 a, s32 b, s32 c, s32 d)
{
	return emac_sat(((((long long)a * b) >> 23) + (((long long)c * d) >> 23) + 128) >> 8);
}

/* Un accumulateur de l'EMAC garde d'un echantillon a l'autre (les noyaux de modal_asm.S y tiennent les etats des
 * filtres) : la valeur en 2^-39 (8 bits sous le LSB). acc_ld : move.l Rx,ACC ; acc_rd : move.l ACC,Rx (troncature,
 * saturation) ; emp, emp1, empr : le produit qu'ajoute (ou retire) mac.l / msac.l, sans decalage, avec << ou avec >>,
 * tronque a 2^-39 apres le decalage. Sur le ColdFire, ces calculs n'existent qu'en assembleur. */
typedef long long acc_t;
static inline acc_t acc_ld(s32 x)
{
	return (acc_t)x * 256;
}
static inline s32 acc_rd(acc_t a)
{
	return emac_sat(a >> 8);
}
static inline acc_t emp(s32 a, s32 b)
{
	return ((acc_t)a * b) >> 23;
}
static inline acc_t emp1(s32 a, s32 b)
{
	return ((acc_t)a * b * 2) >> 23;
}
static inline acc_t empr(s32 a, s32 b)
{
	return ((acc_t)a * b) >> 24;
}
#endif

static inline s32 shl(s32 x, int n)                  /* x << n sans comportement indefini sur les negatifs */
{
	return (s32)((u32)x << n);
}

static inline s32 iabs(s32 x)                        /* |x| ; -2^31 reste -2^31, sans comportement indefini */
{
	return x < 0 ? (s32)(0u - (u32)x) : x;
}

/* ---- xf ---------------------------------------------------------------------------------------------------- */

typedef struct {
	s32 m, e;
} xf;

#define XF_ZE (-100000)
#define XC(n) xmk(n##_M, n##_E)

static inline xf xmk(s32 m, s32 e)
{
	xf r;
	r.m = m;
	r.e = e;
	return r;
}

static inline xf xnorm(s32 m, s32 e)
{
	u32 a;
	int n;

	if (m == 0)
		return xmk(0, XF_ZE);
	a = m < 0 ? 0u - (u32)m : (u32)m;
	n = __builtin_clz(a) - 1;
	if (n < 0)                                       /* m = -2^31 */
		return xmk(m >> 1, e + 1);
	return xmk(shl(m, n), e - n);
}

/* Chaque operation existe en deux formes, la meme arithmetique : _i, en ligne (les boucles par mode, reso_compute),
 * et la fonction, pour le reste du code (la place). */
#define XFI static inline __attribute__((always_inline))

XFI xf xmul_i(xf a, xf b)
{
	return xnorm(qmul(a.m, b.m), a.e + b.e + 1);
}

static __attribute__((noinline)) xf xmul(xf a, xf b)
{
	return xmul_i(a, b);
}

XFI xf xadd_i(xf a, xf b)
{
	int d;

	if (a.m == 0)
		return b;
	if (b.m == 0)
		return a;
	if (a.e < b.e) {
		xf t = a;
		a = b;
		b = t;
	}
	d = a.e - b.e;
	if (d > 30)
		return a;
	return xnorm((a.m >> 1) + (b.m >> (d + 1)), a.e + 1);
}

static __attribute__((noinline)) xf xadd(xf a, xf b)
{
	return xadd_i(a, b);
}

static inline xf xneg(xf a)
{
	return xmk(-a.m, a.e);
}

static inline xf xsub(xf a, xf b)
{
	return xadd(a, xneg(b));
}

XFI xf xrecip_i(xf a)
{
	u32 am, q;
	s32 z, xz, t;

	if (a.m == 0)
		return xmk(Q31ONE, 1000);
	am = a.m < 0 ? 0u - (u32)a.m : (u32)a.m;
	q = 0xffffffffu / (am >> 15);                    /* ~ 2^47 / am, 16 bits justes */
	z = (s32)(q << 13);                              /* 1/x en Q30, x = am / 2^30 dans [1, 2) */
	xz = shl(qmul((s32)am, z), 1);                   /* x z en Q30 */
	t = (s32)(0x80000000u - (u32)xz);                /* 2 - x z */
	z = shl(qmul(z, t), 1);
	if (a.m < 0)
		z = -z;
	return xnorm(z, -a.e);
}

static __attribute__((noinline)) xf xrecip(xf a)
{
	return xrecip_i(a);
}

/* v / 2^frac */
XFI xf xfrom_i(s32 v, int frac)
{
	return xnorm(v, 30 - frac);
}

static __attribute__((noinline)) xf xfrom(s32 v, int frac)
{
	return xfrom_i(v, frac);
}

/* la valeur en entier a frac bits apres la virgule, saturee (troncature vers -infini) */
XFI s32 xto_i(xf a, int frac)
{
	int sh;

	if (a.m == 0)
		return 0;
	sh = a.e - 30 + frac;
	if (sh > 0)                                      /* |m| >= 2^30 : hors des 32 bits */
		return a.m < 0 ? (s32)0x80000000 : Q31ONE;
	if (sh == 0)
		return a.m;
	if (sh <= -32)
		return a.m < 0 ? -1 : 0;
	return a.m >> -sh;
}

static __attribute__((noinline)) s32 xto(xf a, int frac)
{
	return xto_i(a, frac);
}

/* signe de a - b */
static __attribute__((noinline)) int xcmp(xf a, xf b)
{
	xf d = xsub(a, b);
	return d.m > 0 ? 1 : (d.m < 0 ? -1 : 0);
}

static __attribute__((noinline)) xf xmin(xf a, xf b)
{
	return xcmp(a, b) > 0 ? b : a;
}

/* x 2^n */
static inline xf xscale(xf a, int n)
{
	return a.m ? xmk(a.m, a.e + n) : a;
}

/* Les memes operations pour des valeurs positives ou nulles (les coefficients des modes, reso_compute) : sans le
 * traitement du signe, la meme arithmetique. */
XFI xf xnormp(s32 m, s32 e)
{
	int n;

	if (m == 0)
		return xmk(0, XF_ZE);
	n = __builtin_clz((u32)m) - 1;
	return xmk(shl(m, n), e - n);
}

XFI xf xmulp(xf a, xf b)
{
	return xnormp(qmul(a.m, b.m), a.e + b.e + 1);
}

XFI xf xaddp(xf a, xf b)
{
	int d;

	if (a.m == 0)
		return b;
	if (b.m == 0)
		return a;
	if (a.e < b.e) {
		xf t = a;
		a = b;
		b = t;
	}
	d = a.e - b.e;
	if (d > 30)
		return a;
	return xnormp((a.m >> 1) + (b.m >> (d + 1)), a.e + 1);
}

XFI xf xrecipp(xf a)
{
	u32 q;
	s32 z, t;

	if (a.m == 0)
		return xmk(Q31ONE, 1000);
	q = 0xffffffffu / ((u32)a.m >> 15);
	z = (s32)(q << 13);
	t = (s32)(0x80000000u - (u32)shl(qmul(a.m, z), 1));
	return xnormp(shl(qmul(z, t), 1), -a.e);
}

XFI xf xfromp(s32 v, int frac)
{
	return xnormp(v, 30 - frac);
}

XFI s32 xtop(xf a, int frac)
{
	int sh;

	if (a.m == 0)
		return 0;
	sh = a.e - 30 + frac;
	if (sh > 0)
		return Q31ONE;
	if (sh <= -32)
		return 0;
	return a.m >> -sh;
}

/* SemitonesToRatio (stmlib) : demi-tons << 16 -> rapport. Comme stmlib : index = partie entiere + 128 (tables
 * de 257 rapports), fraction tronquee en 1/256 de demi-ton. */
XFI xf xs2r_i(s32 semis)
{
	s32 p = semis + (128 << 16), i, j, k, oct;

	if (p < 0)
		p = 0;
	else if (p > (256 << 16))
		p = 256 << 16;
	i = p >> 16;
	j = (p >> 8) & 255;
	k = i - 128;
	oct = k >= 0 ? k / 12 : -((-k + 11) / 12);
	k -= 12 * oct;
	return xnorm(qmul(M_P12[k], M_P256[j]), oct + 1);
}

static __attribute__((noinline)) xf xs2r(s32 semis)
{
	return xs2r_i(semis);
}

/* Interpolate(table, x, size) de stmlib, x en Q31 dans [0, 1], size = 2^lg */
static inline s32 interp(const s32 *t, s32 x, int lg)
{
	s32 i = x >> (31 - lg);
	s32 f = shl(x, lg) & Q31ONE;
	return t[i] + qmul(t[i + 1] - t[i], f);
}

#endif
