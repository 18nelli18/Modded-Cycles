| Chance B : édition privée, choix et rendu du formatter natif.
| Octet7 : 0 hérité ; 102..165 = index natif0..63.
    .data
    .balign 4
    .globl ml_cond_history,ml_cond_fill
ml_cond_history: .space 96
ml_cond_fill: .long 0
    .text
    .globl mlp_chance_enc,mlp_chance_value,mlp_chance_render
mlp_chance_value:
    moveal ml_repeat_edit_settings,%a0
    tstl %a0
    beq .Lcv_default
    movel mlp_track,%d0
    cmpil #5,%d0
    bhi .Lcv_default
    muluw #520,%d0
    addal %d0,%a0
    tstl mlp_held
    beq .Lcv_read
    movel mlp_step,%d0
    cmpil #63,%d0
    bhi .Lcv_default
    lsll #3,%d0
    lea.l %a0@(8,%d0:l),%a1
    tstb %a1@(7)
    beq .Lcv_read
    moveal %a1,%a0
.Lcv_read:
    moveq #0,%d0
    moveb %a0@(7),%d0
    subil #102,%d0
    cmpil #63,%d0
    bls .Lcv_done
.Lcv_default:
    moveq #-1,%d0
.Lcv_done:
    rts
mlp_chance_enc:
    lea.l %sp@(-16),%sp
    moveml %d2-%d4/%a2,%sp@
    movel %sp@(20),%d3
    tstl %d3
    beq .Lce_done
    jsr ml_repeat_prepare_ui
    tstl ml_repeat_edit_settings
    beq .Lce_done
    jsr mlp_chance_value
    addl %d3,%d0
    cmpil #-1,%d0
    bge .Lce_high
    moveq #-1,%d0
.Lce_high:
    cmpil #63,%d0
    ble .Lce_value
    moveq #63,%d0
.Lce_value:
    cmpil #-1,%d0
    bne .Lce_encode
    moveq #-102,%d0
.Lce_encode:
    addil #102,%d0
    movel %d0,%d4
    moveal ml_repeat_edit_settings,%a2
    movel mlp_track,%d0
    muluw #520,%d0
    addal %d0,%a2
    movel mlp_held,%d2
    bne .Lce_steps
    moveb %d4,%a2@(7)
    bra .Lce_open
.Lce_steps:
    lea.l %a2@(8),%a2
    movel mlp_step,%d0
    andil #48,%d0
    lsll #3,%d0
    addal %d0,%a2
    moveq #15,%d3
.Lce_loop:
    btst #0,%d2
    beq .Lce_next
    moveb %d4,%a2@(7)
.Lce_next:
    lsrl #1,%d2
    addql #8,%a2
    subql #1,%d3
    bpl .Lce_loop
    movel mlp_held,%d0
    orl mlp_changed,%d0
    movel %d0,mlp_changed
.Lce_open:
    moveq #5,%d0
    movel %d0,mlp_setup
.Lce_done:
    moveml %sp@,%d2-%d4/%a2
    lea.l %sp@(16),%sp
    rts
| Le formatter stock garde les marqueurs inversés et les libellés exacts.
mlp_chance_render:
    movel %a2,%sp@-
    moveal %sp@(12),%a2
    clrl %sp@-
    pea 63
    pea 127
    clrl %sp@-
    clrl %sp@-
    movel %a2,%sp@-
    jsr 0x40070dea
    lea.l %sp@(24),%sp
    pea .Lchance_title
    pea .Lchance_fmt
    pea 0x10
    pea 49
    pea 2
    pea 0x40ea14cc
    movel %a2,%sp@-
    jsr 0x40071a04
    lea.l %sp@(28),%sp
    jsr mlp_chance_value
    lsll #8,%d0
    pea 20
    pea 64
    movel %a2,%sp@-
    movel %d0,%sp@-
    clrl %sp@-
    jsr 0x40050046
    lea.l %sp@(20),%sp
    moveal %sp@+,%a2
    rts
    .section .rodata
.Lchance_title: .asciz "Chance"
.Lchance_fmt: .asciz "%s"
