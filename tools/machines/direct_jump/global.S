/* Rendu MenuView natif repris de la vue B (TinyGregAudio/projet, MIT).
 * Six lignes, fenetre native de quatre lignes, aucune copie du firmware. */
.text
.globl mf_global_draw
mf_global_draw:
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
    clrb %a0@(164)
    clrb %a0@(248)
    clrb %a0@(332)
    clrb %a0@(416)
    clrb %a0@(500)
    clrb %a0@(584)
    clrb %a0@(668)
    clrb %a0@(752)
    clrb %a0@(836)
    clrb %a0@(920)
    jsr gc_tree_row
    muluw #84,%d0
    lea.l .Lts_rows,%a0
    addal %d0,%a0
    movel %a0,%sp@-
    jsr ae_global_edit
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
    moveq #11,%d0
    rts
.Lts_zero_value:
    moveq #0,%d0
    rts
.Lts_row_value:
    jsr gc_tree_row
    cmpil #3,%d0
    ble.s 1f
    moveq #3,%d0
1:  rts
.Lts_first_value:
    jsr gc_tree_row
    subql #3,%d0
    bpl.s 1f
    moveq #0,%d0
1:  rts
.Lts_visible_count:
    moveq #4,%d0
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
    .long .Lts_first_value,.Lts_row_value,.Lts_visible_count,0,.Lts_zero_value
.Lts_title_header: .long 6,6,0
.Lts_title_data: .asciz "Global"
    .balign 4
.Lts_subtitle_header: .long 3,3,0
.Lts_subtitle_data: .asciz "Mod"




.Llabel0: .asciz "Pad"
.Llabel1: .asciz "USB"
.Llabel2: .asciz "Num"
.Llabel3: .asciz "Mute"
.Llabel4: .asciz "Dly"
.Llabel5: .asciz "DX"
.Llabel6: .asciz "QntM"
.Llabel7: .asciz "Grv"
.Llabel8: .asciz "LFOs"
.Llabel9: .asciz "FX"
.Lacid_label: .asciz "ACID"
.Lallocator: .byte 0
.balign 4
.Lts_rows:
.long 0,0,0,.Llabel0,0,1,.Lts_label,0,0,0,0,0,0,1,wf_menu_value,0,0,0,0,0,0
.long 0,0,0,.Llabel1,0,1,.Lts_label,0,0,0,0,0,0,1,wf_usb_menu_value,0,0,0,0,0,0
.long 0,0,0,.Llabel2,0,1,.Lts_label,0,0,0,0,0,0,1,vp_menu_value,0,0,0,0,0,0
.long 0,0,0,.Llabel3,0,1,.Lts_label,0,0,0,0,0,0,1,lm_menu_value,0,0,0,0,0,0
.long 0,0,0,.Llabel4,0,1,.Lts_label,0,0,0,0,0,0,1,dl_menu_value,0,0,0,0,0,0
.long 0,0,0,.Llabel5,0,1,.Lts_label,0,0,0,0,0,0,1,dx_menu_value,0,0,0,0,0,0
.long 0,0,0,.Llabel6,0,1,.Lts_label,0,0,0,0,0,0,1,gc_root_value,0,0,0,0,0,0
.long 0,0,0,.Llabel7,0,1,.Lts_label,0,0,0,0,0,0,1,gc_root_value,0,0,0,0,0,0
.long 0,0,0,.Llabel8,0,1,.Lts_label,0,0,0,0,0,0,1,gc_lfo_value,0,0,0,0,0,0

.long 0,0,0,.Llabel9,0,1,.Lts_label,0,0,0,0,0,0,1,mf_global_value,0,0,0,0,0,0

.long 0,0,0,.Lacid_label,0,1,.Lts_label,0,0,0,0,0,0,1,ae_value,0,0,0,0,0,0
