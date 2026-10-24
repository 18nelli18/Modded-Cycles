/* ABI du routeur encodeurs et du processeur reverb conservee. */
.text
.globl ch_encoder_hook,ch_fx
ch_encoder_hook:
 lea -16(%sp),%sp
 movem.l %d0-%d1/%a0-%a1,(%sp)
 move.l 24(%sp),-(%sp)
 jsr ch_encoder
 addq.l #4,%sp
 tst.l %d0
 beq 1f
 movem.l (%sp),%d0-%d1/%a0-%a1
 lea 16(%sp),%sp
 moveq #1,%d0
 rts
1:movem.l (%sp),%d0-%d1/%a0-%a1
 lea 16(%sp),%sp
 jmp ch_previous_encoder
ch_fx:
 move.l 12(%sp),-(%sp)
 move.l 12(%sp),-(%sp)
 move.l 12(%sp),-(%sp)
 jsr ch_process
 lea 12(%sp),%sp
 move.l #0xa0,%d0
 move.l %d0,%macsr
 movclr.l %acc0,%d0
 movclr.l %acc1,%d0
 movclr.l %acc2,%d0
 movclr.l %acc3,%d0
 rts
