| Track Setup B : KbT signé -60..60 en header6, Pad Note XOR72 en header7.
| Zéros hérités = transpose0, PadC5. Données privées incluses au sidecar.
    .text
    .globl mlp_track_setup_open,mlp_track_setup_enc,mlp_track_setup_render
mlp_track_setup_open:
    jsr mlp_keyboard_cancel
    moveq #3,%d0
    movel %d0,mlp_setup
    clrl mlp_row
    clrl mlp_edit
    rts
| delta déjà réduit à -1/+1 ; un seul octet atomique, aucune piste A modifiée.
mlp_track_setup_enc:
    movel %sp@(4),%d1
    movel mlp_row,%d0
    tstl mlp_edit
    bne .Ltse_edit
    addl %d1,%d0
    cmpil #1,%d0
    bhi .Ltse_done
    movel %d0,mlp_row
    rts
.Ltse_edit:
    movel %d1,%sp@-
    jsr mlp_keyboard_cancel
    movel %sp@+,%d1
    movel mlp_track,%d0
    cmpil #5,%d0
    bhi .Ltse_done
    muluw #264,%d0
    moveal ml_pattern,%a0
    addal %d0,%a0
    movel mlp_row,%d0
    tstl %d0
    bne .Ltse_pad
    moveq #0,%d0
    moveb %a0@(6),%d0
    extbl %d0
    addl %d1,%d0
    cmpil #-60,%d0
    blt .Ltse_done
    cmpil #60,%d0
    bgt .Ltse_done
    moveb %d0,%a0@(6)
    rts
.Ltse_pad:
    moveq #0,%d0
    moveb %a0@(7),%d0
    eoril #72,%d0
    addl %d1,%d0
    cmpil #127,%d0
    bhi .Ltse_done
    eoril #72,%d0
    moveb %d0,%a0@(7)
.Ltse_done:
    rts
| Rendu MenuView natif avec modèle et lignes privés : géométrie, polices,
| surbrillance et titre stock ; aucun constructeur/observer de piste audio.
mlp_track_setup_render:
    lea.l %sp@(-584),%sp
    moveml %d2/%a2-%a3,%sp@
    lea.l %sp@(16),%a2
    moveal %a2,%a0
    movel #140,%d0
.Lts_zero:
    clrl %a0@+
    subql #1,%d0
    bpl .Lts_zero
    lea.l .Lts_vtable,%a0
    movel %a0,%a2@
    lea.l .Lts_title_data,%a0
    movel %a0,%a2@(148)
    movel 0x40ea14d0,%d0
    movel %d0,%a2@(156)
    movel %d0,%a2@(160)
    lea.l .Lts_subtitle_data,%a0
    movel %a0,%a2@(556)
    movel %sp@(592),%sp@-
    movel %a2,%sp@-
    jsr 0x400423e4
    addql #8,%sp
    moveml %sp@,%d2/%a2-%a3
    lea.l %sp@(584),%sp
    rts
.Lts_count:
    moveq #2,%d0
    rts
.Lts_zero_value:
    moveq #0,%d0
    rts
.Lts_row_value:
    movel mlp_row,%d0
    rts
.Lts_item:
    movel %sp@(8),%d0
    muluw #84,%d0
    lea.l .Lts_rows,%a1
    addal %d0,%a1
    movel %a1,%a0@
    clrl %a0@(4)
    rts
.Lts_label:
    lea.l %sp@(-8),%sp
    movel %a0,%sp@
    moveal %sp@(12),%a1
    movel %a1@,%sp@-
    pea .Lallocator
    | std::string(this,texte,allocator), même routine que le label stock.
    movel %sp@+,%d0
    movel %sp@+,%d1
    movel %d0,%sp@-
    movel %d1,%sp@-
    movel %a0,%sp@-
    jsr 0x400f980c
    lea.l %sp@(12),%sp
    movel %sp@,%d0
    addql #8,%sp
    rts
.Lts_value:
    lea.l %sp@(-16),%sp
    moveml %d2/%a2-%a3,%sp@
    moveal %sp@(24),%a3
    moveal %sp@(28),%a2
    movel mlp_track,%d0
    muluw #264,%d0
    moveal ml_pattern,%a0
    addal %d0,%a0
    movel %a3@(80),%d2
    tstl %d2
    bne .Lts_pad_text
    moveq #0,%d0
    moveb %a0@(6),%d0
    extbl %d0
    movel %d0,%sp@-
    pea .Lfmt_d
    bra .Lts_draw_value
.Lts_pad_text:
    moveq #0,%d0
    moveb %a0@(7),%d0
    eoril #72,%d0
    jsr mlp_pad_note_text
    moveal %a0,%a1
.Lts_string:
    movel %a1,%sp@-
    pea .Lfmt_s
.Lts_draw_value:
    pea 4
    movel %sp@(48),%sp@-
    movel %sp@(48),%d0
    addil #24,%d0
    movel %d0,%sp@-
    pea 0x40ea14cc
    movel %a2,%sp@-
    jsr 0x40071a04
    lea.l %sp@(28),%sp
    moveml %sp@,%d2/%a2-%a3
    lea.l %sp@(16),%sp
    rts
    .section .rodata
    .balign 4
