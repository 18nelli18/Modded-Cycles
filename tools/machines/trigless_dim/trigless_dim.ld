/* Trigless trigs atténués (notes/45), dans un masque de sprite 47x47 libéré (notes/14 §5, tools/sprites.py) :
 * 0x4018dba8 (376 o). L'état (.data) est écrit à zéro dans l'image : cette zone n'est pas remise à zéro au
 * démarrage. */
SECTIONS
{
  .cave 0x4018dba8 : {
    *(.text.td) . = ALIGN(4); *(.data.td)
  }
  /DISCARD/ : { *(.comment) *(.note*) *(.eh_frame*) }
}
