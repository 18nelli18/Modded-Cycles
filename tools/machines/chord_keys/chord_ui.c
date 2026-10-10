/* Touches TRIG et menu du clavier d'accords, OS 1.13 (notes/40).
 * Les notes passent par les helpers stock ; le moteur interprète leur degré
 * avec la configuration publiée. Aucun état sonore n'est modifié directement.
 * Les seize touches parcourent les degrés, puis les octaves. Les modificateurs
 * de sélection, FUNC et l'édition de grille gardent le consommateur d'origine ;
 * les vues prioritaires sont traitées par le contrôleur avant KeyboardView.
 */
#include "chord_keys.h"
#include "chord_ui.h"
#include "chord_plocks.h"
#include "chord_midi.h"

typedef unsigned char u8;
typedef unsigned u32;
typedef int s32;

#define WORD(p, n) (*(u32 *)((u8 *)(p) + (n)))
#define KEY(code) (((u32 (*)(u32))0x4007faf4)(code))
#define NEW(n) (((void *(*)(u32))0x400802e0)(n))
#define ENABLED 0x80000000u
#define ROOT_MIN 24u
#define ROOT_MAX 48u

struct held_key {
    void *view;
    u32 track, note;
    u8 valid, active, velocity;
};

/* Zéro dans l'image, y compris sans remise à zéro des caves au démarrage. */
static struct held_key held[16];

/* Captures physiques séparées de l'harmonie : relâcher un pad ne change pas
 * le son. La dernière transformation reste propre à sa piste et son pattern.
 */
static u8 held_pads[6];
struct live_modifier { const void *header; u32 modifier; };
static struct live_modifier live_modifiers[6];
/* Geste tenu côté UI : jamais lu par le DSP de la note précédente. Il prépare
 * chaque nouveau TRIG jusqu'au relâchement du pad, même après une attaque live.
 */
static struct live_modifier prepared_modifiers[6];
static void replay_held_key(u32 track);
extern u32 ck_ui_key_original(void *view, u8 *event);
extern void ck_tg_key_release(void *view, u32 track, u32 note);
extern u32 ck_storage_irq_save(void);
extern void ck_storage_irq_restore(u32 sr);

void ck_ui_clear_modifiers(u32 track, const volatile void *header)
{
    u32 i;
    for (i = 0; i < 6; ++i)
        if (track >= 6 || i == track) {
            if (live_modifiers[i].header == header) {
                live_modifiers[i].modifier = 0;
                live_modifiers[i].header = 0;
            }
            if (prepared_modifiers[i].header == header)
                prepared_modifiers[i].modifier = 0;
        }
}

void ck_ui_clear_header(const volatile void *header)
{
    ck_ui_clear_modifiers(6, header);
}

u32 ck_ui_modifier_get(u32 track, const void *header)
{
    u32 i;
    /* track=6 synchronise seulement l'identité du pattern audio. Les mots
     * sont atomiques ; les éditeurs masquent l'IRQ pendant leur publication.
     */
    if (track == 6)
        for (i = 0; i < 6; ++i)
            if (live_modifiers[i].header != header) {
                live_modifiers[i].modifier = 0;
                live_modifiers[i].header = 0;
            }
    return track < 6 && live_modifiers[track].header == header
        ? live_modifiers[track].modifier : 0;
}

u32 ck_ui_modifier_active(u32 track, const void *header)
{
    return header && track < 6 && live_modifiers[track].header == header;
}

static u32 selected_track(void)
{
    void *root = ((void *(*)(void))0x400cf866)();
    void *state = ((void *(*)(void *))0x4000eb90)(root);
    return ((u32 (*)(void *))0x40012412)(state);
}

static int is_chord(u32 track)
{
    /* 0x4001e318 ignore son premier argument et lit la machine du son de piste. */
    return ((s32 (*)(void *, u32))0x4001e318)(0, track) == 5;
}

static __attribute__((noinline)) void pad_live(u32 pad, u32 track, const void *header)
{
    u32 key = ck_ui_active_key(track), sr;
    held_pads[pad] = 1;
    prepared_modifiers[track].header = header;
    prepared_modifiers[track].modifier = pad + 1;
    /* Une capture dont le relâchement a été absorbé n'est plus un TRIG tenu.
     * Préparer le prochain appui ne touche ni la queue audio ni les P-locks.
     */
    if (key >= 16 || !KEY(key + 16)) {
        return;
    }
    sr = ck_storage_irq_save();
    live_modifiers[track].header = header;
    live_modifiers[track].modifier = pad + 1;
    ck_storage_irq_restore(sr);
    /* Le recorder capture HARMONY sur le pas de la nouvelle note. Écrire ici
     * au pas courant peut écraser le TRIG précédent avant la quantification.
     */
    replay_held_key(track);
}

