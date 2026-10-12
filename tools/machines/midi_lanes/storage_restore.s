| Reconstruction UI dans table384 privée VIDE ; aucune publication audio.
| restore(ctx,id,slot,table) ->1 succès ;0 libère les banques créées.
| Copie manquante/invalide = entrée vide ; I/O poison/allocation = abandon.
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
    .globl ml_store_project_restore
ml_store_project_restore:
    lea.l %sp@(-24),%sp
    moveml %d2-%d4/%a2-%a4,%sp@
    movew %sr,%d0
    andil #0x700,%d0
    bne .Lrestore_fail_early
    moveal %sp@(28),%a2
    movel %sp@(32),%d3
    movel %sp@(36),%d4
    moveal %sp@(40),%a3
    tstl %a2
    beq .Lrestore_fail_early
    tstl %d3
    beq .Lrestore_fail_early
    cmpil #95,%d4
    bhi .Lrestore_fail_early
    tstl %a3
    beq .Lrestore_fail_early
    movel %a3,%d0
    andil #3,%d0
    bne .Lrestore_fail_early
    moveq #0,%d2
.Lrestore_check:
    tstl %a3@(0,%d2:l:4)
    bne .Lrestore_fail_early
    addql #1,%d2
    cmpil #96,%d2
    bcs .Lrestore_check
    moveq #0,%d2
.Lrestore_next:
    movel %d2,%sp@-
    movel %d4,%sp@-
    movel %d3,%sp@-
    movel %a2,%sp@-
    jsr ml_store_session_load
    lea.l %sp@(16),%sp
    tstl ml_store_io_poison
    bne .Lrestore_cleanup
    .ifdef ML_STORAGE2
    cmpil #3,%d0
    beq .Lrestore_skip
    tstl %d0
    beq .Lrestore_cleanup
    .else
    tstl %d0
    beq .Lrestore_skip
    .endif
    pea ML_DATA_BYTES
    jsr 0x400802e0
    addql #4,%sp
    moveal %d0,%a4
    tstl %a4
    beq .Lrestore_cleanup
    movel %a4,%a3@(0,%d2:l:4)
    pea ML_DATA_BYTES
    movel %a4,%sp@-
    movel %a2@(20),%sp@-
    jsr ml_store_snapshot
    lea.l %sp@(12),%sp
    tstl %d0
    beq .Lrestore_cleanup
.Lrestore_skip:
    addql #1,%d2
    cmpil #96,%d2
    bcs .Lrestore_next
    moveq #1,%d0
    bra .Lrestore_out
.Lrestore_cleanup:
    moveq #0,%d2
.Lrestore_free:
    movel %a3@(0,%d2:l:4),%d0
    beq .Lrestore_freed
    clrl %a3@(0,%d2:l:4)
    movel %d0,%sp@-
    jsr 0x400802ec
    addql #4,%sp
.Lrestore_freed:
    addql #1,%d2
    cmpil #96,%d2
    bcs .Lrestore_free
.Lrestore_fail_early:
    moveq #0,%d0
.Lrestore_out:
    moveml %sp@,%d2-%d4/%a2-%a4
    lea.l %sp@(24),%sp
    rts