.Lts_vtable:
    .long 0,0,0,.Lts_count,.Lts_item,0,0,0,0,0,0,0,0,0
    .long .Lts_zero_value,.Lts_row_value,.Lts_count,0,.Lts_zero_value
.Lts_title_header: .long 5,5,0
.Lts_title_data: .asciz "Track"
    .balign 4
.Lts_subtitle_header: .long 5,5,0
.Lts_subtitle_data: .asciz "Setup"
.Lfmt_s: .asciz "%s"
.Lfmt_d: .asciz "%d"
.Lkbt: .asciz "KbT"
.Lpad: .asciz "Pad"
.Lallocator: .byte 0
    .balign 4
.Lts_rows:
    .long 0,0,0,.Lkbt,0,1,.Lts_label,0,0,0,0,0,0,1,.Lts_value,0,0,0,0,0,0
    .long 0,0,0,.Lpad,0,1,.Lts_label,0,0,0,0,0,0,1,.Lts_value,0,0,0,0,0,1

    .text
| Nom MIDI stock : note72=C5 ; buffer UI, jamais appelé depuis IRQ.
    .globl mlp_pad_note_text
mlp_pad_note_text:
    divuw #12,%d0
    movel %d0,%d1
    andil #65535,%d1
    subql #1,%d1
    swap %d0
    andil #65535,%d0
    lea.l .Lnames,%a0
    moveal %a0@(0,%d0:l:4),%a0
    lea.l .Lnote_text,%a1
.Lname_copy:
    moveb %a0@+,%d0
    beq .Lname_oct
    moveb %d0,%a1@+
    bra .Lname_copy
.Lname_oct:
    tstl %d1
    bpl .Lname_positive
    moveb #45,%a1@+
    moveq #1,%d1
.Lname_positive:
    addil #48,%d1
    moveb %d1,%a1@+
    clrb %a1@
    lea.l .Lnote_text,%a0
    rts
    .data
.Lnote_text: .space 8
    .section .rodata
    .balign 4
.Lnames: .long .Ln0,.Ln1,.Ln2,.Ln3,.Ln4,.Ln5,.Ln6,.Ln7,.Ln8,.Ln9,.Ln10,.Ln11
.Ln0: .asciz "C"
.Ln1: .asciz "C#"
.Ln2: .asciz "D"
.Ln3: .asciz "D#"
.Ln4: .asciz "E"
.Ln5: .asciz "F"
.Ln6: .asciz "F#"
.Ln7: .asciz "G"
.Ln8: .asciz "G#"
.Ln9: .asciz "A"
.Ln10: .asciz "A#"
.Ln11: .asciz "B"

    .data
    .balign 4
    .globl mlp_live_pad_held
mlp_live_pad_held: .long 0
    .text
| pad_note(lane,down) : note Pad privée, même file sûre que le clavier B.
    .globl mlp_pad_note
mlp_pad_note:
    lea.l %sp@(-12),%sp
    moveml %d2-%d3/%a2,%sp@
    movel %sp@(16),%d2
    cmpil #5,%d2
    bhi .Lpad_done
    tstl %sp@(20)
    beq .Lpad_up
    tstl mlp_setup
    bne .Lpad_done
    movel %d2,%d0
    muluw #264,%d0
    moveal ml_pattern,%a2
    addal %d0,%a2
    tstb %a2@
    beq .Lpad_done

    moveq #0,%d3
    moveb %a2@(2),%d3
    cmpil #15,%d3
    bhi .Lpad_done
    oril #0x90,%d3
    swap %d3
    lsll #8,%d3
    moveq #0,%d0
    moveb %a2@(7),%d0
    eoril #72,%d0
    cmpil #127,%d0
    bhi .Lpad_done
    swap %d0
    orl %d0,%d3
    oril #0x6400,%d3
    moveq #0,%d0
    moveb %a2@(3),%d0
    orl %d0,%d3
    pea 64
    movel %d3,%sp@-
    movel %d2,%sp@-
    pea ml_live_runtime
    jsr ml_step
    lea.l %sp@(16),%sp
    tstl %d0
    beq .Lpad_done
    movel mlp_live_pad_held,%d0
    bset %d2,%d0
    movel %d0,mlp_live_pad_held
    lea.l mlp_live_key,%a0
    clrb %a0@(0,%d2:l)
    bra .Lpad_done
.Lpad_up:
    movel mlp_live_pad_held,%d0
    btst %d2,%d0
    beq .Lpad_done
    bclr %d2,%d0
    movel %d0,mlp_live_pad_held
    movel %d2,%sp@-
    pea ml_live_runtime
    jsr ml_quiet
    addql #8,%sp
.Lpad_done:
    moveml %sp@,%d2-%d3/%a2
    lea.l %sp@(12),%sp
    rts
