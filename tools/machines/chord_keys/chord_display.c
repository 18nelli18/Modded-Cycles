/* Publication audio → UI d'un accord cohérent en un seul mot aligné.
 * Aucun buffer commun de travail : l'interruption publie seulement son résultat.
 */
#include "chord_display.h"
#include "chord_ui.h"

volatile unsigned int ck_chord_live[6];
static unsigned int displayed_chord;

unsigned int ck_chord_packet(unsigned int note, const unsigned int intervals[4],
                             unsigned int count, unsigned int voiced_bass)
{
    unsigned int packet, i;
    packet = 0x80000000u | note | ((voiced_bass % 12u) << 27);
    for (i = 0; i < count; ++i)
        packet |= intervals[i] << (7 + 5 * i);
    return packet;
}

void ck_chord_live_publish(unsigned int track, unsigned int note,
                           const unsigned int intervals[4], unsigned int count,
                           unsigned int voiced_bass)
{
    if (track < 6)
        ck_chord_live[track] = ck_chord_packet(note, intervals, count, voiced_bass);
}

static __attribute__((noinline)) unsigned int visible_chord(void)
{
    unsigned int track, packet;
    void *root, *state;
    /* L'écran sert aussi au démarrage, avant la construction du projet. */
    for (track = 0; track < 6; ++track)
        if (ck_ui_active_note(track) < 128)
            break;
    if (track == 6)
        return 0;
    root = ((void *(*)(void))0x400cf866)();
    state = ((void *(*)(void *))0x4000eb90)(root);
    track = ((unsigned int (*)(void *))0x40012412)(state);
    if (track >= 6 || ((int (*)(void *, unsigned int))0x4001e318)(0, track) != 5 ||
        !(ck_ui_config_get(track) & 0x80000000u))
        return 0;
    packet = ck_chord_live[track];
    return (packet & 127u) == ck_ui_active_note(track) ? packet : 0;
}

unsigned int ck_chord_display_dirty(unsigned char *controller)
{
    /* Application::draw ne reconstruit l'écran que sur ce drapeau. Le marqueur
     * suit l'instantané affiché, donc aussi COLOR/SHAPE et le relâchement. */
    if (visible_chord() != displayed_chord)
        controller[32] = 1;
    return controller[32];
}

static __attribute__((noinline)) void
draw_line(void *bitmap, const char *text, unsigned int font, int y, int width)
{
    unsigned int length = 0;
    while (text[length])
        ++length;
    ((int (*)(void *, unsigned int, int, int, int, unsigned int, const char *))0x400716c0)
        (bitmap, font, (128 - ((int)length * width - 1)) / 2, y, 0, length, text);
}

void ck_chord_display_draw(void)
{
    unsigned int packet = visible_chord(), bitmap[7], *pixels, x;
    char name[24], omissions[24];
    displayed_chord = packet;
    if (!(packet & 0x80000000u))
        return;
    ck_chord_name(packet, name, omissions);
    pixels = ((unsigned int *(*)(void))0x4008e728)();
    /* Les 20 lignes en haut de l'écran sont y=44..63 dans le Bitmap natif,
     * soit les 20 bits bas du second mot de chaque colonne. */
    for (x = 0; x < 128; ++x)
        pixels[2 * x + 1] &= 0xfff00000u;
    ((void (*)(void *, int, int, void *, void *))0x40070172)
        (bitmap, 128, 64, pixels, 0);
    draw_line(bitmap, name, 0x4014120c, 54, 8);
    draw_line(bitmap, omissions, 0x40140ab0, 44, 6);
}
