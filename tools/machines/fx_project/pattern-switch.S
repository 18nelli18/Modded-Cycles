/* Appel natif exact avant publication du pattern actif. Registres et SR
 * conserves ; le move original fixe ensuite ses CCR comme sur l OS stock. */
.text
.globl fxs_switch_hook
fxs_switch_hook:
 lea -20(%sp),%sp
 movem.l %d0-%d1/%a0-%a1,(%sp)
 move.w %sr,%d0
 move.l %d0,16(%sp)
 move.l %a2,-(%sp)
 jsr fxs_change
 addq.l #4,%sp
 move.l 16(%sp),%d0
 move.w %d0,%sr
 movem.l (%sp),%d0-%d1/%a0-%a1
 lea 20(%sp),%sp
 move.l %a2,0x40a7887c
 jmp 0x40055c62
.globl wave_gain_render
wave_gain_render:
 lea -16(%sp),%sp
 movem.l %d2/%a2,(%sp)
 move.l 20(%sp),%a2
 move.l 24(%sp),-(%sp)
 move.l %a2,-(%sp)
 jsr wave_render_original
 addq.l #8,%sp
 move.l %d0,8(%sp)
 moveq #31,%d2
1:move.l (%a2),%d0
 add.l %d0,%d0
 sats.l %d0
 move.l %d0,(%a2)+
 subq.l #1,%d2
 bpl 1b
 move.l 8(%sp),%d0
 movem.l (%sp),%d2/%a2
 lea 16(%sp),%sp
 rts
