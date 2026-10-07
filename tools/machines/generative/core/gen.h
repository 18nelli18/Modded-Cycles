/* SPDX-License-Identifier: MIT — Copyright (c) 2026 Combust. Voir ../LICENSE. */
/* Cœur du générateur de motifs (notes/50). Portage C d'un cœur de référence en JavaScript (tenu à part par
 * l'auteur) : mêmes résultats octet pour octet, ce que vérifient les vecteurs dorés de ../vectors/
 * (tools/emu/test_generative.py). Autonome : ni libc, ni flottants, ni arithmétique 64 bits (le firmware est lié
 * sans libgcc). */
#ifndef GEN_H
#define GEN_H

#include <stdint.h>

#define GEN_TRACKS 6
#define GEN_STEPS 64
#define GEN_CONTROLS 48
#define GEN_MAX_CYCLE 16

/* Disposition des réglages (tableau de 16 bits) : notes/50 §3. Ne jamais renuméroter. */
#define CTRL_DEMO_DENSITY 0
#define CTRL_DENSITY_STYLE 1
#define CTRL_TRACK_BASE 2
#define CTRL_TRACK_STRIDE 5
#define T_MODE 0
#define T_CYCLE 1
#define T_DENSITY 2
#define T_EVENNESS 3
#define T_SHIFT 4
#define CTRL(t, f) (CTRL_TRACK_BASE + (t) * CTRL_TRACK_STRIDE + (f))
#define CTRL_STYLE 32
#define CTRL_CHAOS 33
#define CTRL_ROOT 34
#define CTRL_SCALE 35
#define CTRL_TONE 36      /* + 0 étendue, 1 centre, 2 pas, 3 déjà-vu */
#define CTRL_CHORD 40     /* + 0 aventure, 1 complexité, 2 déjà-vu, 3 octave */

#define MODE_DEMO 0
#define MODE_L2 1
#define MODE_L1 2
#define L1_LANES 4
#define FILL_MAX 127
#define CHAOS_MAX 127
#define DENSITY_EUCLIDEAN 0
#define DENSITY_NESTED 1
#define NESTED_EVEN_MAX 15

/* Flux du générateur pseudo-aléatoire : un flux par usage, pour qu'un tirage ajouté n'en décale aucun autre. */
#define STREAM_DEMO 1
#define STREAM_MAP_CHAOS 2
#define STREAM_TRACK 3
#define STREAM_NOTES 4

/* Tables de colliers : 8 923 masques pour les cycles de 1 à 16 pas. */
#define NECKLACE_ENTRIES 8923
#define NECKLACE_OFFSETS ((GEN_MAX_CYCLE + 1) * (GEN_MAX_CYCLE + 2))
/* Le plus grand groupe (n, k) est n = 16, k = 8 : 810 colliers. Zone de travail pour trier un groupe. */
#define NECKLACE_MAX_GROUP 810
#define NECKLACE_SCRATCH_WORDS (NECKLACE_MAX_GROUP * (GEN_MAX_CYCLE - 1) + 2 * NECKLACE_MAX_GROUP)

typedef struct {
    uint16_t *masks;    /* NECKLACE_ENTRIES mots */
    uint16_t offsets[NECKLACE_OFFSETS];
} necklace_t;

/* Résultat d'une génération : seulement ce que le firmware écrit dans un pattern. */
typedef struct {
    uint8_t written[GEN_TRACKS]; /* 1 si le générateur a produit cette piste */
    uint8_t length[GEN_TRACKS];  /* longueur propre de la piste = le cycle */
    uint8_t trig[GEN_TRACKS][GEN_STEPS];
    int8_t velocity[GEN_TRACKS][GEN_STEPS];  /* couche 1 : vélocité de ses trigs ; -1 = ne pas toucher */
    int8_t note[GEN_TRACKS][GEN_STEPS];      /* couche 3 : note des trigs de Tone et Chord ; -1 = aucune */
    int8_t chord[GEN_TRACKS][GEN_STEPS];     /* couche 3 : qualité d'accord (CHORD_*) des trigs de Chord ; -1 = aucune */
} gen_out_t;

/* Couche 3 */
#define L3_SCALES 7
#define TONE_TRACK 4
#define CHORD_TRACK 5
#define TONE_BASE 60
#define CHORD_BASE 48
#define TONE_LOOP 8
#define CHORD_LOOP 4
#define CHORD_MAJ 0
#define CHORD_MIN 1
#define CHORD_DIM 2
#define CHORD_MAJ7 3
#define CHORD_DOM7 4
#define CHORD_MIN7 5
#define CHORD_HDIM7 6

/* prng.c */
uint32_t gen_hash32(uint32_t x);
uint32_t gen_stream(uint32_t seed, uint32_t stream_id, uint32_t sub);
uint32_t gen_next(uint32_t *state);
uint32_t gen_below(uint32_t *state, uint32_t n);

/* necklace.c : scratch doit contenir NECKLACE_SCRATCH_WORDS mots. */
void necklace_init(necklace_t *nk, uint16_t *masks, uint16_t *scratch);
uint16_t necklace_count(const necklace_t *nk, int n, int k);
uint16_t necklace_mask(const necklace_t *nk, int n, int k, int evenness);
int cycle_hit(int n, uint16_t mask, int shift, int step);

/* layer1.c */
int l1_strength(int style, int lane, int map_step);
int l1_velocity(int strength);
void l1_render(uint32_t seed, int lane, int style, int fill, int chaos, int shift, uint8_t *trig, int8_t *velocity);
uint16_t l1_row16(uint32_t seed, int lane, int style, int fill, int chaos, int shift);

/* layer3.c : k = les quatre réglages de notes de la piste (controls + CTRL_TONE ou CTRL_CHORD) */
int l3_semitones(int scale, int deg);
int l3_chord_quality(int scale, int deg, int seventh);
void l3_tone(uint32_t seed, int root, int scale, const uint16_t *k, const uint8_t *trig, int8_t *note);
void l3_chord(uint32_t seed, int root, int scale, const uint16_t *k, const uint8_t *trig, int8_t *note, int8_t *quality);

/* nested.c */
uint16_t nested_mask(int n, int k, int evenness);

/* generate.c */
void gen_generate(const necklace_t *nk, uint32_t seed, const uint16_t *controls, const uint8_t *locked, gen_out_t *out);
void gen_randomize(const necklace_t *nk, uint32_t seed, uint16_t *controls, const uint8_t *locked);
void gen_default_controls(uint16_t *controls);

#endif
