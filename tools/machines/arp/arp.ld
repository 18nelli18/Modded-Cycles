/* Arpégiateur (notes/32), dans deux masques de sprites libérés (notes/14 §5, tools/sprites.py) :
 *   - 0x4018a788 (1 024 o) : la partie audio et son état ;
 *   - 0x4016cba8..0x4016cee8 (832 o) : le menu. Le début de ce masque (0x4016cae8, 188 o au plus) garde le crochet de
 *     démarrage des moteurs du Syntakt, qui libèrent le même masque (même écriture de pointeur).
 * L'état (.data, .bss) est écrit à zéro dans l'image : ces zones ne sont pas remises à zéro au démarrage. */
SECTIONS
{
  .cave_audio 0x4018a788 : {
    *(.text.audio_hook) *(.text.arp_filter) *(.text.arp_copy) *(.text.beyond) *(.text.cfg_audio) *(.text.mode_of)
    . = ALIGN(4);
    *(.data.seed) *(.bss.st) *(.data.st)
  }
  .cave_menu 0x4016cba8 : {
    *(.text.menu_hook) *(.text*) . = ALIGN(4); *(.rodata*) *(.data*) *(.bss*) *(COMMON)
  }
  /DISCARD/ : { *(.comment) *(.note*) *(.eh_frame*) }
}
