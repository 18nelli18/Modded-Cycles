.text
    .equ ALLOC,            0x40080064
    .equ FREE_CLOSURE,     0x400cf044
    .equ MENUITEM_CTOR,    0x400734b0
    .equ MENUVIEW_ADDITEM, 0x40072ce6
    .equ FORMAT_STRING,    0x400f980c
    .equ TINYSTR_WRAP,     0x400f85bc
    .equ DRAW_FMT_A,       0x40072260
    .equ DRAW_FMT_B,       0x40072080
    .equ DRAW_TEXT,        0x40071a04
    .equ FREE_TINYSTR,     0x400f7d5c
    .equ SLOT2_MANAGER,    0x4002f188
    .equ SLOT2_INVOKER,    0x4002ec3a
    .equ GENERIC_MANAGER,  0x4002f136


.globl bq_menu_tail,bq_install_mode,bq_label_mode,bq_value_mode,bq_rotate_mode,bq_press_mode,bq_scale_string
bq_menu_tail:
 jsr bq_install_mode
 movem.l 0x18(%sp),%d2-%d6/%a2-%a6
 lea.l 0x80(%sp),%sp
 rts
bq_scale_string:
 lea bq_labels,%a0
 move.l (%a0,%d0.l),%d0
 rts
bq_label_mode:
    link.w  %a6,#-4
    move.l  %d2,-(%a7)
    pea.l   -1(%a6)
    pea.l   bq_mode_label
    move.l  %a0,%d2
    move.l  %a0,-(%a7)
    jsr     FORMAT_STRING
    lea.l   0xc(%a7),%a7
    move.l  %d2,%d0
    move.l  -8(%a6),%d2
    unlk    %a6
    rts


bq_value_mode:
    link.w  %a6,#-0x30
    move.l  #0x40fe4278,%d0
    movem.l %d2-%d4/%a2-%a5,(%a7)
    move.l  %d0,-0x10(%a6)
    lea.l   FREE_TINYSTR,%a2
    move.l  %a6,%d2
    subq.l  #8,%d2
    move.l  %a6,%d3
    addi.l  #-0x10,%d3

    moveq   #0,%d0
    move.b  bq_mode,%d0
    lsl.l   #2,%d0
    lea.l   bq_mode_strings,%a0
    move.l  0(%a0,%d0.l),%d0

    move.l  %d0,-(%a7)
    move.l  %d3,-(%a7)
    jsr     TINYSTR_WRAP
    addq.l  #8,%a7

    pea.l   0x40140ab0
    move.l  %d2,-(%a7)
    move.l  -0x10(%a6),%d4
    jsr     DRAW_FMT_A
    move.l  %d4,-(%a7)
    movea.l 0x14(%a6),%a0
    pea.l   4
    move.l  0x18(%a6),-(%a7)
    lea.l   0x18(%a0),%a0
    move.l  %a0,-(%a7)
    move.l  %d2,-(%a7)
    move.l  0x10(%a6),-(%a7)
    jsr     DRAW_TEXT
    lea.l   0x1c(%a7),%a7
    move.l  %d2,(%a7)
    jsr     DRAW_FMT_B
    move.l  %d3,-(%a7)
    jsr     (%a2)
    addq.l  #8,%a7
    movem.l -0x30(%a6),%d2-%d4/%a2-%a5
    unlk    %a6
    rts


bq_rotate_mode:
    lea.l   -24(%a7),%a7
    movem.l %d2-%d4/%a2-%a4,(%a7)
    move.l  36(%a7),%d4
    moveq   #0,%d0
    tst.l   %d4
    beq.b   .zero
    bgt.b   .pos
    moveq   #-1,%d0
    bra.b   .apply
.pos:
    moveq   #1,%d0
.apply:
    jsr     bq_advance_mode
