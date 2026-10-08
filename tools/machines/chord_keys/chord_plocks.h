#ifndef CHORD_PLOCKS_H
#define CHORD_PLOCKS_H

/* Voie native inutilisée par les six machines et Model-TG : 0 repos, 1..6 T1..T6.
 * Model-TG réserve 23..27 (Attack, Filter, Resonance et état Sampler).
 * L'identifiant disque 33 reste celui des anciens patterns Chord Keys.
 */
#define CK_HARMONY_SLOT 28
#define CK_HARMONY_ID 33
#ifndef __ASSEMBLER__
void ck_plock_gesture(unsigned track, unsigned modifier);
unsigned ck_plock_grid(unsigned track, unsigned modifier);
void ck_plock_note(void *track_object, unsigned track, unsigned step);
#endif

#endif
