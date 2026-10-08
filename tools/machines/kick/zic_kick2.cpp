/*
 * Kick2 (zicCycle) - port ColdFire en virgule fixe de zicBox PotKick.h
 * Les algorithmes de PotKick.h :
 *  - chute de hauteur à 4 courbes (SWEEP : punch classique, double chute gabber, smoothstep, glissé long)
 *  - VCO à 5 formes (MRPH : sinus, triangle, scie, carré, scie écrêtée par tanh)
 *  - waveshaper (SHAPE : drive tanh puis repli d'onde)
 *  - résonateur à variable d'état suivant la fréquence de base (CONTOUR), drive, compresseur
 *
 * Le MCF54418 n'a pas d'unité flottante, et la seule libgcc fournie (m68k-linux-gnu) est compilée pour le 68020 :
 * ses routines flottantes logicielles lèvent une exception sur ColdFire. Tout est donc en entiers : Q31 par
 * l'EMAC, Q28 ou Q24 là où il faut de la marge (état du filtre, entrée de tanh). Ni float, ni 64 bits, ni libgcc.
 */

typedef signed char s8;
typedef short s16;
typedef int s32;
typedef unsigned int u32;

#define ONE 0x7fffffff

/* Q31 x Q31 -> Q31 (EMAC : multiplication fractionnaire signée, saturante) */
static inline s32 qmul(s32 a, s32 b) {
    s32 r;
    __asm__ volatile("mac.l %1,%2,%%acc0\n\tmovclr.l %%acc0,%0" : "=d"(r) : "r"(a), "r"(b));
    return r;
}

/* Accès à la voix et aux paramètres de l'OS 1.13 */
#define V32(v, off) (*(s32 *)((char *)(v) + (off)))
#define U32(v, off) (*(u32 *)((char *)(v) + (off)))
#define P16(p, off) (*(const s16 *)((const char *)(p) + (off)))
#define P8(p, off)  (*(const s8  *)((const char *)(p) + (off)))

#define FW_TABLE(a) ((const s32 *)(a))
#define SINE      FW_TABLE(0x8000eee4) /* sinus 256+1 points Q31 (SRAM) */
#define LUT_DECAY FW_TABLE(0x4012228c) /* DECAY -> décroissance de l'enveloppe d'ampli */
#define LUT_ATK   FW_TABLE(0x4012268c) /* DECAY -> attaque de l'enveloppe d'ampli */

#define AMP_ENV(v) ((void (*)(char *))0x400a9252)(v)
#define VCA(o, v)  ((void (*)(s32 *, char *))0x400a9430)(o, v)
#define PUNCH(o, v) ((void (*)(s32 *, char *))0x400a967a)(o, v)

/* État de la voix de Kick2 (zone des opérateurs FM, inutilisée par cette machine) */
#define S_PHASE        0x70 // u32 phase de la porteuse (2^32 = un cycle)
#define S_MOD_ENV      0x74 // Q31 enveloppe de la chute de hauteur
#define S_SVF_LP       0x78 // Q24
#define S_SVF_BP       0x7c // Q24
#define S_INV_T        0x80 // Q31 (1 - t) de l'enveloppe du kick
#define S_STEP         0x84 // Q31 décrément de S_INV_T par échantillon
#define S_COMP_ENV     0x88 // Q31
#define S_BASE_INC     0x8c // u32 incrément de phase de la fréquence de base
#define S_VCO_MORPH    0x90 // Q31
#define S_SWEEP_SHP    0x94 // Q31
#define S_WAVESHAPE    0x98 // Q31
#define S_RESONATOR    0x9c // Q31
#define S_DRIVE        0xa0 // 0/1
#define S_SWEEP_MULT   0xa4 // Q31 multiplicateur de l'enveloppe de chute par bloc de 32 échantillons

#define INC_PER_HZ  0x15d86   /* 2^32 / 48000 */
#define KNOB_NORM   66052     /* 0x7f00 * KNOB_NORM ~= 1.0 in Q31 */

