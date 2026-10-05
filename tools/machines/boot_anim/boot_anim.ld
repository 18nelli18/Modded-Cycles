/* Animation de démarrage (notes/39) : à la place du corps de la tâche d'animation d'origine, 0x40053a6c..0x40053e74
 * (1 032 o). Le seul point d'entrée est l'adresse de la tâche (pea en 0x40053a2e) ; rien d'autre ne pointe dedans. */
SECTIONS
{
  .anim 0x40053a6c : {
    *(.text.boot_anim) . = ALIGN(2); *(.rodata.boot_anim)
  }
  /DISCARD/ : { *(.comment) *(.note*) *(.eh_frame*) }
}
