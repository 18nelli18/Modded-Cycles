/* Meme ABI volatile que le dessinateur MACRO ; autres machines deleguees. */
.text
.globl bf_draw
bf_draw:
 lea -16(%sp),%sp
 movem.l %d0-%d1/%a0-%a1,(%sp)
 jsr bf_active
 tst.l %d0
 bne 1f
 jsr bf_original_draw
 tst.l %d0
 beq 2f
 move.l %d0,12(%sp)
 movem.l (%sp),%d0-%d1/%a0-%a1
 lea 16(%sp),%sp
 jmp (%a1)
2:
 movem.l (%sp),%d0-%d1/%a0-%a1
 lea 16(%sp),%sp
 rts
1:
 movem.l (%sp),%d0-%d1/%a0-%a1
 lea 16(%sp),%sp
 jmp bf_draw_text
