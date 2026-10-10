/* Accord diatonique dans le véritable update CHORD de l'OS 1.13 (notes/40).
 * Le réglage SHAPE est remplacé dans une copie locale des paramètres ; l'OS
 * conserve enveloppes, timbre et Pitch/Fine. COLOR choisit toujours la palette,
 * SHAPE la disposition et la balance des voix.
 * Aucun état de calcul partagé : chaque appel possède sa propre pile.
 */
#include "chord_audio.h"
#include "chord_voicing.h"
#include "chord_display.h"
#include "chord_plocks.h"

/* Trampoline du prologue stock, évite de repasser par le détournement d'entrée. */
extern void chord_audio_original(int pitch_q16, void *voice, const unsigned short *params);

struct chord_audio_frame {
    unsigned short params[34]; /* 33 mots OS, puis deux octets d'alignement. */
    unsigned int ratios[4];
    unsigned int active;
    unsigned int count;
    unsigned int controls;
    unsigned int voicing;
    unsigned int snapshot;
};

_Static_assert(__builtin_offsetof(struct chord_audio_frame, ratios) == CK_AUDIO_RATIOS_OFFSET,
               "offset des rapports");
_Static_assert(__builtin_offsetof(struct chord_audio_frame, active) == CK_AUDIO_ACTIVE_OFFSET,
               "offset du marqueur");
_Static_assert(__builtin_offsetof(struct chord_audio_frame, count) == CK_AUDIO_COUNT_OFFSET,
               "offset du nombre de voix");
_Static_assert(sizeof(struct chord_audio_frame) == 104, "taille de la copie locale");

/* Mêmes modes et voicings que le noyau portable chord_keys.c, vérifiés par les
 * preuves du noyau et de l'audio ; aucun calcul flottant dans l'interruption.
 */
/* Table inverse des gammes : 7 marque une note hors gamme. */
static const unsigned char degrees[7][12] = {
    {0, 7, 1, 7, 2, 3, 7, 4, 7, 5, 7, 6},
    {0, 7, 1, 2, 7, 3, 7, 4, 7, 5, 6, 7},
    {0, 1, 7, 2, 7, 3, 7, 4, 5, 7, 6, 7},
    {0, 7, 1, 7, 2, 7, 3, 4, 7, 5, 7, 6},
    {0, 7, 1, 7, 2, 3, 7, 4, 7, 5, 6, 7},
    {0, 7, 1, 2, 7, 3, 7, 4, 5, 7, 6, 7},
    {0, 1, 7, 2, 7, 3, 4, 7, 5, 7, 6, 7}
};

/* round(2**(n / 12) * 2**26), n = 0..23. Pour 24..35, conserver
 * exactement le double des entrées 12..23, y compris leur arrondi historique.
 * Toutes les dispositions restent dans 0..35 : aucun calcul d'octave au bloc.
 */
static const unsigned int semitone_ratios[36] = {
    67108864u, 71099365u, 75327153u, 79806339u,
    84551870u, 89579586u, 94906266u, 100549686u,
    106528681u, 112863206u, 119574402u, 126684666u,
    134217728u, 142198729u, 150654306u, 159612677u,
    169103741u, 179159172u, 189812531u, 201099372u,
    213057363u, 225726413u, 239148804u, 253369332u,
    268435456u, 284397458u, 301308612u, 319225354u,
    338207482u, 358318344u, 379625062u, 402198744u,
    426114726u, 451452826u, 478297608u, 506738664u
};

static void __attribute__((noinline))
prepare_intervals(struct chord_audio_frame *frame, unsigned int mode,
                  unsigned int degree, unsigned int extension,
                  unsigned int note)
{
    unsigned int i, intervals[4], unvoiced[4];
    unsigned int palette = ck_palette_index((short)frame->params[11]);
    unsigned int count = ck_harmony_intervals(mode, degree, extension, palette,
                                             frame->controls >> 8, intervals);
    /* Une transformation indisponible conserve l'accord de repos. */
    if (!count)
        count = ck_harmony_intervals(mode, degree, extension, palette, 0, intervals);
    frame->count = count;
    frame->params[11] = 32u << 8;
    for (i = 0; i < 4; ++i)
        unvoiced[i] = intervals[i];
    frame->voicing = ck_voicing_index((short)frame->params[12]);
    ck_voicing_apply(intervals, frame->count, frame->voicing);
    frame->snapshot = ck_chord_packet(note, unvoiced, count, intervals[0]);
    for (i = 0; i < 4; ++i)
        frame->ratios[i] = semitone_ratios[intervals[i]];
    frame->params[12] = 7u << 8;
    frame->active = 1;
}

