/* Écoute des samples au casque (notes/48), dans cinq masques de sprites 48x22 libérés (192 o chacun,
 * tools/sprites.py) :
 *   - 0x40152d38 : la note jouée (cue_dec) et le relâchement (cue_off) ;
 *   - 0x401592bc : le départ de l'écoute (cue_start), le son désigné et le chargement (cue_arm, cue_load) ;
 *   - 0x4015943c : le lecteur dans l'interruption audio, début (cue_out) ;
 *   - 0x4015f38c : le lecteur, la boucle des échantillons (cue_play) ;
 *   - 0x40165fec : les appuis tenus (cue_held) et les données.
 * Les données sont écrites dans l'image : ces zones ne sont pas remises à zéro au démarrage. */
SECTIONS
{
  .cave1 0x40152d38 : { *(.text.cue_dec) . = ALIGN(2); *(.text.cue_off) }
  .cave2 0x401592bc : { *(.text.cue_start) . = ALIGN(2); *(.text.cue_arm) }
  .cave3 0x4015943c : { *(.text.cue_out) }
  .cave4 0x4015f38c : { *(.text.cue_play) }
  .cave5 0x40165fec : { *(.text.cue_held) . = ALIGN(4); *(.data.cue) }
  /DISCARD/ : { *(.text) *(.data) *(.bss) *(.comment) *(.note*) *(.eh_frame*) }
}
