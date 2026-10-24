/* Contrat wt_note : tous les registres originaux sauvegardes, lane a64(SP).
 * Rejouer le prologue detourne puis laisser le code natif restaurer la pile. */
.text
.globl wave_original_update
wave_original_update:
 lea -64(%sp),%sp
 movem.l %d2-%d7/%a2-%a6,(%sp)
 jmp 0x46779008
.globl wave_native_browser_key
wave_native_browser_key:
 link.w %a6,#-116
 movem.l %d2-%d7/%a2-%a5,(%sp)
 jmp 0x400a6d64
/* Meme cadre que PresetManager::key, entree directe dans son chemin parent.
 * D3=1 marque l evenement consomme ; la sortie native restaure le cadre. */
.globl wave_parent_navigation
wave_parent_navigation:
 link.w %a6,#-116
 movem.l %d2-%d7/%a2-%a5,(%sp)
 move.l 12(%a6),%d2
 move.l 8(%a6),%a2
 moveq #1,%d3
 jmp 0x400a6f8c
.globl wave_starter_note
wave_starter_note:
 lea -60(%sp),%sp
 movem.l %d0-%d7/%a0-%a6,(%sp)
 move.l 64(%sp),-(%sp)
 jsr wave_allow_pad_import
 addq.l #4,%sp
 jmp 0x4677a758
