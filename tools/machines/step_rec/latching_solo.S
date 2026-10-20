| Test-only FUNC+track-pad solo extension for the existing latched mute view.
| Called in place of the native mute toggle from QuickMuteMenu's pad handler.

    .equ SOLO_ACTIVE, 0x401487c0
    .equ SOLO_TARGET, 0x401487c1
    .equ SOLO_MASK,   0x401487c2
    .equ SOLO_OBJECT, 0x401487c4

    .section .solo,"ax"
    .globl solo_pad, solo_exit

solo_pad:
    lea.l   %sp@(-24),%sp
    movem.l %d2-%d5/%a2-%a3,%sp@
    | The 24-byte local frame holds the saved registers; MOVEM does not
    | move SP for this non-predecrement addressing mode.
    moveal  %sp@(28),%a2
    movel   %sp@(32),%d2
    tstb    0x401487ed
    beqw    sp_native
    moveq   #1,%d0
    movel   %d0,%sp@-
    jsr     0x4007faf4
    addql   #4,%sp
    tstl    %d0
    beqw    sp_normal

    tstb    SOLO_ACTIVE
    beqw    sp_snapshot
    cmpb    SOLO_TARGET,%d2
    beqw    sp_restore
    bra.w   sp_apply

sp_snapshot:
    movel   %a2,SOLO_OBJECT
    clrb    SOLO_MASK
    moveq   #0,%d3
sp_snap_loop:
    movel   %d2,%d4
    movel   %d3,%d2
    bsr.w   sp_get
    movel   %d4,%d2
    tstl    %d0
    beqw    sp_snap_next
    bset    %d3,SOLO_MASK
sp_snap_next:
    addql   #1,%d3
    cmpil   #6,%d3
    bcsw    sp_snap_loop
    moveb   %d2,SOLO_TARGET
    moveq   #1,%d0
    moveb   %d0,SOLO_ACTIVE
    bra.w   sp_apply

sp_restore:
    moveb   SOLO_MASK,%d4
    bsr.w   sp_apply_mask
    clrb    SOLO_ACTIVE
    bra.w   sp_done

sp_normal:
    tstb    SOLO_ACTIVE
    beqw    sp_native
    moveb   SOLO_MASK,%d4
    bsr.w   sp_apply_mask
    clrb    SOLO_ACTIVE
sp_native:
    pea     1
    movel   %d2,%sp@-
    movel   %a2,%sp@-
    jsr     0x40013904
    lea.l   %sp@(12),%sp
    bra.w   sp_done

sp_apply:
    moveb   %d2,SOLO_TARGET
    moveq   #0,%d3
sp_apply_loop:
    movel   %d2,%d5
    movel   %d3,%d2
    bsr.w   sp_get
    movel   %d5,%d2
    moveq   #0,%d4
    cmpb    %d3,%d2
    beqw    sp_desired
    moveq   #1,%d4
sp_desired:
    cmpb    %d4,%d0
    beqw    sp_apply_next
    pea     1
    movel   %d3,%sp@-
    movel   %a2,%sp@-
    jsr     0x40013904
    lea.l   %sp@(12),%sp
sp_apply_next:
    addql   #1,%d3
    cmpil   #6,%d3
    bcsw    sp_apply_loop
sp_done:
    moveq   #1,%d0
    movem.l %sp@,%d2-%d5/%a2-%a3
    lea.l   %sp@(24),%sp
    rts

| d3 = track, a2 = mute object. Return current mute state in d0.
sp_get:
    movel   %d3,%sp@-
    movel   %a2,%sp@-
    jsr     0x4001263c
    addql   #8,%sp
    rts

| d4 = desired mute bitmask, a2 = mute object.
sp_apply_mask:
    lea.l   %sp@(-20),%sp
    movem.l %d2-%d5/%a3,%sp@
    moveq   #0,%d3
sm_loop:
    move.l  %d4,%d2
    move.l  %d3,%d0
    btst    %d0,%d2
    sne     %d5
    andil   #1,%d5
    bsr.w   sp_get
    cmpb    %d5,%d0
    beqw    sm_next
    pea     1
    movel   %d3,%sp@-
    movel   %a2,%sp@-
    jsr     0x40013904
    lea.l   %sp@(12),%sp
sm_next:
    addql   #1,%d3
    cmpil   #6,%d3
    bcsw    sm_loop
    movem.l %sp@,%d2-%d5/%a3
    lea.l   %sp@(20),%sp
    rts

| The native latch handler reaches this when FUNC toggles mute mode off.
| Restore the saved mute bitmap before returning to its normal false result.
solo_exit:
    lea.l   %sp@(-16),%sp
    movem.l %d2-%d4/%a2,%sp@
    clrb    0x401487ed
    tstb    SOLO_ACTIVE
    beqw    sx_done
    moveal  SOLO_OBJECT,%a2
    moveq   #0,%d4
    moveb   SOLO_MASK,%d4
    bsr.w   sp_apply_mask
    clrb    SOLO_ACTIVE
sx_done:
    moveq   #0,%d0
    movem.l %sp@,%d2-%d4/%a2
    lea.l   %sp@(16),%sp
    rts
