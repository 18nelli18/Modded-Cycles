/* Écran principal : valeurs PAN et niveau pendant 90 ticks UI.
 * Contrat : rejouer les prologues puis conserver les registres de l'appelant.
 * Aucun crochet audio ou clavier. Voir notes/50-valeurs-pan-niveau.md.
 */

.text
.globl pan_ui_tick, pan_encoder, pan_draw, level_pan_delta
.extern pan_encoder_stock, pan_draw_stock
pan_ui_tick:
 addq.l #1,pan_clock
 jmp 0x40090f48


level_pan_delta:

 moveq #1,%d0
 move.l %d0,8(%sp)
 jmp 0x4006f73a


pan_encoder:
 link.w %a6,#0
 lea -12(%sp),%sp
 movem.l %d2/%a2-%a3,(%sp)
 move.l 8(%a6),%a2
 move.l 12(%a6),%a3
 move.l %a3,-(%sp)
 move.l %a2,-(%sp)
 jsr pan_encoder_stock
 addq.l #8,%sp
 move.l %d0,%d2
 move.l 12(%a3),%d0
 cmp.l #1,%d0
 bne.s .Lencoder_done
 pea 1
 jsr 0x4007faf4
 addq.l #4,%sp
 tst.l %d0
 beq.s .Lencoder_level
 bsr pan_arm
 bra.s .Lencoder_done
.Lencoder_level:
 bsr level_arm
.Lencoder_done:
 move.l %d2,%d0
 movem.l -12(%a6),%d2/%a2-%a3
 unlk %a6
 rts


pan_arm:
 jsr 0x400cf866
 move.l %d0,-(%sp)
 jsr 0x4000eb90
 move.l %d0,(%sp)
 jsr 0x40012412
 addq.l #4,%sp
 cmp.l #6,%d0
 bcc.s .Larm_done
 lea pan_deadlines,%a0
 move.l pan_clock,%d1
 add.l #90,%d1
 move.l %d1,(%a0,%d0.l*4)
 lea pan_valid,%a0
 moveq #1,%d1
 move.b %d1,(%a0,%d0.l)
 move.l %a2,-(%sp)
 jsr 0x40076082
 addq.l #4,%sp
.Larm_done:
 rts

level_arm:
 jsr 0x400cf866
 move.l %d0,-(%sp)
 jsr 0x4000eb90
 move.l %d0,(%sp)
 jsr 0x40012412
 addq.l #4,%sp
 cmp.l #6,%d0
 bcc.s .Llevel_arm_done
 lea level_deadlines,%a0
 move.l pan_clock,%d1
 add.l #90,%d1
 move.l %d1,(%a0,%d0.l*4)
 lea level_valid,%a0
 moveq #1,%d1
 move.b %d1,(%a0,%d0.l)
 move.l %a2,-(%sp)
 jsr 0x40076082
 addq.l #4,%sp
.Llevel_arm_done:
 rts



pan_draw:
 link.w %a6,#0
 lea -32(%sp),%sp
 movem.l %d2-%d6/%a2-%a4,(%sp)
 move.l 12(%a6),%a2
 move.l %a2,-(%sp)
 move.l 8(%a6),-(%sp)
 jsr pan_draw_stock
 addq.l #8,%sp

 jsr 0x400cf9a8
 move.l %d0,-(%sp)
 jsr 0x4006b704
 addq.l #4,%sp
 tst.b %d0
 bne.w .Ldraw_done
 jsr 0x400cf866
 move.l %d0,-(%sp)
 jsr 0x4000eb90
 move.l %d0,(%sp)
 jsr 0x40012412
 addq.l #4,%sp
 cmp.l #6,%d0
 bcc.w .Ldraw_done
 move.l %d0,%d2
 move.l %d2,%d6
 lea pan_valid,%a0
 tst.b (%a0,%d2.l)
 beq.w .Ldraw_level
 lea pan_deadlines,%a1
 move.l pan_clock,%d1
 sub.l (%a1,%d2.l*4),%d1
 bmi.s .Ldraw_value
 clr.b (%a0,%d2.l)
 bra.w .Ldraw_level
.Ldraw_value:
 jsr 0x400cf866
 move.l %d0,-(%sp)
 jsr 0x4000eb9c
 move.l %d2,-(%sp)
 move.l %d0,-(%sp)
 jsr 0x400097f0
 lea 12(%sp),%sp
 move.l %d0,%a0
 move.l (%a0),%a1
 move.l 28(%a1),%a1
 pea 0x1c
 move.l %a0,-(%sp)
 jsr (%a1)
 addq.l #8,%sp
 asr.l #8,%d0
 sub.l #64,%d0
 move.l %d0,%d4

 clr.l -(%sp)
 pea 29
 pea 127
 pea 21
 pea 114
 move.l %a2,-(%sp)
 jsr 0x40070dea
 lea 24(%sp),%sp
 move.l #115,%d2
 tst.l %d4
 bpl.s .Lunsigned
 neg.l %d4
 moveq #10,%d0
 bsr pan_glyph
