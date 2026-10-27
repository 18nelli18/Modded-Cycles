/* Debut/fin du bloc musical de l'ISR sequenceur. Registres temporaires rendus,
 * tests natifs rejoues ; heartbeat, MIDI clock et metronome restent physiques. */
.text
.globl wp_begin_hook,wp_finish_hook,pl_warp_label
wp_begin_hook:
 lea -16(%sp),%sp
 movem.l %d0-%d1/%a0-%a1,(%sp)
 jsr wp_begin
 tst.l %d0
 beq.s 1f
 movem.l (%sp),%d0-%d1/%a0-%a1
 lea 16(%sp),%sp
 tst.l 0x40a78630
 jmp 0x40054c90
1: movem.l (%sp),%d0-%d1/%a0-%a1
 lea 16(%sp),%sp
 jmp 0x400558e2
wp_finish_hook:
 lea -12(%sp),%sp
 movem.l %d1/%a0-%a1,(%sp)
 jsr wp_finish
 movem.l (%sp),%d1/%a0-%a1
 lea 12(%sp),%sp
 moveq #1,%d0
 cmp.l 0x40a78874,%d0
 jmp 0x400558ea
pl_warp_label:
 link.w %a6,#-4
 move.l %d2,-(%sp)
 pea -1(%a6)
 pea wp_label
 move.l %a0,%d2
 move.l %a0,-(%sp)
 jsr 0x400f980c
 lea 12(%sp),%sp
 move.l %d2,%d0
 move.l -8(%a6),%d2
 unlk %a6
 rts
wp_label: .asciz "Warp"
.balign 2
