#ifndef CHORD_UI_H
#define CHORD_UI_H

/* Interface du mode accords (notes/40). Ces deux adaptateurs appartiennent au
 * stockage : get rend un mot valide, ou OFF / do3 / majeur / triades par défaut ;
 * set sauvegarde, signale le changement et publie le mot pour le moteur audio.
 * Mot : actif31, mode28..30, tonique21..27, extensions I..VII sur trois bits.
 */
unsigned ck_ui_config_get(unsigned track);
void ck_ui_config_set(unsigned track, unsigned word);

/* La révision s'applique au pattern entier ; les pads restent par piste.
 * Le schéma historique ne réinterprète jamais les anciens COLOR/SHAPE/locks.
 */
unsigned ck_ui_revision_get(void);
void ck_ui_revision_set(unsigned revision);
unsigned ck_ui_pad_mode_get(unsigned track);
void ck_ui_pad_mode_set(unsigned track, unsigned harmony);
void *ck_ui_header(void);

/* Modificateurs éphémères : 0 aucun, 1..6 T1..T6. header est celui du
 * pattern réellement lu, pour ne pas appliquer un geste à un autre pattern.
 */
unsigned ck_ui_modifier_get(unsigned track, const void *header);
void ck_ui_clear_modifiers(unsigned track, const volatile void *header);
void ck_ui_clear_header(const volatile void *header);
unsigned ck_ui_modifier_unavailable(unsigned track);
unsigned ck_ui_pad(void *view, unsigned char *event);

/* Pointeur de KeyboardView 0x400ff9cc, repli vers 0x4001a0d2.
 * KeyEvent : code +12 (16..31), indicateurs +16.
 */
unsigned ck_ui_key(void *view, unsigned char *event);

/* Appel du constructeur en 0x4001cb3e : constructeur stock puis lignes ajoutées. */
void ck_ui_menu_ctor(void *view);

/* Libère les notes encore actives ; conserve les identités physiques jusqu'au
 * relâchement, pour que celui-ci ne soit pas réinterprété par le mode stock.
 */
void ck_ui_cancel_track(unsigned track);

#endif
