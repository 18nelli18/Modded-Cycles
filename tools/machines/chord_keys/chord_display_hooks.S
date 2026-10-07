/* Dernier dessin avant l'envoi au LCD, OS 1.13 (notes/40).
 * 0x4008e622 : lea -40(sp),sp ; movem.l d2-d6/a2-a4,(sp).
 * Préserver tous les registres volatils du C, puis rejouer ce prologue exact
 * et continuer en 0x4008e62a. Le flush, le DSPI et l'échange restent stock.
 */
    .section .text.ck_chord_display_hook,"ax"
    .globl ck_chord_display_hook
ck_chord_display_hook:
    lea -16(%sp),%sp
    movem.l %d0-%d1/%a0-%a1,(%sp)
    jsr ck_chord_display_draw
    movem.l (%sp),%d0-%d1/%a0-%a1
    lea 16(%sp),%sp
    lea -40(%sp),%sp
    movem.l %d2-%d6/%a2-%a4,(%sp)
    jmp 0x4008e62a
