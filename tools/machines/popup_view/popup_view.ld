/* Fenêtre de valeur d'Attack, du Filtre et de la Résonance (notes/82), dans le masque de sprite 48x22 libéré
 * 0x401592bc (tools/sprites.py) : 192 o. */
SECTIONS
{
  .cave 0x401592bc : {
    *(.text.popup_view)
  }
  /DISCARD/ : { *(.comment) *(.note*) *(.eh_frame*) }
}
