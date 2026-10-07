/* SPDX-License-Identifier: MIT — Copyright (c) 2026 Combust. Voir ../LICENSE. */
/* Couche 1 : batterie façon Grids d'après le plan de styles (stylemap.h). Style fondu entre voisins, remplissage,
 * chaos (tiré à chaque pas, quel qu'il soit), et vélocité tirée de la force du pas (accents, notes fantômes). */
#include "gen.h"
#define STYLEMAP_WANT_DATA
#include "stylemap.h"

static int clampi(int v, int lo, int hi)
{
    return v < lo ? lo : v > hi ? hi : v;
}

int l1_strength(int style, int lane, int map_step)
{
    int st = clampi(style, 0, STYLE_MAX), i = st >> 4, f = st & 15;
    int a = STYLE_STRENGTHS[(i * MAP_LANES + lane) * MAP_STEPS + map_step];
    int b = i + 1 < STYLE_COUNT ? STYLE_STRENGTHS[((i + 1) * MAP_LANES + lane) * MAP_STEPS + map_step] : a;
    return (a * (16 - f) + b * f) >> 4;
}

int l1_velocity(int strength)
{
    return clampi(24 + ((strength * 100) >> 8), 1, 127);
}

/* La force perturbée de chaque pas, dans l'ordre ; le chaos est tiré à chaque pas, quelle que soit sa valeur. */
static int step_strength(uint32_t *rng, int style, int lane, int chaos, int shift, int s)
{
    int r = (int)gen_below(rng, 256);
    int map_step = (s % MAP_STEPS + MAP_STEPS - shift) % MAP_STEPS;
    return clampi(l1_strength(style, lane, map_step) + (((r - 128) * chaos) >> 6), 0, 255);
}

void l1_render(uint32_t seed, int lane, int style, int fill, int chaos, int shift, uint8_t *trig, int8_t *velocity)
{
    int thr = 255 - 2 * clampi(fill, 0, FILL_MAX), ch = clampi(chaos, 0, CHAOS_MAX), sh = shift % MAP_STEPS, s;
    uint32_t rng = gen_stream(seed, STREAM_MAP_CHAOS, (uint32_t)lane);
    for (s = 0; s < GEN_STEPS; s++) {
        int v = step_strength(&rng, style, lane, ch, sh, s);
        trig[s] = (uint8_t)(v > thr);
        velocity[s] = (int8_t)(v > thr ? l1_velocity(v) : -1);
    }
}

uint16_t l1_row16(uint32_t seed, int lane, int style, int fill, int chaos, int shift)
{
    int thr = 255 - 2 * clampi(fill, 0, FILL_MAX), ch = clampi(chaos, 0, CHAOS_MAX), sh = shift % MAP_STEPS, s;
    uint32_t rng = gen_stream(seed, STREAM_MAP_CHAOS, (uint32_t)lane), row = 0;
    for (s = 0; s < 16; s++)
        row = (row << 1) | (uint32_t)(step_strength(&rng, style, lane, ch, sh, s) > thr);
    return (uint16_t)row;
}
