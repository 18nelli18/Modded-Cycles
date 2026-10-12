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

| Scale Setup : moteur de dessin stock, objet et onze MenuItem privés sur pile.
| Ni constructeur ScaleMenuView, ni observer projet, ni setter audio.
| La vue expose tous les réglages B avec les mêmes polices/positions/cadre de sélection.
    .globl mlp_scale_render
mlp_scale_render:
    lea.l %sp@(-1576),%sp
    movem.l %d2-%d4/%a2-%a3,%sp@
    moveal %sp@(1584),%a3
    lea.l %sp@(20),%a2
    moveal %a2,%a0
    moveq #0,%d0
    movel #388,%d1
.Lscale_zero:
    movel %d0,%a0@+
    subql #1,%d1
    bpl .Lscale_zero
    lea.l %a2@(564),%a1
    movel %a1,%a2@
    lea.l 0x40103f34,%a0
    moveq #16,%d0
.Lscale_vt_copy:
    movel %a0@+,%a1@+
    subql #1,%d0
    bpl .Lscale_vt_copy
    lea.l %a2@(564),%a1
    movel #mlp_scale_count,%d1
    movel %d1,%a1@(12)
    movel #mlp_scale_item,%d1
    movel %d1,%a1@(16)
    movel #mlp_scale_start,%d1
    movel %d1,%a1@(56)
    movel #mlp_scale_selected,%d1
    movel %d1,%a1@(60)
    movel #mlp_scale_visible,%d1
    movel %d1,%a1@(64)
    movel #mlp_scale_title,%d1
    movel %d1,%a2@(148)
    movel #mlp_scale_subtitle,%d1
    movel %d1,%a2@(556)
    movel #0x40140ab0,%d1
    movel %d1,%a2@(160)
    moveq #1,%d0
    moveb %d0,%a2@(560)
    lea.l %a2@(632),%a0
    moveq #0,%d2
.Lscale_items:
    movel #0x40103470,%a0@
    movel %d2,%a0@(12)
    movel %d2,%a0@(44)
    movel #1,%d1
    movel %d1,%a0@(20)
    movel #mlp_scale_label,%d1
    movel %d1,%a0@(24)
    movel #1,%d1
    movel %d1,%a0@(52)
    movel #mlp_scale_draw,%d1
    movel %d1,%a0@(56)
    cmpl mlp_row,%d2
    bne .Lscale_item_next
    movel mlp_edit,%d0
    moveb %d0,%a0@(80)
.Lscale_item_next:
    lea.l %a0@(84),%a0
    addql #1,%d2
    cmpil #10,%d2
    bls .Lscale_items
    movel %a3,%sp@-
    movel %a2,%sp@-
    jsr 0x400423e4
    addql #8,%sp
    movem.l %sp@,%d2-%d4/%a2-%a3
    lea.l %sp@(1576),%sp
    rts
mlp_scale_count:
    moveq #11,%d0
    rts
mlp_scale_visible:
    moveq #4,%d0
    rts
mlp_scale_start:
    movel mlp_row,%d0
    subql #1,%d0
    bpl .Lscale_start_max
    moveq #0,%d0
.Lscale_start_max:
    cmpil #7,%d0
    bls .Lscale_start_done
    moveq #7,%d0
.Lscale_start_done:
    rts
mlp_scale_selected:
    bsr mlp_scale_start
    movel mlp_row,%d1
    subl %d0,%d1
    movel %d1,%d0
    rts
mlp_scale_item:
    moveal %sp@(4),%a1
    movel %sp@(8),%d0
    muluw #84,%d0
    lea.l %a1@(632),%a1
    addal %d0,%a1
    movel %a1,%a0@
    clrl %a0@(4)
    movel %a0,%d0
    rts
mlp_scale_label:
    moveal %sp@(4),%a1
    movel %a1@,%d0
    lea.l mlp_scale_labels,%a1
    moveal %a1@(0,%d0:l:4),%a1
.Lscale_label_string:
    | std::string résultat caché dans a0, constructeur avec copie normale.
    clrl %sp@-
    movel %a1,%sp@-
    movel %a0,%sp@-
    jsr 0x400f980c
    lea.l %sp@(12),%sp
    rts
mlp_scale_draw:
    movel %d2,%sp@-
    lea.l %sp@(-8),%sp
    movel #0x401117e0,%d0
    movel %d0,%sp@
    movel #0x40140ab0,%d0
    movel %d0,%sp@(4)
    moveal %sp@(16),%a0
    movel %a0@,%d2
    jsr mlp_value
    cmpil #2,%d2
    bne .Lscale_draw_kind
    lea.l mlp_scale_ports,%a0
    moveal %a0@(0,%d0:l:4),%a0
.Lscale_draw_kind:
    tstl %a0
    beq .Lscale_draw_number
    movel %a0,%sp@-
    pea mlp_scale_fmt_s
    bra .Lscale_draw_args
.Lscale_draw_number:
    movel %d0,%sp@-
    pea mlp_scale_fmt_d
.Lscale_draw_args:
    pea 0x14
    movel %sp@(44),%sp@-
    pea 121
    pea %sp@(20)
    movel %sp@(48),%sp@-
    jsr 0x40071a04
    lea.l %sp@(36),%sp
    movel %sp@+,%d2
    rts
    .data
    .balign 4
    .long 5,5,-1
mlp_scale_title: .asciz "Scale"
    .balign 4
    .long 5,5,-1
mlp_scale_subtitle: .asciz "Setup"
    .balign 4
    .long 0,0,-1
mlp_scale_empty: .asciz ""
mlp_scale_len: .asciz "Len"
mlp_scale_scl: .asciz "Scl"
mlp_scale_fmt_s: .asciz "%s"
mlp_scale_fmt_d: .asciz "%d"

    .balign 4
mlp_scale_labels: .long .LsTrk,.LsChn,.LsOut,mlp_scale_len,mlp_scale_scl,.LsStp,.LsTrg,.LsNot,.LsVel,.LsGat,.LsOn
mlp_scale_ports: .long .LsUSB,.LsDIN,.LsBoth
.LsTrk: .asciz "Trk"
.LsChn: .asciz "Chn"
.LsOut: .asciz "Out"
.LsStp: .asciz "Stp"
.LsTrg: .asciz "Trg"
.LsNot: .asciz "Not"
.LsVel: .asciz "Vel"
.LsGat: .asciz "Gat"
.LsOn: .asciz "On"
.LsUSB: .asciz "USB"
.LsDIN: .asciz "DIN"
.LsBoth: .asciz "Both"
