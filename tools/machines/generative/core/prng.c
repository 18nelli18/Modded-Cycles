/* SPDX-License-Identifier: MIT — Copyright (c) 2026 Combust. Voir ../LICENSE. */
/* Générateur pseudo-aléatoire à flux nommés : hachage lowbias32 et xorshift32 (13, 17, 5). */
#include "gen.h"

uint32_t gen_hash32(uint32_t x)
{
    x ^= x >> 16;
    x *= 0x7feb352dU;
    x ^= x >> 15;
    x *= 0x846ca68bU;
    x ^= x >> 16;
    return x;
}

uint32_t gen_stream(uint32_t seed, uint32_t stream_id, uint32_t sub)
{
    uint32_t s = gen_hash32(seed ^ gen_hash32(stream_id * 0x9e3779b9U + sub));
    return s ? s : 0x6d2b79f5U;
}

uint32_t gen_next(uint32_t *state)
{
    uint32_t x = *state;
    x ^= x << 13;
    x ^= x >> 17;
    x ^= x << 5;
    *state = x;
    return x;
}

/* Uniforme dans [0, n) pour 1 <= n <= 65 536. */
uint32_t gen_below(uint32_t *state, uint32_t n)
{
    return ((gen_next(state) >> 16) * n) >> 16;
}
