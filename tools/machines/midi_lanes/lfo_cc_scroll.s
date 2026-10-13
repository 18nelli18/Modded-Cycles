| Fenêtre de cinq caractères (30 px maximum), défilement aller-retour.
| Horloge audio monotone, mais dessin et tampon exclusivement dans la tâche UI.
    .data
    .balign 4
mlccp_scroll_name: .long 0
mlccp_scroll_time: .long 0
mlccp_scroll_draw: .long 0
mlccp_scroll_pos: .long 0
mlccp_scroll_dir: .long 1
mlccp_scroll_buf: .space 8
    .text
    .globl mlccp_window,mlccp_tick
mlccp_window:
    movel %d2,%sp@-
    moveal %sp@(8),%a0
    movel TG_blk_clk,%d2
    cmpal mlccp_scroll_name,%a0
    beq .Lsw_same
    movel %a0,mlccp_scroll_name
    movel %d2,mlccp_scroll_time
    clrl mlccp_scroll_pos
    moveq #1,%d0
    movel %d0,mlccp_scroll_dir
.Lsw_same:
    moveal %a0,%a1
    moveq #0,%d1
.Lsw_len:
    tstb %a1@+
    beq .Lsw_length
    addql #1,%d1
    bra .Lsw_len
.Lsw_length:
    subql #5,%d1
    ble .Lsw_short
    subl mlccp_scroll_time,%d2
    moveq #0,%d0
    movel mlccp_scroll_pos,%d0
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
    movel %d2,mlccp_scroll_time
    addl mlccp_scroll_dir,%d0
    movel %d0,mlccp_scroll_pos
    tstl %d0
    beq .Lsw_forward
    cmpl %d1,%d0
    bne .Lsw_copy
    moveq #-1,%d2
    movel %d2,mlccp_scroll_dir
    bra .Lsw_copy
.Lsw_forward:
    moveq #1,%d2
    movel %d2,mlccp_scroll_dir
.Lsw_copy:
    addal %d0,%a0
    lea mlccp_scroll_buf,%a1
    moveq #4,%d1
.Lsw_chars:
    moveb %a0@+,%a1@+
    subql #1,%d1
    bpl .Lsw_chars
    clrb %a1@
    lea mlccp_scroll_buf,%a0
.Lsw_short:
    movel %a0,%d0
    movel %sp@+,%d2
    rts
mlccp_tick:
    tstl mlccp_obj
    beq .Lst_done
    movel TG_blk_clk,%d0
    movel %d0,%d1
    subl mlccp_scroll_draw,%d1
    cmpil #375,%d1
    bcs .Lst_done
    movel %d0,mlccp_scroll_draw
    movel mlccp_obj,%sp@-
    jsr 0x40076082
    addql #4,%sp
.Lst_done:
    rts