/* tanh(x) pour x = 0..4 en 256 pas, Q31 */
static const s32 TANH[257] = {
    0x00000000, 0x01fff556, 0x03ffaab3, 0x05fee041, 0x07fd5666, 0x09facdea, 0x0bf70812, 0x0df1c6c2,
    0x0feacc96, 0x11e1dd05, 0x13d6bc7b, 0x15c93072, 0x17b8ff90, 0x19a5f1be, 0x1b8fd041, 0x1d7665d0,
    0x1f597ea7, 0x2138e89f, 0x2314733d, 0x24ebefc4, 0x26bf3142, 0x288e0ca0, 0x2a5858ac, 0x2c1dee24,
    0x2ddea7bd, 0x2f9a622c, 0x3150fc29, 0x33025676, 0x34ae53dd, 0x3654d932, 0x37f5cd57, 0x39911932,
    0x3b26a7af, 0x3cb665b8, 0x3e404234, 0x3fc42dfa, 0x41421bcc, 0x42ba004d, 0x442bd1f8, 0x45978915,
    0x46fd1fab, 0x485c9177, 0x49b5dbdd, 0x4b08fddb, 0x4c55f7fa, 0x4d9ccc44, 0x4edd7e2f, 0x50181292,
    0x514c8f95, 0x527afca3, 0x53a36257, 0x54c5ca71, 0x55e23fc4, 0x56f8ce28, 0x5809826b, 0x59146a3e,
    0x5a19942e, 0x5b190f8e, 0x5c12ec6e, 0x5d073b88, 0x5df60e39, 0x5edf766c, 0x5fc38693, 0x60a25199,
    0x617bead4, 0x625065fb, 0x631fd71b, 0x63ea5289, 0x64afecdc, 0x6570bae1, 0x662cd18f, 0x66e44601,
    0x67972d6f, 0x68459d1e, 0x68efaa61, 0x69956a8d, 0x6a36f2f1, 0x6ad458d2, 0x6b6db163, 0x6c0311c2,
    0x6c948eee, 0x6d223dc4, 0x6dac32fc, 0x6e328322, 0x6eb54293, 0x6f348579, 0x6fb05fc7, 0x7028e539,
    0x709e294b, 0x71103f3b, 0x717f3a06, 0x71eb2c66, 0x725428cd, 0x72ba4168, 0x731d881b, 0x737e0e7f,
    0x73dbe5e2, 0x74371f47, 0x748fcb63, 0x74e5faa1, 0x7539bd19, 0x758b229a, 0x75da3aa2, 0x76271463,
    0x7671bec0, 0x76ba484d, 0x7700bf52, 0x774531cb, 0x7787ad65, 0x77c83f82, 0x7806f53a, 0x7843db59,
    0x787efe60, 0x78b86a88, 0x78f02bc3, 0x79264dba, 0x795adbd0, 0x798de122, 0x79bf688b, 0x79ef7ca0,
    0x7a1e27b4, 0x7a4b73da, 0x7a776ae5, 0x7aa21667, 0x7acb7fb7, 0x7af3afee, 0x7b1aafe8, 0x7b408848,
    0x7b654178, 0x7b88e3aa, 0x7bab76d9, 0x7bcd02c8, 0x7bed8f08, 0x7c0d22f5, 0x7c2bc5ba, 0x7c497e50,
    0x7c66537e, 0x7c824bde, 0x7c9d6ddd, 0x7cb7bfb8, 0x7cd14782, 0x7cea0b23, 0x7d021059, 0x7d195cb9,
    0x7d2ff5b1, 0x7d45e086, 0x7d5b225b, 0x7d6fc02a, 0x7d83becb, 0x7d9722f4, 0x7da9f136, 0x7dbc2e03,
    0x7dcdddad, 0x7ddf0463, 0x7defa63a, 0x7dffc725, 0x7e0f6afd, 0x7e1e957b, 0x7e2d4a40, 0x7e3b8cd1,
    0x7e496098, 0x7e56c8e6, 0x7e63c8f4, 0x7e7063e2, 0x7e7c9cb9, 0x7e88766b, 0x7e93f3d4, 0x7e9f17bc,
    0x7ea9e4d3, 0x7eb45db7, 0x7ebe84f3, 0x7ec85cfc, 0x7ed1e836, 0x7edb28f4, 0x7ee42174, 0x7eecd3e8,
    0x7ef5426c, 0x7efd6f0f, 0x7f055bd0, 0x7f0d0a9e, 0x7f147d5a, 0x7f1bb5d7, 0x7f22b5d8, 0x7f297f15,
    0x7f301337, 0x7f3673db, 0x7f3ca292, 0x7f42a0e0, 0x7f48703e, 0x7f4e121a, 0x7f5387d6, 0x7f58d2cb,
    0x7f5df444, 0x7f62ed87, 0x7f67bfcd, 0x7f6c6c46, 0x7f70f418, 0x7f755863, 0x7f799a3c, 0x7f7dbaaf,
    0x7f81bac2, 0x7f859b71, 0x7f895db3, 0x7f8d0274, 0x7f908a9d, 0x7f93f70c, 0x7f97489a, 0x7f9a801a,
    0x7f9d9e57, 0x7fa0a418, 0x7fa3921c, 0x7fa6691e, 0x7fa929d0, 0x7fabd4e3, 0x7fae6aff, 0x7fb0ecc9,
    0x7fb35ae0, 0x7fb5b5de, 0x7fb7fe5a, 0x7fba34e4, 0x7fbc5a09, 0x7fbe6e52, 0x7fc07243, 0x7fc2665c,
    0x7fc44b19, 0x7fc620f3, 0x7fc7e85f, 0x7fc9a1ce, 0x7fcb4dad, 0x7fccec68, 0x7fce7e66, 0x7fd00409,
    0x7fd17db5, 0x7fd2ebc6, 0x7fd44e97, 0x7fd5a682, 0x7fd6f3db, 0x7fd836f6, 0x7fd97023, 0x7fda9fb1,
    0x7fdbc5ea, 0x7fdce318, 0x7fddf783, 0x7fdf036e, 0x7fe0071e, 0x7fe102d2, 0x7fe1f6c9, 0x7fe2e341,
    0x7fe3c873, 0x7fe4a69a, 0x7fe57ded, 0x7fe64ea1, 0x7fe718eb, 0x7fe7dcfc, 0x7fe89b07, 0x7fe95339,
    0x7fea05c2,
};

