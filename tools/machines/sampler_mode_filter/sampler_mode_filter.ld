/* Filtre et Résonance de piste pour le Sampler en modes Granular/Stretch/Pluck/Wave (notes/83),
 * dans le masque de sprite 48x22 libéré 0x4016bcd8 (tools/sprites.py) : 192 o. */
SECTIONS
{
  .cave 0x4016bcd8 : {
    *(.text.sampler_mode_filter)
  }
  /DISCARD/ : { *(.comment) *(.note*) *(.eh_frame*) }
}