.Lunsigned:
 moveq #0,%d5
.Ltens:
 cmp.l #10,%d4
 bcs.s .Ltens_done
 sub.l #10,%d4
 addq.l #1,%d5
 bra.s .Ltens
.Ltens_done:
 tst.l %d5
 beq.s .Lones
 move.l %d5,%d0
 bsr pan_glyph
.Lones:
 move.l %d4,%d0
 bsr pan_glyph

.Ldraw_level:
 lea level_valid,%a0
 tst.b (%a0,%d6.l)
 beq.w .Ldraw_done
 lea level_deadlines,%a1
 move.l pan_clock,%d1
 sub.l (%a1,%d6.l*4),%d1
 bmi.s .Llevel_value
 clr.b (%a0,%d6.l)
 bra.w .Ldraw_done
.Llevel_value:
 jsr 0x400cf866
 move.l %d0,-(%sp)
 jsr 0x4000eb9c
 move.l %d6,-(%sp)
 move.l %d0,-(%sp)
 jsr 0x40009c5a
 lea 12(%sp),%sp
 and.l #0xff,%d0
 move.l %d0,%d4

 clr.l -(%sp)
 pea 16
 pea 77
 pea 8
 pea 65
 move.l %a2,-(%sp)
 jsr 0x40070dea
 lea 24(%sp),%sp
 move.l #66,%d2
 cmp.l #100,%d4
 bcs.s .Llevel_two
 sub.l #100,%d4
 moveq #1,%d0
 bsr level_glyph
 bra.s .Llevel_tens_start
.Llevel_two:
 addq.l #4,%d2
 cmp.l #10,%d4
 bcc.s .Llevel_tens_start
 addq.l #4,%d2
 bra.s .Llevel_ones
.Llevel_tens_start:
 moveq #0,%d5
.Llevel_tens:
 cmp.l #10,%d4
 bcs.s .Llevel_tens_done
 sub.l #10,%d4
 addq.l #1,%d5
 bra.s .Llevel_tens
.Llevel_tens_done:
 move.l %d5,%d0
 bsr level_glyph
.Llevel_ones:
 move.l %d4,%d0
 bsr level_glyph
.Ldraw_done:
 movem.l -32(%a6),%d2-%d6/%a2-%a4
 unlk %a6
 rts


level_glyph:
 moveq #9,%d1
 bra.s .Lglyph_common
pan_glyph:
 moveq #22,%d1
.Lglyph_common:
 lea -24(%sp),%sp
 movem.l %d3-%d6/%a3-%a4,(%sp)
 move.l %d1,%d3
 move.l %d3,%d4
 addq.l #7,%d4
 move.l %d0,%d1
 lsl.l #3,%d0
 sub.l %d1,%d0
 lea pan_font,%a3
 adda.l %d0,%a3
 addq.l #7,%a3
.Lrow:
 moveq #0,%d6
 move.b -(%a3),%d6
 moveq #0,%d5
.Lcol:
 moveq #2,%d0
 sub.l %d5,%d0
 btst %d0,%d6
 beq.s .Lnextcol
 move.l %d2,%d0
 add.l %d5,%d0
 move.l 12(%a2),%d1
 muls.l %d1,%d0
 lsl.l #2,%d0
 move.l 16(%a2),%a4
 adda.l %d0,%a4
 moveq #31,%d0
 sub.l %d3,%d0
 moveq #1,%d1
 lsl.l %d0,%d1
 or.l %d1,(%a4)
.Lnextcol:
 addq.l #1,%d5
 cmp.l #3,%d5
 bne.s .Lcol
 addq.l #1,%d3
 cmp.l %d4,%d3
 bne.s .Lrow
 movem.l (%sp),%d3-%d6/%a3-%a4
 lea 24(%sp),%sp
 addq.l #4,%d2
 rts

.section .rodata
pan_font:
 .byte 7,5,5,5,5,5,7
 .byte 2,6,2,2,2,2,7
 .byte 7,1,1,7,4,4,7
 .byte 7,1,1,7,1,1,7
 .byte 5,5,5,7,1,1,1
 .byte 7,4,4,7,1,1,7
 .byte 7,4,4,7,5,5,7
 .byte 7,1,1,2,2,2,2
 .byte 7,5,5,7,5,5,7
 .byte 7,5,5,7,1,1,7
 .byte 0,0,0,7,0,0,0
.data
.balign 4
pan_clock: .long 0
pan_deadlines: .long 0,0,0,0,0,0
pan_valid: .byte 0,0,0,0,0,0
.balign 4

.balign 4
level_deadlines: .long 0,0,0,0,0,0
level_valid: .byte 0,0,0,0,0,0
.balign 4
