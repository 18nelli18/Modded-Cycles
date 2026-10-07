/* SPDX-License-Identifier: MIT — Copyright (c) 2026 Combust. Voir ../LICENSE. */
/* Génération d'un pattern (couches 1 à 3) et tirage du bouton Random. Les pistes en mode démo (outil de mise au
 * point de la référence) ne sont pas écrites dans le firmware. */
#include "gen.h"
#include "stylemap.h"

static uint16_t track_mask(const necklace_t *nk, int style, int n, int k, int e)
{
    return style == DENSITY_NESTED ? nested_mask(n, k, e) : necklace_mask(nk, n, k, e);
}

static int clamp_cycle(int n)
{
    return n < 1 ? 1 : n > GEN_MAX_CYCLE ? GEN_MAX_CYCLE : n;
}

static int is_l1(const uint16_t *c, int t)
{
    return c[CTRL(t, T_MODE)] == MODE_L1 && t < L1_LANES;
}

void gen_generate(const necklace_t *nk, uint32_t seed, const uint16_t *c, const uint8_t *locked, gen_out_t *out)
{
    int style = c[CTRL_DENSITY_STYLE], t, s;
    for (t = 0; t < GEN_TRACKS; t++) {
        int n, k, mode = c[CTRL(t, T_MODE)];
        uint16_t mask;
        out->written[t] = 0;
        for (s = 0; s < GEN_STEPS; s++) {
            out->velocity[t][s] = -1;
            out->note[t][s] = -1;
            out->chord[t][s] = -1;
        }
        if (locked && locked[t]) continue;
        if (is_l1(c, t)) {
            out->written[t] = 1;
            out->length[t] = GEN_STEPS;
            l1_render(seed, t, c[CTRL_STYLE], c[CTRL(t, T_DENSITY)], c[CTRL_CHAOS], c[CTRL(t, T_SHIFT)],
                      out->trig[t], out->velocity[t]);
            continue;
        }
        if (mode != MODE_L2 && mode != MODE_L1) continue;
        n = clamp_cycle(c[CTRL(t, T_CYCLE)]);
        k = c[CTRL(t, T_DENSITY)] > n ? n : c[CTRL(t, T_DENSITY)];
        mask = track_mask(nk, style, n, k, c[CTRL(t, T_EVENNESS)]);
        out->written[t] = 1;
        out->length[t] = (uint8_t)n;
        for (s = 0; s < GEN_STEPS; s++) out->trig[t][s] = (uint8_t)cycle_hit(n, mask, c[CTRL(t, T_SHIFT)], s);
        if (t == TONE_TRACK)
            l3_tone(seed, c[CTRL_ROOT], c[CTRL_SCALE], c + CTRL_TONE, out->trig[t], out->note[t]);
        else if (t == CHORD_TRACK)
            l3_chord(seed, c[CTRL_ROOT], c[CTRL_SCALE], c + CTRL_CHORD, out->trig[t], out->note[t], out->chord[t]);
    }
}

static const uint8_t DEFAULTS[GEN_TRACKS][4] = {
    {16, 4, 0, 0}, {16, 2, 0, 4}, {16, 4, 0, 2}, {16, 5, 0, 0}, {16, 3, 0, 0}, {16, 2, 0, 0},
};

void gen_default_controls(uint16_t *c)
{
    int i, t;
    for (i = 0; i < GEN_CONTROLS; i++) c[i] = 0;
    c[CTRL_DEMO_DENSITY] = 40;
    c[CTRL_SCALE] = 1;                     /* mineur */
    c[CTRL_TONE] = 48; c[CTRL_TONE + 1] = 64; c[CTRL_TONE + 2] = 64; c[CTRL_TONE + 3] = 64;
    c[CTRL_CHORD] = 24; c[CTRL_CHORD + 1] = 32; c[CTRL_CHORD + 2] = 64; c[CTRL_CHORD + 3] = 2;
    for (t = 0; t < GEN_TRACKS; t++) {
        c[CTRL(t, T_MODE)] = MODE_L2;
        c[CTRL(t, T_CYCLE)] = DEFAULTS[t][0];
        c[CTRL(t, T_DENSITY)] = DEFAULTS[t][1];
        c[CTRL(t, T_EVENNESS)] = DEFAULTS[t][2];
        c[CTRL(t, T_SHIFT)] = DEFAULTS[t][3];
    }
}

