.text
.globl lxr178_reset_hook,lxr178_old_reset
/* Meme pile et registres avant le prologue natif ; aucun acces privilegie.
 * Le reset natif reconstruit ses propres flags depuis des constantes. */
lxr178_reset_hook:
 lea -20(%sp),%sp
 movem.l %d0-%d2/%a0-%a1,(%sp)
 move.l 24(%sp),-(%sp)
 jsr lxr178_reset_voice
 addq.l #4,%sp
 movem.l (%sp),%d0-%d2/%a0-%a1
 lea 20(%sp),%sp
 jmp lxr178_old_reset
.balign 4
lxr178_old_reset:
 .space 32

#ifdef ESTUS_CONTROLS
.globl lxr178_ui_old
.balign 4
lxr178_ui_old:
 .space 32
#endif

#ifdef ESTUS_ADVANCED
.globl estus_old_encoder
.balign 4
estus_old_encoder:
 .space 32
#endif