static void __attribute__((noinline))
chord_audio_prepare(struct chord_audio_frame *frame, unsigned int cfg, unsigned int note)
{
    unsigned int mode = (cfg >> 28) & 7u;
    unsigned int relative, degree, extension;
    if (!(cfg & 0x80000000u) || mode >= 7)
        return;
    /* 144 est un multiple de douze supérieur à toute tonique encodée :
     * même classe relative sans reste intermédiaire ni soustraction négative.
     */
    relative = (note + 144u - ((cfg >> 21) & 127u)) % 12u;
    degree = degrees[mode][relative];
    /* Une note extérieure à la gamme reste un accord SHAPE stock. */
    if (degree == 7)
        return;
    extension = (cfg >> (3 * degree)) & 7u;
    if (extension >= 5)
        return;
    prepare_intervals(frame, mode, degree, extension, note);
}

static void __attribute__((noinline))
apply_balance(void *voice, const struct chord_audio_frame *frame)
{
    unsigned int i;
    for (i = 1; i < frame->count; ++i) {
        unsigned int *gain = (unsigned int *)voice + 2 + i;
        unsigned int weight = ck_voicing_gain(frame->voicing, i, frame->count);
        /* Ne jamais réactiver une voix coupée par la protection aiguë stock.
         * La multiplication tient sur 32 bits ; BASE garde le gain exact.
         */
        if (weight != 32768u)
            *gain = (*gain >> 15) * weight;
    }
}

static void __attribute__((noinline))
publish_chord(unsigned int track, const void *voice, const struct chord_audio_frame *frame)
{
    const unsigned int *words = voice;
    unsigned int i, packet = frame->snapshot;
    /* Le nom indique l'harmonie demandée ; prévenir si la protection native
     * a coupé une voix ou plafonné la fréquence de l'opérateur principal.
     * Publier une seule fois le résultat final, après l'update et la balance.
     */
    if (words[0x70 / 4] == 0x000bd2f1u)
        packet |= CK_CHORD_LIMITED;
    for (i = 1; i < frame->count; ++i)
        if (!words[2 + i])
            packet |= CK_CHORD_LIMITED;
    ck_chord_live[track] = packet;
}

void chord_audio_update(int pitch_q16, void *voice, const unsigned short *params)
{
    struct chord_audio_frame frame;
    unsigned int i, track = 0;
    unsigned int voice_offset = (unsigned int)voice - 0x42308828u;
    int note = pitch_q16 >> 16;

    /* La copie existe AUSSI en mode inactif : le crochet interne peut toujours
     * lire son marqueur, sans dépasser le tableau de paramètres natif.
     */
    /* Quatre mots par tour, sans imposer un alignement long aux paramètres
     * natifs (pas de 66 octets). Le dernier mot reste lu une seule fois.
     */
    for (i = 0; i < 32; i += 4) {
        frame.params[i] = params[i];
        frame.params[i + 1] = params[i + 1];
        frame.params[i + 2] = params[i + 2];
        frame.params[i + 3] = params[i + 3];
    }
    frame.params[32] = params[32];
    frame.active = 0;
    frame.controls = 0;

    /* Six soustractions au plus, sans division ou appel à une bibliothèque. */
    while (voice_offset >= 0x31cu && track < 6) {
        voice_offset -= 0x31cu;
        ++track;
    }
    if (track < 6 && voice_offset == 0 && note >= 0 && note <= 127) {
        unsigned int cfg = ck_audio_config(track);
        /* L'update natif borne la fondamentale MIDI à 96. Choisir le degré
         * et publier le nom depuis cette même note, y compris pour 97..127.
         * Le pitch Q16 original reste confié à l'accordage natif de l'OS.
         */
        if (note > 96)
            note = 96;
        if (cfg & 0x80000000u)
            frame.controls = ck_audio_locked_controls(track, params[CK_HARMONY_SLOT]);
        chord_audio_prepare(&frame, cfg, (unsigned int)note);
        if (!frame.active)
            ck_chord_live[track] = 0;
    }

    /* Au-delà du seuil aigu, l'OS garde l'ancien incrément de l'opérateur 0,
     * contrairement aux autres voix qu'il rend muettes. Préparer son plafond
     * évite une note périmée avec les inversions ; en plage normale, l'update
     * le réécrit. Conversion stock : ((0x454800 * 0x57619f10) >> 31) >> 2.
     */
    if (frame.active)
        ((unsigned int *)voice)[0x70 / 4] = 0x000bd2f1u;
    chord_audio_original(pitch_q16, voice, frame.params);
    /* BASE ne change aucun gain actif ; la quatrième voix d'une triade est
     * déjà coupée ci-dessous. Éviter ses trois appels de balance neutres.
     */
    if (frame.active && frame.voicing)
        apply_balance(voice, &frame);
    if (frame.active && frame.count == 3)
        ((unsigned int *)voice)[5] = 0; /* Triade : quatrième opérateur inaudible. */
    if (frame.active)
        publish_chord(track, voice, &frame);
}
