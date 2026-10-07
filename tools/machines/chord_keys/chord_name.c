/* Noms exacts des voicings à trois/quatre notes de CHORD Keys (notes/40).
 * Les extensions naturelles prennent leur nom usuel, avec les notes omises
 * sur une seconde ligne ; une tension altérée reste explicite sur la septième.
 * Sans libc, allocation, calcul flottant ni état partagé.
 */
#include "chord_display.h"

static const char *const note_names[] = {
    "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"
};

static char *append(char *out, const char *text)
{
    while (*text)
        *out++ = *text++;
    *out = 0;
    return out;
}

/* Fonctions séparées pour tenir dans les masques libérés de 376 octets. */
static __attribute__((noinline)) const char *
seventh_name(unsigned int third, unsigned int seventh)
{
    return third == 6 ? "m7b5" : third == 3 ? "m7" : seventh == 11 ? "maj7" : "7";
}

static __attribute__((noinline)) char *
extended_name(char *out, char *omissions, unsigned int third,
              unsigned int seventh, unsigned int tension)
{
    if (tension == 13 || tension == 18 || tension == 20) {
        out = append(out, seventh_name(third, seventh));
        out = append(out, tension == 13 ? "(b9)" : tension == 18 ? "(#11)" : "(b13)");
        append(omissions, third == 6 ? "no3" : "no5");
        return out;
    }
    if (third == 3 || third == 6)
        out = append(out, "m");
    else if (seventh == 11)
        out = append(out, "maj");
    out = append(out, tension == 14 ? "9" : tension == 17 ? "11" : "13");
    if (third == 6)
        out = append(out, "b5");
    omissions = append(omissions, third == 6 ? "no3" : "no5");
    if (tension != 14)
        omissions = append(omissions, ",9");
    if (tension == 21)
        append(omissions, ",11");
    return out;
}

static __attribute__((noinline)) char *
quality_name(char *out, char *omissions, unsigned int third,
             unsigned int middle, unsigned int top)
{
    if (!top)
        return append(out, middle == 6 ? "dim" : third == 3 ? "m" : "");
    if (third == 5)
        return append(out, "7sus4");
    if (middle == 6)
        return append(out, "m7b5");
    if (middle == 7)
        return append(out, seventh_name(third, top));
    return extended_name(out, omissions, third, middle, top);
}

void ck_chord_name(unsigned int packet, char name[24], char omissions[24])
{
    unsigned int note, offset, root, bass, third, middle, top;
    char *out;
    name[0] = omissions[0] = 0;
    if (!(packet & 0x80000000u))
        return;
    note = packet & 127u;
    offset = (packet >> 7) & 7u;
    root = (note + offset) % 12u;
    bass = (note + ((packet >> 27) & 15u)) % 12u;
    third = ((packet >> 12) & 31u) - offset;
    middle = ((packet >> 17) & 31u) - offset;
    top = (packet >> 22) & 31u;
    if (top)
        top -= offset;
    out = append(name, note_names[root]);
    out = quality_name(out, omissions, third, middle, top);
    if (bass != root) {
        out = append(out, "/");
        append(out, note_names[bass]);
    }
    if (packet & CK_CHORD_LIMITED)
        append(omissions, "HIGH LIMIT");
}