static inline s32 qlerp(s32 a, s32 b, s32 t) {
    return a + qmul(b - a, t);
}

static inline s32 clampq(s32 v, s32 lo, s32 hi) {
    return v < lo ? lo : (v > hi ? hi : v);
}

/* sin(2 pi ph / 2^32), Q31 */
static inline s32 sine(u32 ph) {
    const s32 *t = SINE + (ph >> 24);
    return t[0] + qmul(t[1] - t[0], (s32)((ph & 0xffffff) << 7));
}

/* tanh d'une entrée Q24 (plage +-128), sortie Q31 */
static inline s32 tanh24(s32 x) {
    u32 a = x < 0 ? (u32)0 - (u32)x : (u32)x;
    s32 y;
    if (a >= (4u << 24)) {
        y = TANH[256];
    } else {
        const s32 *t = TANH + (a >> 18);
        y = t[0] + qmul(t[1] - t[0], (s32)((a & 0x3ffff) << 13));
    }
    return x < 0 ? -y : y;
}

/* racine carrée d'une valeur Q31 de [0, 1], Q31 */
static s32 sqrt31(s32 p) {
    if (p <= 0) return 0;
    u32 x = (u32)p << 1; // sqrt(p * 2^31) = sqrt(2p) * 2^15
    u32 r = 0, bit = 1u << 30;
    while (bit > x) bit >>= 2;
    while (bit) {
        if (x >= r + bit) {
            x -= r + bit;
            r = (r >> 1) + bit;
        } else {
            r >>= 1;
        }
        bit >>= 2;
    }
    u32 out = r << 15;
    return out > (u32)ONE ? ONE : (s32)out;
}

/* VCO à morphing, potard MRPH : sinus -> triangle -> scie -> carré -> scie écrêtée (tanh).
 * Toutes les formes partent de 0 et montent comme le sinus : le morphing ne saute jamais de phase. */
