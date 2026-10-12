| Rendu stock : mêmes valeurs/algorithmes, panneau lampe original.
| Basé sur menu.s : construction adaptée de Model-TG, TinyGregAudio (MIT).
| Bundle MIDI expérimental ; aperçu RAM par render_seq_gen_stock.py.
.equ SG_GO,20
.equ SG_UNDO,21
.equ SG_LAST,23
.globl sg_render
    .section .text.sg_render,"ax"
sg_render:
    .ifdef SG_ADVANCED
    tstl sg_intro
    .ifdef SG_SEQUENCE_ONLY
    bnew sg_large_intro
    .else
    bnew sg_intro_render
    .endif
    .endif
    .ifdef SG_SCROLL
    jmp sg_render_start
    .section .text.sg_render_start,"ax"
sg_render_start:
    lea.l %sp@(-20),%sp
    movem.l %d2-%d5/%a2,%sp@
    movel %sp@(28),%d2
    .else
    lea.l %sp@(-16),%sp
    movem.l %d2-%d4/%a2,%sp@
    movel %sp@(24),%d2
    .endif
    clrl %sp@-
    pea 63
    pea 127
    clrl %sp@-
    clrl %sp@-
    movel %d2,%sp@-
    jsr 0x40070dea
    lea.l %sp@(24),%sp
    .ifdef SG_SCROLL
    jmp sg_view_start
    .section .text.sg_view_start,"ax"
sg_view_start:
    | Quatre lignes de 15 pixels ; sélection centrée, marges aux extrémités.
    movel sg_row,%d5
    subql #2,%d5
    bplw smr_view_nonnegative
    moveq #0,%d5
smr_view_nonnegative:
    .ifdef SG_SEQUENCE_ONLY
    jsr sg_ui_last
    subql #3,%d0
    bpls smr_last_nonnegative
    moveq #0,%d0
smr_last_nonnegative:
    cmpl %d0,%d5
    blew smr_view_ready
    movel %d0,%d5
    .else
    cmpil #(SG_LAST-3),%d5
    blew smr_view_ready
    moveq #(SG_LAST-3),%d5
    .endif
smr_view_ready:
    movel %d5,%d3
    jmp smr_loop
    .section .text.sg_render,"ax"
    .else
    moveq #0,%d3
    .endif
smr_loop:
    .ifdef SG_SEQUENCE_ONLY
    movel %d3,%d0
    jsr sg_map_row
    movel %d0,%d3
    .endif
    lea.l sg_stock_labels,%a0
    moveal %a0@(0,%d3:l:4),%a2
    cmpil #SG_GO,%d3
    bnew smr_label
    tstl sg_error
    beqw smr_label
    lea.l sg_error_text,%a2
smr_label:
    .ifdef SG_QUEUE
    jsr sg_q_label
    .endif
    .ifdef SG_SEQUENCE_ONLY
    movel %d3,%d0
    jsr sg_unmap_row
    movel %d0,%d4
    .else
    movel %d3,%d4
    .endif
    .ifdef SG_SCROLL
    subl %d5,%d4
    muluw #15,%d4
    moveq #49,%d0
    .else
    muluw #9,%d4
    moveq #55,%d0
    .endif
    subl %d4,%d0
    movel %a2,%sp@-
    pea sg_fmt_s
    pea 0x10
    movel %d0,%sp@-
    pea 44
    pea 0x40ea14cc
    movel %d2,%sp@-
    jsr 0x40071a04
    lea.l %sp@(28),%sp
    cmpil #SG_GO,%d3
    bgew smr_action
    .ifdef SG_ADVANCED
    cmpil #5,%d3
    bgew sg_advanced_value
    .else
    .ifdef SG_DYNAMICS
    cmpil #5,%d3
    bgew smr_option
    .endif
    .endif
    moveq #0,%d0
    tstl %d3
    bnew smr_root
    moveb TG_scale_state,%d0
    lea.l sg_scales,%a0
    moveal %a0@(0,%d0:l:4),%a2
    braw smr_string
smr_root:
    cmpil #1,%d3
    bnew smr_number
    moveb TG_key_state,%d0
    lea.l sg_keys,%a0
    moveal %a0@(0,%d0:l:4),%a2
