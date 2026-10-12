| Libérer une table exclusivement retirée ou candidate privée, à IPL0.
| Protège la table active, le contexte initial et sa table embarquée.
| retire(table) ->1 succès,0 refus. Entrées uniques allouées par le runtime.
    .text
    .globl ml_store_retire
ml_store_retire:
    lea.l %sp@(-12),%sp
    moveml %d2/%a2-%a3,%sp@
    movew %sr,%d0
    andil #0x700,%d0
    bne .Lretire_fail
    moveal %sp@(16),%a2
    tstl %a2
    beq .Lretire_fail
    movel %a2,%d0
    andil #3,%d0
    bne .Lretire_fail
    cmpal ml_bank_table,%a2
    beq .Lretire_fail
    moveal ml_context,%a3
    moveq #0,%d2
.Lretire_loop:
    movel %a2@(0,%d2:l:4),%d0
    beq .Lretire_next
    clrl %a2@(0,%d2:l:4)
    cmpl %a3,%d0
    beq .Lretire_next
    .ifdef ML_STORAGE2
    lea.l %a3@(2340),%a0
    cmpl %a0,%d0
    beq .Lretire_next
    .endif
    cmpl ml_bank_empty,%d0
    beq .Lretire_next
    movel %d0,%sp@-
    jsr 0x400802ec
    addql #4,%sp
.Lretire_next:
    addql #1,%d2
    cmpil #96,%d2
    bcs .Lretire_loop
    lea.l %a3@(1956),%a0
    cmpal %a0,%a2
    beq .Lretire_ok
    movel %a2,%sp@-
    jsr 0x400802ec
    addql #4,%sp
.Lretire_ok:
    moveq #1,%d0
    bra .Lretire_out
.Lretire_fail:
    moveq #0,%d0
.Lretire_out:
    moveml %sp@,%d2/%a2-%a3
    lea.l %sp@(12),%sp
    rts