static __attribute__((noinline)) int pad_press(u32 pad, u8 *event)
{
    u32 track, i;
    const void *header;
    void *state;
    /* PadEvent::function est un booléen d'un octet. Son constructeur laisse
     * +29..31 intacts : lire un mot confond les restes de pile avec FUNC.
     */
    if (event[28])
        return 0;
    for (i = 1; i <= 4; ++i)
        if (KEY(i))
            return 0;
    state = ((void *(*)(void))0x400cf9a8)();
    track = selected_track();
    if (track >= 6 || !is_chord(track) || !(ck_ui_config_get(track) & ENABLED))
        return 0;
    header = ck_ui_header();
    if (ck_plock_grid(track, pad + 1)) {
        /* Un pas tenu reçoit le verrou, sans transformer un accord live.
         * Garder l'identité physique consomme aussi la fin de ce geste.
         */
        held_pads[pad] = 1;
        return 1;
    }
    /* Sans pas tenu, l'édition de grille et les modes réservés restent stock. */
    if (((u8 (*)(void *))0x4006b978)(state) || ((u8 (*)(void *))0x4006bb18)(state))
        return 0;
    pad_live(pad, track, header);
    return 1;
}

u32 ck_ui_pad_finish(u8 *event)
{
    u32 i, pad = WORD(event, 20) - 1;
    if (WORD(event, 12) != 1 || pad >= 6 || WORD(event, 16) || !held_pads[pad])
        return 0;
    held_pads[pad] = 0;
    for (i = 0; i < 6; ++i)
        if (prepared_modifiers[i].modifier == pad + 1)
            prepared_modifiers[i].modifier = 0;
    return 1;
}

u32 ck_ui_pad(void *view, u8 *event)
{
    u32 pad = WORD(event, 20) - 1;
    if (WORD(event, 12) == 1 && pad < 6) {
        if (ck_ui_pad_finish(event) || held_pads[pad])
            return 1;
        if (WORD(event, 16) && pad_press(pad, event))
            return 1;
    }
    return ((u32 (*)(void *, u8 *))0x4001d180)(view, event);
}

static void release_key(struct held_key *key)
{
    if (key->active) {
        ck_tg_key_release(key->view, key->track, key->note);
        key->active = 0;
    }
}

void ck_ui_cancel_track(u32 track)
{
    u32 i;
    for (i = 0; i < 16; ++i)
        if (held[i].valid && held[i].track == track)
            release_key(&held[i]);
}

u32 ck_ui_active_key(u32 track)
{
    u32 i;
    for (i = 0; i < 16; ++i)
        if (held[i].active && held[i].track == track)
            return i;
    return 16;
}

u32 ck_ui_active_note(u32 track)
{
    u32 key = ck_ui_active_key(track);
    return key < 16 ? held[key].note : 128;
}

u32 ck_ui_has_active_note(void)
{
    u32 i, seen = 0;
    /* Même priorité que six appels à active_note : seule la première touche
     * active de chaque piste compte, même si sa note est hors plage. Une seule
     * traversée suffit au rafraîchissement, y compris sans aucune touche.
     */
    for (i = 0; i < 16; ++i) {
        u32 track = held[i].track;
        if (held[i].active && track < 6 && !(seen & (1u << track))) {
            seen |= 1u << track;
            if (held[i].note < 128)
                return 1;
        }
    }
    return 0;
}

static __attribute__((noinline)) u32 key_velocity(u32 track)
{
    void *root = ((void *(*)(void))0x400cf866)();
    void *pattern = ((void *(*)(void *))0x4000f208)(root);
    void *data = ((void *(*)(void *, u32))0x4000cfcc)(pattern, track);
    /* Les boutons TRIG, sans capteur de force, utilisent la vélocité de piste. */
    u32 velocity = ((u8 (*)(void *))0x40015ac4)(data);
    return velocity > 127 ? 127 : velocity;
}

/* La dernière frappe remplace la précédente sur sa piste. Le relâchement de
 * l'ancienne touche sera consommé, sans couper la nouvelle même à note égale.
 */
