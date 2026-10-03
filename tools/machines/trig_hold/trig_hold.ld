/* Plus de temps pour effacer un trig (notes/33), au début du masque de sprite libéré 0x4015c044 (tools/sprites.py).
 * 6ch-usbup en occupe le milieu (0x4015c116..0x4015c23a) : la zone va jusqu'à 0x4015c116 (210 o).
 * Les heures d'appui (.data) sont écrites à zéro dans l'image. */
SECTIONS
{
  .cave 0x4015c044 : {
    *(.text.trig_hold) . = ALIGN(2); *(.data.trig_hold)
  }
  /DISCARD/ : { *(.comment) *(.note*) *(.eh_frame*) }
}
