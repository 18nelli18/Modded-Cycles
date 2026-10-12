| Restauration incrémentale UI : un seul pattern par appel.
| step(ctx,id,slot,table384 privée vide,index) ->0 erreur,1 suite,2 terminé.
| Le demandeur libère toute la table sur0 ; aucune publication audio ici.
    .ifdef ML_STORAGE3
    .equ ML_DATA_BYTES,4992
    .equ ML_RECORD_BYTES,5024
    .else
    .ifdef ML_STORAGE2
    .equ ML_DATA_BYTES,4896
    .equ ML_RECORD_BYTES,4928
    .else
    .equ ML_DATA_BYTES,1584
    .equ ML_RECORD_BYTES,1616
    .endif
    .endif
    .text
    .globl ml_store_restore_step
ml_store_restore_step:
    lea.l %sp@(-24),%sp
    moveml %d2-%d4/%a2-%a4,%sp@
    movew %sr,%d0
    andil #0x700,%d0
    bne .Lstep_fail
    moveal %sp@(28),%a2
    movel %sp@(32),%d3
    movel %sp@(36),%d4
    moveal %sp@(40),%a3
    movel %sp@(44),%d2
    tstl ml_store_io_busy
    bne .Lstep_fail
    tstl ml_store_io_poison
    bne .Lstep_fail
    tstl %a2
    beq .Lstep_fail
    movel %a2,%d0
    andil #3,%d0
    bne .Lstep_fail
    tstl %d3
    beq .Lstep_fail
    cmpil #95,%d4
    bhi .Lstep_fail
    cmpil #95,%d2
    bhi .Lstep_fail
    tstl %a3
    beq .Lstep_fail
    movel %a3,%d0
    andil #3,%d0
    bne .Lstep_fail
    tstl %a3@(0,%d2:l:4)
    bne .Lstep_fail
    movel %d2,%sp@-
    movel %d4,%sp@-
    movel %d3,%sp@-
    movel %a2,%sp@-
    jsr ml_store_session_load
    lea.l %sp@(16),%sp
    tstl ml_store_io_poison
    bne .Lstep_fail
    .ifdef ML_STORAGE2
    cmpil #3,%d0
    beq .Lstep_ok
    tstl %d0
    beq .Lstep_fail
    .else
    tstl %d0
    beq .Lstep_ok
    .endif
    pea ML_DATA_BYTES
    jsr 0x400802e0
    addql #4,%sp
    moveal %d0,%a4
    tstl %a4
    beq .Lstep_fail
    pea ML_DATA_BYTES
    movel %a4,%sp@-
    movel %a2@(20),%sp@-
    jsr ml_store_snapshot
    lea.l %sp@(12),%sp
    tstl %d0
    beq .Lstep_free
    movel %a4,%a3@(0,%d2:l:4)
.Lstep_ok:
    moveq #1,%d0
    cmpil #95,%d2
    bne .Lstep_out
    moveq #2,%d0
    bra .Lstep_out
.Lstep_free:
    movel %a4,%sp@-
    jsr 0x400802ec
    addql #4,%sp
.Lstep_fail:
    moveq #0,%d0
.Lstep_out:
    moveml %sp@,%d2-%d4/%a2-%a4
    lea.l %sp@(24),%sp
    rts