static void play_key(void *view, u32 key, u32 track, u32 note, u32 velocity)
{
    struct held_key *h = &held[key];
    release_key(h);
    ck_ui_cancel_track(track);
    h->view = view;
    h->track = track;
    h->note = note;
    h->velocity = velocity;
    h->valid = h->active = 1;
    ((void (*)(void *, u32, u32, u32, s32))0x40019e7a)(view, track, note, velocity, -1);
}

static __attribute__((noinline)) int chord_for(u32 word, u32 key, struct chord_keys_result *result)
{
    struct chord_keys_config config;
    u32 i;
    config.root = (word >> 21) & 127;
    config.mode = (word >> 28) & 7;
    for (i = 0; i < 7; ++i)
        config.extensions[i] = (word >> (3 * i)) & 7;
    return chord_keys_build(&config, key, result) == CHORD_KEYS_OK;
}

u32 ck_ui_modifier_unavailable(u32 track)
{
    u32 key, word = ck_ui_config_get(track);
    struct chord_keys_result chord;
    if (ck_ui_modifier_get(track, ck_ui_header()) < 5)
        return 0;
    /* Seule la fondamentale de la dernière touche tenue est connue ici.
     * Le moteur contrôle aussi les notes du séquenceur et de l'entrée MIDI.
     */
    for (key = 0; key < 16; ++key)
        if (held[key].active && held[key].track == track) {
            word &= ~(7u << (3 * (key % 7)));
            return chord_for(word, key, &chord) && chord.offsets[2] == 6;
        }
    return 0;
}

static void replay_held_key(u32 track)
{
    u32 key = ck_ui_active_key(track);
    /* Une capture peut survivre au relâchement absorbé par une vue prioritaire.
     * Seul un TRIG physiquement tenu peut réarticuler l'accord.
     */
    if (key < 16 && KEY(key + 16) && !ck_ui_modifier_unavailable(track)) {
        struct held_key *h = &held[key];
        play_key(h->view, key, track, h->note, h->velocity);
    }
}

static __attribute__((noinline)) int handle_press(void *view, u8 *event, u32 key)
{
    struct chord_keys_result chord;
    void *state;
    u32 track, word, sr, modifier;
    const void *header;
    if ((WORD(event, 16) & 2) || KEY(1) || KEY(2) || KEY(3))
        return 0;
    state = ((void *(*)(void))0x400cf9a8)();
    /* Contrat stock de KeyboardView : l'édition des pas reste à PatternGridView. */
    if (((u8 (*)(void *))0x4006b978)(state) || ((u8 (*)(void *))0x4006bb18)(state))
        return 0;
    track = selected_track();
    if (track >= 6 || !is_chord(track))
        return 0;
    word = ck_ui_config_get(track);
    if (!(word & ENABLED))
        return 0;
    if (!chord_for(word, key, &chord))
        return 1; /* réglage invalide : ne pas déclencher une autre piste */
    /* Chaque nouveau TRIG applique le pad encore tenu sur sa piste et son
     * pattern, sinon il part de son extension. Seuls le relâchement du pad ou
     * un changement de réglage annulent cette préparation.
     */
    header = ck_ui_header();
    modifier = prepared_modifiers[track].header == header
        ? prepared_modifiers[track].modifier : 0;
    sr = ck_storage_irq_save();
    live_modifiers[track].header = header;
    live_modifiers[track].modifier = modifier;
    ck_storage_irq_restore(sr);
    play_key(view, key, track, chord.notes[0], key_velocity(track));
    return 1;
}

u32 ck_ui_key(void *view, u8 *event)
{
    u32 code = WORD(event, 12), flags = WORD(event, 16);
    if (code >= 16 && code <= 31) {
        u32 key = code - 16;
        if (!(flags & 1) && held[key].valid) {
            release_key(&held[key]);
            held[key].valid = 0;
            return 1;
        }
        /* Les répétitions de maintien ne doivent jamais redéclencher un accord. */
        if ((flags & 8) && held[key].valid)
            return 1;
        if ((flags & 9) == 1) {
            /* Une vue prioritaire ou le masque des touches a pu consommer le
             * relâchement précédent. La nouvelle frappe termine cette capture
             * avant tout repli, sinon son futur note-off stock serait volé.
             */
            release_key(&held[key]);
            held[key].valid = 0;
            if (handle_press(view, event, key))
                return 1;
        }
    }
    return ck_ui_key_original(view, event);
}

/* Menu FUNC + RETRIG : conventions de MenuItem déjà éprouvées par l'arpège.
 * Les fermetures de quatre octets sont copiées/détruites par l'OS.
 */
