/* Keep Step Recorder and its hooks in the verified free tail of the fixed main beat-repeat payload.
 * The host loader zero-fills this space before copying its pieces, so sr_active starts false. */
SECTIONS
{
  .steprec 0x467ada5e : {
    *(.bss.sr_active) *(.data.sr_active)
    *(.text*) *(.rodata*) *(.data*)
    . = ALIGN(2); SHORT(0)
  }
  .ram 0x4233e800 (NOLOAD) : { *(.bss*) *(COMMON) *(.data*) }
  /DISCARD/ : { *(.comment) *(.note*) *(.eh_frame*) }
}
