/* Palettes, gestes temporaires et disposition des notes (notes/40 §14.7–14.8).
 * Au plus quatre notes ; aucun flottant, allocation ou état partagé.
 */
#include "chord_voicing.h"

/* Le degré maximal (6) et la treizième (12 pas) demandent l'indice 18.
 * Prolonger chaque gamme supprime divisions et restes dans l'IRQ audio.
 */
static const unsigned char scales[7][19] = {
    {0, 2, 4, 5, 7, 9, 11, 12, 14, 16, 17, 19, 21, 23, 24, 26, 28, 29, 31},
    {0, 2, 3, 5, 7, 9, 10, 12, 14, 15, 17, 19, 21, 22, 24, 26, 27, 29, 31},
    {0, 1, 3, 5, 7, 8, 10, 12, 13, 15, 17, 19, 20, 22, 24, 25, 27, 29, 31},
    {0, 2, 4, 6, 7, 9, 11, 12, 14, 16, 18, 19, 21, 23, 24, 26, 28, 30, 31},
    {0, 2, 4, 5, 7, 9, 10, 12, 14, 16, 17, 19, 21, 22, 24, 26, 28, 29, 31},
    {0, 2, 3, 5, 7, 8, 10, 12, 14, 15, 17, 19, 20, 22, 24, 26, 27, 29, 31},
    {0, 1, 3, 5, 6, 8, 10, 12, 13, 15, 17, 18, 20, 22, 24, 25, 27, 29, 30}
};

static const unsigned char positions[5][4] = {
    {0, 2, 4, 0}, {0, 2, 4, 6}, {0, 2, 6, 8},
    {0, 2, 6, 10}, {0, 2, 6, 12}
};

enum harmonic_family { MAJOR, MINOR, DOMINANT, DIMINISHED };

unsigned int ck_palette_index(int color_q8)
{
    return color_q8 < 43 * 256 ? CK_PALETTE_DIATONIC :
           color_q8 < 86 * 256 ? CK_PALETTE_JAZZ : CK_PALETTE_TENSION;
}

static __attribute__((noinline)) unsigned int
harmonic_family(unsigned int mode, unsigned int degree)
{
    /* Les sept modes sont les rotations successives de la gamme majeure. */
    static const unsigned char families[7] = {
        MAJOR, MINOR, MINOR, MAJOR, DOMINANT, MINOR, DIMINISHED
    };
    unsigned int position = mode + degree;
    if (position >= 7)
        position -= 7;
    return families[position];
}

/* Un appel séparé évite de dépasser les masques de sprites de 376 octets. */
static __attribute__((noinline)) void
diatonic_intervals(unsigned int mode, unsigned int degree,
                    unsigned int extension, unsigned int notes[4])
{
    unsigned int i;
    const unsigned char *scale = scales[mode] + degree;
    unsigned int root = scale[0];
    for (i = 0; i < 4; ++i)
        notes[i] = scale[positions[extension][i]] - root;
}

static __attribute__((noinline)) unsigned int
palette_tension(unsigned int family, unsigned int extension, unsigned int palette)
{
    if (extension == 2)
        return family == DOMINANT && palette == CK_PALETTE_TENSION ? 13 : 14;
    if (extension == 3)
        return family == MAJOR || family == DOMINANT ? 18 : 17;
    return family == DOMINANT && palette == CK_PALETTE_TENSION ? 20 : 21;
}

static __attribute__((noinline)) void
parallel_intervals(unsigned int family, unsigned int extension,
                    unsigned int palette, unsigned int notes[4])
{
    /* La famille transformée suffit ; aucune mutation du réglage enregistré. */
    family = family == MINOR ? MAJOR : MINOR;
    notes[0] = 0;
    notes[1] = family == MINOR ? 3 : 4;
    notes[2] = 7;
    notes[3] = extension ? (family == MINOR ? 10 : 11) : 0;
    if (extension >= 2) {
        notes[2] = notes[3];
        notes[3] = palette == CK_PALETTE_DIATONIC ?
            (extension == 2 ? 14 : extension == 3 ? 17 : family == MINOR ? 20 : 21) :
            palette_tension(family, extension, palette);
    }
}

