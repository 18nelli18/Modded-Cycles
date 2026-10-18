/* Meme pile que le relais lo-fi. Deleguer tous les gestes apres preparation
 * des callbacks PITCH ; le descripteur43 et son lo-fi ne sont jamais modifies.
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
 .globl mf_knob
mf_knob:
 save
 move.l 52(%sp),%d0
 move.l %d5,-(%sp)
 move.l %d2,-(%sp)
 move.l %d0,-(%sp)
 jsr mf_prepare
 lea 12(%sp),%sp
 restore
 move.l mf_api+8,-(%sp)
 rts
 .globl mf_key_hook
mf_key_hook:
 save
 move.l 24(%sp),-(%sp)
 jsr mf_key
 addq.l #4,%sp
 tst.l %d0
 beq 1f
 restore
 moveq #1,%d0
 rts
1: restore
 tst.l mf_api+12
 beq 2f
 move.l mf_api+12,-(%sp)
 rts
2: lea -96(%sp),%sp
 movem.l %d2-%d7/%a2-%fp,(%sp)
 jmp 0x40077728
 .globl mf_draw
mf_draw:
 save
 jsr mf_active
 tst.l %d0
 bne 1f
 jsr mf_original_draw
 move.l %d0,12(%sp)
 restore
 jmp (%a1)
1: restore
 jmp mf_draw_text
