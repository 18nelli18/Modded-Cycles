| Fenêtre de treize caractères (78 px maximum), défilement aller-retour.
| Horloge audio monotone, mais dessin et tampon exclusivement dans la tâche UI.
    .data
    .balign 4
mlkc_scroll_name: .long 0
mlkc_scroll_time: .long 0
mlkc_scroll_draw: .long 0
mlkc_scroll_pos: .long 0
mlkc_scroll_dir: .long 1
mlkc_scroll_buf: .space 16
    .text
    .globl mlkc_window,mlkc_tick
mlkc_window:
    movel %d2,%sp@-
    moveal %sp@(8),%a0
    movel TG_blk_clk,%d2
    cmpal mlkc_scroll_name,%a0
    beq .Lsw_same
    movel %a0,mlkc_scroll_name
    movel %d2,mlkc_scroll_time
    clrl mlkc_scroll_pos
    moveq #1,%d0
    movel %d0,mlkc_scroll_dir
.Lsw_same:
    moveal %a0,%a1
    moveq #0,%d1
.Lsw_len:
    tstb %a1@+
    beq .Lsw_length
    addql #1,%d1
    bra .Lsw_len
.Lsw_length:
    subil #13,%d1
    ble .Lsw_short
    subl mlkc_scroll_time,%d2
    moveq #0,%d0
    movel mlkc_scroll_pos,%d0
    beq .Lsw_pause
    cmpl %d1,%d0
    bne .Lsw_move
.Lsw_pause:
    cmpil #1500,%d2
    bcs .Lsw_copy
.Lsw_move:
    cmpil #375,%d2
    bcs .Lsw_copy
    movel TG_blk_clk,%d2
    movel %d2,mlkc_scroll_time
    addl mlkc_scroll_dir,%d0
    movel %d0,mlkc_scroll_pos
    tstl %d0
    beq .Lsw_forward
    cmpl %d1,%d0
    bne .Lsw_copy
    moveq #-1,%d2
    movel %d2,mlkc_scroll_dir
    bra .Lsw_copy
.Lsw_forward:
    moveq #1,%d2
    movel %d2,mlkc_scroll_dir
.Lsw_copy:
    addal %d0,%a0
    lea mlkc_scroll_buf,%a1
    moveq #12,%d1
.Lsw_chars:
    moveb %a0@+,%a1@+
    subql #1,%d1
    bpl .Lsw_chars
    clrb %a1@
    lea mlkc_scroll_buf,%a0
.Lsw_short:
    movel %a0,%d0
    movel %sp@+,%d2
    rts
mlkc_tick:
    tstl mlkc_show
    beq .Lst_done
    tstl mlp_obj
    beq .Lst_done
    movel TG_blk_clk,%d0
    movel %d0,%d1
    subl mlkc_scroll_draw,%d1
    cmpil #375,%d1
    bcs .Lst_done
    movel %d0,mlkc_scroll_draw
    movel mlp_obj,%sp@-
    jsr 0x40076082
    addql #4,%sp
.Lst_done:
    rts
