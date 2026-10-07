/* SPDX-License-Identifier: MIT — Copyright (c) 2026 Combust. Voir ../LICENSE. */
/* Couche 2 : les colliers binaires (rythmes à rotation près) par longueur de cycle et nombre de coups, rangés du
 * plus régulier au plus groupé, chacun gardé dans la rotation qui s'aligne sur son voisin de régularité, pour qu'un
 * cran de potard bouge le moins de pas possible (notes/50 §3.2). */
#include "gen.h"

#define MAX_K (GEN_MAX_CYCLE + 1)
#define MAX_WINDOWS (GEN_MAX_CYCLE - 1)
#define OFF(n, k) ((n) * (MAX_K + 1) + (k))

static uint16_t rotl(uint16_t m, int n)
{
    uint32_t full = (1U << n) - 1;
    return (uint16_t)((((uint32_t)m << 1) | ((uint32_t)m >> (n - 1))) & full);
}


/* Nombre de bits à 1 sur 16 bits, sans boucle. */
static int popcount(uint32_t m)
{
    m = m - ((m >> 1) & 0x5555U);
    m = (m & 0x3333U) + ((m >> 2) & 0x3333U);
    m = (m + (m >> 4)) & 0x0f0fU;
    return (int)((m + (m >> 8)) & 0x1fU);
}

static void evenness_key(uint16_t m, int n, uint16_t *keys)
{
    uint8_t gaps[GEN_MAX_CYCLE], win[GEN_MAX_CYCLE];
    int k = 0, first = -1, prev = -1, i, w, j;
    for (i = 0; i < MAX_WINDOWS; i++) keys[i] = 0;
    for (i = 0; i < n; i++) {
        if (m & (1U << (n - 1 - i))) {
            if (first < 0) first = i;
            else gaps[k - 1] = (uint8_t)(i - prev);
            prev = i;
            k++;
        }
    }
    if (k > 0) gaps[k - 1] = (uint8_t)(n - prev + first);
    /* fenêtre i de w écarts = fenêtre i de w-1 écarts + écart (i + w - 1) mod k : chaque fenêtre grandit d'un écart */
    for (i = 0; i < k; i++) win[i] = 0;
    for (w = 1; w < k; w++) {
        uint32_t s = 0;
        j = w - 1;                 /* (i + w - 1) mod k, pour i = 0 */
        for (i = 0; i < k; i++) {
            win[i] = (uint8_t)(win[i] + gaps[j]);
            s += (uint32_t)win[i] * win[i];
            if (++j == k) j = 0;
        }
        keys[w - 1] = (uint16_t)s;
    }
}

static int more_even(const uint16_t *keys, int a, int b, uint16_t ma, uint16_t mb)
{
    int w;
    for (w = 0; w < MAX_WINDOWS; w++) {
        uint16_t ka = keys[a * MAX_WINDOWS + w], kb = keys[b * MAX_WINDOWS + w];
        if (ka != kb) return ka < kb;
    }
    return ma > mb;
}

static void sort_group(uint16_t *masks, int start, int end, int n, uint16_t *scratch)
{
    int count = end - start, i, j, w;
    uint16_t *keys = scratch;
    uint16_t *order = scratch + NECKLACE_MAX_GROUP * MAX_WINDOWS;
    uint16_t *sorted = order + NECKLACE_MAX_GROUP;
    if (count < 2) return;
    for (i = 0; i < count; i++) {
        order[i] = (uint16_t)i;
        evenness_key(masks[start + i], n, keys + i * MAX_WINDOWS);
    }
    /* Tri fusion ascendant de order[] (sorted[] sert de tampon). La comparaison est un ordre total strict (les
     * égalités se départagent sur le masque, unique) : le résultat est celui du tri par insertion de référence. */
    for (w = 1; w < count; w <<= 1) {
        for (i = 0; i < count; i += 2 * w) {
            int a = i, mid = i + w < count ? i + w : count, end = i + 2 * w < count ? i + 2 * w : count;
            int b = mid, o = i;
            while (a < mid && b < end) {
                if (more_even(keys, order[b], order[a], masks[start + order[b]], masks[start + order[a]]))
                    sorted[o++] = order[b++];
                else
                    sorted[o++] = order[a++];
            }
            while (a < mid) sorted[o++] = order[a++];
            while (b < end) sorted[o++] = order[b++];
        }
        for (j = 0; j < count; j++) order[j] = sorted[j];
    }
    for (i = 0; i < count; i++) sorted[i] = masks[start + order[i]];
    for (i = 0; i < count; i++) masks[start + i] = sorted[i];
}

