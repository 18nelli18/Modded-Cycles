/* SPDX-License-Identifier: MIT */
/* Périmètre explicite : LICENSE dans ce répertoire. */
#include "settings.h"

#include <stdlib.h>
#include <string.h>

/* Extraction portable du stockage clairsemé, validation puis publication.
 * Aucun adaptateur RAM, octet de firmware ou valeur par défaut embarquée. */
typedef struct {
    uint16_t key;
    uint8_t data[LF4S_PAYLOAD_BYTES];
} entry;

struct lf4s_store {
    lf4s_options options;
    uint32_t count;
    entry *rows;
};

static uint32_t read16(const uint8_t *p) {
    return ((uint32_t)p[0] << 8) | p[1];
}

static uint32_t read32(const uint8_t *p) {
    return (read16(p) << 16) | read16(p + 2);
}

static void write16(uint8_t *p, uint32_t value) {
    p[0] = (uint8_t)(value >> 8);
    p[1] = (uint8_t)value;
}

static void write32(uint8_t *p, uint32_t value) {
    write16(p, value >> 16);
    write16(p + 2, value);
}

static uint32_t crc32(const uint8_t *p, size_t count) {
    uint32_t crc = UINT32_MAX;
    for (size_t i = 0; i < count; ++i) {
        crc ^= p[i];
        for (unsigned bit = 0; bit < 8; ++bit)
            crc = (crc >> 1) ^ (0xedb88320u & (0u - (crc & 1u)));
    }
    return ~crc;
}

static void *heap_allocate(void *user, size_t bytes) {
    (void)user;
    return malloc(bytes);
}

static void heap_release(void *user, void *memory) {
    (void)user;
    free(memory);
}

static int valid(const lf4s_options *options, const uint8_t *data) {
    for (size_t i = 0; i < LF4S_PAYLOAD_BYTES; i += 2)
        if (read16(data + i) > options->max_word)
            return 0;
    return 1;
}

static int defaults(const lf4s_store *store, const uint8_t *data) {
    return memcmp(data, store->options.defaults, LF4S_PAYLOAD_BYTES) == 0;
}

/* Recherche dans la table triée ; le résultat peut être la fin. */
static uint32_t position(const entry *rows, uint32_t count, uint32_t key) {
    uint32_t low = 0, high = count;
    while (low < high) {
        uint32_t mid = low + (high - low) / 2;
        if (rows[mid].key < key)
            low = mid + 1;
        else
            high = mid;
    }
    return low;
}

static lf4s_status put(const lf4s_store *store, entry *rows, uint32_t *count,
                        uint32_t key, const uint8_t *data) {
    uint32_t at = position(rows, *count, key);
    int found = at < *count && rows[at].key == key;
    if (defaults(store, data)) {
        if (found) {
            --*count;
            memmove(rows + at, rows + at + 1, (*count - at) * sizeof(entry));
        }
        return LF4S_OK;
    }
    if (!found) {
        if (*count == store->options.capacity)
            return LF4S_CAPACITY;
        memmove(rows + at + 1, rows + at, (*count - at) * sizeof(entry));
        ++*count;
    }
    rows[at].key = (uint16_t)key;
    memcpy(rows[at].data, data, LF4S_PAYLOAD_BYTES);
    return LF4S_OK;
}

static lf4s_status stage(const lf4s_store *store, entry **out) {
    *out = NULL;
    if (store->options.capacity == 0)
        return LF4S_OK;
    *out = store->options.allocate(store->options.allocator_user,
                                   store->options.capacity * sizeof(entry));
    if (!*out)
        return LF4S_MEMORY;
    if (store->count)
        memcpy(*out, store->rows, store->count * sizeof(entry));
    return LF4S_OK;
}

static void release_rows(const lf4s_store *store, entry *rows) {
    if (rows)
        store->options.release(store->options.allocator_user, rows);
}

static void commit(lf4s_store *store, const entry *rows, uint32_t count) {
    if (count)
        memcpy(store->rows, rows, count * sizeof(entry));
    store->count = count;
}

