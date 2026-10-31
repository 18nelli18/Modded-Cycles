/* Fenêtre de valeur d'Attack, du Filtre et de la Résonance (notes/82), dans deux masques de sprite 48x22 libérés
 * (tools/sprites.py) : 0x401592bc (192 o) pour la fenêtre, 0x40168a84 (192 o) pour le texte de la valeur
 * enregistrée. */
SECTIONS
{
  .cave 0x401592bc : {
    *(.text.popup_view)
  }
  .cave2 0x40168a84 : {
    *(.text.popup_text)
  }
  /DISCARD/ : { *(.comment) *(.note*) *(.eh_frame*) }
}