static uint16_t align_to(uint16_t m, int n, uint16_t anchor)
{
    uint16_t best = m, r = m;
    int best_ov = popcount(m & anchor), i;
    for (i = 1; i < n; i++) {
        int ov;
        r = rotl(r, n);
        ov = popcount(r & anchor);
        if (ov > best_ov || (ov == best_ov && r > best)) {
            best = r;
            best_ov = ov;
        }
    }
    return best;
}

static void align_length(necklace_t *nk, int n)
{
    uint16_t anchor = 0;
    int k, i;
    for (k = 0; k <= n; k++) {
        int start = nk->offsets[OFF(n, k)], end = nk->offsets[OFF(n, k + 1)];
        anchor = align_to(nk->masks[start], n, anchor);
        nk->masks[start] = anchor;
        for (i = start + 1; i < end; i++) nk->masks[i] = align_to(nk->masks[i], n, nk->masks[i - 1]);
    }
}

/* m est-il la plus grande rotation de son collier ? Sort à la première rotation plus grande (le cas courant). */
static int is_canonical(uint16_t m, int n)
{
    uint16_t r = m;
    int i;
    for (i = 1; i < n; i++) {
        r = rotl(r, n);
        if (r > m) return 0;
    }
    return 1;
}

/* Même résultat que la référence : chaque groupe (n, k) reçoit ses masques canoniques en ordre croissant avant le
 * tri. Deux passes sur les masques par longueur (compter, puis remplir) au lieu d'une par nombre de coups. */
void necklace_init(necklace_t *nk, uint16_t *masks, uint16_t *scratch)
{
    uint16_t fill[MAX_K];
    int at = 0, n, k;
    uint32_t m;
    nk->masks = masks;
    for (n = 0; n < NECKLACE_OFFSETS; n++) nk->offsets[n] = 0;
    for (n = 1; n <= GEN_MAX_CYCLE; n++) {
        /* Une plus grande rotation commence par un coup : seuls 0 et les masques au bit de poids fort à 1 peuvent
         * en être une. La passe 1 les marque dans un bitmap (dans la zone de tri, pas encore utilisée) ; la passe 2
         * remplit d'après lui. */
        uint16_t *seen = scratch;
        uint32_t lo = n > 1 ? 1U << (n - 1) : 1U;
        for (k = 0; k <= n; k++) fill[k] = 0;
        for (m = 0; m < (1U << n) >> 4; m++) seen[m] = 0;
        seen[0] = 1;
        fill[0] = 1;
        for (m = lo; m < (1U << n); m++)
            if (is_canonical((uint16_t)m, n)) {
                seen[m >> 4] |= (uint16_t)(1U << (m & 15));
                fill[popcount(m)]++;
            }
        for (k = 0; k <= n; k++) {
            uint16_t count = fill[k];
            nk->offsets[OFF(n, k)] = (uint16_t)at;
            fill[k] = (uint16_t)at;
            at += count;
        }
        nk->offsets[OFF(n, n + 1)] = (uint16_t)at;
        masks[fill[0]++] = 0;
        for (m = lo; m < (1U << n); m++)
            if (seen[m >> 4] & (1U << (m & 15))) masks[fill[popcount(m)]++] = (uint16_t)m;
        for (k = 0; k <= n; k++) sort_group(masks, nk->offsets[OFF(n, k)], nk->offsets[OFF(n, k + 1)], n, scratch);
        align_length(nk, n);
    }
}

uint16_t necklace_count(const necklace_t *nk, int n, int k)
{
    return (uint16_t)(nk->offsets[OFF(n, k + 1)] - nk->offsets[OFF(n, k)]);
}

uint16_t necklace_mask(const necklace_t *nk, int n, int k, int evenness)
{
    int count = necklace_count(nk, n, k);
    int e = evenness < count ? evenness : count - 1;
    return nk->masks[nk->offsets[OFF(n, k)] + e];
}

int cycle_hit(int n, uint16_t mask, int shift, int step)
{
    int pos = (step % n + n - shift % n) % n;
    return (mask >> (n - 1 - pos)) & 1;
}
