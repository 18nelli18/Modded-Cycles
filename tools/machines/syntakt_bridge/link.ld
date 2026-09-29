/* Passerelle Syntakt (notes/17) : le crochet de demarrage dans un masque de sprite libere de l'image,
 * la passerelle et ses donnees dans la charge utile copiee en SDRAM a 0x46061000. */
SECTIONS
{
  .stub 0x4016cae8 : { *(.text) }
  .bridge 0x46061000 : { *(.text.bridge_update) *(.text.bridge_render) *(.text*) . = ALIGN(4); *(.rodata*) }
  .bridge_data 0x46062000 : { *(.data*) *(.bss*) *(COMMON) }
  /DISCARD/ : { *(.comment) *(.note*) *(.eh_frame*) }
}
