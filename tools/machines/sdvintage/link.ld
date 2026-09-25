/* SD VINTAGE : deux masques 0xFF de sprites du MAIN OS 1.13, liberes par
 * tools/sprites.py (le sprite lit alors le masque partage, identique). notes/14 §5. */
SECTIONS
{
  /* masque du sprite 64x128 (damier de test), 1024 o */
  .cave_a 0x4016cae8 : { *(.text.sdv_update) *(.text.note_inc) . = ALIGN(4); *(.rodata.lp_tab) *(.rodata*) }
  /* masque du sprite 64x128 (damier inverse), 1024 o */
  .cave_b 0x4018a788 : { *(.text.sdv_render) *(.text*) }
  /DISCARD/ : { *(.comment) *(.note*) *(.eh_frame*) }
}
