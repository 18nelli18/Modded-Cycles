#ifndef CHORD_UI_H
#define CHORD_UI_H

/* Interface du mode accords (notes/40). Ces deux adaptateurs appartiennent au
 * stockage : get rend un mot valide, ou OFF / do3 / majeur / triades par défaut ;
 * set sauvegarde, signale le changement et publie le mot pour le moteur audio.
 * Mot : actif31, mode28..30, tonique21..27, extensions I..VII sur trois bits.
 */
unsigned ck_ui_config_get(unsigned track);
void ck_ui_config_set(unsigned track, unsigned word);

/* Les contrôles améliorés sont permanents, y compris pour les anciens patterns. */
unsigned ck_ui_revision_get(void);
void *ck_ui_header(void);

/* Modificateurs éphémères : 0 aucun, 1..6 T1..T6, conservés au relâchement
 * du pad pour la note courante. Un pad tenu prépare tous les nouveaux appuis
 * TRIG ; une fois relâché, le prochain appui revient à zéro. header est celui du pattern
 * réellement lu, pour ne pas appliquer un geste à un autre pattern.
 */
unsigned ck_ui_modifier_get(unsigned track, const void *header);
unsigned ck_ui_modifier_active(unsigned track, const void *header);
void ck_ui_clear_modifiers(unsigned track, const volatile void *header);
void ck_ui_clear_header(const volatile void *header);
unsigned ck_ui_modifier_unavailable(unsigned track);
unsigned ck_ui_pad(void *view, unsigned char *event);

/* Entrée KeyboardView 0x4001a0d2 ; repli par trampoline vers 0x4001a0da.
 * La vtable 0x400ff9cc et son éventuel relais Model-TG restent intacts.
 * KeyEvent : code +12 (16..31), indicateurs +16.
 */
unsigned ck_ui_key(void *view, unsigned char *event);

/* Appel du constructeur en 0x4001cb3e : constructeur stock puis lignes ajoutées. */
void ck_ui_menu_ctor(void *view);

/* Libère les notes encore actives ; conserve les identités physiques jusqu'au
 * relâchement, pour que celui-ci ne soit pas réinterprété par le mode stock.
 */
void ck_ui_cancel_track(unsigned track);

/* Indice de la dernière touche encore sonore de la piste, ou 16 si aucune. */
unsigned ck_ui_active_key(unsigned track);
unsigned ck_ui_active_note(unsigned track);
unsigned ck_ui_has_active_note(void);

#endif
