.text
.globl lp1_widget_get,lp_label,lp2_value,lp1_key_sub,lp1_encoder_sub
lp1_key_sub:
 moveq #-56,%d0
 add.l %d0,4(%sp)
 jmp lp1_key
lp1_encoder_sub:
 moveq #-60,%d0
 add.l %d0,4(%sp)
 jmp lp1_encoder
lp1_widget_get:
 lea -8(%sp),%sp
 movem.l %d2/%a2,(%sp)
 move.l %a0,%a2
 move.l 16(%sp),%d2
 move.l 12(%sp),-(%sp)
 jsr lp1_old_count
 addq.l #4,%sp
 cmp.l %d0,%d2
 bne.s 1f
 move.l 12(%sp),-(%sp)
 jsr lp1_prepare
 addq.l #4,%sp
 move.l %d0,(%a2)
 clr.l 4(%a2)
 movem.l (%sp),%d2/%a2
 lea 8(%sp),%sp
 rts
1: move.l %a2,%a0
 movem.l (%sp),%d2/%a2
 lea 8(%sp),%sp
 jmp lp1_old_widget
lp_label:
 subq.l #4,%sp
 pea 3(%sp)
 pea lp_pol_text
 move.l %a0,-(%sp)
 jsr 0x400f980c
 lea 16(%sp),%sp
 rts
lp2_value:
 move.l 4(%sp),%a0
 moveq #9,%d0
 cmp.l (%a0),%d0
 beq.s 2f
 jmp lf2l_value
2: jmp lp2_pol_value
.section .rodata
.balign 4
.long 4,4,-1
lp_pol_text: .asciz "Pol."