typedef struct {
    void *storage, *unused;
    u32 manager;
    void *invoke;
} function_t;

extern char ck_ui_item_label[];
static const char *const labels[] = {
    "Keys", "Root", "Scale", "I", "II", "III", "IV", "V", "VI", "VII", "MIDI"
};
static const char *const modes[] = { "MAJ", "DOR", "PHR", "LYD", "MIX", "MINOR", "LOC" };
static const char *const extensions[] = { "TRI", "7", "9", "11", "13" };
static const char *const notes[] = { "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B" };

static u32 field_shift(u32 field)
{
    return field == 0 ? 31 : field == 1 ? 21 : field == 2 ? 28 : 3 * (field - 3);
}

static u32 field_value(u32 word, u32 field)
{
    return (word >> field_shift(field)) & (field == 0 ? 1 : field == 1 ? 127 : 7);
}

static __attribute__((noinline)) const char *field_text(u32 field, u32 value)
{
    if (field == 10)
        return value ? "CHORD" : "ROOT";
    if (!field)
        return value ? "ON" : "OFF";
    if (field == 2)
        return modes[value < 7 ? value : 0];
    return extensions[value < 5 ? value : 0];
}

void ck_ui_item_draw(u32 **closure, u32 unused, u32 canvas, u8 *item, u32 flags)
{
    u32 field = **closure, track = selected_track(), word, value, buffer[2];
    (void)unused;
    word = track < 6 ? ck_ui_config_get(track) : 0;
    value = field == 10 ? ck_ui_midi_get(track) : field_value(word, field);
    ((void (*)(u32 *, u32))0x40072260)(buffer, 0x40140ab0);
    if (field == 1)
        ((void (*)(u32, u32 *, u8 *, u32, u32, const char *, const char *, int))0x40071a04)
            (canvas, buffer, item + 24, flags, 4, "%s%d", notes[value % 12], (int)(value / 12) - 1);
    else
        ((void (*)(u32, u32 *, u8 *, u32, u32, const char *, const char *))0x40071a04)
            (canvas, buffer, item + 24, flags, 4, "%s", field_text(field, value));
    ((void (*)(u32 *))0x40072080)(buffer);
}

void ck_ui_item_change(u32 **closure, u32 unused, s32 delta)
{
    u32 field = **closure, track = selected_track(), word, shift, mask, high;
    s32 value, low;
    (void)unused;
    if (track >= 6)
        return;
    if (field == 10) {
        value = (s32)ck_ui_midi_get(track) + delta;
        if (value < 0)
            value = 0;
        if (value > 1)
            value = 1;
        ck_ui_cancel_track(track);
        ck_ui_midi_set(track, value);
        return;
    }
    word = ck_ui_config_get(track);
    low = field == 1 ? ROOT_MIN : 0;
    high = !field ? 1 : field == 1 ? ROOT_MAX : field == 2 ? 6 : 4;
    value = (s32)field_value(word, field) + delta;
    if (value < low)
        value = low;
    if ((u32)value > high)
        value = high;
    if (!field && value && !is_chord(track))
        return;
    shift = field_shift(field);
    mask = (!field ? 1u : field == 1 ? 127u : 7u) << shift;
    ck_ui_cancel_track(track);
    ck_ui_config_set(track, (word & ~mask) | ((u32)value << shift));
}

static void add_item(void *view, u32 field)
{
    static void *const invoke[] = {
        ck_ui_item_label, (void *)0x4002ccd0, ck_ui_item_draw, ck_ui_item_change
    };
    function_t funcs[4];
    void *item;
    u32 i;
    for (i = 0; i < 4; ++i) {
        u32 *data = NEW(4);
        *data = !i ? (u32)labels[field] : i == 1 ? (u32)view : field;
        funcs[i].storage = data;
        funcs[i].unused = 0;
        funcs[i].manager = 0x4002cf00;
        funcs[i].invoke = invoke[i];
    }
    item = NEW(0x54);
    ((void (*)(void *, function_t *, function_t *, function_t *, function_t *, s32, s32))0x400734b0)
        (item, &funcs[0], &funcs[1], &funcs[2], &funcs[3], -1, 8);
    ((void (*)(void *, void *))0x40072ce6)(view, item);
    for (i = 0; i < 4; ++i)
        ((void (*)(function_t *))0x400cf044)(&funcs[i]);
}

void ck_ui_menu_ctor(void *view)
{
    u32 field;
    ((void (*)(void *))0x4002d138)(view);
    for (field = 0; field < 11; ++field)
        add_item(view, field);
}
