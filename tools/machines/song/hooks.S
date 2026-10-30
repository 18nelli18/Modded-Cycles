/* Raccord avant le hook FX pattern existant, conserve tous les registres/CCR. */
.text
.globl sg_switch,sg_mute_irq
.globl sg_live_switch
sg_live_switch:
 move.l (%a1),0x40a7887c
 lea -20(%sp),%sp
 movem.l %d0-%d1/%a0-%a1,(%sp)
 move.w %sr,%d0
 move.l %d0,16(%sp)
 move.l (%a1),-(%sp)
 jsr sg_boundary
 addq.l #4,%sp
 move.l 16(%sp),%d0
 move.w %d0,%sr
 movem.l (%sp),%d0-%d1/%a0-%a1
 lea 20(%sp),%sp
 rts
sg_switch:
 lea -20(%sp),%sp
 movem.l %d0-%d1/%a0-%a1,(%sp)
 move.w %sr,%d0
 move.l %d0,16(%sp)
 move.l %a2,-(%sp)
 jsr sg_boundary
 addq.l #4,%sp
 move.l 16(%sp),%d0
 move.w %d0,%sr
 movem.l (%sp),%d0-%d1/%a0-%a1
 lea 20(%sp),%sp
 jmp sg_old_switch
/* Le masque Song s'ajoute seulement au resultat de lecture : aucun mute utilisateur efface. */
sg_mute_irq:
 jsr sg_old_mute_irq
 lea -16(%sp),%sp
 movem.l %d0-%d1/%a0-%a1,(%sp)
 jsr sg_mutes
 or.l %d0,4(%sp)
 movem.l (%sp),%d0-%d1/%a0-%a1
 lea 16(%sp),%sp
 tst.l %d1
 rts
