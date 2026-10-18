/* Relais live apres le traitement natif audio/enregistrement. Les autres
 * machines reprennent exactement le chemin stock. Tous les volatils sont
 * sauvegardes ; l'ABI C preserve d2-d7/a2-a6. Aucun contexte global de pile.
 */
 .text
 .macro save
 lea -16(%sp),%sp
 movem.l %d0-%d1/%a0-%a1,(%sp)
 .endm
 .macro restore
 movem.l (%sp),%d0-%d1/%a0-%a1
 lea 16(%sp),%sp
 .endm
 .macro on
 move.l %d4,-(%sp)
 move.l %d3,-(%sp)
 move.l %d2,-(%sp)
 jsr mm_live_on
 lea 12(%sp),%sp
 tst.l %d0
 .endm
 .macro off
 move.l %d3,-(%sp)
 move.l %d2,-(%sp)
 jsr mm_live_off
 addq.l #8,%sp
 tst.l %d0
 .endm
 .globl mm_key_on_hook
mm_key_on_hook:
 jsr (%a2)
 save
 on
 beq 1f
 restore
 lea 28(%sp),%sp
 jmp 0x40019f3a
1: restore
#ifdef MM_CONTROLS
 tst.l mm_live_api
 beq 2f
 move.l mm_live_api,-(%sp)
 rts
2:
#endif
 move.l %d0,-(%sp)
 jsr 0x4000f208
 jmp 0x40019eec
 .globl mm_pad_on_hook
mm_pad_on_hook:
 save
 on
 beq 1f
 restore
 lea 28(%sp),%sp
 jmp 0x4001d0f2
1: restore
#ifdef MM_CONTROLS
 tst.l mm_live_api+4
 beq 2f
 move.l mm_live_api+4,-(%sp)
 rts
2:
#endif
 lea 0x400cf866,%a2
 jmp 0x4001d09a
 .globl mm_key_off_hook
mm_key_off_hook:
 save
 off
 beq 1f
 restore
 lea 16(%sp),%sp
 jmp 0x40019cf6
1: restore
#ifdef MM_CONTROLS
 tst.l mm_live_api+8
 beq 2f
 move.l mm_live_api+8,-(%sp)
 rts
2:
#endif
 move.l %d4,-(%sp)
 jsr 0x40016e90
 jmp 0x40019cc2
 .globl mm_pad_off_hook
mm_pad_off_hook:
 save
 off
 beq 1f
 restore
 lea 12(%sp),%sp
 jmp 0x4001d176
1: restore
#ifdef MM_CONTROLS
 tst.l mm_live_api+12
 beq 2f
 move.l mm_live_api+12,-(%sp)
 rts
2:
#endif
 lea 0x400cf866,%a2
 jmp 0x4001d126
#ifdef MM_CONTROLS
 .data
 .globl mm_live_api
mm_live_api:
 .long 0,0,0,0
#endif
