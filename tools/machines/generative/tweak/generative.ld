/* SPDX-License-Identifier: MIT — Copyright (c) 2026 Combust. Voir ../LICENSE. */
/* Ajouté juste après le bloc de Model-TG, exécuté sur place dans les blocs 5 et 6 retirés du cache du système de
 * fichiers (0x401bf750..0x401c7750), notes/50 §4.1. Partie image : .text/.rodata/.data, jusqu'à ours_res_end (aligné
 * sur 16), que l'effacement du démarrage épargne. La .bss suit ; l'effacement la met à zéro. Tout doit finir
 * avant 0x401c7750 (limite des blocs retirés). */
SECTIONS
{
  . = 0x401bf8c0;
  .text : { *(.text.boot) *(.text.key) *(.text*) *(.rodata*) . = ALIGN(4); *(.data*) . = ALIGN(16); }
  ours_res_end = .;
  .bss (NOLOAD) : { *(.bss*) *(COMMON) . = ALIGN(16); }
  ours_end = .;
  ASSERT(ours_end <= 0x401c7750, "au-delà des blocs 5 et 6 retirés du cache")
  /DISCARD/ : { *(.comment) *(.note*) *(.eh_frame*) }
}