lf4s_status lf4s_create(const lf4s_options *options, lf4s_store **out) {
    if (!options || !out || !options->key_count || options->key_count > UINT16_MAX
            || options->capacity > options->key_count
            || (!!options->allocate != !!options->release)
            || !valid(options, options->defaults))
        return LF4S_INVALID;
    lf4s_options config = *options;
    if (!config.allocate) {
        config.allocate = heap_allocate;
        config.release = heap_release;
    }
    lf4s_store *store = config.allocate(config.allocator_user, sizeof(*store));
    if (!store)
        return LF4S_MEMORY;
    store->options = config;
    store->count = 0;
    store->rows = NULL;
    lf4s_status status = stage(store, &store->rows);
    if (status != LF4S_OK) {
        config.release(config.allocator_user, store);
        return status;
    }
    *out = store;
    return LF4S_OK;
}

void lf4s_destroy(lf4s_store *store) {
    if (store) {
        release_rows(store, store->rows);
        store->options.release(store->options.allocator_user, store);
    }
}

uint32_t lf4s_count(const lf4s_store *store) {
    return store ? store->count : 0;
}

lf4s_status lf4s_get(const lf4s_store *store, uint32_t key, uint8_t *out) {
    if (!store || !out || key >= store->options.key_count)
        return LF4S_INVALID;
    uint32_t at = position(store->rows, store->count, key);
    const uint8_t *data = at < store->count && store->rows[at].key == key
                            ? store->rows[at].data : store->options.defaults;
    memcpy(out, data, LF4S_PAYLOAD_BYTES);
    return LF4S_OK;
}

lf4s_status lf4s_apply(lf4s_store *store, const lf4s_edit *edits, size_t count) {
    if (!store || (count && !edits) || count > store->options.key_count)
        return LF4S_INVALID;
    for (size_t i = 0; i < count; ++i) {
        if (edits[i].key >= store->options.key_count
                || !valid(&store->options, edits[i].data))
            return LF4S_INVALID;
        for (size_t j = 0; j < i; ++j)
            if (edits[j].key == edits[i].key)
                return LF4S_INVALID;
    }
    if (!count)
        return LF4S_OK;
    entry *rows;
    lf4s_status status = stage(store, &rows);
    if (status != LF4S_OK)
        return status;
    uint32_t next_count = store->count;
    for (int pass = 0; pass < 2 && status == LF4S_OK; ++pass)
        for (size_t i = 0; i < count && status == LF4S_OK; ++i)
            if (defaults(store, edits[i].data) == (pass == 0))
                status = put(store, rows, &next_count, edits[i].key, edits[i].data);
    if (status == LF4S_OK)
        commit(store, rows, next_count);
    release_rows(store, rows);
    return status;
}

lf4s_status lf4s_set(lf4s_store *store, uint32_t key, const uint8_t *data) {
    if (!data)
        return LF4S_INVALID;
    lf4s_edit edit;
    edit.key = key;
    memcpy(edit.data, data, LF4S_PAYLOAD_BYTES);
    return lf4s_apply(store, &edit, 1);
}

lf4s_status lf4s_copy(const lf4s_store *source, lf4s_store *destination,
                      uint32_t first, uint32_t target, uint32_t count) {
    if (!source || !destination || !count || first >= source->options.key_count
            || target >= destination->options.key_count
            || count > source->options.key_count - first
            || count > destination->options.key_count - target
            || source->options.max_word != destination->options.max_word
            || memcmp(source->options.defaults, destination->options.defaults,
                       LF4S_PAYLOAD_BYTES))
        return LF4S_INVALID;
    entry *rows;
    lf4s_status status = stage(destination, &rows);
    if (status != LF4S_OK)
        return status;
    uint32_t next_count = 0;
    /* Libère toute la plage cible avant insertion ; la source n'est pas publiée. */
    for (uint32_t i = 0; i < destination->count; ++i) {
        uint32_t key = rows[i].key;
        if (key < target || key - target >= count)
            rows[next_count++] = rows[i];
    }
    for (uint32_t i = 0; i < count && status == LF4S_OK; ++i) {
        uint8_t data[LF4S_PAYLOAD_BYTES];
        status = lf4s_get(source, first + i, data);
        if (status == LF4S_OK)
            status = put(destination, rows, &next_count, target + i, data);
    }
    if (status == LF4S_OK)
        commit(destination, rows, next_count);
    release_rows(destination, rows);
    return status;
}

