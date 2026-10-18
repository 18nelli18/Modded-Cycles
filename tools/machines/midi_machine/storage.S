/* Sauvegarde/charge natifs d'abord, extension MIDI ensuite. Tous les arguments
 * et registres ABI sont conserves ; pas de pointeur de retour global.
 */
 .text
 .globl mm_save2_hook,mm_save1_hook,mm_load_hook
mm_save2_hook:
 move.l 8(%sp),-(%sp)
 move.l 8(%sp),-(%sp)
 pea mm_save_return
 move.l mm_storage_api,%a0
 tst.l %a0
 bne 2f
 lea -12(%sp),%sp
 movem.l %a2-%a4,(%sp)
 jmp 0x4005afa8
2: jmp (%a0)
mm_save1_hook:
 move.l 8(%sp),-(%sp)
 move.l 8(%sp),-(%sp)
 pea mm_save_return
 move.l mm_storage_api+4,%a0
 tst.l %a0
 bne 2f
 lea -12(%sp),%sp
 movem.l %a2-%a4,(%sp)
 jmp 0x4005b05c
2: jmp (%a0)
mm_load_hook:
 move.l 8(%sp),-(%sp)
 move.l 8(%sp),-(%sp)
 pea mm_load_return
 move.l mm_storage_api+8,%a0
 tst.l %a0
 bne 2f
 lea -12(%sp),%sp
 movem.l %a2-%a4,(%sp)
 jmp 0x4005aed4
2: jmp (%a0)
mm_save_return:
 lea -16(%sp),%sp
 movem.l %d0-%d1/%a0-%a1,(%sp)
 tst.b %d0
 beq 1f
 move.l 20(%sp),-(%sp)
 move.l 20(%sp),-(%sp)
 jsr mm_save_post
 addq.l #8,%sp
1: movem.l (%sp),%d0-%d1/%a0-%a1
 lea 24(%sp),%sp
 rts
mm_load_return:
 lea -16(%sp),%sp
 movem.l %d0-%d1/%a0-%a1,(%sp)
 tst.b %d0
 beq 1f
 move.l 20(%sp),-(%sp)
 move.l 20(%sp),-(%sp)
 jsr mm_load_post
 addq.l #8,%sp
1: movem.l (%sp),%d0-%d1/%a0-%a1
 lea 24(%sp),%sp
 rts
