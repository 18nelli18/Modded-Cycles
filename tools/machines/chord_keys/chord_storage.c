/* Réglages du clavier d'accords dans l'en-tête du pattern (notes/40).
 * L'OS sauve ses 64 octets, mais ne charge que 0..28 et 38 : signature 32..35,
 * six mots 40..63, sans toucher les champs musicaux stock ni l'octet de l'arp.
 * Les hooks de chargement et d'initialisation rétablissent ces champs réservés.
 */
#include "chord_ui.h"
typedef unsigned char u8;
typedef unsigned int u32;

#define CK_DEFAULT (48u << 21)
#define CK_MAGIC 0x434b01a7u
#define CK_MAGIC_NEW 0x434b0200u
#define CK_ROOT_PTR 0x40fe4228u
#define CK_ACTIVE_PTR 0x40a7887cu

extern u32 ck_storage_irq_save(void);
extern void ck_storage_irq_restore(u32 sr);
static const void *last_audio_header;

static u32 get32(const volatile u8 *p)
{
    return ((u32)p[0] << 24) | ((u32)p[1] << 16) | ((u32)p[2] << 8) | p[3];
}

static void put32(volatile u8 *p, u32 value)
{
    p[0] = value >> 24;
    p[1] = value >> 16;
    p[2] = value >> 8;
    p[3] = value;
}

static u32 signature_valid(u32 magic)
{
    return magic == CK_MAGIC || (magic & ~63u) == CK_MAGIC_NEW;
}

u32 ck_storage_valid(u32 word)
{
    u32 i, root = (word >> 21) & 127u;
    if (root < 24 || root > 48 || ((word >> 28) & 7u) >= 7)
        return 0;
    for (i = 0; i < 7; ++i, word >>= 3)
        if ((word & 7u) >= 5)
            return 0;
    return 1;
}

u32 ck_storage_read(const volatile u8 *header, u32 track)
{
    u32 word;
    if (!header || track >= 6 || !signature_valid(get32(header + 32)))
        return CK_DEFAULT;
    word = get32(header + 40 + 4 * track);
    return ck_storage_valid(word) ? word : CK_DEFAULT;
}

/* Appelé avec les interruptions masquées : aucun lecteur audio ne voit un
 * mot partiellement écrit, y compris si le buffer n'est aligné que sur 2 o.
 */
static void defaults(volatile u8 *header)
{
    u32 track;
    put32(header + 32, 0);
    for (track = 0; track < 6; ++track)
        put32(header + 40 + 4 * track, CK_DEFAULT);
    put32(header + 32, CK_MAGIC_NEW);
}

void ck_storage_reset(volatile u8 *header)
{
    u32 sr;
    if (!header)
        return;
    sr = ck_storage_irq_save();
    ck_ui_clear_header(header);
    defaults(header);
    ck_storage_irq_restore(sr);
}

void ck_storage_load(volatile u8 *destination, const volatile u8 *source)
{
    u32 track, good, sr;
    if (!destination || !source)
        return;
    good = signature_valid(get32(source + 32));
    for (track = 0; good && track < 6; ++track)
        good = ck_storage_valid(get32(source + 40 + 4 * track));
    sr = ck_storage_irq_save();
    ck_ui_clear_header(destination);
    if (good) {
        for (track = 0; track < 6; ++track)
            put32(destination + 40 + 4 * track, get32(source + 40 + 4 * track));
        put32(destination + 32, get32(source + 32));
    } else {
        defaults(destination);
    }
    ck_storage_irq_restore(sr);
}

/* Renvoie l'objet d'en-tête du pattern affiché, comme les accesseurs stock.
 * Ne déclenche jamais l'allocation paresseuse du singleton pendant le boot.
 */
static u8 *ui_header_object(void)
{
    u8 *root = *(u8 * volatile *)CK_ROOT_PTR;
    u8 *pattern;
    if (!root)
        return 0;
    pattern = ((u8 *(*)(u8 *))0x4000f208)(root);
    return pattern ? pattern + 44 : 0;
}

