/* Frontiere live : capturer l'ancien FX avant publication, puis appliquer MFT.
 * Copies RAM seulement ; aucun fichier, allocation ou service UI dans l'ISR. */
.text
.globl fl_live
fl_live:
 lea -20(%sp),%sp
 movem.l %d0-%d1/%a0-%a1,(%sp)
 move.w %sr,%d0
 move.l %d0,16(%sp)
 move.w #0x2700,%sr
 move.l (%a1),-(%sp)
 jsr fl_change
 addq.l #4,%sp
 movem.l (%sp),%d0-%d1/%a0-%a1
 jsr fl_old_live
 jsr fl_sync
 move.l 16(%sp),%d0
 move.w %d0,%sr
 movem.l (%sp),%d0-%d1/%a0-%a1
 lea 20(%sp),%sp
 /* Le MOVE natif publiait aussi ces CCR ; X et le niveau IPL sont conserves. */
 tst.l 0x40a7887c
 rts