smr_string:
    movel %a2,%sp@-
    pea sg_fmt_s
    braw smr_value
smr_number:
    lea.l sg_config,%a0
    movel %a0@(4),%d0
    cmpil #4,%d3
    beqw smr_num
    movel %a0@(0,%d3:l:4),%d0
smr_num:
    movel %d0,%sp@-
    pea sg_fmt_d
smr_value:
    pea 0x14
    .ifdef SG_SCROLL
    moveq #49,%d0
    .else
    moveq #55,%d0
    .endif
    subl %d4,%d0
    movel %d0,%sp@-
    pea 125
    pea 0x40ea14cc
    movel %d2,%sp@-
    jsr 0x40071a04
    lea.l %sp@(28),%sp
    braw smr_next
    .ifdef SG_DYNAMICS
    .section .text.sg_option,"ax"
smr_option:
    movel %d3,%d0
    subql #5,%d0
    lea.l sg_options,%a0
    tstl %a0@(0,%d0:l:4)
    lea.l sg_off,%a2
    beqw smr_string
    lea.l sg_on,%a2
    braw smr_string
    .section .text.sg_render,"ax"
    .endif
smr_action:
    jmp smr_action_body
    .section .text.sg_render_tail,"ax"
smr_action_body:
    .ifndef SG_SEQUENCE_ONLY
    .ifdef SG_ADVANCED
    cmpil #23,%d3
    bnew smr_sequence_undo
    lea.l sg_no_undo,%a2
    tstl sg_sound_valid
    beqw smr_string
    lea.l sg_ready,%a2
    braw smr_string
smr_sequence_undo:
    .endif
    .endif
    cmpil #SG_UNDO,%d3
    bnew smr_next
    lea.l sg_no_undo,%a2
    tstl sg_undo_valid
    beqw smr_string
    lea.l sg_ready,%a2
    braw smr_string
smr_next:
    .ifdef SG_SEQUENCE_ONLY
    movel %d3,%d0
    jsr sg_unmap_row
    movel %d0,%d3
    .endif
    addql #1,%d3
    .ifdef SG_SEQUENCE_ONLY
    jsr sg_ui_last
    cmpl %d0,%d3
    bgtw smr_highlight
    .endif
    .ifdef SG_SCROLL
    movel %d3,%d0
    subl %d5,%d0
    cmpil #4,%d0
    .else
    cmpil #7,%d3
    .endif
    bltw smr_loop
smr_highlight:
    pea -1
    movel sg_row,%d0
    .ifdef SG_SCROLL
    subl %d5,%d0
    muluw #15,%d0
    moveq #62,%d1
    .else
    muluw #9,%d0
    moveq #63,%d1
    .endif
    subl %d0,%d1
    movel %d1,%sp@-
    pea 127
    .ifdef SG_SCROLL
    subil #13,%d1
    .else
    subql #8,%d1
    .endif
    movel %d1,%sp@-
    moveq #42,%d0
    tstl sg_edit
    beqw smr_cursor
    moveq #84,%d0
smr_cursor:
    movel %d0,%sp@-
    movel %d2,%sp@-
    jsr 0x40070dea
    lea.l %sp@(24),%sp
    movel %d2,%sp@-
    jsr sg_stock_panel
    addql #4,%sp
    .ifdef SG_SCROLL
    movem.l %sp@,%d2-%d5/%a2
    lea.l %sp@(20),%sp
    .else
    movem.l %sp@,%d2-%d4/%a2
    lea.l %sp@(16),%sp
    .endif
    rts

    .section .text.sg_advanced_value,"ax"
sg_advanced_value:
    movel %d3,%d0
    subql #5,%d0
    lsll #4,%d0
    lea.l sg_fields,%a0
    moveal %a0@(0,%d0:l),%a0
    movel %a0@,%d0
    cmpil #5,%d3
    beqs sav_bool
    cmpil #8,%d3
    beqs sav_bool
    cmpil #11,%d3
    beqs sav_bool
    cmpil #14,%d3
    beqs sav_target
    cmpil #16,%d3
    beqs sav_rhythm
    braw smr_num
sav_bool:
    lea.l sg_bool_names,%a0
    bras sav_string
