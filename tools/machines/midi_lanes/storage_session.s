| Coordination UI par identité projet, slot, pattern. Prototype hors flasher.
| ctx44 = contexte storage_initial, tampons privés et chemins >=35 octets.
| save(ctx,id,slot,pattern,bank) / load(ctx,id,slot,pattern) -> bool/copie.
| load remplit ctx.payload privé ; publication musicale séparée obligatoire.
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
    .ifdef ML_WORKING
    .data
    .balign 4
    .globl ml_store_namespace
ml_store_namespace: .long 0
    .endif
    .text
    .globl ml_store_session_save,ml_store_session_load
ml_store_session_save:
    lea.l %sp@(-16),%sp
    moveml %d2/%a2-%a4,%sp@
    moveal %sp@(20),%a2
    .ifdef ML_STORAGE2
    movel %d0,%sp@-
    moveq #8,%d0
    movel %d0,ml_store_save_error
    movel %sp@+,%d0
    .endif
    jsr .Lsession_paths
    tstl %d0
    beq .Lsession_fail
    | Créer/valider racine, puis sous-dossier identité (préfixe des chemins).
    .ifdef ML_STORAGE2
    movel %d0,%sp@-
    moveq #9,%d0
    movel %d0,ml_store_save_error
    movel %sp@+,%d0
    .endif
    movel %a2@(16),%sp@-
    pea .Lroot_path
    pea .Lroot_name
    pea 2
    jsr ml_store_directory
    lea.l %sp@(16),%sp
    tstl %d0
    beq .Lsession_fail
    moveal %a2@,%a3
    .ifdef ML_STORAGE2
    movel %d0,%sp@-
    moveq #10,%d0
    movel %d0,ml_store_save_error
    movel %sp@+,%d0
    .endif
    clrb %a3@(25)
    movel %a2@(16),%sp@-
    movel %a3,%sp@-
    pea %a3@(14)
    movel %d0,%sp@-
    jsr ml_store_directory
    lea.l %sp@(16),%sp
    moveb #47,%a3@(25)
    tstl %d0
    beq .Lsession_fail
    movel %d0,%a2@(32)
    .ifdef ML_STORAGE2
    movel %d0,%sp@-
    moveq #11,%d0
    movel %d0,ml_store_save_error
    movel %sp@+,%d0
    .endif
    pea ML_DATA_BYTES
    movel %a2@(20),%sp@-
    movel %sp@(44),%sp@-
    jsr ml_store_snapshot
    lea.l %sp@(12),%sp
    tstl %d0
    beq .Lsession_fail
    | Renouvellement valide prioritaire ; initial refuse toute copie existante.
    .ifdef ML_STORAGE2
    movel %d0,%sp@-
    moveq #12,%d0
    movel %d0,ml_store_save_error
    movel %sp@+,%d0
    .endif
    movel %a2,%sp@-
    jsr ml_store_io_begin
    tstl %d0
    beq .Lsession_unpush
    jsr ml_store_commit
    movel %d0,%d2
    jsr ml_store_io_end
    andl %d2,%d0
    addql #4,%sp
    tstl %d0
    bne .Lsession_out
    .ifdef ML_STORAGE2
    | Ne pas masquer une erreur writer par un faux échec de création.
    movel ml_store_save_error,%d0
    cmpil #14,%d0
    bcc .Lsession_fail
    movel %d0,%sp@-
    moveq #13,%d0
    movel %d0,ml_store_save_error
    movel %sp@+,%d0
    .endif
    movel %a2,%sp@-
    jsr ml_store_initial
    addql #4,%sp
    bra .Lsession_out
.Lsession_unpush:
    addql #4,%sp
    bra .Lsession_fail
ml_store_session_load:
    lea.l %sp@(-16),%sp
    moveml %d2/%a2-%a4,%sp@
    moveal %sp@(20),%a2
    jsr .Lsession_paths
    tstl %d0
    beq .Lsession_fail
    jsr ml_store_io_begin
    tstl %d0
    beq .Lsession_fail
    movel %a2@(28),%sp@-
    movel %a2@(24),%sp@-
    movel %a2@(12),%sp@-
    movel %a2@(8),%sp@-
    movel %a2@(4),%sp@-
    movel %a2@,%sp@-
    movel %a2@(20),%sp@-
    jsr ml_store_load
    lea.l %sp@(28),%sp
    movel %d0,%d2
    jsr ml_store_io_end
    tstl %d0
    beq .Lsession_fail
    movel %d2,%d0
    .ifdef ML_STORAGE2
    bne .Lsession_out
    movel %a2,%sp@-
    jsr ml_store_presence
    addql #4,%sp
    tstl %d0
    bne .Lsession_fail
    moveq #3,%d0
    .endif
    bra .Lsession_out
.Lsession_fail:
    moveq #0,%d0
.Lsession_out:
    moveml %sp@,%d2/%a2-%a4
    lea.l %sp@(16),%sp
    rts
| Sous-routine interne : arguments caller +24/+28/+32, décalage retour +4.
.Lsession_paths:
    tstl %a2
    beq .Lpaths_bad
    movel %a2,%d0
    andil #3,%d0
    bne .Lpaths_bad
    movel %sp@(32),%d0
    movel %d0,%a2@(24)
    movel %sp@(36),%d0
    movel %d0,%a2@(28)
    movel %sp@(28),%d2
    moveq #0,%d0
    moveq #0,%d1
    movel %a2@,%a3
    movel %a2@(4),%a4
.Lpaths_next:
    movel %a2@(24),%sp@-
    .ifdef ML_WORKING
    movel ml_store_namespace,%sp@-
    .else
    clrl %sp@-
    .endif
    movel %d0,%sp@-
    movel %a2@(28),%sp@-
    movel %d2,%sp@-
    pea 35
    movel %a3,%sp@-
    jsr ml_store_path
    lea.l %sp@(28),%sp
    tstl %d0
    beq .Lpaths_bad
    cmpal %a4,%a3
    beq .Lpaths_ready
    movel %a4,%a3
    moveq #1,%d0
    bra .Lpaths_next
.Lpaths_ready:
    moveal %a2@,%a0
    lea.l %a0@(26),%a0
    movel %a0,%a2@(36)
    moveal %a2@(4),%a0
    lea.l %a0@(26),%a0
    movel %a0,%a2@(40)
    moveq #1,%d0
    rts
.Lpaths_bad:
    moveq #0,%d0
    rts
    .section .rodata
.Lroot_name: .asciz "ModdedCycles"
.Lroot_path: .asciz "/ModdedCycles"