static __attribute__((noinline)) unsigned int
transform_intervals(unsigned int family, unsigned int extension, unsigned int palette,
                    unsigned int transform, unsigned int notes[4])
{
    if (transform == CK_TRANSFORM_PARALLEL || transform == CK_TRANSFORM_V7) {
        if (family == DIMINISHED)
            return 0;
        if (transform == CK_TRANSFORM_PARALLEL) {
            parallel_intervals(family, extension, palette, notes);
            return extension ? 4 : 3;
        }
        notes[0] = 7; notes[1] = 11; notes[2] = 14; notes[3] = 17;
        return 4;
    }
    if (transform == CK_TRANSFORM_SUS7) {
        notes[0] = 0; notes[1] = 5; notes[2] = 7; notes[3] = 10;
        return 4;
    }
    if (extension >= 2) {
        /* La quinte diminuée identifie cette famille, y compris avec tension. */
        if (family == DIMINISHED)
            notes[1] = 6;
        if (palette != CK_PALETTE_DIATONIC)
            notes[3] = palette_tension(family, extension, palette);
    }
    return extension ? 4 : 3;
}

unsigned int ck_harmony_intervals(unsigned int mode, unsigned int degree,
                                  unsigned int extension, unsigned int palette,
                                  unsigned int transform, unsigned int intervals[4])
{
    unsigned int notes[4], count, i;
    if (!intervals || mode >= 7 || degree >= 7 || extension >= 5 ||
        palette >= CK_PALETTE_COUNT || transform >= CK_TRANSFORM_COUNT)
        return 0;
    if (transform >= CK_TRANSFORM_NINTH && transform <= CK_TRANSFORM_THIRTEENTH)
        extension = transform + 1;
    /* SUS7, PARALLÈLE et V7 remplacent les quatre notes entièrement. */
    if (transform < CK_TRANSFORM_SUS7)
        diatonic_intervals(mode, degree, extension, notes);
    count = transform_intervals(harmonic_family(mode, degree), extension,
                                palette, transform, notes);
    if (count)
        for (i = 0; i < 4; ++i)
            intervals[i] = notes[i];
    return count;
}

unsigned int ck_voicing_gain(unsigned int index, unsigned int voice,
                             unsigned int count)
{
    /* Multiples de 1024, gain de l'opérateur natif multiplié après son update.
     * Les lignes suivent les registres graves→aigus, après leur disposition.
     */
    static const unsigned char gains[9][3] = {
        {32, 32, 32}, {30, 26, 28}, {26, 32, 28},
        {28, 26, 32}, {32, 28, 26}, {22, 28, 32},
        {28, 22, 32}, {32, 22, 28}, {28, 32, 22}
    };
    if (voice >= count || voice >= 4)
        return 0;
    if (!voice || index >= 9)
        return 32768;
    return (unsigned int)gains[index][voice - 1] << 10;
}

unsigned int ck_voicing_index(int shape_q8)
{
    if (shape_q8 < 0)
        return 0;
    if (shape_q8 >= 32 * 256)
        return 8;
    return (unsigned int)shape_q8 >> 10;
}

static __attribute__((noinline)) void sort_notes(unsigned int *notes, unsigned int count)
{
    unsigned int i, j;
    for (i = 1; i < count; ++i) {
        unsigned int note = notes[i];
        for (j = i; j && notes[j - 1] > note; --j)
            notes[j] = notes[j - 1];
        notes[j] = note;
    }
}

void ck_voicing_apply(unsigned int notes[4], unsigned int count, unsigned int index)
{
    unsigned int i, rotations;
    if (!index)
        return;
    for (i = 0; i < count; ++i)
        notes[i] %= 12u;
    sort_notes(notes, count);
    rotations = (index - 1) & 3u;
    while (rotations--) {
        /* Après le tri des classes, l'étendue reste au plus une octave :
         * le minimum relevé d'une octave devient directement le maximum.
         */
        unsigned int note = notes[0] + 12;
        for (i = 1; i < count; ++i)
            notes[i - 1] = notes[i];
        notes[i - 1] = note;
    }
    if (index >= 5) {
        for (i = 1; i < count; i += 2)
            notes[i] += 12;
        /* L'étendue reste <= 12 avant l'ouverture. La troisième note passe
         * donc devant la deuxième relevée ; la quatrième reste la plus haute.
         */
        if (count >= 3) {
            unsigned int note = notes[1];
            notes[1] = notes[2];
            notes[2] = note;
        }
    }
}
