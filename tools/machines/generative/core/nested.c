/* SPDX-License-Identifier: MIT — Copyright (c) 2026 Combust. Voir ../LICENSE. */
/* Couche 2, densité « imbriquée » (façon Grids) : la densité fait jouer les k pas les plus prioritaires, un coup de
 * plus ou de moins par cran ; la régularité passe d'un remplissage hiérarchique (0) à un groupe (15). */
#include "gen.h"

static void hierarchical_rank(int n, uint8_t *rank)
{
    uint8_t taken[GEN_MAX_CYCLE];
    int r, s;
    for (s = 0; s < GEN_MAX_CYCLE; s++) taken[s] = 0;
    taken[0] = 1;
    rank[0] = 0;
    for (r = 1; r < n; r++) {
        int best_start = 0, best_len = 0, pick;
        for (s = 0; s < n; s++) {
            int len = 1;
            if (!taken[s]) continue;
            while (!taken[(s + len) % n]) len++;
            if (len > best_len) {
                best_len = len;
                best_start = s;
            }
        }
        pick = (best_start + (best_len >> 1)) % n;
        taken[pick] = 1;
        rank[pick] = (uint8_t)r;
    }
}

uint16_t nested_mask(int n, int k, int evenness)
{
    uint8_t rank[GEN_MAX_CYCLE];
    uint16_t score[GEN_MAX_CYCLE];
    int ev = evenness > NESTED_EVEN_MAX ? NESTED_EVEN_MAX : evenness;
    uint32_t mask = 0;
    int s, h;
    hierarchical_rank(n, rank);
    for (s = 0; s < n; s++) score[s] = (uint16_t)((NESTED_EVEN_MAX - ev) * rank[s] + ev * s);
    for (h = 0; h < k && h < n; h++) {
        int best = -1;
        for (s = 0; s < n; s++) {
            if (mask & (1U << (n - 1 - s))) continue;
            if (best < 0 || score[s] < score[best]) best = s;
        }
        mask |= 1U << (n - 1 - best);
    }
    return (uint16_t)mask;
}