sav_target:
    lea.l sg_target_names,%a0
    bras sav_string
sav_rhythm:
    lea.l sg_rhythm_names,%a0
sav_string:
    moveal %a0@(0,%d0:l:4),%a2
    braw smr_string


    .text
sg_stock_panel:
    lea.l %sp@(-16),%sp
    moveml %d2-%d3/%a2-%a3,%sp@
    moveal %sp@(20),%a3
    clrl %sp@-
    pea 63
    pea 38
    clrl %sp@-
    clrl %sp@-
    movel %a3,%sp@-
    jsr 0x40070dea
    lea.l %sp@(24),%sp
    lea.l sg_stock_lamp,%a2
    moveq #19,%d3
.Llamp:
    pea -1
    movel %a2@(12),%sp@-
    movel %a2@(8),%sp@-
    movel %a2@(4),%sp@-
    movel %a2@,%sp@-
    movel %a3,%sp@-
    jsr 0x40070dea
    lea.l %sp@(24),%sp
    lea.l %a2@(16),%a2
    subql #1,%d3
    bpl .Llamp
    pea sg_stock_title
    pea sg_fmt_s
    pea 0x12
    pea 46
    pea 19
    pea 0x40ea14cc
    movel %a3,%sp@-
    jsr 0x40071a04
    lea.l %sp@(28),%sp
    | Deux rectangles disjoints et deux bandes forment le cartouche arrondi.
    lea.l sg_stock_box,%a2
    moveq #3,%d3
.Lbox:
    pea -1
    movel %a2@(12),%sp@-
    movel %a2@(8),%sp@-
    movel %a2@(4),%sp@-
    movel %a2@,%sp@-
    movel %a3,%sp@-
    jsr 0x40070dea
    lea.l %sp@(24),%sp
    lea.l %a2@(16),%a2
    subql #1,%d3
    bpl .Lbox
    moveml %sp@,%d2-%d3/%a2-%a3
    lea.l %sp@(16),%sp
    rts
    .section .rodata.sg_stock,"a"
sg_stock_title: .asciz "S.G."
    .balign 4
sg_stock_box:
    .long 2,0,36,63, 0,2,1,61, 37,2,38,61, 1,1,1,1
sg_stock_lamp:
    .long 10,22,27,22, 8,23,29,23, 7,24,30,25
    .long 6,26,29,27, 8,28,27,29, 10,30,25,31
    .long 12,32,23,32, 15,33,20,33
    .long 29,27,31,28, 30,29,32,30, 31,31,33,31
    .long 12,20,25,20, 16,21,21,21
    .long 11,33,24,33, 14,34,21,34
    .long 5,27,5,29, 4,29,4,31, 5,32,7,32
    .long 7,31,7,31, 17,37,18,38
sg_stock_labels:
    .long sg_sl0,sg_sl1,sg_sl2,sg_sl3,sg_sl4,sg_sl5,sg_sl6,sg_sl7,sg_sl8,sg_sl9,sg_sl10,sg_sl11,sg_sl12,sg_sl13,sg_sl14,sg_sl15,sg_sl16,sg_sl17,sg_sl18,sg_sl19,sg_sl20,sg_sl21,sg_sl22,sg_sl23
sg_sl0: .asciz "Scl"
sg_sl1: .asciz "Key"
sg_sl2: .asciz "Lo"
sg_sl3: .asciz "Hi"
sg_sl4: .asciz "Den %"
sg_sl5: .asciz "Vel"
sg_sl6: .asciz "V.Min"
sg_sl7: .asciz "V.Max"
sg_sl8: .asciz "Dec"
sg_sl9: .asciz "D.Min"
sg_sl10: .asciz "D.Max"
sg_sl11: .asciz "Pan"
sg_sl12: .asciz "P.Min"
sg_sl13: .asciz "P.Max"
sg_sl14: .asciz "Target"
sg_sl15: .asciz "Mut %"
sg_sl16: .asciz "Rhythm"
sg_sl17: .asciz "Hits"
sg_sl18: .asciz "Rot"
sg_sl19: .asciz "Sound"
sg_sl20: .asciz "Generate"
sg_sl21: .asciz "Undo"
sg_sl22: .asciz "Sound"
sg_sl23: .asciz "Undo"
