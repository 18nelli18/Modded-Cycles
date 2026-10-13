| Clipboard CC B complémentaire : 24 octets/pas,1536/voie. UI et IPL7 permis.
    .data
    .balign 4
.Lstep: .rept 6
    .long -1
    .endr
.Llane: .rept 384
    .long -1
    .endr
.Lundo: .rept 384
    .long -1
    .endr
    .text
    .globl mlkc_clip_prepare,mlkc_step_clip,mlkc_lane_clip
mlkc_clip_prepare:
    pea 1
    movel ml_pattern,%sp@-
    jsr mlkc_locks_for
    addql #8,%sp
    rts
| step_clip(op0copie/2colle,pattern,voie,pas)
mlkc_step_clip:
    lea %sp@(-12),%sp
    moveml %d2/%a2-%a3,%sp@
    movel %sp@(16),%d2
    clrl %sp@-
    movel %sp@(24),%sp@-
    jsr mlkc_locks_for
    addql #8,%sp
    tstl %d0
    beq .Lsc_empty
    clrl %sp@-
    movel %sp@(32),%sp@-
    movel %sp@(32),%sp@-
    movel %d0,%sp@-
    jsr mlkc_lock_at
    lea %sp@(16),%sp
    moveal %d0,%a2
    lea .Lstep,%a3
    tstl %d2
    beq .Lsc_copy
    movel %a2,%d0
    moveal %a3,%a2
    moveal %d0,%a3
.Lsc_copy:
    moveq #5,%d2
.Lsc_loop:
    movel %a2@+,%a3@+
    subql #1,%d2
    bpl .Lsc_loop
    bra .Lsc_done
.Lsc_empty:
    tstl %d2
    bne .Lsc_done
    lea .Lstep,%a0
    moveq #-1,%d0
    moveq #5,%d2
.Lsc_zero:
    movel %d0,%a0@+
    subql #1,%d2
    bpl .Lsc_zero
.Lsc_done:
    moveml %sp@,%d2/%a2-%a3
    lea %sp@(12),%sp
    rts
| lane_clip(op0copy/1snapshot/2undo/3paste/4clear)
mlkc_lane_clip:
    lea %sp@(-16),%sp
    moveml %d2-%d3/%a2-%a3,%sp@
    movel %sp@(20),%d3
    clrl %sp@-
    movel ml_pattern,%sp@-
    jsr mlkc_locks_for
    addql #8,%sp
    tstl %d0
    beq .Llane_none
    moveal %d0,%a2
    movel mlp_track,%d0
    muluw #1536,%d0
    addal %d0,%a2
    lea .Llane,%a3
    tstl %d3
    beq .Llane_copy
    lea .Lundo,%a3
    cmpil #1,%d3
    beq .Llane_copy
    cmpil #4,%d3
    beq .Llane_clear
    cmpil #2,%d3
    beq .Llane_apply
    lea .Llane,%a3
.Llane_apply:
    movel %a2,%d0
    moveal %a3,%a2
    moveal %d0,%a3
.Llane_copy:
    movel #383,%d2
.Llane_loop:
    movel %a2@+,%a3@+
    subql #1,%d2
    bpl .Llane_loop
    bra .Llane_done
.Llane_none:
    lea .Llane,%a2
    tstl %d3
    beq .Llane_clear
    lea .Lundo,%a2
    cmpil #1,%d3
    bne .Llane_done
.Llane_clear:
    movel #383,%d2
    moveq #-1,%d0
.Llane_erase:
    movel %d0,%a2@+
    subql #1,%d2
    bpl .Llane_erase
.Llane_done:
    moveml %sp@,%d2-%d3/%a2-%a3
    lea %sp@(16),%sp
    rts
