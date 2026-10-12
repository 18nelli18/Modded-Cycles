| Note 57 : rendu stock, données MIDI fournies aux seuls sites de dessin.
| Aucun remplacement de projet/kit/sélection audio. Objet de rendu privé
| sur pile, champs lus par MainScreenView nuls ; aucun constructeur/observer.
    .text
    .globl mlp_stock_render,mlp_stock_track,mlp_stock_volume,mlp_stock_pan
mlp_stock_render:
    lea.l %sp@(-308),%sp
    movem.l %d2-%d4/%a2-%a3,%sp@
    moveal %sp@(316),%a3
    lea.l %sp@(20),%a2
    moveal %a2,%a0
    moveq #71,%d0
.Lstock_zero:
    clrl %a0@+
    subql #1,%d0
    bpl .Lstock_zero
    moveq #1,%d0
    movel %d0,mlp_stock_drawing
    movel %a3,%sp@-
    movel %a2,%sp@-
    bsr mlp_stock_main
    addql #8,%sp
    clrl mlp_stock_drawing
    tstl mlp_held
    beq .Lstock_badge
    bsr mlp_stock_step
    moveal %a0,%a1
    moveq #0,%d0
    moveb %a1@,%d0
    moveq #-1,%d1
.Lstock_oct:
    cmpil #12,%d0
    bcs .Lstock_name
    subil #12,%d0
    addql #1,%d1
    bra .Lstock_oct
.Lstock_name:
    lea.l mlp_stock_names,%a0
    moveal %a0@(0,%d0:l:4),%a0
    lea.l %a2@(144),%a1
.Lstock_name_copy:
    moveb %a0@+,%d0
    beq .Lstock_oct_text
    moveb %d0,%a1@+
    bra .Lstock_name_copy
.Lstock_oct_text:
    tstl %d1
    bpl .Lstock_oct_positive
    moveq #45,%d0
    moveb %d0,%a1@+
    moveq #1,%d1
.Lstock_oct_positive:
    addil #48,%d1
    moveb %d1,%a1@+
    clrb %a1@
    bsr mlp_stock_step
    moveq #0,%d0
    moveb %a0@(1),%d0
    lea.l %a2@(152),%a0
    bsr mlp_stock_decimal
    bsr mlp_stock_step
    moveq #0,%d0
    moveb %a0@(2),%d0
    lea.l %a2@(160),%a0
    bsr mlp_stock_decimal
    movel %a3,%sp@-
    movel %a2,%sp@-
    bsr mlp_stock_note_view
    addql #8,%sp
.Lstock_badge:
    pea mlp_stock_b
    pea mlp_stock_fmt
    pea 0x10
    pea 49
    pea 119
    pea 0x40ea14cc
    movel %a3,%sp@-
    jsr 0x40071a04
    lea.l %sp@(28),%sp
    movem.l %sp@,%d2-%d4/%a2-%a3
    lea.l %sp@(308),%sp
    rts

| Prologues natifs ; les épilogues stock restaurent exactement ces cadres.
mlp_stock_main:
    linkw %a6,#-64
    movem.l %d2-%d7/%a2-%a5,%sp@
    jmp 0x4001b232
mlp_stock_note_view:
    lea.l %sp@(-40),%sp
    movem.l %d2-%d4/%a2-%a6,%sp@
    moveal %sp@(44),%a2
    movel %sp@(48),%d2
    jmp 0x40029a04

| Pointeur du pas affiché, domaine validé même si la vue n'est pas ouverte.
mlp_stock_step:
    moveal ml_pattern,%a0
    movel mlp_track,%d0
    cmpil #5,%d0
    bls .Lstock_lane_ok
    moveq #0,%d0
.Lstock_lane_ok:
    muluw #264,%d0
    addal %d0,%a0
    movel mlp_step,%d0
    andil #63,%d0
    lsll #2,%d0
    lea.l %a0@(8,%d0:l),%a0
    rts

| d0 entier positif <=127, a0 tampon de huit octets.
mlp_stock_decimal:
    cmpil #100,%d0
    bcs .Lstock_tens
    moveq #49,%d1
    moveb %d1,%a0@+
    subil #100,%d0
    moveq #48,%d1
    bra .Lstock_tens_loop
.Lstock_tens:
    moveq #48,%d1
    cmpil #10,%d0
    bcs .Lstock_units
.Lstock_tens_loop:
    cmpil #10,%d0
    bcs .Lstock_write_tens
    subil #10,%d0
    addql #1,%d1
    bra .Lstock_tens_loop
.Lstock_write_tens:
    moveb %d1,%a0@+
.Lstock_units:
    addil #48,%d0
    moveb %d0,%a0@+
    clrb %a0@
    rts

| Detours limités aux callsites MainScreenView::draw, jamais aux getters
| globaux qui pourraient être utilisés par le moteur audio.
mlp_stock_track:
    tstl mlp_stock_drawing
    beq .Lstock_track_native
    movel mlp_track,%d0
    rts
.Lstock_track_native:
    jmp 0x40012412
mlp_stock_volume:
    tstl mlp_stock_drawing
    beq .Lstock_volume_native
    bsr mlp_stock_step
    moveq #0,%d0
    moveb %a0@(1),%d0
    rts
.Lstock_volume_native:
    jmp 0x40009c5a
mlp_stock_pan:
    tstl mlp_stock_drawing
    beq .Lstock_pan_native
    movel #16384,%d0           | centre ; aucune émission CC10
    rts
.Lstock_pan_native:
    moveal %a0@(28),%a0
    jmp %a0@
    .data
    .balign 4
    .globl mlp_stock_drawing
mlp_stock_drawing: .long 0
mlp_stock_fmt: .asciz "%s"
mlp_stock_b: .asciz "B"
    .balign 4
mlp_stock_names: .long .LnC,.LnCs,.LnD,.LnDs,.LnE,.LnF,.LnFs,.LnG,.LnGs,.LnA,.LnAs,.LnB
.LnC: .asciz "C"
.LnCs: .asciz "C#"
.LnD: .asciz "D"
.LnDs: .asciz "D#"
.LnE: .asciz "E"
.LnF: .asciz "F"
.LnFs: .asciz "F#"
.LnG: .asciz "G"
.LnGs: .asciz "G#"
.LnA: .asciz "A"
.LnAs: .asciz "A#"
.LnB: .asciz "B"

    .text
    .globl mlp_stock_track_label
| Argument TR seulement : les getters conservent l'index interne 0..5.
mlp_stock_track_label:
    movel %a2,%d4
    addql #1,%d4
    tstl mlp_stock_drawing
    beq .Lstock_track_label_push
    addql #6,%d4
.Lstock_track_label_push:
    movel %d4,%sp@-
    movel #0x401117e0,%d4
    jmp 0x4001b6c4
