/* Presentation/cycle de vie du popup : relais du support projet MIT (beat_repeat/popup.s). */
.text
.globl cr_show
cr_show:
 linkw %fp,#-28
 moveml %d2-%d3/%a2,(%sp)
 move.l 0x40fe4178,%d0
 beq cr_show_out
 lea 0x400802e0,%a2
 move.l %fp,%d2
 add.l #-12,%d2
 pea -13(%fp)
 pea cr_empty
 move.l %d2,-(%sp)
 jsr 0x400f980c
 lea 12(%sp),%sp
 pea 160
 jsr (%a2)
 addq.l #4,%sp
 move.l %d0,%d3
 move.l %d2,-(%sp)
 move.l %d3,-(%sp)
 jsr 0x400747c0
 addq.l #8,%sp
 move.l 8(%fp),-(%sp)
 move.l %d3,-(%sp)
 jsr cr_popup_bind
 addq.l #8,%sp
 move.l %d3,-8(%fp)
 clr.l -4(%fp)
 pea 16
 jsr (%a2)
 addq.l #4,%sp
 move.l %d0,%a0
 moveq #1,%d0
 move.l %d0,4(%a0)
 move.l #0x400fbf40,(%a0)
 move.l %d0,8(%a0)
 move.l %d3,12(%a0)
 move.l %a0,-4(%fp)
 jsr 0x400d0974
 move.l %d0,-(%sp)
 jsr 0x400060d8
 addq.l #4,%sp
 clr.l -(%sp)
 pea -8(%fp)
 move.l %d0,-(%sp)
 jsr 0x4007700e
 lea 12(%sp),%sp
 pea -4(%fp)
 jsr 0x400cf23c
 addq.l #4,%sp
 move.l %d2,-(%sp)
 jsr 0x400f7d5c
 addq.l #4,%sp
cr_show_out:
 moveml -28(%fp),%d2-%d3/%a2
 unlk %fp
 rts
.section .rodata
cr_empty: .asciz " "
