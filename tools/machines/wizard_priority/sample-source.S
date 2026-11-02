/* Sites natifs OS1.13. Ne changer ni pointeur CUR_SNDS ni contrat d'appel.
 * ws_copy remplace move.l d2,d0 / addi.l #20,d3 ; d3=son, d2=piste.
 * ws_restore rejoue lea -36(sp),sp / move.l 40(sp),d0 avant40058310.
 * Le chemin non-Wizard ne passe pas par le helper C. */
.text
.globl ws_copy,ws_restore
ws_copy:
 movea.l %d3,%a0
 moveq #0,%d0
 move.b 38(%a0),%d0
 cmpi.l #6,%d0
 bne.s 1f
 lea -12(%sp),%sp
 movem.l %d1/%a0-%a1,(%sp)
 move.l %d2,-(%sp)
 move.l %d3,-(%sp)
 jsr ws_source
 addq.l #8,%sp
 move.l %d0,%d3
 movem.l (%sp),%d1/%a0-%a1
 lea 12(%sp),%sp
1:
 move.l %d2,%d0
 addi.l #20,%d3
 jmp 0x40058a30
ws_restore:
 movea.l 12(%sp),%a0
 moveq #0,%d0
 move.b 38(%a0),%d0
 cmpi.l #6,%d0
 bne.s 2f
 lea -16(%sp),%sp
 movem.l %d0-%d1/%a0-%a1,(%sp)
 move.l 20(%sp),-(%sp)
 move.l 32(%sp),-(%sp)
 jsr ws_source
 addq.l #8,%sp
 move.l %d0,28(%sp)
 movem.l (%sp),%d0-%d1/%a0-%a1
 lea 16(%sp),%sp
2:
 lea -36(%sp),%sp
 move.l 40(%sp),%d0
 jmp 0x40058310