u32 ck_ui_config_get(u32 track)
{
    u8 *object = ui_header_object();
    return object ? ck_storage_read(*(u8 **)(object + 16), track) : CK_DEFAULT;
}

void *ck_ui_header(void)
{
    u8 *object = ui_header_object();
    return object ? *(u8 **)(object + 16) : 0;
}

u32 ck_ui_revision_get(void)
{
    u8 *header = ck_ui_header();
    return header && (get32(header + 32) & ~63u) == CK_MAGIC_NEW;
}

u32 ck_ui_pad_mode_get(u32 track)
{
    u8 *header = ck_ui_header();
    u32 magic = header ? get32(header + 32) : 0;
    return track < 6 && (magic & ~63u) == CK_MAGIC_NEW && (magic & (1u << track));
}

static void signature_set(u32 magic, u32 track)
{
    u8 *object = ui_header_object(), *header;
    u32 sr;
    if (!object || !(header = *(u8 **)(object + 16)))
        return;
    if (get32(header + 32) == magic)
        return;
    sr = ck_storage_irq_save();
    ck_ui_clear_modifiers(track, header);
    if (!signature_valid(get32(header + 32)))
        defaults(header);
    put32(header + 32, magic);
    ck_storage_irq_restore(sr);
    ((void (*)(u8 *, u32))(*(u32 **)object)[4])(object, 0);
}

void ck_ui_revision_set(u32 revision)
{
    if (ck_ui_revision_get() == !!revision)
        return;
    signature_set(revision ? CK_MAGIC_NEW : CK_MAGIC, 6);
}

void ck_ui_pad_mode_set(u32 track, u32 harmony)
{
    u8 *header = ck_ui_header();
    u32 magic = header ? get32(header + 32) : 0;
    if (track >= 6 || (magic & ~63u) != CK_MAGIC_NEW)
        return;
    signature_set((magic & ~(1u << track)) | (harmony ? 1u << track : 0), track);
}

void ck_ui_config_set(u32 track, u32 word)
{
    u8 *object, *header;
    u32 sr;
    if (track >= 6 || !ck_storage_valid(word))
        return;
    object = ui_header_object();
    if (!object || !(header = *(u8 **)(object + 16)))
        return;
    sr = ck_storage_irq_save();
    ck_ui_clear_modifiers(track, header);
    if (!signature_valid(get32(header + 32)))
        defaults(header);
    put32(header + 40 + 4 * track, word);
    ck_storage_irq_restore(sr);
    /* Notification identique aux setters de l'en-tête (ex. A.On 0x4000cd2a).
     * L'observateur stock conserve déjà les 64 octets lors de la sauvegarde.
     */
    ((void (*)(u8 *, u32))(*(u32 **)object)[4])(object, 0);
}

static u8 *audio_header(void)
{
    u8 *root = *(u8 * volatile *)CK_ROOT_PTR;
    u8 *active = *(u8 * volatile *)CK_ACTIVE_PTR;
    u8 *object;
    u32 pattern;
    if (!root || !active)
        return 0;
    pattern = get32(active + 30706);
    if (pattern >= 96)
        return 0;
    /* Tableau de 96 objets construit en 0x40011408 ; pointeurs reliés aux
     * buffers du projet par 0x4000ea46 / 0x4000c5d0. Aucun cache de réglages,
     * aucun appel d'interface, allocation ou verrou dans l'interruption audio.
     */
    object = root + 5192 + 732 * pattern;
    object = *(u8 * volatile *)(object + 60);
    if (object != last_audio_header) {
        ck_ui_modifier_get(6, object);
        last_audio_header = object;
    }
    return object;
}

u32 ck_audio_config(u32 track)
{
    return ck_storage_read(audio_header(), track);
}

u32 ck_audio_controls(u32 track)
{
    u8 *header = audio_header();
    u32 magic = header ? get32(header + 32) : 0;
    if (track >= 6 || (magic & ~63u) != CK_MAGIC_NEW)
        return 0;
    if (!(magic & (1u << track)) || !(ck_storage_read(header, track) & 0x80000000u))
        return 1;
    return 1 | (ck_ui_modifier_get(track, header) << 8);
}
