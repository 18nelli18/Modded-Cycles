/* Sortie MIDI des accords, OS 1.13 (notes/40).
 * Le jeu direct capture les notes, le canal et la destination de chaque attaque.
 * Le séquenceur conserve sa file native et ses durées : une entrée par voix.
 * Aucun calcul MIDI dans l'update DSP ; aucun état de pile partagé.
 */
#include "chord_midi.h"
#include "chord_ui.h"
#include "chord_audio.h"
#include "chord_voicing.h"
#include "chord_plocks.h"
typedef unsigned char u8;
typedef unsigned int u32;

struct midi_capture { u8 count, root, channel, destination, notes[4]; };
static struct midi_capture live[6];
/* Identités des accords remplacés : leur relâchement ne doit ni couper une
 * voix du nouvel accord ni avaler le note-off d'une ancienne note ROOT. */
static u32 expanded[6][4];

static const u8 scales[7][7] = {
    {0,2,4,5,7,9,11}, {0,2,3,5,7,9,10}, {0,1,3,5,7,8,10},
    {0,2,4,6,7,9,11}, {0,2,4,5,7,9,10}, {0,2,3,5,7,8,10},
    {0,1,3,5,6,8,10}
};

/* Même harmonie entière que le DSP ; PITCH/FINE restent propres à l'audio.
 * Les voix hors MIDI 0..127 sont omises, sans replier les notes valides.
 */
static __attribute__((noinline)) u32 midi_notes(u32 cfg, u32 note,
        const unsigned short *params, u32 modifier, u32 notes[4])
{
    u32 mode = (cfg >> 28) & 7u, degree, count, i, used = 0, relative;
    if (!(cfg & 0x80000000u) || mode >= 7 || note > 127 || !params || params[9] != 5u << 8)
        return 0;
    if (note > 96)
        note = 96;
    relative = (note + 12u - (((cfg >> 21) & 127u) % 12u)) % 12u;
    for (degree = 0; degree < 7 && scales[mode][degree] != relative; ++degree) {}
    if (degree == 7)
        return 0;
    count = ck_harmony_intervals(mode, degree, (cfg >> (3 * degree)) & 7u,
             ck_palette_index((short)params[11]), modifier, notes);
    if (!count)
        count = ck_harmony_intervals(mode, degree, (cfg >> (3 * degree)) & 7u,
                 ck_palette_index((short)params[11]), 0, notes);
    ck_voicing_apply(notes, count, ck_voicing_index((short)params[12]));
    for (i = 0; i < count; ++i)
        if (notes[i] + note < 128)
            notes[used++] = notes[i] + note;
    return used;
}

static void send(u32 channel, u32 note, u32 velocity, u32 destination)
{
    u8 bytes[3];
    bytes[0] = (velocity ? 0x90u : 0x80u) | channel;
    bytes[1] = note;
    bytes[2] = velocity;
    ((void (*)(u32, const u8 *, u32))0x400826b0)(3, bytes, destination);
}

static __attribute__((noinline)) void release(struct midi_capture *capture)
{
    u32 i, count = capture->count;
    capture->count = 0;
    for (i = 0; i < count; ++i)
        send(capture->channel, capture->notes[i], 0, capture->destination);
}

static __attribute__((noinline)) u32 live_channel(u32 track)
{
    void *root = ((void *(*)(void))0x400cf866)();
    void *pattern = ((void *(*)(void *))0x4000f208)(root);
    void *object = ((void *(*)(void *, u32))0x4000cfcc)(pattern, track);
    if (!((u8 (*)(void *))0x40016e90)(object))
        return 16;
    return ((u32 (*)(void *, u32))0x40012e82)(
        ((void *(*)(void *))0x4000eb90)(root), track);
}

static __attribute__((noinline)) const unsigned short *live_params(u32 track)
{
    void *root = ((void *(*)(void))0x400cf866)();
    void *bank = ((void *(*)(void *))0x4000eb9c)(root);
    void *object = ((void *(*)(void *, u32))0x40009c1a)(bank, track);
    u8 *raw = ((u8 *(*)(void *))(*(u32 **)object)[10])(object);
    return raw ? (const unsigned short *)(raw + 20) : 0;
}

u32 ck_midi_live_off(u32 track, u32 note)
{
    if (track >= 6)
        return 0;
    if (note < 128 && (expanded[track][note >> 5] & (1u << (note & 31u)))) {
        expanded[track][note >> 5] &= ~(1u << (note & 31u));
        if (live[track].root == note)
            release(&live[track]);
        return 1;
    }
    /* Le relais rejoue le vrai chemin natif, y compris sa sélection MOut. */
    return 0;
}

static __attribute__((noinline)) void capture_on(u32 track, u32 channel, u32 note,
                                               u32 velocity, const u32 notes[4], u32 count)
{
    struct midi_capture *capture = &live[track];
    u32 i;
    capture->channel = channel;
    capture->destination = ((u32 (*)(void))0x40082686)();
    /* Le résolveur rend 1 pour OFF, mais l'émetteur interprète 1 comme AUTO.
     * Capturer une destination explicitement vide évite qu'un relâchement
     * ultérieur utilise un routage activé après une attaque silencieuse. */
    if (capture->destination == 1)
        capture->destination = 0;
    capture->root = note;
    expanded[track][note >> 5] |= 1u << (note & 31u);
    for (i = 0; i < count; ++i)
        capture->notes[i] = notes[i];
    capture->count = count;
    for (i = 0; i < count; ++i)
        send(channel, notes[i], velocity, capture->destination);
}

void ck_midi_live_on(u32 track, u32 note, u32 velocity)
{
    u32 channel, count = 0, notes[4];
    if (track >= 6)
        return;
    if (live[track].count)
        release(&live[track]);
    channel = live_channel(track);
    if (channel > 15 || note > 127 || !velocity || velocity > 127)
        return;
    if (ck_ui_midi_get(track))
        count = midi_notes(ck_ui_config_get(track), note, live_params(track),
                          ck_ui_modifier_get(track, ck_ui_header()), notes);
    if (count)
        capture_on(track, channel, note, velocity, notes, count);
    else {
        expanded[track][note >> 5] &= ~(1u << (note & 31u));
        ((void (*)(u32, u32, u32))0x4008273c)(channel, note, velocity);
    }
}

/* Appelé après l'application des P-locks, avant de recycler l'événement.
 * La condition MOut est celle du producteur natif (octet événement +20).
 * Le consommateur natif choisit le canal, règle les notes répétées, LEN et STOP.
 */
void ck_midi_sequence(u32 track, const u32 *event, u32 time)
{
    u32 notes[4], count = 0, i;
    const unsigned short *params = (const unsigned short *)(0x800015aeu + 66u * track);
    if (track >= 6 || !((const u8 *)event)[20])
        return;
    if (ck_audio_midi_get(track))
        count = midi_notes(ck_audio_config(track), event[7], params,
                 ck_audio_locked_controls(track, params[CK_HARMONY_SLOT]) >> 8, notes);
    if (!count) {
        count = 1;
        notes[0] = event[7];
    }
    for (i = 0; i < count; ++i) {
        u8 *message = ((u8 *(*)(void))0x4008a5d0)();
        message[0] = 1;
        *(u32 *)(message + 4) = time;
        message[8] = track;
        message[9] = notes[i];
        message[10] = ((const u8 *)event)[22];
        *(u32 *)(message + 12) = event[13];
        ((void (*)(void *, void *))0x40001fba)((void *)0x40fcb2ec, message);
    }
}
