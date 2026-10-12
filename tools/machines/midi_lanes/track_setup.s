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
    tstl mlp_row
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
| Dessin borné : deux lignes, panneau noir à gauche comme les menus stock.
mlp_track_setup_render:
    lea.l %sp@(-16),%sp
    moveml %d2-%d3/%a2-%a3,%sp@
    moveal %sp@(24),%a2
    clrl %sp@-
    pea 63
    pea 127
    clrl %sp@-
    clrl %sp@-
    movel %a2,%sp@-
    jsr 0x40070dea
    lea.l %sp@(24),%sp
    pea 1
    pea 63
    pea 40
    clrl %sp@-
    clrl %sp@-
    movel %a2,%sp@-
    jsr 0x40070dea
    lea.l %sp@(24),%sp
    pea .Ltitle
    pea .Lfmt_s
    pea 0x10
    pea 46
    pea 2
    pea 0x40ea14cc
    movel %a2,%sp@-
    jsr 0x40071a04
    lea.l %sp@(28),%sp
    movel mlp_track,%d0
    muluw #264,%d0
    moveal ml_pattern,%a3
    addal %d0,%a3
    moveq #0,%d2
.Ltsr_loop:
    lea.l .Llabels,%a0
    movel %a0@(0,%d2:l:4),%sp@-
    pea .Lfmt_s
    pea 0x10
    movel %d2,%d3
    muluw #18,%d3
    addil #16,%d3
    movel %d3,%sp@-
    pea 52
    pea 0x40ea14cc
    movel %a2,%sp@-
    jsr 0x40071a04
    lea.l %sp@(28),%sp
    moveq #0,%d0
    tstl %d2
    bne .Ltsr_pad
    moveb %a3@(6),%d0
    extbl %d0
    bra .Ltsr_number
.Ltsr_pad:
    moveb %a3@(7),%d0
    eoril #72,%d0
    bsr mlp_pad_note_text
    movel %a0,%sp@-
    pea .Lfmt_s
    bra .Ltsr_value
.Ltsr_number:
    movel %d0,%sp@-
    pea .Lfmt_d
.Ltsr_value:
    pea 0x14
    movel %d3,%sp@-
    pea 125
    pea 0x40ea14cc
    movel %a2,%sp@-
    jsr 0x40071a04
    lea.l %sp@(28),%sp
    addql #1,%d2
    cmpil #2,%d2
    bcs .Ltsr_loop
    lea.l .Lcursor,%a0
    tstl mlp_edit
    beq .Ltsr_cursor
    lea.l .Lediting,%a0
.Ltsr_cursor:
    movel %a0,%sp@-
    pea .Lfmt_s
    pea 0x10
    movel mlp_row,%d0
    muluw #18,%d0
    addil #16,%d0
    movel %d0,%sp@-
    pea 43
    pea 0x40ea14cc
    movel %a2,%sp@-
    jsr 0x40071a04
    lea.l %sp@(28),%sp
    moveml %sp@,%d2-%d3/%a2-%a3
    lea.l %sp@(16),%sp
    rts
    .section .rodata
.Ltitle: .asciz "TRACK"
.Lfmt_s: .asciz "%s"
.Lfmt_d: .asciz "%d"
.Llabels: .long .Lkbt,.Lpad
.Lcursor: .asciz ">"
.Lediting: .asciz "*"
.Lkbt: .asciz "KbT"
.Lpad: .asciz "Pad"

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
