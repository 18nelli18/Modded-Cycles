/* SPDX-License-Identifier: MIT — Copyright (c) 2026 Combust. Voir ../LICENSE. */
/* Le cœur compilé pour l'hôte, pour les preuves (tools/emu/test_generative.py) : vecteurs dorés et résultats
 * attendus des écritures en émulation. Lit des commandes sur l'entrée standard, une par ligne :
 *   tables                                  -> FNV-1a des masques puis des offsets (mots de 16 bits, petit-boutiste)
 *   defaults                                -> gen_default_controls
 *   gen  <graine> <c0..c47> <v0..v5>        -> par piste : écrite longueur trigs vélocités-hex notes-hex accords-hex
 *   rand <graine> <c0..c47> <v0..v5>        -> les 48 réglages après gen_randomize
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../core/gen.h"

static uint16_t masks[NECKLACE_ENTRIES];
static uint16_t scratch[NECKLACE_SCRATCH_WORDS];

static uint32_t fnv(uint32_t h, uint16_t w)
{
    h = (h ^ (w & 0xff)) * 0x01000193U;
    h = (h ^ (w >> 8)) * 0x01000193U;
    return h;
}

int main(void)
{
    necklace_t nk;
    char cmd[16];
    necklace_init(&nk, masks, scratch);
    while (scanf("%15s", cmd) == 1) {
        uint16_t c[GEN_CONTROLS];
        uint8_t locked[GEN_TRACKS];
        unsigned v;
        int i, t, s;
        if (!strcmp(cmd, "tables")) {
            uint32_t h = 0x811c9dc5U;
            for (i = 0; i < NECKLACE_ENTRIES; i++) h = fnv(h, masks[i]);
            for (i = 0; i < NECKLACE_OFFSETS; i++) h = fnv(h, nk.offsets[i]);
            printf("%u\n", h);
        } else if (!strcmp(cmd, "defaults")) {
            gen_default_controls(c);
            for (i = 0; i < GEN_CONTROLS; i++) printf("%u%c", c[i], i + 1 < GEN_CONTROLS ? ' ' : '\n');
        } else if (!strcmp(cmd, "gen") || !strcmp(cmd, "rand")) {
            uint32_t seed;
            if (scanf("%u", &v) != 1) return 1;
            seed = v;
            for (i = 0; i < GEN_CONTROLS; i++) {
                if (scanf("%u", &v) != 1) return 1;
                c[i] = (uint16_t)v;
            }
            for (i = 0; i < GEN_TRACKS; i++) {
                if (scanf("%u", &v) != 1) return 1;
                locked[i] = (uint8_t)v;
            }
            if (!strcmp(cmd, "gen")) {
                gen_out_t out;
                gen_generate(&nk, seed, c, locked, &out);
                for (t = 0; t < GEN_TRACKS; t++) {
                    printf("%d %d ", out.written[t], out.written[t] ? out.length[t] : 0);
                    for (s = 0; s < GEN_STEPS; s++) putchar(out.written[t] && out.trig[t][s] ? '1' : '0');
                    putchar(' ');
                    for (s = 0; s < GEN_STEPS; s++) printf("%02x", out.written[t] ? (uint8_t)out.velocity[t][s] : 0xff);
                    putchar(' ');
                    for (s = 0; s < GEN_STEPS; s++) printf("%02x", out.written[t] ? (uint8_t)out.note[t][s] : 0xff);
                    putchar(' ');
                    for (s = 0; s < GEN_STEPS; s++) printf("%02x", out.written[t] ? (uint8_t)out.chord[t][s] : 0xff);
                    putchar(t + 1 < GEN_TRACKS ? ' ' : '\n');
                }
            } else {
                gen_randomize(&nk, seed, c, locked);
                for (i = 0; i < GEN_CONTROLS; i++) printf("%u%c", c[i], i + 1 < GEN_CONTROLS ? ' ' : '\n');
            }
        } else {
            return 2;
        }
        fflush(stdout);
    }
    return 0;
}