static s32 getVCO(u32 ph, s32 morph) {
    s32 s = sine(ph);
    if (morph <= 0) return s;

    s32 saw = (s32)ph; // part de 0, boucle à mi-cycle
    u32 seg = (u32)morph >> 29; // 0..3
    s32 t = (s32)(((u32)morph << 2) & 0x7fffffffu);

    switch (seg) {
        case 0: { // sinus -> triangle
            s32 x = (s32)(ph + 0x40000000u);
            u32 a = x < 0 ? ~(u32)x : (u32)x;
            s32 tri = (s32)((a << 1) ^ 0x80000000u);
            return qlerp(s, tri, t);
        }
        case 1: { // triangle -> scie
            s32 x = (s32)(ph + 0x40000000u);
            u32 a = x < 0 ? ~(u32)x : (u32)x;
            s32 tri = (s32)((a << 1) ^ 0x80000000u);
            return qlerp(tri, saw, t);
        }
        case 2: { // scie -> carré
            s32 sq = (s > 0) ? 0x60000000 : -0x60000000;
            return qlerp(saw, sq, t);
        }
        default: { // carré -> scie écrêtée (tanh)
            s32 sq = (s > 0) ? 0x60000000 : -0x60000000;
            s32 softClipped = tanh24((saw >> 7) * 5 / 2);
            return qlerp(sq, softClipped, t);
        }
    }
}

/* Chute de hauteur gabber : 4 courbes fondues par le potard SWEEP (p = enveloppe de 1 à 0, résultat Q31).
 *   0%    p^2                       punch classique
 *   33%   0,75 p^8 + 0,25 p         double chute : plongeon rapide, puis longue queue
 *   67%   smoothstep(p)             garde la hauteur, puis tombe (laser / hoover)
 *   100%  p^1,5                     glissé long, la chute n'arrive qu'à la fin du balayage */
static s32 getShapedPitch(s32 p, s32 shape) {
    p = clampq(p, 0, ONE);
    s32 p2 = qmul(p, p);
    s32 p4 = qmul(p2, p2);
    s32 dd = qmul(0x60000000, qmul(p4, p4)) + qmul(0x20000000, p);
    s32 hoover = (s32)((u32)p2 * 3u - 2u * (u32)qmul(p2, p));
    s32 a, b;
    u32 base;
    if (shape < 0x2aaaaaaa) {
        a = p2; b = dd; base = 0;
    } else if (shape < 0x55555555) {
        a = dd; b = hoover; base = 0x2aaaaaaa;
    } else {
        a = hoover; b = qmul(p, sqrt31(p)); base = 0x55555555;
    }
    u32 t = ((u32)shape - base) * 3u;
    return qlerp(a, b, t > (u32)ONE ? ONE : (s32)t);
}

/* Waveshaper (potard SHAPE, Q31). Chaque étage entre en fondu depuis zéro, rien ne saute :
 *   0 .. 35%   propre -> drive tanh, gain 1x .. 8x (le gain monte comme le carré du potard)
 *   35 .. 100% drive tanh -> repli d'onde du signal sec, profondeur 1x .. 3,5x, fondu linéaire */
#define WS_SPLIT 0x2ccccccd // 0.35

static s32 waveshape(s32 sig, s32 shape) {
    if (shape <= 0) return sig;
    s32 s1 = shape >= WS_SPLIT ? ONE : (shape >> 8) * 731;   // 0 .. 1 sur les 35 premiers %
    s32 g = ONE / 8 + qmul(qmul(s1, s1), ONE - ONE / 8);     // gain 1 .. 8 (Q31 / 8)
    s32 sat = qlerp(sig, tanh24(qmul(sig >> 7, g) << 3), s1);
    if (shape <= WS_SPLIT) return sat;

    s32 f = ((shape - WS_SPLIT) >> 8) * 393;                 // 0 .. 1 sur les 65 derniers %
    s32 x = sig >> 7;                                        // Q24
    s32 xf = qmul(x, f);
    x += 2 * xf + (xf >> 1);                                 // profondeur du repli 1x .. 3,5x
    s32 fold = sine((u32)x << 6);                            // 1,0 = un quart de cycle, le repliement vient du bouclage
    return qlerp(sat, fold, f);
}

/* Fréquence de la chute de hauteur, en incrément de phase : part de 13 fois la fréquence de base */
static u32 rootInc(u32 baseInc, s32 modEnv, s32 shape) {
    s32 pMorph = getShapedPitch(modEnv, shape);
    s32 add = qmul((s32)baseInc, pMorph) * 12;
    return (u32)((s32)baseInc + add);
}

