/*
 * Kick3 (zicCycle) - port ColdFire en virgule fixe de zicBox KickWave.h
 * La forme d'onde du kick se construit avec les potards, la chute de hauteur est celle de KickWave :
 *  - PITCH   caractère de la chute : glissé doux / classique / double chute gabber / plongeon long
 *            (la hauteur elle-même suit la note du trig, 52 Hz à C4)
 *  - COLOR   waveShape : sinus -> triangle -> scie -> carré
 *  - SHAPE   fold :      repli d'onde (wavefold)
 *  - SWEEP   skew :      déformation asymétrique de la phase (centre = symétrique)
 *  - CONTOUR harmonique 2 : l'octave, bipolaire (centre = aucune)
 *  - PUNCH   drive
 *
 * Le MCF54418 n'a pas d'unité flottante, et la seule libgcc fournie (m68k-linux-gnu) est compilée pour le 68020 :
 * ses routines flottantes logicielles lèvent une exception sur ColdFire. Tout est donc en entiers : Q31 par
 * l'EMAC, Q28 là où il faut de la marge. Ni float, ni 64 bits, ni libgcc.
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

/* État de la voix de Kick3 (zone des opérateurs FM, inutilisée par cette machine) */
#define S_PHASE        0x70 // u32 phase de la porteuse (2^32 = un cycle)
#define S_PITCH_ENV    0x74 // Q31 enveloppe de hauteur (1 -> 0)
#define S_MOD_PHASE    0x78 // u32 phase du modulateur FM
#define S_INV_T        0x80 // Q31 (1 - t) de l'enveloppe du kick
#define S_STEP         0x84 // Q31 décrément de S_INV_T par échantillon
#define S_COMP_ENV     0x88 // Q28
#define S_BASE_INC     0x8c // s32 incrément de phase de la fréquence de base
#define S_WAVE         0x90 // Q31 waveShape
#define S_FOLD         0x94 // Q31 fold
#define S_HARM2        0x98 // Q31 harmonique 2, signée
#define S_SKEW_K       0x9c // u32 point de déformation (phase)
#define S_SKEW_R1      0xa0 // Q27 0,5 / skew   (/16)
#define S_SKEW_R2      0xa4 // Q27 0,5 / (1 - skew) (/16)
#define S_DRIVE        0xa8 // 0/1
#define S_PITCH_DECAY  0xac // Q31 multiplicateur par échantillon de la 1re exponentielle de hauteur
#define S_PITCH_ENV2   0xb0 // Q31 2e exponentielle de hauteur (queue lente)
#define S_PITCH_DECAY2 0xb4 // Q31 multiplicateur par échantillon de la 2e exponentielle
#define S_PITCH_W1     0xb8 // Q31 poids de la 1re exponentielle (la 2e a 1 - w1)
#define S_PITCH_DEPTH  0xbc // Q31 profondeur de la chute / 16

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


/* Incrément de phase par échantillon d'une hauteur donnée en demi-tons depuis le la 440 Hz, Q16 */
#define INC440 39370534 /* 2^32 * 440 / 48000 */
static s32 note_inc(s32 n) {
    s32 o = qmul(n, 0x0aaaaaab);
    s32 e = o >> 16;
    s32 x = (o & 0xffff) << 15;
    s32 y = qmul(0x09e79bdb, x) + 0x1d0c5fa9;
    y = qmul(y, x) + 0x5903d9d4;
    y = qmul(y, x);
    s32 inc = qmul((1 << 30) + (y >> 1), INC440) << 1;
    if (e >= 0) {
        if (e > 8) e = 8;
        inc <<= e;
    } else {
        if (e < -8) e = -8;
        inc >>= -e;
    }
    return inc;
}

/* Forme d'onde de KickWave : phase déformée (skew) -> morphing sinus/triangle/scie/carré -> + harmonique 2 ->
 * repli d'onde. Triangle et scie partent de 0 et montent comme le sinus (ceux de KickWave partent de -1 / +1) :
 * le morphing ne saute jamais de phase. Sortie Q31. */
