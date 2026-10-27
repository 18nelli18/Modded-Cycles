.text
.globl fc_dispatch
fc_dispatch:
 move.l 8(%sp),%d0
 cmpi.l #6,%d0
 bcc.s 2f
 lea fc_type,%a0
 tst.l (%a0,%d0.l*4)
 bne.s 1f
 jmp fc_low
1: jmp fc_filter
2: rts
