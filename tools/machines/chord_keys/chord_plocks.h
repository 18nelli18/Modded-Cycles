#ifndef CHORD_PLOCKS_H
#define CHORD_PLOCKS_H

/* Voie de lock inutilisée par les six machines et Model-TG : 0 repos, 1..6 T1..T6.
 * Model-TG réserve les mots son 26/27 pour le Sampler, jamais p-lockés.
 * Son miroir audio ne les lit pas ; HARMONY ne modifie pas ces mots du son.
 * LFO 2 réserve les voies 28..32.
 * L'identifiant disque 33 reste celui des anciens patterns Chord Keys.
 */
#define CK_HARMONY_SLOT 27
#define CK_HARMONY_ID 33
#ifndef __ASSEMBLER__
void ck_plock_gesture(unsigned track, unsigned modifier);
unsigned ck_plock_grid(unsigned track, unsigned modifier);
void ck_plock_note(void *track_object, unsigned track, unsigned step);
#endif

#endif
