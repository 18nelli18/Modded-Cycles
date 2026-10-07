/* Palettes, gestes temporaires et disposition des notes (notes/40 §14.7–14.8).
 * Au plus quatre notes ; aucun flottant, allocation ou état partagé.
 */
#include "chord_voicing.h"

static const unsigned char scales[7][7] = {
    {0, 2, 4, 5, 7, 9, 11}, {0, 2, 3, 5, 7, 9, 10},
    {0, 1, 3, 5, 7, 8, 10}, {0, 2, 4, 6, 7, 9, 11},
    {0, 2, 4, 5, 7, 9, 10}, {0, 2, 3, 5, 7, 8, 10},
    {0, 1, 3, 5, 6, 8, 10}
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
scale_interval(unsigned int mode, unsigned int degree, unsigned int step)
{
    unsigned int position = degree + step;
    return 12u * (position / 7u) + scales[mode][position % 7u]
         - scales[mode][degree];
}

static __attribute__((noinline)) unsigned int
harmonic_family(unsigned int mode, unsigned int degree)
{
    if (scale_interval(mode, degree, 4) == 6)
        return DIMINISHED;
    if (scale_interval(mode, degree, 2) == 3)
        return MINOR;
    return scale_interval(mode, degree, 6) == 11 ? MAJOR : DOMINANT;
}

/* Un appel séparé évite de dépasser les masques de sprites de 376 octets. */
static __attribute__((noinline)) void
diatonic_intervals(unsigned int mode, unsigned int degree,
                    unsigned int extension, unsigned int notes[4])
{
    unsigned int i;
    for (i = 0; i < 4; ++i)
        notes[i] = scale_interval(mode, degree, positions[extension][i]);
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
        notes[0] += 12;
        sort_notes(notes, count);
    }
    if (index >= 5) {
        for (i = 1; i < count; i += 2)
            notes[i] += 12;
        sort_notes(notes, count);
    }
}
