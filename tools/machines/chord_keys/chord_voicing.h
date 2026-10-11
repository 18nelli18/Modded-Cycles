#ifndef CHORD_VOICING_H
#define CHORD_VOICING_H

/* SHAPE signé 8.8 : BASE, CLS0..3, OPN0..3. */
unsigned int ck_voicing_index(int shape_q8);
void ck_voicing_apply(unsigned int notes[4], unsigned int count, unsigned int index);

enum ck_palette {
    CK_PALETTE_DIATONIC,
    CK_PALETTE_JAZZ,
    CK_PALETTE_TENSION,
    CK_PALETTE_COUNT
};

enum ck_transform {
    CK_TRANSFORM_NONE,
    CK_TRANSFORM_NINTH,
    CK_TRANSFORM_ELEVENTH,
    CK_TRANSFORM_THIRTEENTH,
    CK_TRANSFORM_SUS7,
    CK_TRANSFORM_PARALLEL,
    CK_TRANSFORM_V7,
    CK_TRANSFORM_COUNT
};

/* COLOR signé 8.8 : 0..42 DIATONIC, 43..85 JAZZ, 86..127 TENSION. */
unsigned int ck_palette_index(int color_q8);

/* Réservé au nouveau mode ; le chemin historique conserve ses propres calculs.
 * mode/degré 0..6, extension TRI/7/9/11/13 = 0..4. Renvoie 3/4 voix ou zéro
 * pour un argument invalide, PARALLÈLE ou V7 sur un accord diminué. En cas de
 * refus, intervals reste intact. Les intervalles sont relatifs à la cible,
 * donc V7 commence à +7 ; les cases inutilisées valent zéro.
 * m7b5 étendu : fondamentale, quinte diminuée, septième, tension (sans tierce).
 * PARALLÈLE DIATONIC emploie les tensions du mode ionien/éolien de la famille
 * obtenue. Les gestes chromatiques explicites peuvent sortir du mode choisi.
 */
unsigned int ck_harmony_intervals(unsigned int mode, unsigned int degree,
                                  unsigned int extension, unsigned int palette,
                                  unsigned int transform, unsigned int intervals[4]);

/* Gain relatif Q15 par registre après disposition, BASE = 32768. La racine
 * native n'a pas de gain propre : voix 0 toujours intacte. Les autres voix
 * actives restent entre 22528 et 32768 ; voix inutilisées muettes.
 */
unsigned int ck_voicing_gain(unsigned int index, unsigned int voice,
                             unsigned int count);

#endif
