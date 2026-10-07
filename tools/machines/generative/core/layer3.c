/* SPDX-License-Identifier: MIT — Copyright (c) 2026 Combust. Voir ../LICENSE. */
/* Couche 3 : notes façon Marbles pour Tone (mélodie) et Chord (fondamentales et qualités d'accord diatoniques),
 * ramenées à une tonique et une gamme. */
#include "gen.h"

static const uint8_t SCALE_STEPS[L3_SCALES][7] = {
    {0, 2, 4, 5, 7, 9, 11}, {0, 2, 3, 5, 7, 8, 10}, {0, 2, 3, 5, 7, 9, 10}, {0, 2, 4, 5, 7, 9, 10},
    {0, 2, 3, 5, 7, 8, 11}, {0, 2, 4, 7, 9, 0, 0}, {0, 3, 5, 7, 10, 0, 0},
};
static const uint8_t SCALE_LEN[L3_SCALES] = {7, 7, 7, 7, 7, 5, 5};
static const uint8_t ROOT_WEIGHTS[7] = {6, 3, 2, 5, 5, 4, 1};
static const uint8_t PENT_WEIGHTS[5] = {5, 1, 3, 4, 2};

static int clampi(int v, int lo, int hi)
{
    return v < lo ? lo : v > hi ? hi : v;
}

static int chance(int r, int v)
{
    return r < v + (v >> 6);
}

static int fold_octaves(int n)
{
    while (n < 0) n += 12;
    while (n > 127) n -= 12;
    return n;
}

int l3_semitones(int scale, int deg)
{
    int sc = clampi(scale, 0, L3_SCALES - 1), n = SCALE_LEN[sc], oct = 0, d = deg;
    while (d < 0) { d += n; oct -= 1; }
    while (d >= n) { d -= n; oct += 1; }
    return oct * 12 + SCALE_STEPS[sc][d];
}

int l3_chord_quality(int scale, int deg, int seventh)
{
    int r = l3_semitones(scale, deg);
    int third = l3_semitones(scale, deg + 2) - r, fifth = l3_semitones(scale, deg + 4) - r;
    int sev = l3_semitones(scale, deg + 6) - r;
    int minor = third == 3, flat5 = fifth == 6;
    if (!seventh) return flat5 ? CHORD_DIM : minor ? CHORD_MIN : CHORD_MAJ;
    if (flat5) return CHORD_HDIM7;
    if (minor) return CHORD_MIN7;
    return sev == 11 ? CHORD_MAJ7 : CHORD_DOM7;
}

void l3_tone(uint32_t seed, int root, int scale, const uint16_t *k, const uint8_t *trig, int8_t *note)
{
    int width = 1 + ((clampi(k[0], 0, 127) * 15) >> 7);
    int centre = ((clampi(k[1], 0, 127) - 64) * 7) >> 5;
    int stepwise = clampi(k[2], 0, 127), dejavu = clampi(k[3], 0, 127), n = 0, prev = centre, s;
    int8_t history[TONE_LOOP];
    uint32_t rng = gen_stream(seed, STREAM_NOTES, TONE_TRACK);
    for (s = 0; s < GEN_STEPS; s++) {
        int a, b, move, dir, repeat, deg;
        note[s] = -1;
        if (!trig[s]) continue;
        a = (int)gen_below(&rng, (uint32_t)width + 1);
        b = (int)gen_below(&rng, (uint32_t)width + 1);
        move = (int)gen_below(&rng, 128);
        dir = (int)gen_below(&rng, 5);
        repeat = (int)gen_below(&rng, 128);
        deg = centre + a + b - width;
        if (chance(move, stepwise)) deg = clampi(prev + dir - 2, centre - width, centre + width);
        if (n >= TONE_LOOP && chance(repeat, dejavu)) deg = history[n % TONE_LOOP];
        history[n % TONE_LOOP] = (int8_t)deg;
        prev = deg;
        n++;
        note[s] = (int8_t)fold_octaves(TONE_BASE + root + l3_semitones(scale, deg));
    }
}

void l3_chord(uint32_t seed, int root, int scale, const uint16_t *k, const uint8_t *trig, int8_t *note, int8_t *quality)
{
    int adv = clampi(k[0], 0, 127), cpx = clampi(k[1], 0, 127), dejavu = clampi(k[2], 0, 127);
    int oct = clampi(k[3], 0, 4) - 2, sc = clampi(scale, 0, L3_SCALES - 1), seven = SCALE_LEN[sc] == 7;
    const uint8_t *weights = seven ? ROOT_WEIGHTS : PENT_WEIGHTS;
    int count = seven ? 7 : 5, total = seven ? 26 : 15, n = 0, s;
    int8_t h_deg[CHORD_LOOP], h_q[CHORD_LOOP];
    uint32_t rng = gen_stream(seed, STREAM_NOTES, CHORD_TRACK);
    for (s = 0; s < GEN_STEPS; s++) {
        int any, any_deg, w, seventh, repeat, deg = 0, q;
        note[s] = -1;
        quality[s] = -1;
        if (!trig[s]) continue;
        any = chance((int)gen_below(&rng, 128), adv);
        any_deg = (int)gen_below(&rng, (uint32_t)count);
        w = (int)gen_below(&rng, (uint32_t)total);
        seventh = chance((int)gen_below(&rng, 128), cpx);
        repeat = chance((int)gen_below(&rng, 128), dejavu);
        while (w >= weights[deg]) { w -= weights[deg]; deg++; }
        if (any) deg = any_deg;
        q = l3_chord_quality(scale, deg, seventh);
        if (n >= CHORD_LOOP && repeat) {
            deg = h_deg[n % CHORD_LOOP];
            q = h_q[n % CHORD_LOOP];
        }
        h_deg[n % CHORD_LOOP] = (int8_t)deg;
        h_q[n % CHORD_LOOP] = (int8_t)q;
        n++;
        note[s] = (int8_t)fold_octaves(CHORD_BASE + 12 * oct + root + l3_semitones(scale, deg));
        quality[s] = (int8_t)q;
    }
}
