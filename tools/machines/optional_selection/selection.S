.text
.globl opt_increment,opt_dispatch,opt_marks,opt_mask,opt_idle
/* L'entree du dispatch partage garde D0/D1 et tout registre non volatile. */
opt_dispatch:
 cmpi.l #6,%d4
 bcs.w 4f
 lea -8(%sp),%sp
 movem.l %d0-%d1,(%sp)
 move.l %d4,%d0
 subq.l #6,%d0
 cmpi.l #19,%d0
 bcc.s 2f
 move.l opt_mask,%d1
 lsr.l %d0,%d1
 btst #0,%d1
 beq.s 2f
 movem.l (%sp),%d0-%d1
 lea 8(%sp),%sp
 bra.s 4f
2:
 movem.l (%sp),%d0-%d1
 lea 8(%sp),%sp
 movea.l %d3,%a0
 moveq #31,%d0
3: clr.l (%a0)+
 subq.l #1,%d0
 bpl.s 3b
 jmp 0x400a7e24
4:
 cmp.l %d4,%d0
 bcs.s 5f
 jmp 0x46788700
5: jmp 0x400a7e24
opt_increment:
 lea -8(%sp),%sp
 movem.l %a0-%a1,(%sp)
 move.l %d5,-(%sp)
 move.l %d0,-(%sp)
 jsr opt_step
 addq.l #8,%sp
 movem.l (%sp),%a0-%a1
 lea 8(%sp),%sp
 moveq #-1,%d1
 jmp 0x400148bc
/* Reperes compacts pour la liste effectivement installee. */
opt_marks:
 move.l %d3,-(%sp)
 move.l %d2,-(%sp)
 jsr opt_draw_marks
 addq.l #8,%sp
 jmp 0x400a26f2
opt_idle: rts
.section .optmask,"a"
.balign 4
opt_mask: .long 0x7ffff
