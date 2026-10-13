| Note 58 : seuls k28..32 transitent par le son natif ; aucune E/S annexe.
    .ifdef LF2_NATIVE_SOUND
    .section .text.lf2n_copy,"ax"
    .globl lf2n_copy_frame
lf2n_copy_frame:
    movel %a0,%sp@-
    movel %a1,%sp@-
    movel %d2,%sp@-
    movel %a2,%sp@-
    jsr lf2n_sync
    addql #8,%sp
    moveal %sp@+,%a1
    moveal %sp@+,%a0
    jmp lf2_copy_frame
    .section .text.lf2n_sync,"ax"
    .globl lf2n_sync
lf2n_sync:
    movel %d2,%sp@-
    moveal %sp@(8),%a0
    lea.l %a0@(192),%a0
    moveal %sp@(12),%a1
    lea.l %a1@(70),%a1
    movel lf2n_epoch,%d2
    cmpl lf2n_seen,%d2
    beq .Lsync_same
    movel %d2,lf2n_seen
    moveq #1,%d2
    bra .Lsync_start
.Lsync_same:
    moveq #0,%d2
.Lsync_start:
    moveq #5,%d0
.Lsync_loop:
    movew %a1@,%d1
    movew %d1,%a0@
    movew %a1@(2),%d1
    movew %d1,%a0@(2)
    movew %a1@(4),%d1
    movew %d1,%a0@(8)
    movew %a1@(6),%d1
    bne .Lsync_dest
    movel #0x7f00,%d1
.Lsync_dest:
    movew %d1,%a0@(6)
    movew %a1@(8),%d1
    movew %d1,%a0@(14)
    tstl %d2
    beq .Lsync_next
    movew #0x4000,%a0@(4)
    clrw %a0@(10)
    clrw %a0@(12)
.Lsync_next:
    lea.l %a0@(16),%a0
    lea.l %a1@(66),%a1
    subql #1,%d0
    bpl .Lsync_loop
    movel %sp@+,%d2
    rts

| write(track,field,valeur native) ; notification native de modification du son.
    .section .text.lf2n_write,"ax"
    .globl lf2n_write
lf2n_write:
    lea.l %sp@(-24),%sp
    moveml %d2-%d4/%a2,%sp@
    movel %sp@(28),%d2
    movel %sp@(32),%d3
    movel %sp@(36),%d4
    lea.l .Lnative_k,%a0
    moveb %a0@(0,%d3:l),%d3
    andil #255,%d3
    cmpil #255,%d3
    beq .Lwrite_done
    jsr 0x400cf866
    movel %d0,%sp@-
    jsr 0x4000eb9c
    addql #4,%sp
    movel %d2,%sp@-
    movel %d0,%sp@-
    jsr 0x400097f0
    addql #8,%sp
    moveal %d0,%a0
    moveal %a0@(4),%a2
    tstl %a2
    beq .Lwrite_done
    moveal %a2@,%a0
    moveal %a0@(40),%a0
    movel %a2,%sp@-
    jsr %a0@
    addql #4,%sp
    tstl %d0
    beq .Lwrite_done
    moveal %d0,%a0
    cmpil #31,%d3
    bne .Lwrite_value
    cmpil #0x7f00,%d4
    bne .Lwrite_value
    moveq #0,%d4
.Lwrite_value:
    movew %d4,%a0@(20,%d3:l:2)
    movel #0x400fd0ac,%d0
    movel %d0,%sp@(16)
    movel %d3,%sp@(20)
    moveal %a2@,%a0
    moveal %a0@(16),%a0
    pea %sp@(16)
    movel %a2,%sp@-
    jsr %a0@
    addql #8,%sp
.Lwrite_done:
    moveml %sp@,%d2-%d4/%a2
    lea.l %sp@(24),%sp
    rts
.Lnative_k: .byte 28,29,255,31,30,255,255,32
    .endif
