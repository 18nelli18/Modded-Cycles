/* Rendu MenuView natif repris de la vue B (TinyGregAudio/projet, MIT).
 * Modele prive4lignes, aucune copie du firmware. */
.text
.globl mi_lfo_menu_draw
mi_lfo_menu_draw:
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
    jsr mi_lfo_number
    lea.l .Lts_subtitle_data,%a0
    cmpil #2,%d0
    bne.s .Lsubtitle_ready
    lea.l .Lts_subtitle2_data,%a0
.Lsubtitle_ready:
    movel %a0,%a2@(556)
    lea.l .Lts_rows,%a0
    clrb %a0@(80)
    clrb %a0@(164)
    clrb %a0@(248)
    clrb %a0@(332)
    clrb %a0@(416)
    clrb %a0@(500)
    clrb %a0@(584)
    clrb %a0@(668)
    jsr mm_menu_row
    muluw #84,%d0
    lea.l .Lts_rows,%a0
    addal %d0,%a0
    movel %a0,%sp@-
    jsr mm_menu_edit
    moveal %sp@+,%a0
    moveb %d0,%a0@(80)
    movel %sp@(592),%sp@-
    movel %a2,%sp@-
    jsr 0x400423e4
    addql #8,%sp
    moveml %sp@,%d2/%a2-%a3
    lea.l %sp@(584),%sp
    rts
.Lts_count:
    moveq #8,%d0
    rts
.Lts_visible:
    moveq #4,%d0
    rts
.Lts_zero_value:
    moveq #0,%d0
    rts
.Lts_row_value:
    jmp mm_menu_row
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
    .section .rodata
    .balign 4
.Lts_vtable:
    .long 0,0,0,.Lts_count,.Lts_item,0,0,0,0,0,0,0,0,0
    .long mi_lfo_scroll,mi_lfo_relative,.Lts_visible,0,.Lts_zero_value
.Lts_title_header: .long 4,4,0
.Lts_title_data: .asciz "MIDI"
    .balign 4
.Lts_subtitle_header: .long 5,5,0
.Lts_subtitle_data: .asciz "LFO 1"
    .balign 4
    .long 5,5,0
.Lts_subtitle2_data: .asciz "LFO 2"
.Lfmt_s: .asciz "%s"
.Lfmt_d: .asciz "%d"
.Lfield0: .asciz "Spd"
.Lfield1: .asciz "Mul"
.Lfield2: .asciz "Fad"
.Lfield3: .asciz "Dst"
.Lfield4: .asciz "Wav"
.Lfield5: .asciz "SPH"
.Lfield6: .asciz "Rst"
.Lfield7: .asciz "Dep"
.Lallocator: .byte 0
    .balign 4
.Lts_rows:
    .long 0,0,0,.Lfield4,0,1,.Lts_label,0,0,0,0,0,0,1,mi_lfo_value,0,0,0,0,0,4
    .long 0,0,0,.Lfield1,0,1,.Lts_label,0,0,0,0,0,0,1,mi_lfo_value,0,0,0,0,0,1
.long 0,0,0,.Lfield3,0,1,.Lts_label,0,0,0,0,0,0,1,mi_lfo_value,0,0,0,0,0,3
    .long 0,0,0,.Lfield7,0,1,.Lts_label,0,0,0,0,0,0,1,mi_lfo_value,0,0,0,0,0,7
.long 0,0,0,.Lfield0,0,1,.Lts_label,0,0,0,0,0,0,1,mi_lfo_value,0,0,0,0,0,0
    .long 0,0,0,.Lfield2,0,1,.Lts_label,0,0,0,0,0,0,1,mi_lfo_value,0,0,0,0,0,2
    .long 0,0,0,.Lfield5,0,1,.Lts_label,0,0,0,0,0,0,1,mi_lfo_value,0,0,0,0,0,5
    .long 0,0,0,.Lfield6,0,1,.Lts_label,0,0,0,0,0,0,1,mi_lfo_value,0,0,0,0,0,6
