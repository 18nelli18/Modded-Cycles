#ifndef CHORD_PLOCKS_H
#define CHORD_PLOCKS_H

/* Voie native inutilisée par les six machines : 0 repos, 1..6 T1..T6.
 * Les hooks de sérialisation associent ce slot RAM à l'identifiant disque 33.
 */
#define CK_HARMONY_SLOT 23u
void ck_plock_gesture(unsigned track, unsigned modifier);
unsigned ck_plock_grid(unsigned track, unsigned modifier);
void ck_plock_note(void *track_object, unsigned track, unsigned step);

#endif
