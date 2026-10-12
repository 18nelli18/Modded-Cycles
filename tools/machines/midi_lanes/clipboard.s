| Presse-papiers B privé. REC9 copy / PLAY10 clear / STOP11 paste.
| Longueur/vitesse et64 pas copiés ; canal/port/mute/enable destination gardés.
| Deuxième clear/paste même lane : undo. Aucune donnée audio ni clipboard stock.
    .data
    .balign 4
mlp_clip_ready: .long 0
mlp_clip_keys: .long 0
mlp_clip_undo_op: .long 0
mlp_clip_undo_lane: .long 0
mlp_clip_buffer: .space 264
mlp_clip_undo: .space 264
    .text
    .globl mlp_clip_key
mlp_clip_key:
    lea.l %sp@(-24),%sp
    moveml %d2-%d4/%a2-%a3,%sp@
    movew %sr,%d0
    movel %d0,%sp@(20)
    andil #0x700,%d0
    bne .Lclip_pass
    movel %sp@(28),%d2
    subql #8,%d2
    subql #1,%d2
    cmpil #2,%d2
    bhi .Lclip_pass
    movel %sp@(32),%d3
    btst #0,%d3
    bne .Lclip_down
    movel mlp_clip_keys,%d0
    btst %d2,%d0
    beq .Lclip_pass
    bclr %d2,%d0
    movel %d0,mlp_clip_keys
    bra .Lclip_used
.Lclip_down:
    movel mlp_clip_keys,%d0
    btst %d2,%d0
    bne .Lclip_used
    tstl mlp_func
    beq .Lclip_pass
    btst #5,%d3
    bne .Lclip_used
    bset %d2,%d0
    movel %d0,mlp_clip_keys
    movel mlp_track,%d4
    cmpil #5,%d4
    bhi .Lclip_used
    moveal ml_pattern,%a2
    tstl %a2
    beq .Lclip_used
    movel %d4,%d0
    muluw #264,%d0
    addal %d0,%a2
    tstl %d2
    beq .Lclip_copy
    cmpil #2,%d2
    bne .Lclip_mutate
    tstl mlp_clip_ready
    beq .Lclip_used
.Lclip_mutate:
    jsr mlp_keyboard_cancel
    movel %d4,%sp@-
    movel ml_runtime,%sp@-
    jsr ml_stop
    addql #8,%sp
    movew #0x2700,%sr
    lea mlp_clip_undo,%a3
    cmpal mlp_clip_undo_lane,%a2
    bne .Lclip_new_undo
    cmpl mlp_clip_undo_op,%d2
    bne .Lclip_new_undo
    clrl mlp_clip_undo_op
    clrl mlp_clip_undo_lane
    bra .Lclip_apply
.Lclip_new_undo:
    movel %a2,mlp_clip_undo_lane
    movel %d2,mlp_clip_undo_op
    moveal %a2,%a0
    moveal %a3,%a1
    moveq #65,%d0
.Lclip_snapshot:
    movel %a0@+,%a1@+
    subql #1,%d0
    bpl .Lclip_snapshot
    cmpil #1,%d2
    beq .Lclip_clear
    lea mlp_clip_buffer,%a3
.Lclip_apply:
    movew %a3@(4),%d0
    movew %d0,%a2@(4)
    lea %a3@(8),%a0
    lea %a2@(8),%a1
    moveq #63,%d0
.Lclip_apply_loop:
    movel %a0@+,%a1@+
    subql #1,%d0
    bpl .Lclip_apply_loop
    bra .Lclip_changed
.Lclip_clear:
    lea %a2@(8),%a0
    moveq #63,%d0
    movel #0x48640100,%d1
.Lclip_clear_loop:
    movel %d1,%a0@+
    subql #1,%d0
    bpl .Lclip_clear_loop
.Lclip_changed:
    clrl mlp_held
    clrl mlp_remove
    clrl mlp_changed
    movel %sp@(20),%d0
    movew %d0,%sr
    movel mlp_obj,%sp@-
    jsr mlp_redraw
    addql #4,%sp
    bra .Lclip_used
.Lclip_copy:
    movew #0x2700,%sr
    moveal %a2,%a0
    lea mlp_clip_buffer,%a1
    moveq #65,%d0
.Lclip_copy_loop:
    movel %a0@+,%a1@+
    subql #1,%d0
    bpl .Lclip_copy_loop
    moveq #1,%d0
    movel %d0,mlp_clip_ready
    movel %sp@(20),%d0
    movew %d0,%sr
.Lclip_used:
    moveq #1,%d0
    bra .Lclip_out
.Lclip_pass:
    moveq #0,%d0
.Lclip_out:
    moveml %sp@,%d2-%d4/%a2-%a3
    lea.l %sp@(24),%sp
    rts
