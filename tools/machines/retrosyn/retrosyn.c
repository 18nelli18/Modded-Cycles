/* Origin: AveyCole fork (https://github.com/AveyCole/Modded-Cycles), MIT License.
 * RETROSYN : passerelle OS 1.13, meme contrat update/render que MACRO.
 * Etat par piste en BSS, marque effacee par le changement de machine.
 * DECAY/GATE : enveloppe TONE ; PUNCH quantifie le coeur a quatre bits.
 */
#include "retrosyn_dsp.h"
#define V32(o) (*(s32 *)(v + (o)))
#define P16(o) (*(const s16 *)(p + (o)))
#define MARK 0x52535931
#define AMP_ENV(v) ((void (*)(char *))0x400a9252)(v)
#define VCA(o,v) ((void (*)(s32 *,char *))0x400a9430)(o,v)
#define LUT_DECAY ((const s32 *)0x4011d84c)
struct Track { retrosyn_t osc; retrosyn_in_t in; };
static struct Track tracks[6];
static struct Track *track_of(char *v) {
    return &tracks[((u32)v - 0x42308828u) / 0x31c];
}
static s32 knob(s32 x) {
    x = x < 0 ? 0 : (x > 0x7f00 ? 0x7f00 : x);
    return x + (x >> 7);
}
static u32 mag(s32 x) { return x < 0 ? 0u - (u32)x : (u32)x; }
void retrosyn_update(s32 pmod, char *v, const char *p) {
    struct Track *t = track_of(v);
    s32 n, dec, shape;
    if (V32(0x2c) != MARK) {
        retrosyn_reset(&t->osc);
        V32(0x2c) = MARK;
    }
    dec = (s8)p[0x24];
    dec = dec < 0 ? 0 : (dec > 127 ? 127 : dec);
    V32(0x250) = LUT_DECAY[dec];
    if (V32(0x38)) {
        V32(0x274) = V32(0x278) = 0x012c0f26;
        V32(0x280) = V32(0x284) = 0x001f7c5c;
        V32(0x290) = V32(0x294) = 0x7fffffff;
        V32(0x27c) = (s32)0x82581e4bu;
        V32(0x288) = (s32)0x803ef8b8u;
        V32(0x29c) = 0x7fffffff;
        V32(0x2a0) = V32(0x2a4) = 0x20000000;
        V32(0x48) = 0;
    }
    n = (s32)P16(0x14) * 256 - (64 << 16) + pmod;
    n += ((s32)P16(0x22) - 0x4000) * 2;
    t->in.note = n < 0 ? 0 : (n > (127 << 16) ? 127 << 16 : n);
    shape = P16(0x18) >> 8;
    shape = shape < 0 ? 0 : (shape > 5 ? 5 : shape);
    t->in.shape = shape * 5462 + 2731;
    t->in.color = knob(P16(0x16));
    /* Le centre physique 64 vaut exactement le centre du balayage. */
    t->in.sweep = P16(0x1a) == 0x4000 ? 16384 : knob(P16(0x1a));
    t->in.contour = knob(P16(0x1c));
    t->in.punch = P16(0x1e) != 0;
    t->in.trig = V32(0x38) != 0;
}
void retrosyn_render(s32 *out, char *v) {
    struct Track *t = track_of(v);
    if (!V32(0x34) && !V32(0x38) && mag(V32(0x230)) < (1 << 14)
        && mag(V32(0x234)) < (1 << 14)) {
        for (s32 i = 0; i < RS_BLOCK; i++) out[i] = 0;
        return;
    }
    retrosyn_block(&t->osc, &t->in, out);
    AMP_ENV(v);
    VCA(out,v);
}