lf4s_status lf4s_reset(lf4s_store *store) {
    if (!store)
        return LF4S_INVALID;
    store->count = 0;
    return LF4S_OK;
}

size_t lf4s_encoded_size(const lf4s_store *store) {
    return store ? LF4S_HEADER_BYTES + LF4S_ROW_BYTES * (size_t)store->count + 4 : 0;
}

static int valid_base(const uint8_t *base, size_t size) {
    return size <= UINT32_MAX && (!size || base);
}

lf4s_status lf4s_save(const lf4s_store *store, const uint8_t *base,
                      size_t base_size, uint8_t *out, size_t capacity,
                      size_t *written) {
    if (!store || !valid_base(base, base_size) || !out || !written)
        return LF4S_INVALID;
    size_t bytes = lf4s_encoded_size(store);
    if (capacity < bytes)
        return LF4S_CAPACITY;
    uint32_t base_crc = crc32(base, base_size);
    write32(out, 0x4c463453u);
    write16(out + 4, 1);
    write16(out + 6, LF4S_ROW_BYTES);
    write32(out + 8, (uint32_t)bytes);
    write16(out + 12, store->options.key_count);
    write16(out + 14, store->count);
    write32(out + 16, (uint32_t)base_size);
    write32(out + 20, base_crc);
    for (uint32_t i = 0; i < store->count; ++i) {
        uint8_t *row = out + LF4S_HEADER_BYTES + LF4S_ROW_BYTES * i;
        write16(row, store->rows[i].key);
        write16(row + 2, 0);
        for (size_t j = 0; j < LF4S_PAYLOAD_BYTES; ++j)
            row[4 + j] = store->rows[i].data[j] ^ store->options.defaults[j];
    }
    write32(out + bytes - 4, crc32(out, bytes - 4));
    *written = bytes;
    return LF4S_OK;
}

lf4s_status lf4s_load(lf4s_store *store, const uint8_t *base, size_t base_size,
                      const uint8_t *section, size_t section_size) {
    if (!store || !valid_base(base, base_size))
        return LF4S_INVALID;
    if (!section || section_size < LF4S_HEADER_BYTES + 4
            || section_size > LF4S_HEADER_BYTES + 4
                                + LF4S_ROW_BYTES * (size_t)store->options.key_count
            || read32(section) != 0x4c463453u || read16(section + 4) != 1
            || read16(section + 6) != LF4S_ROW_BYTES
            || read32(section + 8) != section_size
            || read16(section + 12) != store->options.key_count
            || read32(section + section_size - 4)
                != crc32(section, section_size - 4))
        return LF4S_FORMAT;
    uint32_t count = read16(section + 14);
    if (section_size != LF4S_HEADER_BYTES + 4 + LF4S_ROW_BYTES * (size_t)count)
        return LF4S_FORMAT;
    if (read32(section + 16) != base_size || read32(section + 20) != crc32(base, base_size))
        return LF4S_BINDING;
    if (count > store->options.capacity)
        return LF4S_CAPACITY;
    /* Valide tout le fichier avant allocation et remplacement de l'état. */
    uint32_t previous = 0;
    for (uint32_t i = 0; i < count; ++i) {
        const uint8_t *row = section + LF4S_HEADER_BYTES + LF4S_ROW_BYTES * i;
        uint32_t key = read16(row);
        uint8_t data[LF4S_PAYLOAD_BYTES];
        for (size_t j = 0; j < LF4S_PAYLOAD_BYTES; ++j)
            data[j] = row[4 + j] ^ store->options.defaults[j];
        if (key >= store->options.key_count || read16(row + 2)
                || (i && key <= previous) || !valid(&store->options, data)
                || defaults(store, data))
            return LF4S_FORMAT;
        previous = key;
    }
    entry *rows;
    lf4s_status status = stage(store, &rows);
    if (status != LF4S_OK)
        return status;
    for (uint32_t i = 0; i < count; ++i) {
        const uint8_t *row = section + LF4S_HEADER_BYTES + LF4S_ROW_BYTES * i;
        rows[i].key = (uint16_t)read16(row);
        for (size_t j = 0; j < LF4S_PAYLOAD_BYTES; ++j)
            rows[i].data[j] = row[4 + j] ^ store->options.defaults[j];
    }
    commit(store, rows, count);
    release_rows(store, rows);
    return LF4S_OK;
}
