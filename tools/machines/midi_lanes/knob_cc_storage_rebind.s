| Reprise d'une notification de projet devenue périmée pendant le boot.
| Identité et slot natifs revérifiés ; jamais de fichier lu/écrit ici.
| Une nouvelle notification gagne toujours : comparaison serial sous IPL7.
    .text
    .globl ml_store_rebind_live
ml_store_rebind_live:
    lea %sp@(-16),%sp
    moveml %d2-%d3/%a2,%sp@
    movew %sr,%d0
    movel %d0,%sp@(12)
    andil #0x700,%d0
    bne .Lrebind_no
    movel ml_store_load_serial,%d2
    jsr 0x400cf866
    tstl %d0
    beq .Lrebind_no
    movel %d0,%sp@-
    jsr 0x4000eae2
    addql #4,%sp
    movel %d0,%d3
    beq .Lrebind_no
    pea 96
    movel %d3,%sp@-
    jsr ml_store_resolve_slot
    addql #8,%sp
    tstl %d0
    bmi .Lrebind_no
    jsr 0x400cf866
    tstl %d0
    beq .Lrebind_no
    movel %d0,%sp@-
    jsr 0x4000eae2
    addql #4,%sp
    cmpl %d3,%d0
    bne .Lrebind_no
    movew #0x2700,%sr
    cmpl ml_store_load_serial,%d2
    bne .Lrebind_no
    movel %d3,ml_store_load_pending_id
    moveq #96,%d0
    movel %d0,ml_store_load_pending_slot
    clrl ml_store_load_ready
    moveq #1,%d0
    movel %d0,ml_store_suspend_pending
    addql #1,ml_store_load_serial
    clrl ml_store_load_status
    moveq #1,%d0
    bra .Lrebind_done
.Lrebind_no:
    moveq #0,%d0
.Lrebind_done:
    movel %sp@(12),%d1
    movew %d1,%sr
    moveml %sp@,%d2-%d3/%a2
    lea %sp@(16),%sp
    rts

| Diagnostic court sur Save refusé : étape identitaire/notes/CC/publication.
    .data
.Lprogress: .asciz "LOAD I00/96"
    .text
    .globl ml_store_loading_message
ml_store_loading_message:
    lea .Lprogress,%a0
    moveb #73,%a0@(5)
    movel ml_store_restore_phase,%d0
    cmpil #1,%d0
    bne .Lphase_cc
    moveb #78,%a0@(5)
.Lphase_cc:
    cmpil #2,%d0
    bne .Lphase_publish
    moveb #67,%a0@(5)
.Lphase_publish:
    cmpil #3,%d0
    bne .Ldigits
    moveb #80,%a0@(5)
.Ldigits:
    movel ml_store_restore_cursor,%d0
    cmpil #95,%d0
    bls .Lbounded
    moveq #95,%d0
.Lbounded:
    moveq #48,%d1
.Ltens:
    cmpil #10,%d0
    bcs .Lones
    subil #10,%d0
    addql #1,%d1
    bra .Ltens
.Lones:
    moveb %d1,%a0@(6)
    addil #48,%d0
    moveb %d0,%a0@(7)
    movel %a0,%d0
    rts
