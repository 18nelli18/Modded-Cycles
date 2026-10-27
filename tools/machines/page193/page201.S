/* Contrats : A2=pattern, A4=next-step ; D1 pas suivant, D0 preserve.
 * Le second crochet remplace la longueur commune du compteur maitre.
 * Aucun changement du timer, des sous-pas, des files ni des timestamps. */
.text
.globl pl_step_hook,pl_master_hook,pl_menu_tail,pl_label
pl_step_hook:
 lea -12(%sp),%sp
 movem.l %d0/%a0-%a1,(%sp)
 addq.l #1,%d1
#ifdef PAGE_TRACK201
 move.l %d2,-(%sp)
#endif
 move.l %d1,-(%sp)
 move.l %a2,-(%sp)
#ifdef PAGE_TRACK201
 jsr pt_next
 lea 12(%sp),%sp
#else
 jsr pl_next
 addq.l #8,%sp
#endif
 move.l %d0,%d1
 movem.l (%sp),%d0/%a0-%a1
 lea 12(%sp),%sp
 move.b %d1,(%a4)
 tst.b 0x77cb(%a2)
 jmp 0x4005534c
pl_master_hook:
 lea -12(%sp),%sp
 movem.l %d1/%a0-%a1,(%sp)
 moveq #0,%d0
 move.w 0x77c6(%a2),%d0
 move.l %d0,-(%sp)
 move.l %a2,-(%sp)
 jsr pl_effective
 addq.l #8,%sp
 movem.l (%sp),%d1/%a0-%a1
 lea 12(%sp),%sp
 move.l (%a3,%d1.l*4),%d2
 jmp 0x4005544a
pl_menu_tail:
 move.l %a2,-(%sp)
 jsr pl_menu_add
 addq.l #4,%sp
 jmp pl_previous_menu
pl_label:
 link.w %a6,#-4
 move.l %d2,-(%sp)
 pea -1(%a6)
 pea pl_label_text
 move.l %a0,%d2
 move.l %a0,-(%sp)
 jsr 0x400f980c
 lea 12(%sp),%sp
 move.l %d2,%d0
 move.l -8(%a6),%d2
 unlk %a6
 rts
pl_label_text: .asciz "Page Len"
.balign 2
