/* Arpégiateur (notes/32), dans des masques de sprites libérés (notes/14 §5, tools/sprites.py) :
 *   - 0x4018a788 (1 024 o) : la partie audio ;
 *   - 0x4016cba8..0x4016cee8 (832 o) : le menu. Le début de ce masque (0x4016cae8, 188 o au plus) garde le crochet de
 *     démarrage des moteurs du Syntakt, qui libèrent le même masque (même écriture de pointeur) ;
 *   - 0x40189930 et 0x4018a220 (376 o chacun, masques de deux sprites 47x47, notes/32 §11) : le live rec et l'état.
 * L'état (.data, .bss) est écrit à zéro dans l'image : ces zones ne sont pas remises à zéro au démarrage. */
SECTIONS
{
  .cave_audio 0x4018a788 : {
    *(.text.audio_hook) *(.text.arp_filter) *(.text.arp_copy) *(.text.beyond) *(.text.mode_of) *(.text.arp_rate)
    *(.text.track_data)
  }
  .cave_rec1 0x40189930 : {
    *(.text.post) *(.text.live_rec) *(.text.post_hook) *(.text.arp_ui_post)
  }
  .cave_rec2 0x4018a220 : {
    *(.text.rec)
    . = ALIGN(4);
    *(.data.seed) *(.bss.ui_cfg) *(.data.ui_cfg) *(.bss.st) *(.data.st) *(.bss.ring) *(.bss.ring_i)
  }
  .cave_menu 0x4016cba8 : {
    *(.text.menu_hook) *(.text*) . = ALIGN(4); *(.rodata*) *(.data*) *(.bss*) *(COMMON)
  }
  /DISCARD/ : { *(.comment) *(.note*) *(.eh_frame*) }
}
