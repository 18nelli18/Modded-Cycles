/* Identites MACHINES privees : detours UI uniquement, pas de chemin audio.
 * d2=canvas, d3=machine, d4=decalage icone stock. Garder les autres registres.
 * Les six machines natives suivent exactement leurs pointeurs initiaux.
 */
.text
.globl identity_left,identity_right,identity_wizard
identity_left:
 movea.l 0x40fe32cc,%a1
 cmpi.l #6,%d3
 blt.s 1f
 cmpi.l #17,%d3
 bgt.s 1f
 move.l %d0,-(%sp)
 move.l %d3,%d0
 subq.l #6,%d0
 mulu.w #28,%d0
 lea identity_stats,%a1
 adda.l %d0,%a1
 suba.l %d4,%a1
 move.l (%sp)+,%d0
1: jmp 0x4678812a
identity_right:
 cmpi.l #6,%d3
 blt.s 1f
 cmpi.l #17,%d3
 bgt.s 1f
 move.l %d0,-(%sp)
 move.l %d3,%d0
 subq.l #6,%d0
 mulu.w #28,%d0
 addi.l #identity_icons,%d0
 move.l %d0,%d4
 move.l (%sp)+,%d0
 jmp 0x46788144
1: add.l 0x40fe384c,%d4
 jmp 0x46788144
identity_wizard:
 cmpi.l #6,%d3
 bne.s 1f
 lea -16(%sp),%sp
 movem.l %d0-%d1/%a0-%a1,(%sp)
 pea 1
 pea 23
 pea 32
 pea identity_stats
 move.l %d2,-(%sp)
 jsr 0x40071da4
 lea 20(%sp),%sp
 movem.l (%sp),%d0-%d1/%a0-%a1
 lea 16(%sp),%sp
1: cmpi.l #6,%d3
 jmp 0x467b6692