static s32 waveform(u32 phase, s32 wave, s32 fold, s32 h2, u32 skewK, s32 r1, s32 r2) {
    // skew : p < skew -> 0,5 p / skew, sinon 0,5 + 0,5 (p - skew) / (1 - skew)
    u32 pw;
    if (phase < skewK) pw = (u32)(qmul((s32)(phase >> 1), r1) << 4) << 1;
    else pw = 0x80000000u + ((u32)(qmul((s32)((phase - skewK) >> 1), r2) << 4) << 1);

    s32 s = sine(pw);
    s32 saw = (s32)pw;
    s32 x = (s32)(pw + 0x40000000u);
    u32 a = x < 0 ? ~(u32)x : (u32)x;
    s32 tri = (s32)((a << 1) ^ 0x80000000u);
    s32 sq = s > 0 ? ONE : -ONE;

    u32 base;
    s32 p0, p1;
    if (wave < 0x2aaaaaaa) { p0 = s; p1 = tri; base = 0; }
    else if (wave < 0x55555555) { p0 = tri; p1 = saw; base = 0x2aaaaaaa; }
    else { p0 = saw; p1 = sq; base = 0x55555555; }
    u32 t = ((u32)wave - base) * 3u;
    s32 m = qlerp(p0, p1, t > (u32)ONE ? ONE : (s32)t) >> 3; // Q28, de la marge pour l'harmonique

    if (h2 != 0) m += qmul(h2, sine(pw << 1)) >> 3;
    m = clampq(m, -0x0fffffff, 0x0fffffff);
    s32 out = m << 3;                                           // Q31 sec

    if (fold > 0) {
        s32 xf = qmul(m, fold);
        s32 xd = m + 3 * xf + (xf >> 1);                        // profondeur du repli 1 + 3,5 fold
        s32 folded = sine((u32)xd << 2);                        // 1,0 = un quart de cycle
        s32 mix = fold < 0x08000000 ? fold << 4 : ONE;          // le repli entre en fondu sur les 6 premiers %
        out = qlerp(out, folded, mix);
    }
    return out;
}

