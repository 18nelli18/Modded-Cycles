/* Wrappers chaines, registres et ABI natifs conserves. */
.text
.macro save
 lea -16(%sp),%sp
 movem.l %d0-%d1/%a0-%a1,(%sp)
.endm
.macro restore
 movem.l (%sp),%d0-%d1/%a0-%a1
 lea 16(%sp),%sp
.endm
.globl wf_encoder_hook,wf_key_hook,wf_draw_hook,wf_cut,wf_res,wf_pad
wf_encoder_hook:
 save
 move.l 24(%sp),-(%sp)
 jsr wf_menu_encoder
 addq.l #4,%sp
 tst.l %d0
 beq 1f
 restore
 moveq #1,%d0
 rts
1: move.l 24(%sp),-(%sp)
 jsr wf_before
 addq.l #4,%sp
 restore
 move.l 8(%sp),-(%sp)
 move.l 8(%sp),-(%sp)
 move.l wf_api,%a0
 jsr (%a0)
 addq.l #8,%sp
 save
 move.l 24(%sp),-(%sp)
 jsr wf_after
 addq.l #4,%sp
 restore
 rts
wf_key_hook:
 save
 move.l 24(%sp),-(%sp)
 jsr wf_key
 addq.l #4,%sp
 tst.l %d0
 beq 1f
 restore
 moveq #1,%d0
 rts
1: restore
 move.l wf_api+4,-(%sp)
 rts
wf_draw_hook:
 save
 move.l 24(%sp),-(%sp)
 move.l 24(%sp),-(%sp)
 jsr wf_draw
 addq.l #8,%sp
 tst.l %d0
 beq 1f
 restore
 rts
1: restore
 move.l wf_api+8,-(%sp)
 rts
wf_cut:
 save
 clr.l -(%sp)
 move.l %d2,-(%sp)
 move.l %a2,-(%sp)
 jsr wf_value
 lea 12(%sp),%sp
 move.l %d0,4(%sp)
 restore
 rts
wf_res:
 save
 pea 1
 move.l %d2,-(%sp)
 move.l %a2,-(%sp)
 jsr wf_value
 lea 12(%sp),%sp
 move.l %d0,%d4
 restore
 rts
/* D7 et D3 sont ceux du PadsView ; aucune modification du code en cours d'execution. */
wf_pad:
 tst.l wf_stock
 bne 1f
 tst.b %d7
 bne 2f
 bra 3f
1: tst.b %d7
 beq 2f
3: tst.b %d3
 jmp 0x4001d378
2: jmp 0x4001d34e