/* Bouton Random : réglages tirés par rôle (grosse caisse clairsemée et sur le premier temps, caisse claire sur le 2,
 * charleston plus dense…), et jamais deux pistes au même rythme (notes/50 §3.1). */
static const uint8_t ROLE_DENSITY_MIN[GEN_TRACKS] = {2, 1, 4, 2, 2, 1};
static const uint8_t ROLE_DENSITY_MAX[GEN_TRACKS] = {6, 4, 12, 7, 8, 4};
static const uint8_t ROLE_ANCHOR[GEN_TRACKS] = {0, 4, 0, 0, 0, 0};
static const uint8_t ROLE_ANCHOR_CHANCE[GEN_TRACKS] = {15, 11, 2, 4, 8, 10};
static const uint8_t ROLE_EVEN_CAP[GEN_TRACKS] = {6, 4, 24, 24, 40, 12};
static const uint8_t CYCLES[10] = {16, 8, 12, 4, 6, 7, 5, 3, 10, 14};
static const uint8_t CYCLE_WEIGHTS[10] = {34, 12, 5, 3, 2, 2, 2, 1, 2, 1};
#define MAX_ATTEMPTS 16

static int pick_cycle(uint32_t *rng)
{
    int r = (int)gen_below(rng, 64), i;
    for (i = 0; i < 10; i++) {
        if (r < CYCLE_WEIGHTS[i]) return CYCLES[i];
        r -= CYCLE_WEIGHTS[i];
    }
    return 16;
}

static int low_biased(uint32_t *rng, int count)
{
    int v = (int)gen_below(rng, (uint32_t)count), i;
    for (i = 0; i < 2; i++) {
        int w = (int)gen_below(rng, (uint32_t)count);
        if (w < v) v = w;
    }
    return v;
}

static int anchor_shift(const necklace_t *nk, int style, int n, int k, int e, int anchor, int from)
{
    uint16_t mask = track_mask(nk, style, n, k, e);
    int i;
    for (i = 0; i < n; i++) {
        int s = (from + i) % n;
        if (cycle_hit(n, mask, s, anchor)) return s;
    }
    return from;
}

/* Pistes de couche 1 dans Random : une position de style et un chaos faible pour tout le kit, puis un remplissage par
 * rôle. */
static const uint8_t L1_FILL_MIN[L1_LANES] = {56, 56, 48, 30};
static const uint8_t L1_FILL_MAX[L1_LANES] = {80, 84, 100, 80};
static const uint8_t L1_SHIFT_CHANCE[L1_LANES] = {0, 1, 3, 4};
#define L1_CHAOS_RANDOM_MAX 48
#define GLOBAL_SUB 6

static uint16_t rhythm16(const necklace_t *nk, int style, int n, int k, int e, int shift)
{
    uint16_t mask = track_mask(nk, style, n, k, e);
    uint32_t r = 0;
    int s;
    for (s = 0; s < 16; s++) r = (r << 1) | (uint32_t)cycle_hit(n, mask, shift, s);
    return (uint16_t)r;
}

static uint16_t row16(const necklace_t *nk, uint32_t seed, const uint16_t *c, int t)
{
    if (is_l1(c, t))
        return l1_row16(seed, t, c[CTRL_STYLE], c[CTRL(t, T_DENSITY)], c[CTRL_CHAOS], c[CTRL(t, T_SHIFT)]);
    return rhythm16(nk, c[CTRL_DENSITY_STYLE], c[CTRL(t, T_CYCLE)], c[CTRL(t, T_DENSITY)],
                    c[CTRL(t, T_EVENNESS)], c[CTRL(t, T_SHIFT)]);
}

