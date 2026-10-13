| Un emplacement CC maximum tous les trois blocs audio (<=500messages/s).
| Balayage round-robin borné72, coalescence via queue privée existante.
| Pas de port MIDI, allocation, filesystem ou attente depuis l'IRQ.
    .data
    .balign 4
    .globl mlkc_slide_cursor,mlkc_slide_rate
mlkc_slide_cursor: .long 0
mlkc_slide_rate: .long 0
    .text
    .globl mlkc_slide_tick
mlkc_slide_tick:
    lea %sp@(-44),%sp
    moveml %d2-%d7/%a2-%a5,%sp@
    moveal ml_clock_state,%a0
    tstl %a0
    beq .Ltick_cancel
    movel %a0@,%d0
    subql #1,%d0
    bne .Ltick_cancel
    moveal ml_play_pattern,%a5
    tstl %a5
    beq .Ltick_cancel
    cmpal mlkcq_owner,%a5
    bne .Ltick_cancel
    addql #1,mlkc_slide_rate
    movel mlkc_slide_rate,%d0
    cmpil #3,%d0
    bcs .Ltick_done
    clrl mlkc_slide_rate
    movel mlkc_slide_cursor,%d7
    cmpil #71,%d7
    bhi .Ltick_cancel
    moveq #71,%d3
.Ltick_scan:
    movel %d7,%d0
    divuw #12,%d0
    movel %d0,%d2
    andil #65535,%d2
    swap %d0
    andil #65535,%d0
    movel %d0,%d6
    movel %d2,%d0
    lsll #6,%d0
    lea mlkc_slide_states,%a2
    addal %d0,%a2
    cmpal %a2@,%a5
    bne .Ltick_next
    movel %a2@(12),%d4
    btst %d6,%d4
    beq .Ltick_next
    movel %d2,%d0
    muluw #264,%d0
    lea %a5@(0,%d0:l),%a3
    tstb %a3@
    beq .Ltick_lane_cancel
    tstb %a3@(1)
    bne .Ltick_lane_cancel
    moveb %a2@(12),%d0
    cmpb %a3@(2),%d0
    bne .Ltick_lane_cancel
    moveb %a2@(13),%d0
    cmpb %a3@(3),%d0
    bne .Ltick_lane_cancel
    movel TG_blk_clk,%d5
    subl %a2@(4),%d5
    bmi .Ltick_lane_cancel
    lea %a2@(16,%d6:l:4),%a4
    movel %a2@(8),%sp@-
    movel %d5,%sp@-
    moveq #0,%d0
    moveb %a4@(2),%d0
    movel %d0,%sp@-
    moveb %a4@(1),%d0
    andil #255,%d0
    movel %d0,%sp@-
    jsr mlkc_slide_value
    lea %sp@(16),%sp
    tstl %d0
    bmi .Ltick_lane_cancel
    cmpl %a2@(8),%d5
    bcs .Ltick_changed
    bclr %d6,%d4
    movel %d4,%a2@(12)
.Ltick_changed:
    cmpb %a4@(3),%d0
    beq .Ltick_advance_done
    moveb %d0,%a4@(3)
    movel %d0,%sp@(40)
    moveq #0,%d0
    moveb %a3@(3),%d0
    movel %d0,%sp@-
    movel %sp@(44),%sp@-
    moveq #0,%d0
    moveb %a4@,%d0
    movel %d0,%sp@-
    moveb %a3@(2),%d0
    andil #255,%d0
    movel %d0,%sp@-
    movel %d7,%sp@-
    pea mlkc_queue
    jsr mlkcq_put
    lea %sp@(24),%sp
.Ltick_advance_done:
    addql #1,%d7
    cmpil #72,%d7
    bcs .Ltick_cursor
    moveq #0,%d7
.Ltick_cursor:
    movel %d7,mlkc_slide_cursor
    bra .Ltick_done
.Ltick_lane_cancel:
    clrl %a2@(12)
    clrl %a2@
.Ltick_next:
    addql #1,%d7
    cmpil #72,%d7
    bcs .Ltick_scan_count
    moveq #0,%d7
.Ltick_scan_count:
    subql #1,%d3
    bpl .Ltick_scan
    bra .Ltick_done
.Ltick_cancel:
    jsr mlkc_slide_cancel
    clrl mlkc_slide_rate
.Ltick_done:
    moveml %sp@,%d2-%d7/%a2-%a5
    lea %sp@(44),%sp
    rts
