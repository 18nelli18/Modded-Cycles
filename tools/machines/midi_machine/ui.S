/* UI seulement : retour consomme avant les vues de synthese, sinon prologues
 * natifs rejoues exactement. Aucun pointeur de retour global.
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
 .globl mm_encoder_hook
mm_encoder_hook:
 save
 move.l 24(%sp),-(%sp)
 jsr mm_encoder
 addq.l #4,%sp
 tst.l %d0
 beq 1f
 restore
 moveq #1,%d0
 rts
1: restore
 move.l 8(%sp),-(%sp)
 move.l 8(%sp),-(%sp)
 bsr mm_encoder_delegate
 addq.l #8,%sp
 save
 jsr mm_audio_poll
 restore
 rts
mm_encoder_delegate:
 tst.l mm_ui_api+8
 beq 2f
 move.l mm_ui_api+8,-(%sp)
 rts
2:
 lea -64(%sp),%sp
 movem.l %d2/%a2-%a3,(%sp)
 jmp 0x40077600
 .globl mm_native_default
mm_native_default:
 lea -16(%sp),%sp
 move.l 24(%sp),-(%sp)
 move.l 24(%sp),-(%sp)
 jsr 0x4005a692
 addq.l #8,%sp
 move.l %d0,-(%sp)
 lea 4(%sp),%a0
 jsr 0x4005a65a
 addq.l #4,%sp
 move.l 8(%sp),%d0
 lea 16(%sp),%sp
 rts
 .globl mm_draw_hook
mm_draw_hook:
 save
 move.l 24(%sp),-(%sp)
 move.l 24(%sp),-(%sp)
 jsr mm_draw
 addq.l #8,%sp
 tst.l %d0
 beq 1f
 restore
 rts
1: restore
 tst.l mm_ui_api+12
 beq 2f
 move.l mm_ui_api+12,-(%sp)
 rts
2:
 link.w %fp,#-64
 movem.l %d2-%d7/%a2-%a5,(%sp)
 jmp 0x4001b232
 .globl mm_ui_key_hook
mm_ui_key_hook:
 save
 move.l 24(%sp),-(%sp)
 jsr mm_ui_key
 addq.l #4,%sp
 tst.l %d0
 beq 1f
 restore
 moveq #1,%d0
 rts
1: restore
 tst.l mm_ui_api+16
 beq 2f
 move.l mm_ui_api+16,-(%sp)
 rts
2:
 lea -96(%sp),%sp
 movem.l %d2-%d7/%a2-%fp,(%sp)
 jmp 0x40077728
