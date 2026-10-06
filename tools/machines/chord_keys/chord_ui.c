/* Pads et menu du clavier d'accords, OS 1.13 (notes/42).
 * Les notes passent par les helpers stock ; le moteur interprète leur degré
 * avec la configuration publiée. Aucun état sonore n'est modifié directement.
 * RETRIG donne la seconde banque dans ce mode. Les modificateurs de sélection
 * et FUNC gardent le consommateur d'origine ; les vues prioritaires restent
 * prises en charge par le contrôleur avant l'appel de PadsView.
 */
#include "chord_keys.h"
#include "chord_ui.h"

typedef unsigned char u8;
typedef unsigned u32;
typedef int s32;

#define WORD(p, n) (*(u32 *)((u8 *)(p) + (n)))
#define KEY(code) (((u32 (*)(u32))0x4007faf4)(code))
#define NEW(n) (((void *(*)(u32))0x400802e0)(n))
#define ENABLED 0x80000000u
#define ROOT_MIN 24u
#define ROOT_MAX 48u

struct held_pad {
    void *view;
    u32 track, note;
    u8 valid, active;
};

/* Zéro dans l'image, y compris sans remise à zéro des caves au démarrage. */
static struct held_pad held[6];

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

static void release_pad(struct held_pad *pad)
{
    if (pad->active) {
        ((void (*)(void *, u32, u32))0x4001d0fc)(pad->view, pad->track, pad->note);
        pad->active = 0;
    }
}

void ck_ui_cancel_track(u32 track)
{
    u32 i;
    for (i = 0; i < 6; ++i)
        if (held[i].valid && held[i].track == track)
            release_pad(&held[i]);
}

static __attribute__((noinline)) u32 pad_velocity(const u8 *event)
{
    void *root = ((void *(*)(void))0x400cf866)();
    void *state = ((void *(*)(void *))0x4000eb90)(root);
    u32 velocity = WORD(event, 24);
    /* Même priorité que PadsView stock : le réglage fixe remplace la frappe. */
    if (((u8 (*)(void *))0x40013464)(state))
        velocity = ((u32 (*)(void *))0x4001351e)(state);
    return velocity > 127 ? 127 : velocity;
}

/* La dernière frappe remplace la précédente sur sa piste. Le relâchement de
 * l'ancien pad sera consommé, sans couper le nouveau même si les notes égalaient.
 */
static void play_pad(void *view, u32 pad, u32 track, u32 note, u32 velocity)
{
    struct held_pad *h = &held[pad];
    release_pad(h);
    ck_ui_cancel_track(track);
    h->view = view;
    h->track = track;
    h->note = note;
    h->valid = h->active = 1;
    ((void (*)(void *, u32, u32, u32, s32))0x4001d05e)(view, track, note, velocity, -1);
}

static int chord_for(u32 word, u32 pad, u32 bank, struct chord_keys_result *result)
{
    struct chord_keys_config config;
    u32 i;
    config.root = (word >> 21) & 127;
    config.mode = (word >> 28) & 7;
    for (i = 0; i < 7; ++i)
        config.extensions[i] = (word >> (3 * i)) & 7;
    return chord_keys_build(&config, pad, bank, result) == CHORD_KEYS_OK;
}

static __attribute__((noinline)) int handle_press(void *view, u8 *event, u32 pad)
{
    struct chord_keys_result chord;
    u32 track, word;
    if (event[28] || KEY(1) || KEY(2) || KEY(3))
        return 0;
    track = selected_track();
    if (track >= 6 || !is_chord(track))
        return 0;
    word = ck_ui_config_get(track);
    if (!(word & ENABLED))
        return 0;
    if (!chord_for(word, pad, KEY(4) != 0, &chord))
        return 1; /* réglage invalide : ne pas déclencher une autre piste */
    play_pad(view, pad, track, chord.notes[0], pad_velocity(event));
    return 1;
}

u32 ck_ui_pad(void *view, u8 *event)
{
    u32 pad = WORD(event, 20), state = WORD(event, 16);
    if (WORD(event, 12) == 1 && pad >= 1 && pad <= 6) {
        --pad;
        if (!state && held[pad].valid) {
            release_pad(&held[pad]);
            held[pad].valid = 0;
            return 1;
        }
        if (state == 1 && handle_press(view, event, pad))
            return 1;
    }
    return ((u32 (*)(void *, u8 *))0x4001d180)(view, event);
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
    "Keys", "Root", "Scale", "I Ext", "II Ext", "III Ext", "IV Ext", "V Ext", "VI Ext", "VII Ext"
};
static const char *const modes[] = { "MAJOR", "DOR", "PHR", "LYD", "MIX", "MINOR", "LOC" };
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

static const char *field_text(u32 field, u32 value)
{
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
    value = field_value(word, field);
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
    for (field = 0; field < 10; ++field)
        add_item(view, field);
}