extern "C" {

void kick2_update(s32 pmod, char* v, const char* p) {
    if (!v || !p) return;
    (void)pmod;

    s32 pitch_val = (s32)P16(p, 0x14) >> 8; // potard PITCH : 0..127
    s32 color     = P16(p, 0x16); if (color < 0) color = 0; if (color > 0x7f00) color = 0x7f00;
    s32 shape     = P16(p, 0x18); if (shape < 0) shape = 0; if (shape > 0x7f00) shape = 0x7f00;
    s32 sweep     = P16(p, 0x1a); if (sweep < 0) sweep = 0; if (sweep > 0x7f00) sweep = 0x7f00;
    s32 contour   = P16(p, 0x1c); if (contour < 0) contour = 0; if (contour > 0x7f00) contour = 0x7f00;
    s32 punch     = P16(p, 0x1e) > 0 ? 1 : 0;
    s32 dec       = P8(p, 0x24);  if (dec < 0) dec = 0;     if (dec > 127) dec = 127;
    if (pitch_val < 0) pitch_val = 0;

    // Fréquence de base du sub : 30 Hz à 100 Hz (potard PITCH), 0,551 Hz par pas
    V32(v, S_BASE_INC)      = 30 * INC_PER_HZ + pitch_val * 0xc097;
    V32(v, S_VCO_MORPH)     = color * KNOB_NORM;
    V32(v, S_SWEEP_SHP)     = sweep * KNOB_NORM;
    V32(v, S_WAVESHAPE)    = shape * KNOB_NORM;
    V32(v, S_RESONATOR)     = contour * KNOB_NORM;
    V32(v, S_DRIVE)         = punch;

    // Décroissance de la chute : tau fixe de 70 ms, par bloc de 32 échantillons (exp(-32 / 3360))
    V32(v, S_SWEEP_MULT) = 0x7ec967ba;

    // Durée du kick : 50 ms à 3000 ms (potard DECAY)
    s32 totalSamples = 2400 + (dec * 11146) / 10;
    V32(v, S_STEP) = ONE / totalSamples;

    // Enveloppe d'ampli de l'OS tenue ouverte (DECAY le plus long) : le kick fait sa propre enveloppe
    V32(v, 0x250) = LUT_DECAY[127];

    /* Au trig : niveau de l'enveloppe d'ampli (0x230) et état du kick */
    if (V32(v, 0x38)) {
        V32(v, 0x230) = ONE; // niveau de l'enveloppe d'ampli = 100 %
        V32(v, 0x274) = V32(v, 0x278) = 0x01f10e1d; // constantes de l'étage PUNCH (comme SNARE)
        V32(v, 0x280) = V32(v, 0x284) = 0x001f7c5c;
        V32(v, 0x290) = V32(v, 0x294) = ONE;
        V32(v, 0x27c) = 0x83e21c3a;
        V32(v, 0x288) = 0x803ef8b8;
        V32(v, 0x248) = LUT_ATK[127];
        if (punch) {
            V32(v, 0x29c) = 0x40000000; V32(v, 0x2a0) = ONE; V32(v, 0x2a4) = 0x40000000;
            V32(v, 0x48) = 1; V32(v, 0x2b8) = 0x80000000;
        } else {
            V32(v, 0x29c) = ONE; V32(v, 0x2a0) = 0x20000000; V32(v, 0x2a4) = ONE;
            V32(v, 0x48) = 0; V32(v, 0x2b8) = 0xc028db9c;
        }

        U32(v, S_PHASE)    = 0;
        V32(v, S_MOD_ENV)  = ONE;
        V32(v, S_SVF_LP)   = 0;
        V32(v, S_SVF_BP)   = 0;
        V32(v, S_COMP_ENV) = 0;
        V32(v, S_INV_T)    = ONE;
    }
}

void kick2_render(s32* out, char* v) {
    if (!out || !v) return;

    u32 phase     = U32(v, S_PHASE);
    s32 modEnv    = V32(v, S_MOD_ENV);
    s32 svfLp     = V32(v, S_SVF_LP);
    s32 svfBp     = V32(v, S_SVF_BP);
    s32 compEnv   = V32(v, S_COMP_ENV);
    s32 invT      = V32(v, S_INV_T);
    s32 step      = V32(v, S_STEP);

    u32 baseInc   = U32(v, S_BASE_INC);
    s32 vcoMorph  = V32(v, S_VCO_MORPH);
    s32 sweepShp  = V32(v, S_SWEEP_SHP);
    s32 wshape    = V32(v, S_WAVESHAPE);
    s32 resonator = V32(v, S_RESONATOR);
    s32 drive     = V32(v, S_DRIVE);

    // Chute évaluée aux deux bouts du bloc, interpolée échantillon par échantillon
    s32 modEnvEnd = qmul(modEnv, V32(v, S_SWEEP_MULT));
    u32 inc0 = rootInc(baseInc, modEnv, sweepShp);
    u32 inc1 = rootInc(baseInc, modEnvEnd, sweepShp);
    s32 incStep = ((s32)inc1 - (s32)inc0) >> 5;
    u32 inc = inc0;

    // Coefficients du résonateur, fréquence de coupure suivant la hauteur (30 .. 3500 Hz)
    s32 svfF = 0, svfQ = 0, resMix = 0, resGain = 0;
    if (resonator > 0) {
        u32 fc = clampq((s32)((inc0 >> 1) + (inc1 >> 1)), 30 * INC_PER_HZ, 3500 * INC_PER_HZ);
        svfF = sine(fc >> 1) << 1;                         // 2 * sin(pi * fc / 48000)
        svfQ = ONE - qmul(resonator, 0x7ae147ae);         // 1 - res * 0.96
        resGain = 0x20000000 + qmul(resonator, 0x50000000); // (1 + res * 2.5) / 4
        u32 mix = (u32)resonator + ((u32)resonator >> 2);  // res * 1.25
        resMix = mix > (u32)ONE ? ONE : (s32)mix;
    }

    for (int i = 0; i < 32; i++) {
        s32 envAmp = 0;
        if (invT > 0) {
            s32 i2 = qmul(invT, invT);
            envAmp = qmul(qmul(i2, i2), invT); // (1 - t)^5
            invT -= step;
        }

        s32 sig = 0;
        if (envAmp > 0x000346dc) { // > 0.0001
            phase += inc;
            sig = getVCO(phase, vcoMorph);

            if (resonator > 0) {
                s32 in = sig >> 7; // Q24
                svfLp += qmul(svfF, svfBp);
                s32 hp = in - svfLp - qmul(svfQ, svfBp);
                svfBp += qmul(svfF, hp);
                svfLp = clampq(svfLp, -(1 << 30), 1 << 30);
                svfBp = clampq(svfBp, -(1 << 30), 1 << 30);

                s32 peak = svfLp + svfBp + qmul(svfBp, 0x66666666); // lp + bp * 1.8
                s32 y = qmul(peak, resGain);
                s32 sat;
                if (y >= (1 << 24)) sat = ONE;
                else if (y <= -(1 << 24)) sat = -ONE;
                else sat = tanh24(y << 2);
                sig = qlerp(sig, sat, resMix);
            }

            sig = waveshape(sig, wshape);
            sig = qmul(sig, envAmp);
        }
        inc += incStep;

        if (drive) {
            sig = tanh24(qmul(sig >> 7, 0x42666666) << 3); // tanh(sig * 4.15)
        }

        // Compresseur de colle (ratio 0,65)
        s32 absSig = sig < 0 ? (sig == (s32)0x80000000 ? ONE : -sig) : sig;
        compEnv += qmul(absSig - compEnv, 0x06666666); // 0.05
        if (compEnv > 0x53333333) {
            u32 g = 0x53333333u / ((u32)compEnv >> 15);
            sig = qmul(sig, g >= 0x8000 ? ONE : (s32)(g << 16));
        }

        out[i] = sig;
    }

    modEnv = modEnvEnd;
    if (invT < 0) invT = 0;

    U32(v, S_PHASE)    = phase;
    V32(v, S_MOD_ENV)  = modEnv;
    V32(v, S_SVF_LP)   = svfLp;
    V32(v, S_SVF_BP)   = svfBp;
    V32(v, S_COMP_ENV) = compEnv;
    V32(v, S_INV_T)    = invT;

    AMP_ENV(v);
    VCA(out, v);
    PUNCH(out, v);
}

} // extern "C"
