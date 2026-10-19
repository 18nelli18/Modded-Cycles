/* Rendu MenuView natif repris de la vue B (TinyGregAudio/projet, MIT).
 * Modele prive4lignes, aucune copie du firmware. */
.text
.globl wf_menu_draw
wf_menu_draw:
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
    lea.l .Lts_rows,%a0
    clrb %a0@(80)
    jsr wf_menu_row
    muluw #84,%d0
    lea.l .Lts_rows,%a0
    addal %d0,%a0
    movel %a0,%sp@-
    jsr wf_menu_edit
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
    moveq #1,%d0
    rts
.Lts_zero_value:
    moveq #0,%d0
    rts
.Lts_row_value:
    jmp wf_menu_row
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
    .long .Lts_zero_value,.Lts_row_value,.Lts_count,0,.Lts_zero_value
.Lts_title_header: .long 3,3,0
.Lts_title_data: .asciz "Pad"
    .balign 4
.Lts_subtitle_header: .long 5,5,0
.Lts_subtitle_data: .asciz "Setup"
.Lfmt_s: .asciz "%s"
.Lfmt_d: .asciz "%d"
.Lchannel: .asciz "Md"
.Loutput: .asciz "Out"
.Lkbt: .asciz "KbT"
.Lpad: .asciz "Pad"
.Lallocator: .byte 0
    .balign 4
.Lts_rows:
    .long 0,0,0,.Lchannel,0,1,.Lts_label,0,0,0,0,0,0,1,wf_menu_value,0,0,0,0,0,0
