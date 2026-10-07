/* Écoute des samples (notes/45), dans quatre masques de sprites 47x47 libérés (376 o chacun, tools/sprites.py) :
 *   - 0x4018cd48 : la copie audio (pv_copy), la table des copies et les copies des pistes 1 et 2 ;
 *   - 0x4018d1b8 : les copies des pistes 3 à 5 ;
 *   - 0x4018d4a8 : la note jouée (pv_note) et la copie de la piste 6 ;
 *   - 0x4018dba8 : le navigateur (pv_parse) et le son écouté qu'il construit.
 * Les données sont écrites dans l'image : ces zones ne sont pas remises à zéro au démarrage. */
SECTIONS
{
  .cave1 0x4018cd48 : { *(.text.pv_copy) . = ALIGN(4); *(.data.pv_tab) *(.data.pv_b01) }
  .cave2 0x4018d1b8 : { *(.data.pv_b234) }
  .cave3 0x4018d4a8 : { *(.text.pv_note) . = ALIGN(4); *(.data.pv_b5) }
  .cave4 0x4018dba8 : { *(.text.pv_parse) . = ALIGN(4); *(.data.pv_src) }
  /DISCARD/ : { *(.text) *(.data) *(.bss) *(.comment) *(.note*) *(.eh_frame*) }
}
