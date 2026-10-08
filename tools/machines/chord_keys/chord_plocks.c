/* HARMONY dans les véritables P-locks OS 1.13 (notes/40).
 * Aucun détournement de COLOR, de ses fractions, du MIDI ou du LFO : le slot28
 * n'a aucun descripteur et n'est lu ni par les six moteurs stock ni par Model-TG.
 * Les écritures, les flags de présence, la copie et l'effacement restent natifs.
 */
#include "chord_ui.h"
#include "chord_plocks.h"
typedef unsigned char u8;
typedef unsigned int u32;

static __attribute__((noinline)) u8 *track_object(u32 track)
{
    u8 *root = *(u8 * volatile *)0x40fe4228u;
    u8 *pattern;
    if (!root || track >= 6 || !(ck_ui_config_get(track) & 0x80000000u)
        || ((int (*)(void *, u32))0x4001e318)(0, track) != 5)
        return 0;
    pattern = ((u8 *(*)(u8 *))0x4000f208)(root);
    return pattern ? ((u8 *(*)(u8 *, u32))0x4000cfcc)(pattern, track) : 0;
}

static __attribute__((noinline)) void write_lock(u8 *object, u32 step, u32 modifier)
{
    if (step >= (u32)((int (*)(u8 *))0x40016402)(object) || step >= 64)
        return;
    /* Même chemin que l'enregistrement natif des encodeurs 0x4000f4b8 : un
     * pas vide devient un lock-only, sans redéclencher la note ni l'enveloppe.
     */
    if (!((u8 (*)(u8 *, u32))0x40015c20)(object, step)
        && !((u8 (*)(u8 *, u32))0x40015c7c)(object, step))
        ((void (*)(u8 *, u32, u32))0x40017bb0)(object, step, 1);
    ((void (*)(u8 *, u32, u32, u32))0x4001646a)(object, step, CK_HARMONY_SLOT, modifier);
}

void ck_plock_gesture(u32 track, u32 modifier)
{
    u8 *state, *object;
    u32 step;
    if (modifier > 6 || !(object = track_object(track)))
        return;
    state = ((u8 *(*)(void))0x400cf9a8)();
    if (!((u8 (*)(u8 *))0x4006ba76)(state))
        return;
    step = ((u32 (*)(void *, u32))0x4006a984)(
        ((void *(*)(void))0x400cfd0e)(), track);
    write_lock(object, step, modifier);
}

u32 ck_plock_grid(u32 track, u32 modifier)
{
    u8 *state, *object;
    u32 step, limit, lo, hi, wrote = 0;
    if (modifier > 6 || !(object = track_object(track)))
        return 0;
    state = ((u8 *(*)(void))0x400cf9a8)();
    if (!state[357] || state[389])
        return 0;
    hi = *(u32 *)(state + 348);
    lo = *(u32 *)(state + 352);
    if (!(lo | hi))
        return 0;
    limit = ((u32 (*)(u8 *))0x40016402)(object);
    for (step = 0; step < 64 && step < limit; ++step) {
        if ((step < 32 ? lo >> step : hi >> (step - 32)) & 1u) {
            /* Un second appui sur le même T remet EXT sur ce pas sans
             * effacer les autres locks. Zéro explicite vaut aussi pour un
             * lock-only qui prolonge une note jouée plusieurs pas auparavant.
             */
            int old = ((int (*)(void *, u32, u32, u32))0x4000da2a)(
                *(void **)(object + 44), track, step, CK_HARMONY_SLOT);
            write_lock(object, step, old == (int)modifier ? 0 : modifier);
            wrote = 1;
        }
    }
    return wrote;
}

/* Le recorder de notes natif a déjà choisi son pas (microtiming/quantification)
 * et écrit sa note. Capturer aussi zéro empêche une ancienne extension du même
 * pas de survivre à une nouvelle prise sans pad.
 */
void ck_plock_note(void *object, u32 track, u32 step)
{
    if (object == track_object(track))
        write_lock(object, step, ck_ui_modifier_get(track, ck_ui_header()));
}