extern "C" {

void kick3_update(s32 pmod, char* v, const char* p) {
    if (!v || !p) return;

    s32 pitch     = (s32)P16(p, 0x14) >> 8;                 // potard PITCH 0..127 : caractère de la chute
    s32 color     = P16(p, 0x16); if (color < 0) color = 0; if (color > 0x7f00) color = 0x7f00;
    s32 shape     = P16(p, 0x18); if (shape < 0) shape = 0; if (shape > 0x7f00) shape = 0x7f00;
    s32 sweep     = P16(p, 0x1a); if (sweep < 0) sweep = 0; if (sweep > 0x7f00) sweep = 0x7f00;
    s32 contour   = P16(p, 0x1c); if (contour < 0) contour = 0; if (contour > 0x7f00) contour = 0x7f00;
    s32 punch     = P16(p, 0x1e) > 0 ? 1 : 0;
    s32 dec       = P8(p, 0x24);  if (dec < 0) dec = 0;     if (dec > 127) dec = 127;
    if (pitch < 0) pitch = 0;
    if (pitch > 127) pitch = 127;

    // Fréquence de base 52 Hz à la note du trig (C4), elle suit la note
    s32 n = pmod - (97 << 16);
    if (n < -(48 << 16)) n = -(48 << 16);
    if (n > (30 << 16)) n = 30 << 16;
    V32(v, S_BASE_INC) = note_inc(n);

    V32(v, S_WAVE) = color * KNOB_NORM;
    V32(v, S_FOLD) = shape * KNOB_NORM;
    V32(v, S_HARM2) = (contour - 0x4000) * 131072;          // -1 .. +1, centré sur 64

    // Skew de 5 % à 95 % (centre du potard = 50 %), en 0,5/skew et 0,5/(1-skew), Q27
    s32 sk16 = 3277 + (sweep * 58982) / 0x7f00;
    s32 dk16 = 65536 - sk16;
    U32(v, S_SKEW_K) = (u32)sk16 << 16;
    V32(v, S_SKEW_R1) = (s32)(((1u << 31) / (u32)sk16) << 11);
    V32(v, S_SKEW_R2) = (s32)(((1u << 31) / (u32)dk16) << 11);
    V32(v, S_DRIVE) = punch;

    // Potard PITCH = caractère de la chute, fondu entre 4 réglages (tau en échantillons, profondeur x base) :
    //   0    glissé doux       profondeur 1,2,  tau 30 ms
    //   1/3  classique         profondeur 3,5,  tau 7 ms     (réglage par défaut de KickWave)
    //   2/3  gabber            profondeur 7,    0,65 x 5 ms + 0,35 x 45 ms (plongeon rapide, puis longue queue)
    //   1    plongeon long     profondeur 10,   tau 90 ms
    static const s32 P_DEPTH[4] = { 161061273, 469762048, 939524096, 1342177280 }; // profondeur / 16, Q31
    static const s32 P_N1[4]    = { 1440, 336, 240, 4320 };
    static const s32 P_N2[4]    = { 2160, 2160, 2160, 2160 };
    static const s32 P_W1[4]    = { ONE, ONE, 0x53333333, ONE };
    s32 seg = (pitch * 3) / 127; if (seg > 2) seg = 2;
    s32 tp = (pitch * 3 - seg * 127) * (ONE / 127);
    if (tp > ONE) tp = ONE;
    s32 n1 = qlerp(P_N1[seg], P_N1[seg + 1], tp);
    s32 n2 = qlerp(P_N2[seg], P_N2[seg + 1], tp);
    s32 x1 = ONE / n1, x2 = ONE / n2;
    V32(v, S_PITCH_DECAY)  = ONE - x1 + (qmul(x1, x1) >> 1);   // exp(-1 / n)
    V32(v, S_PITCH_DECAY2) = ONE - x2 + (qmul(x2, x2) >> 1);
    V32(v, S_PITCH_W1)     = qlerp(P_W1[seg], P_W1[seg + 1], tp);
    V32(v, S_PITCH_DEPTH)  = qlerp(P_DEPTH[seg], P_DEPTH[seg + 1], tp);

    // Durée de 50 ms à 1500 ms (potard DECAY)
    V32(v, S_STEP) = ONE / (2400 + dec * 548);

    // Enveloppe d'ampli de l'OS tenue ouverte (DECAY le plus long) : le kick fait sa propre enveloppe
    V32(v, 0x250) = LUT_DECAY[127];

    if (V32(v, 0x38)) {                                       // trig
        V32(v, 0x230) = ONE;
        V32(v, 0x274) = V32(v, 0x278) = 0x01f10e1d;           // constantes de l'étage PUNCH (comme SNARE)
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

        U32(v, S_PHASE) = 0;
        U32(v, S_MOD_PHASE) = 0;
        V32(v, S_PITCH_ENV) = ONE;
        V32(v, S_PITCH_ENV2) = ONE;
        V32(v, S_COMP_ENV) = 0;
        V32(v, S_INV_T) = ONE;
    }
}

void kick3_render(s32* out, char* v) {
    if (!out || !v) return;

    u32 phase     = U32(v, S_PHASE);
    u32 modPhase  = U32(v, S_MOD_PHASE);
    s32 pitchEnv  = V32(v, S_PITCH_ENV);
    s32 pitchEnv2 = V32(v, S_PITCH_ENV2);
    s32 compEnv   = V32(v, S_COMP_ENV);
    s32 invT      = V32(v, S_INV_T);
    s32 step      = V32(v, S_STEP);

    s32 baseInc   = V32(v, S_BASE_INC);
    s32 wave      = V32(v, S_WAVE);
    s32 fold      = V32(v, S_FOLD);
    s32 h2        = V32(v, S_HARM2);
    u32 skewK     = U32(v, S_SKEW_K);
    s32 r1        = V32(v, S_SKEW_R1);
    s32 r2        = V32(v, S_SKEW_R2);
    s32 drive     = V32(v, S_DRIVE);
    s32 pitchMul  = V32(v, S_PITCH_DECAY);
    s32 pitchMul2 = V32(v, S_PITCH_DECAY2);
    s32 pitchW1   = V32(v, S_PITCH_W1);
    s32 pitchDepth = V32(v, S_PITCH_DEPTH);

    for (int i = 0; i < 32; i++) {
        s32 envAmp = 0;
        if (invT > 0) {
            s32 i2 = qmul(invT, invT);
            envAmp = qmul(qmul(i2, i2), invT); // (1 - t)^5
            invT -= step;
        }

        s32 sig = 0;
        if (envAmp > 0x000346dc) { // > 0.0001
            pitchEnv = qmul(pitchEnv, pitchMul);
            pitchEnv2 = qmul(pitchEnv2, pitchMul2);
            s32 env = qmul(pitchW1, pitchEnv) + qmul(ONE - pitchW1, pitchEnv2);
            s32 add = qmul(qmul(baseInc, env), pitchDepth);          // base * env * profondeur / 16
            if (add > 0x07ffffff) add = 0x07ffffff;
            s32 inc = baseInc + (add << 4);

            modPhase += (u32)inc + ((u32)inc >> 1);                 // modulateur à 1,5 fois
            s32 fm = qmul(qmul(sine(modPhase), env), 11008000);     // profondeur de FM 35 %
            phase += (u32)inc + (u32)fm;

            sig = qmul(waveform(phase, wave, fold, h2, skewK, r1, r2), envAmp);
        }

        // PUNCH = drive : tanh(sig * 6,25) * 6,25, en Q28 (applyDrive de KickWave à 35 %)
        s32 o;
        if (drive) {
            s32 sat = tanh24(qmul(sig >> 7, 0x32000000) << 4) >> 3;
            o = sat * 6 + (sat >> 2);
        } else {
            o = sig >> 3;
        }

        // Compresseur de colle (ratio 0,65), Q28
        s32 absO = o < 0 ? -o : o;
        compEnv += qmul(absO - compEnv, 0x06666666);               // 0.05
        if (compEnv > 0x0a666666) {
            u32 g = 0x53333333u / ((u32)compEnv >> 12);
            o = qmul(o, g >= 0x8000 ? ONE : (s32)(g << 16));
        }

        o = clampq(o, -0x0fffffff, 0x0fffffff);
        out[i] = o << 3;
    }

    U32(v, S_PHASE)     = phase;
    U32(v, S_MOD_PHASE) = modPhase;
    V32(v, S_PITCH_ENV) = pitchEnv;
    V32(v, S_PITCH_ENV2) = pitchEnv2;
    V32(v, S_COMP_ENV)  = compEnv;
    V32(v, S_INV_T)     = invT;

    AMP_ENV(v);
    VCA(out, v);
    PUNCH(out, v);
}

} // extern "C"
