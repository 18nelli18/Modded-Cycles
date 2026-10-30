/* Lo-fi de piste (notes/86), dans huit masques de sprite 48x22 libérés (tools/sprites.py) : 192 o chacun. */
SECTIONS
{
  .cave 0x4015943c : {
    *(.text.track_lofi)
  }
  .cave2 0x4015f38c : {
    *(.text.tl_fmt)
  }
  .cave3 0x40165fec : {
    *(.text.tl_draw)
  }
  .cave4 0x40168da4 : {
    *(.text.tl_post)
  }
  .cave5 0x4016dab8 : {
    *(.text.tl_trk)
  }
  .cave6 0x4016fae8 : {
    *(.text.tl_data)
  }
  .cave7 0x40170c48 : {
    *(.text.tl_par)
  }
  .cave8 0x40171a48 : {
    *(.text.tl_step)
  }
  /DISCARD/ : { *(.comment) *(.note*) *(.eh_frame*) }
}
