| Extensions CC RAM privées : 96 couples {banque,locks9216}.
| for(banque,créer) : recherche IRQ autorisée, création uniquement UI.
| reset UI avant retrait des banques ; aucune adresse sérialisée.
    .data
    .balign 4
.Lpatterns: .space 768
    .text
    .globl mlkc_locks_for,mlkc_locks_reset
mlkc_locks_for:
    lea %sp@(-16),%sp
    moveml %d2/%a2-%a4,%sp@
    moveal %sp@(20),%a2
    moveq #0,%d0
    tstl %a2
    beq .Llp_done
    lea .Lpatterns,%a3
    subal %a4,%a4
    moveq #95,%d2
.Llp_search:
    cmpal %a3@,%a2
    beq .Llp_found
    tstl %a3@
    bne .Llp_next
    tstl %a4
    bne .Llp_next
    moveal %a3,%a4
.Llp_next:
    addql #8,%a3
    subql #1,%d2
    bpl .Llp_search
    tstl %sp@(24)
    beq .Llp_fail
    tstl %a4
    beq .Llp_fail
    movew %sr,%d0
    andil #0x700,%d0
    bne .Llp_fail
    pea 9216
    jsr 0x400802e0
    addql #4,%sp
    tstl %d0
    beq .Llp_done
    moveal %d0,%a3
    movel %a3,%sp@-
    jsr mlkc_lock_init
    addql #4,%sp
    movew %sr,%d1
    movel %d1,%sp@-
    movew #0x2700,%sr
    movel %a3,%a4@(4)
    movel %a2,%a4@
    movel %sp@+,%d1
    movew %d1,%sr
    movel %a3,%d0
    bra .Llp_done
.Llp_found:
    movel %a3@(4),%d0
    bra .Llp_done
.Llp_fail:
    moveq #0,%d0
.Llp_done:
    moveml %sp@,%d2/%a2-%a4
    lea %sp@(16),%sp
    rts
mlkc_locks_reset:
    lea %sp@(-12),%sp
    moveml %d2/%a2-%a3,%sp@
    movew %sr,%d0
    andil #0x700,%d0
    bne .Llreset_done
    lea .Lpatterns,%a2
    moveq #95,%d2
.Llreset_next:
    movew %sr,%d0
    movel %d0,%sp@-
    movew #0x2700,%sr
    moveal %a2@(4),%a3
    clrl %a2@
    clrl %a2@(4)
    movel %sp@+,%d0
    movew %d0,%sr
    tstl %a3
    beq .Llreset_skip
    movel %a3,%sp@-
    jsr 0x400802ec
    addql #4,%sp
.Llreset_skip:
    addql #8,%a2
    subql #1,%d2
    bpl .Llreset_next
.Llreset_done:
    moveml %sp@,%d2/%a2-%a3
    lea %sp@(12),%sp
    rts