void gen_randomize(const necklace_t *nk, uint32_t seed, uint16_t *c, const uint8_t *locked)
{
    int style = c[CTRL_DENSITY_STYLE], t, i, any_l1 = 0;
    uint16_t taken[GEN_TRACKS];
    int taken_count = 0;
    for (t = 0; t < GEN_TRACKS; t++)
        if (!locked[t] && is_l1(c, t)) any_l1 = 1;
    if (any_l1) {                          /* les tirages communs au kit, seulement si une piste MAP sera tirée */
        uint32_t g = gen_stream(seed, STREAM_TRACK, GLOBAL_SUB);
        c[CTRL_STYLE] = (uint16_t)gen_below(&g, STYLE_MAX + 1);
        c[CTRL_CHAOS] = (uint16_t)low_biased(&g, L1_CHAOS_RANDOM_MAX + 1);
    }
    for (t = 0; t < GEN_TRACKS; t++) {
        if (!locked[t]) continue;
        taken[taken_count++] = row16(nk, seed, c, t);
    }
    for (t = 0; t < GEN_TRACKS; t++) {
        uint32_t rng;
        int n = 16, k = 0, e = 0, shift = 0, attempt;
        if (locked[t]) continue;
        rng = gen_stream(seed, STREAM_TRACK, (uint32_t)t);
        if (is_l1(c, t)) {
            for (attempt = 0; attempt < MAX_ATTEMPTS; attempt++) {
                int clash = 0;
                uint16_t r;
                c[CTRL(t, T_DENSITY)] = (uint16_t)(L1_FILL_MIN[t] +
                    (int)gen_below(&rng, (uint32_t)(L1_FILL_MAX[t] - L1_FILL_MIN[t] + 1)));
                c[CTRL(t, T_SHIFT)] = (uint16_t)((int)gen_below(&rng, 16) < L1_SHIFT_CHANCE[t] ? 2 * gen_below(&rng, 16) : 0);
                r = row16(nk, seed, c, t);
                for (i = 0; i < taken_count; i++)
                    if (taken[i] == r) clash = 1;
                if (!clash) {
                    taken[taken_count++] = r;
                    break;
                }
            }
            continue;
        }
        for (attempt = 0; attempt < MAX_ATTEMPTS; attempt++) {
            int span, per16, count, clash = 0;
            uint16_t r;
            n = pick_cycle(&rng);
            span = ROLE_DENSITY_MAX[t] - ROLE_DENSITY_MIN[t] + 1;
            per16 = ROLE_DENSITY_MIN[t] + (int)gen_below(&rng, (uint32_t)span);
            k = (per16 * n + 8) >> 4;
            if (k < 1) k = 1;
            if (k > n) k = n;
            count = style == DENSITY_NESTED ? NESTED_EVEN_MAX + 1 : necklace_count(nk, n, k);
            e = low_biased(&rng, count < ROLE_EVEN_CAP[t] ? count : ROLE_EVEN_CAP[t]);
            shift = (int)gen_below(&rng, (uint32_t)n);
            if ((int)gen_below(&rng, 16) < ROLE_ANCHOR_CHANCE[t])
                shift = anchor_shift(nk, style, n, k, e, ROLE_ANCHOR[t], shift);
            r = rhythm16(nk, style, n, k, e, shift);
            for (i = 0; i < taken_count; i++)
                if (taken[i] == r) clash = 1;
            if (!clash) {
                taken[taken_count++] = r;
                break;
            }
        }
        c[CTRL(t, T_MODE)] = MODE_L2;
        c[CTRL(t, T_CYCLE)] = (uint16_t)n;
        c[CTRL(t, T_DENSITY)] = (uint16_t)k;
        c[CTRL(t, T_EVENNESS)] = (uint16_t)e;
        c[CTRL(t, T_SHIFT)] = (uint16_t)shift;
    }
}
