/* Pas tenu + MACHINES (notes/86 §7), dans les masques de sprite libérés 0x4018d918 (41x41, 328 o) et 0x4016ea78
 * (52x22, 208 o) (tools/sprites.py). */
SECTIONS
{
  .cave 0x4018d918 : {
    *(.text.trig_machines)
  }
  .cave2 0x4016ea78 : {
    *(.text.mt_side)
  }
  /DISCARD/ : { *(.comment) *(.note*) *(.eh_frame*) }
}