.zero:
    | live redraw, take 4: FUN_40030d74 (our slot4 template) never
    | calls FUN_400750e2/FUN_40075c4e at all - those turned out to
    | just set unread "dirty" flags with no direct effect. It only
    | ever tail-jumps into the generic setter (FUN_4000d3e4), whose
    | OWN last step is "(**(code**)(*param_1+0x10))()" - calling
    | vtable slot 0x10 (notify) directly on the "current track"
    | accessor object itself. We already know this exact object has
    | a valid vtable, since its +0x28 slot (get-storage) has been
    | called successfully via this same chain throughout this whole
    | session (every getter/setter we've used does that). Call its
    | +0x10 slot the same way instead of the flag-setting functions.
    jsr     0x400cf866
    move.l  %d0,-(%a7)
    jsr     0x4000f208
    addq.l  #4,%a7
    move.l  %d0,-(%a7)
    jsr     0x4000d0dc
    addq.l  #4,%a7
    movea.l %d0,%a0
    movea.l (%a0),%a1
    movea.l 0x10(%a1),%a1
    move.l  %a0,-(%a7)
    jsr     (%a1)
    addq.l  #4,%a7
    movem.l (%a7),%d2-%d4/%a2-%a4
    lea.l   24(%a7),%a7
    rts


bq_press_mode:
    move.l  %d2,-(%a7)
    move.l  0xc(%a7),%d2
    move.l  %d2,-(%a7)
    jsr     0x400732f8
    addq.l  #4,%a7
    moveq   #1,%d1
    mvz.b   %d0,%d0
    move.l  %d2,8(%a7)
    eor.l   %d0,%d1
    move.l  %d1,12(%a7)
    move.l  (%a7)+,%d2
    jmp     0x400732ec

bq_install_mode:
    lea.l   -0x30(%a7),%a7
    movem.l %d0-%d7/%a0-%a1/%a3-%a4,(%a7)
    lea.l   -0x40(%a7),%a7
    movea.l %a7,%a5

    | --- item1: SCALE LOCK ---
    move.l  #1,-(%a7)
    jsr     ALLOC
    addq.l  #4,%a7
    move.l  %d0,0x00(%a5)
    clr.l   0x04(%a5)
    move.l  #GENERIC_MANAGER,%d0
    move.l  %d0,0x08(%a5)
    move.l  #bq_label_mode,%d0
    move.l  %d0,0x0c(%a5)

    move.l  #4,-(%a7)
    jsr     ALLOC
    addq.l  #4,%a7
    movea.l %d0,%a0
    move.l  %a2,(%a0)
    move.l  %d0,0x10(%a5)
    clr.l   0x14(%a5)
    move.l  #SLOT2_MANAGER,%d0
    move.l  %d0,0x18(%a5)
    move.l  #bq_press_mode,%d0
    move.l  %d0,0x1c(%a5)

    move.l  #1,-(%a7)
    jsr     ALLOC
    addq.l  #4,%a7
    move.l  %d0,0x20(%a5)
    clr.l   0x24(%a5)
    move.l  #GENERIC_MANAGER,%d0
    move.l  %d0,0x28(%a5)
    move.l  #bq_value_mode,%d0
    move.l  %d0,0x2c(%a5)

    | closure4: rotation handler (slot4). Same capture (a2) and
    | manager as closure2 - proven-safe generic 4-byte-capture
    | manager, reused here since the shape is identical.
    move.l  #4,-(%a7)
    jsr     ALLOC
    addq.l  #4,%a7
    movea.l %d0,%a0
    move.l  %a2,(%a0)
    move.l  %d0,0x30(%a5)
    clr.l   0x34(%a5)
    move.l  #SLOT2_MANAGER,%d0
    move.l  %d0,0x38(%a5)
    move.l  #bq_rotate_mode,%d0
    move.l  %d0,0x3c(%a5)

    move.l  #0x54,-(%a7)
    jsr     ALLOC
    addq.l  #4,%a7
    movea.l %d0,%a3

    move.l  #8,-(%a7)
    move.l  #0xffffffff,-(%a7)
    lea.l   0x30(%a5),%a0
    move.l  %a0,-(%a7)
    lea.l   0x20(%a5),%a0
    move.l  %a0,-(%a7)
    lea.l   0x10(%a5),%a0
    move.l  %a0,-(%a7)
    move.l  %a5,-(%a7)
    move.l  %a3,-(%a7)
    jsr     MENUITEM_CTOR
    lea.l   0x1c(%a7),%a7

    move.l  %a3,-(%a7)
    move.l  %a2,-(%a7)
    jsr     MENUVIEW_ADDITEM
    addq.l  #8,%a7

    lea.l   0x30(%a5),%a0
    move.l  %a0,-(%a7)
    jsr     FREE_CLOSURE
    addq.l  #4,%a7
    lea.l   0x20(%a5),%a0
    move.l  %a0,-(%a7)
    jsr     FREE_CLOSURE
    addq.l  #4,%a7
    lea.l   0x10(%a5),%a0
    move.l  %a0,-(%a7)
    jsr     FREE_CLOSURE
    addq.l  #4,%a7
    move.l  %a5,-(%a7)
    jsr     FREE_CLOSURE
    addq.l  #4,%a7

    lea.l 0x40(%a7),%a7
    movem.l (%a7),%d0-%d7/%a0-%a1/%a3-%a4
    lea.l 0x30(%a7),%a7
    rts

.globl bq_labels,bq_masks,bq_names,bq_mode_strings
bq_labels:
 .long bq_s0,bq_s1,bq_s2,bq_s3,bq_s4,bq_s5,bq_s6,bq_s7,bq_s8,bq_s9,bq_s10,bq_s11,bq_s12,bq_s13,bq_s14,bq_s15,bq_s16,bq_s17,bq_s18
bq_names:
 .long bq_n0,bq_n1,bq_n2,bq_n3,bq_n4,bq_n5,bq_n6,bq_n7,bq_n8,bq_n9,bq_n10,bq_n11,bq_n12,bq_n13,bq_n14,bq_n15,bq_n16,bq_n17,bq_n18
bq_masks:
 .long 4095,2741,1453,1709,661,1451,2773,1717,1387,1689,1257,1193,1467,419,395,2509,2483,1459,1365
bq_s0: .asciz "CHR"
bq_n0: .asciz "Chromatic"
bq_s1: .asciz "MAJ"
bq_n1: .asciz "Major"
bq_s2: .asciz "MIN"
bq_n2: .asciz "Minor"
bq_s3: .asciz "DOR"
bq_n3: .asciz "Dorian"
bq_s4: .asciz "PEN"
bq_n4: .asciz "Maj Pent"
bq_s5: .asciz "PHR"
bq_n5: .asciz "Phrygian"
bq_s6: .asciz "LYD"
bq_n6: .asciz "Lydian"
bq_s7: .asciz "MIX"
bq_n7: .asciz "Mixolyd"
bq_s8: .asciz "LOC"
bq_n8: .asciz "Locrian"
bq_s9: .asciz "MBL"
bq_n9: .asciz "Maj Blues"
bq_s10: .asciz "mBL"
bq_n10: .asciz "Min Blues"
bq_s11: .asciz "mPN"
bq_n11: .asciz "Min Pent"
bq_s12: .asciz "FLK"
bq_n12: .asciz "Folk"
bq_s13: .asciz "JPN"
bq_n13: .asciz "Japanese"
bq_s14: .asciz "GAM"
bq_n14: .asciz "Gamelan"
bq_s15: .asciz "GYP"
bq_n15: .asciz "Gypsy"
bq_s16: .asciz "ARB"
bq_n16: .asciz "Arabian"
bq_s17: .asciz "FLA"
bq_n17: .asciz "Flamenco"
bq_s18: .asciz "WHO"
bq_n18: .asciz "Whole Tone"
 .even
bq_mode_label: .asciz "Lock"
 .even
bq_mode_strings: .long bq_off,bq_orig,bq_braids
bq_off: .asciz "Off"
#ifdef BQ_COMPACT_LABELS
bq_orig: .asciz "ORGN"
bq_braids: .asciz "BRDS"
#else
bq_orig: .asciz "Original"
bq_braids: .asciz "Braids"
#endif
 .even
