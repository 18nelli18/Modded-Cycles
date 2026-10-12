| Note 57 : vraie base LedHandler privée ajoutée à +0x500.
| LED des pas et pads MIDI via le writer natif first-wins.
| Aucun port MIDI, aucune allocation et aucune sélection audio modifiée.
    .text
    .globl mlp_led
mlp_led:
    lea.l %sp@(-24),%sp
    movem.l %d2-%d5/%a2-%a3,%sp@
    moveal %sp@(28),%a0
    lea.l %a0@(-0x500),%a0
    cmpal mlp_obj,%a0
    bne .Lled_done
    moveal ml_pattern,%a2
    tstl %a2
    beq .Lled_done
    jsr mlp_cursor
    movel %d0,%d5
    movel mlp_track,%d0
    cmpil #5,%d0
    bhi .Lled_done
    muluw #264,%d0
    addal %d0,%a2
    movel mlp_step,%d0
    andil #48,%d0
    lsll #2,%d0
    lea.l %a2@(8),%a2
    addal %d0,%a2
    jsr 0x400cfaf4
    tstl %d0
    beq .Lled_done
    moveal %d0,%a3
    moveq #0,%d2
.Lled_loop:
    movel %d2,%sp@-
    jsr 0x4000608c
    addql #4,%sp
    movel %d0,%d3
    cmpil #53,%d3
    bhi .Lled_next
    movel %d3,%d0
    lsrl #5,%d0
    | Masque natif 64 bits big-endian : IDs 0..31 dans le second mot.
    moveq #1,%d1
    eorl %d1,%d0
    lsll #2,%d0
    moveal %sp@(36),%a0
    addal %d0,%a0
    movel %d3,%d1
    andil #31,%d1
    moveq #1,%d0
    lsll %d1,%d0
    orl %d0,%a0@
    moveq #1,%d4
    btst #0,%a2@(3)
    beq .Lled_write
    moveq #3,%d4
.Lled_write:
    pea 0x404a8cb8
    movel %d4,%sp@-
    movel %d3,%sp@-
    movel %a3,%sp@-
    jsr 0x40005f86
    lea.l %sp@(16),%sp
    cmpl %d5,%d2
    bne .Lled_next
    pea 6
    movel %d3,%sp@-
    jsr 0x4008e8c4
    addql #8,%sp
.Lled_next:
    addql #4,%a2
    addql #1,%d2
    cmpil #16,%d2
    bcs .Lled_loop
    moveq #0,%d2
.Lpad_loop:
    movel %d2,%sp@-
    jsr 0x400060bc
    addql #4,%sp
    movel %d0,%d3
    cmpil #53,%d3
    bhi .Lpad_next
    movel %d3,%d0
    lsrl #5,%d0
    moveq #1,%d1
    eorl %d1,%d0
    lsll #2,%d0
    moveal %sp@(36),%a0
    addal %d0,%a0
    movel %d3,%d1
    andil #31,%d1
    moveq #1,%d0
    lsll %d1,%d0
    orl %d0,%a0@
    moveq #1,%d4
    cmpl mlp_track,%d2
    bne .Lpad_write
    moveq #3,%d4
.Lpad_write:
    pea 0x404a8cb8
    movel %d4,%sp@-
    movel %d3,%sp@-
    movel %a3,%sp@-
    jsr 0x40005f86
    lea.l %sp@(16),%sp
    lea.l ml_pad_serial,%a0
    movel %a0@(0,%d2:l:4),%d0
    lea.l ml_pad_drawn,%a0
    cmpl %a0@(0,%d2:l:4),%d0
    beq .Lpad_next
    movel %d0,%a0@(0,%d2:l:4)
    pea 6
    movel %d3,%sp@-
    jsr 0x4008e8c4
    addql #8,%sp
.Lpad_next:
    addql #1,%d2
    cmpil #6,%d2
    bcs .Lpad_loop
.Lled_done:
    moveq #1,%d0
    movem.l %sp@,%d2-%d5/%a2-%a3
    lea.l %sp@(24),%sp
    rts

| Dernier pas émis, relatif à la page affichée ; -1 hors page/à l'arrêt.
    .globl mlp_cursor
mlp_cursor:
    .ifdef ML_PATTERN_BANKS
    movel ml_pattern,%d0
    cmpl ml_play_pattern,%d0
    bne .Lcursor_none
    .endif
    moveal ml_clock_state,%a0
    tstl %a0
    beq .Lcursor_none
    moveq #1,%d0
    cmpl %a0@,%d0
    bne .Lcursor_none
    movel mlp_track,%d0
    cmpil #5,%d0
    bhi .Lcursor_none
    movel %d0,%d1
    lsll #3,%d1
    movel %a0@(8,%d1:l),%d1
    subql #1,%d1
    bpl .Lcursor_step
    muluw #264,%d0
    moveal ml_pattern,%a0
    tstl %a0
    beq .Lcursor_none
    moveq #0,%d1
    moveb %a0@(4,%d0:l),%d1
    subql #1,%d1
.Lcursor_step:
    cmpil #63,%d1
    bhi .Lcursor_none
    movel mlp_step,%d0
    andil #48,%d0
    subl %d0,%d1
    cmpil #15,%d1
    bhi .Lcursor_none
    movel %d1,%d0
    rts
.Lcursor_none:
    moveq #-1,%d0
    rts

mlp_led_dtor0:
    moveal %sp@(4),%a0
    lea.l %a0@(-0x500),%a0
    movel %a0,%sp@(4)
    jmp mlp_dtor0
mlp_led_dtor1:
    moveal %sp@(4),%a0
    lea.l %a0@(-0x500),%a0
    movel %a0,%sp@(4)
    jmp mlp_dtor1
    .globl mlp_led_dtor0,mlp_led_dtor1

    .globl mlp_redraw,mlp_led_poll
mlp_redraw:
    movel %sp@(4),%sp@-
    jsr 0x400760ba
    addql #4,%sp
    jmp 0x40076082
mlp_led_poll:
    tstl mlp_obj
    beq .Lpoll_done
    jsr mlp_cursor
    cmpl mlp_led_last,%d0
    bne .Lpoll_changed
    lea.l ml_pad_serial,%a0
    lea.l ml_pad_polled,%a1
    moveq #5,%d1
.Lpoll_pad:
    movel %a0@+,%d0
    cmpl %a1@+,%d0
    bne .Lpoll_serial
    subql #1,%d1
    bpl .Lpoll_pad
    bra .Lpoll_done
.Lpoll_serial:
    lea.l ml_pad_serial,%a0
    lea.l ml_pad_polled,%a1
    moveq #5,%d1
.Lpoll_copy:
    movel %a0@+,%a1@+
    subql #1,%d1
    bpl .Lpoll_copy
    jsr mlp_cursor
.Lpoll_changed:
    movel %d0,mlp_led_last
    movel mlp_obj,%sp@-
    jsr 0x400760ba
    addql #4,%sp
.Lpoll_done:
    rts
    .data
mlp_led_last: .long -2
ml_pad_drawn: .space 24
ml_pad_polled: .space 24
