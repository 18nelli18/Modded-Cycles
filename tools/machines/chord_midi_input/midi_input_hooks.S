/* Les detours reprennent les pushes remplaces et les epilogues natifs.
 * Aucun registre volatil du code appelant n'est suppose conserve par jsr.
 */
.text
.globl mi_on_hook,mi_off_hook,mi_pad_hook,mi_reset_hook
.globl mi_receive_on_original,mi_receive_off_original,mi_encoder_hook
mi_receive_on_original:
 lea -36(%sp),%sp
 movem.l %d2-%d7/%a2-%a4,(%sp)
 jmp 0x40081920
mi_receive_off_original:
 lea -24(%sp),%sp
 movem.l %d2-%d6/%a2,(%sp)
 jmp 0x40081602
mi_encoder_hook:
 lea -16(%sp),%sp
 movem.l %d0-%d1/%a0-%a1,(%sp)
 move.l 24(%sp),%sp@-
 jsr mi_encoder_block
 addq.l #4,%sp
 tst.l %d0
 beq.s .Lencoder_native
 movem.l (%sp),%d0-%d1/%a0-%a1
 lea 16(%sp),%sp
 moveq #1,%d0
 rts
.Lencoder_native:
 movem.l (%sp),%d0-%d1/%a0-%a1
 lea 16(%sp),%sp
 jmp mi_encoder_previous
mi_on_hook:
 move.l %d6,%sp@-
 move.l %d5,%sp@-
 /* Apres sept pushes : canal entrant dans le frame natif a sp+68.
  * d2 garde la note brute, d6 sa version percussion/transposee native. */
 move.l 68(%sp),%sp@-
 move.l %d2,%sp@-
 jsr mi_on_received
 addq.l #8,%sp
 jmp 0x40081a24
mi_off_hook:
 move.l %d2,%sp@-
 move.l %d4,%sp@-
 /* Frame natif24o, source puis note/piste : canal+40, note brute+44. */
 move.l 40(%sp),%sp@-
 move.l 48(%sp),%sp@-
 jsr mi_off_received
 addq.l #8,%sp
 jmp 0x400816d0
mi_pad_hook:
 /* Prologue pad_live : d3=piste, header au sp+28, pad au sp+20. */
 move.l %a0,%d0
 cmpi.l #16,%d0
 bcc.s .Lexternal
 pea 16(%a0)
 jsr 0x4007faf4
 addq.l #4,%sp
 tst.l %d0
 bne.s .Lphysical
.Lexternal:
 move.l 28(%sp),%sp@-
 move.l 24(%sp),%sp@-
 move.l %d3,%sp@-
 jsr mi_pad
 lea 12(%sp),%sp
 tst.l %d0
 bne.s .Ldone
 move.l 20(%sp),%d0
 addq.l #1,%d0
 move.l %d0,%sp@-
 move.l %d3,%sp@-
 jsr ck_gesture
 addq.l #8,%sp
.Ldone:
 jmp 0x401602d8
.Lphysical:
 jmp 0x4016025a
mi_reset_hook:
 lea -16(%sp),%sp
 movem.l %d0-%d1/%a0-%a1,(%sp)
 move.l 20(%sp),%sp@-
 jsr mi_reset
 addq.l #4,%sp
 movem.l (%sp),%d0-%d1/%a0-%a1
 lea 16(%sp),%sp
 move.l 4(%sp),%d0
 moveq #9,%d1
 jmp 0x40081a90
