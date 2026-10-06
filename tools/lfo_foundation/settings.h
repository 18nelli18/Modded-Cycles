/* SPDX-License-Identifier: MIT */
/* Périmètre explicite : LICENSE dans ce répertoire. */
#ifndef LF4S_SETTINGS_H
#define LF4S_SETTINGS_H

#include <stddef.h>
#include <stdint.h>

/* Réglages des trois LFO supplémentaires ; aucun état de phase ni pointeur.
 * Adapté du code original de lachlanfysh, voir notes/41 pour l'origine.
 * L'appelant fournit les valeurs par défaut et les identités logiques.
 * Il sérialise tous les accès : aucune fonction n'est destinée à l'IRQ audio.
 * Les tampons empruntés restent stables et disjoints pendant chaque appel. */
#define LF4S_PAYLOAD_BYTES 48u
#define LF4S_HEADER_BYTES 24u
#define LF4S_ROW_BYTES 52u

typedef enum {
    LF4S_OK = 0,
    LF4S_INVALID = 1,
    LF4S_CAPACITY = 2,
    LF4S_MEMORY = 3,
    LF4S_FORMAT = 4,
    LF4S_BINDING = 5
} lf4s_status;

typedef void *(*lf4s_allocate)(void *user, size_t bytes);
typedef void (*lf4s_release)(void *user, void *memory);

typedef struct {
    uint32_t key_count;     /* 1..65 535 ; bornes logiques, sans adresse RAM. */
    uint32_t capacity;      /* Nombre maximal de lignes non standard. */
    uint16_t max_word;      /* Borne commune des 24 mots big-endian. */
    uint8_t defaults[LF4S_PAYLOAD_BYTES];
    /* Paire facultative ; NULL/NULL utilise malloc/free. */
    lf4s_allocate allocate;
    lf4s_release release;
    void *allocator_user;
} lf4s_options;

typedef struct lf4s_store lf4s_store;
typedef struct {
    uint32_t key;
    uint8_t data[LF4S_PAYLOAD_BYTES];
} lf4s_edit;

/* En cas de refus, store et les sorties restent inchangés. */
lf4s_status lf4s_create(const lf4s_options *options, lf4s_store **out);
void lf4s_destroy(lf4s_store *store);
uint32_t lf4s_count(const lf4s_store *store);
lf4s_status lf4s_get(const lf4s_store *store, uint32_t key,
                     uint8_t out[LF4S_PAYLOAD_BYTES]);
lf4s_status lf4s_set(lf4s_store *store, uint32_t key,
                     const uint8_t data[LF4S_PAYLOAD_BYTES]);
/* Lot atomique, clés uniques ; suppression des défauts avant insertion.
 * Conçu pour de petits lots d'édition, pas pour charger tout un projet. */
lf4s_status lf4s_apply(lf4s_store *store, const lf4s_edit *edits, size_t count);
/* Copie atomique, chevauchement compris ; même schéma (défauts et borne).
 * La source reste inchangée. Les plages appartiennent aux espaces logiques. */
lf4s_status lf4s_copy(const lf4s_store *source, lf4s_store *destination,
                      uint32_t first, uint32_t target, uint32_t count);
/* Migration explicite d'un conteneur sans extension : rétablit les défauts. */
lf4s_status lf4s_reset(lf4s_store *store);

/* LF4S v1 : 24 octets d'en-tête, lignes triées de 52 octets, CRC32 final.
 * Le conteneur de base est opaque, sa longueur et son CRC32 lient la section.
 * Ce CRC n'est pas une authentification. Les défauts ne sont pas sérialisés :
 * l'application doit conserver le même schéma entre écriture et lecture.
 * Le format refuse les lignes par défaut, doublons et octets réservés non nuls.
 * Les sorties et l'état restent inchangés en cas de refus.
 * Taille base <= UINT32_MAX ; NULL est accepté seulement pour une base vide. */
size_t lf4s_encoded_size(const lf4s_store *store);
lf4s_status lf4s_save(const lf4s_store *store, const uint8_t *base,
                      size_t base_size, uint8_t *out, size_t capacity,
                      size_t *written);
lf4s_status lf4s_load(lf4s_store *store, const uint8_t *base, size_t base_size,
                      const uint8_t *section, size_t section_size);

#endif
