| Service UI incrémental Load ; activé uniquement avec ML_STORAGE.
| Préparation hors IRQ, un pattern/appel, publication après96 succès.
| Un nouveau serial annule la candidature. Le hook disque doit être installé
| dès le boot ; l'association du slot working96 reste traitée séparément.
    .ifdef ML_WORKING
    .equ ML_BOOT_CONTEXT,1
    .endif
    .ifdef ML_SAVE_FIRST
    .equ ML_BOOT_CONTEXT,1
    .endif
    .data
    .balign 4
    .globl ml_store_load_active,ml_store_load_status
ml_store_load_active: .long 0
ml_store_load_status: .long 0
    .globl ml_store_load_error
ml_store_load_error: .long 0
    .ifdef ML_STORAGE2
    .globl ml_store_ram_only
ml_store_ram_only: .long 0
    .endif
.Lseen: .long 0
.Lserial: .long 0
.Lid: .long 0
.Lslot: .long 0
.Lcursor: .long 0
.Ltable: .long 0
    .text
    .globl ml_store_service
ml_store_service:
    lea.l %sp@(-12),%sp
    moveml %d2/%a2-%a3,%sp@
    movew %sr,%d0
    andil #0x700,%d0
    bne .Lservice_out
    .ifdef ML_BOOT_CONTEXT
    tstl ml_store_load_serial
    bne .Lservice_notified
    jsr ml_store_bootstrap
.Lservice_notified:
    .endif
    .ifdef ML_STORAGE2
    tstl ml_store_suspend_pending
    beq .Lservice_suspend_ready
    clrl ml_store_suspend_pending
    jsr ml_store_suspend
.Lservice_suspend_ready:
    .endif
    tstl ml_store_io_busy
    bne .Lservice_out
    movel ml_store_load_serial,%d2
    beq .Lservice_out
    cmpl .Lseen,%d2
    beq .Lservice_out
    tstl ml_store_io_poison
    bne .Lservice_abort
    tstl ml_store_load_active
    beq .Lservice_start
    cmpl .Lserial,%d2
    beq .Lservice_current
    jsr .Lservice_discard
.Lservice_start:
    moveq #1,%d0
    movel %d0,ml_store_load_error
    jsr ml_store_prepare
    tstl %d0
    beq .Lservice_out
    moveq #2,%d0
    movel %d0,ml_store_load_error
    movel ml_store_load_pending_id,%d0
    beq .Lservice_abort
    movel %d0,.Lid
    moveq #3,%d0
    movel %d0,ml_store_load_error
    movel ml_store_load_pending_slot,%sp@-
    movel .Lid,%sp@-
    jsr ml_store_resolve_slot
    addql #8,%sp
    tstl %d0
    bmi .Lservice_abort
    movel %d0,.Lslot
    .ifdef ML_WORKING
    clrl ml_store_namespace
    movel ml_store_load_pending_slot,%d0
    cmpil #96,%d0
    bne .Lservice_namespace_ready
    moveq #2,%d0
    movel %d0,ml_store_namespace
.Lservice_namespace_ready:
    .endif
    movel %d2,.Lserial
    jsr .Lservice_matches
    tstl %d0
    beq .Lservice_out
    moveq #4,%d0
    movel %d0,ml_store_load_error
    pea 384
    jsr 0x400802e0
    addql #4,%sp
    tstl %d0
    beq .Lservice_abort
    movel %d0,.Ltable
    moveal %d0,%a0
    moveq #95,%d0
.Lservice_zero:
    clrl %a0@+
    subql #1,%d0
    bpl .Lservice_zero
    clrl .Lcursor
    moveq #1,%d0
    movel %d0,ml_store_load_active
    clrl ml_store_load_status
.Lservice_current:
    jsr .Lservice_matches
    tstl %d0
    beq .Lservice_abort
    .ifdef ML_SAVE_FIRST
    | Diagnostic écriture seule : aucun fichier lu au démarrage/Load.
    | Une table B vide est publiée ; Save garde sa relecture de vérification.
    bra .Lservice_publish
    .endif
    moveq #5,%d0
    movel %d0,ml_store_load_error
    movel .Lcursor,%sp@-
    movel .Ltable,%sp@-
    movel .Lslot,%sp@-
    movel .Lid,%sp@-
    movel ml_store_project_ctx,%sp@-
    jsr ml_store_restore_step
    lea.l %sp@(20),%sp
    tstl %d0
    beq .Lservice_abort
    cmpil #2,%d0
    beq .Lservice_publish
    addql #1,.Lcursor
    bra .Lservice_out
.Lservice_publish:
    moveq #6,%d0
    movel %d0,ml_store_load_error
    jsr ml_store_ui_cancel
    movel .Lserial,%sp@-
    movel .Lid,%sp@-
    movel .Ltable,%sp@-
    jsr ml_store_publish
    lea.l %sp@(12),%sp
    tstl %d0
    beq .Lservice_abort
    clrl .Ltable
    movel %d0,%sp@-
    jsr ml_store_retire
    addql #4,%sp
    movel .Lserial,%d0
    movel %d0,.Lseen
    clrl ml_store_load_active
    .ifdef ML_STORAGE2
    moveq #1,%d0
    movel %d0,ml_store_load_ready
    clrl ml_store_ram_only
    .endif
    moveq #1,%d0
    movel %d0,ml_store_load_status
    clrl ml_store_load_error
    bra .Lservice_out
.Lservice_abort:
    jsr .Lservice_discard
    movel ml_store_load_serial,%d0
    movel %d0,.Lseen
    moveq #-1,%d0
    movel %d0,ml_store_load_status
    .ifdef ML_STORAGE2
    tstl ml_store_load_ready
    bne .Lservice_out
    jsr ml_store_load_feedback
    | Une lecture invalide ne doit pas interdire tout jeu B. Table neuve,
    | aucune écriture annexe permise tant qu'un Reload n'a pas réussi.
    movel ml_store_load_error,%d0
    cmpil #5,%d0
    bne .Lservice_out
    jsr ml_store_recover_ram
    .endif
.Lservice_out:
    moveml %sp@,%d2/%a2-%a3
    lea.l %sp@(12),%sp
    rts
.Lservice_discard:
    movel .Ltable,%d0
    beq .Lservice_discarded
    movel %d0,%sp@-
    jsr ml_store_retire
    addql #4,%sp
.Lservice_discarded:
    clrl .Ltable
    clrl ml_store_load_active
    rts
.Lservice_matches:
    jsr 0x400cf866
    tstl %d0
    beq .Lservice_nomatch
    movel %d0,%sp@-
    jsr 0x4000eae2
    addql #4,%sp
    cmpl .Lid,%d0
    bne .Lservice_nomatch
    moveq #1,%d0
    rts
.Lservice_nomatch:
    moveq #0,%d0
    rts

| Le projet de démarrage peut précéder notre hook Load. Récupérer le contexte
| vivant depuis les getters natifs, uniquement si slot/type/identité concordent.
| Aucun accès disque ici. Une notification native ultérieure reste prioritaire.
    .ifdef ML_BOOT_CONTEXT
    .data
    .balign 4
    .globl ml_store_bootstrap_error
ml_store_bootstrap_error: .long 0
    .text
    .globl ml_store_bootstrap
ml_store_bootstrap:
    lea.l %sp@(-12),%sp
    moveml %d2-%d3,%sp@
    movew %sr,%d0
    movel %d0,%sp@(8)
    andil #0x700,%d0
    bne .Lbootstrap_done
    tstl ml_store_load_serial
    bne .Lbootstrap_done
    moveq #1,%d0
    movel %d0,ml_store_bootstrap_error
    jsr 0x400cf866
    tstl %d0
    beq .Lbootstrap_done
    movel %d0,%sp@-
    moveq #2,%d0
    movel %d0,ml_store_bootstrap_error
    jsr 0x4000eae2
    addql #4,%sp
    movel %d0,%d2
    beq .Lbootstrap_done
    moveq #3,%d0
    movel %d0,ml_store_bootstrap_error
    pea 96
    movel %d2,%sp@-
    jsr ml_store_resolve_slot
    addql #8,%sp
    tstl %d0
    bmi .Lbootstrap_done
    | Revalider l'identité après les getters de stockage, avant publication.
    moveq #4,%d0
    movel %d0,ml_store_bootstrap_error
    jsr 0x400cf866
    tstl %d0
    beq .Lbootstrap_done
    movel %d0,%sp@-
    jsr 0x4000eae2
    addql #4,%sp
    cmpl %d2,%d0
    bne .Lbootstrap_done
    movew #0x2700,%sr
    tstl ml_store_load_serial
    bne .Lbootstrap_done
    movel %d2,ml_store_load_pending_id
    moveq #96,%d0
    movel %d0,ml_store_load_pending_slot
    clrl ml_store_load_ready
    moveq #1,%d0
    movel %d0,ml_store_suspend_pending
    movel %d0,ml_store_load_serial
    clrl ml_store_bootstrap_error
.Lbootstrap_done:
    movel %sp@(8),%d0
    movew %d0,%sr
    moveml %sp@,%d2-%d3
    lea.l %sp@(12),%sp
    rts
    .endif

    .ifdef ML_STORAGE2
    .globl ml_store_recover_ram
ml_store_recover_ram:
    lea.l %sp@(-8),%sp
    moveml %d2/%a2,%sp@
    jsr .Lservice_matches
    tstl %d0
    beq .Lram_done
    moveq #1,%d0
    movel %d0,ml_store_ram_only
    pea 384
    jsr 0x400802e0
    addql #4,%sp
    moveal %d0,%a2
    tstl %a2
    beq .Lram_done
    moveal %a2,%a0
    moveq #95,%d0
.Lram_zero:
    clrl %a0@+
    subql #1,%d0
    bpl .Lram_zero
    movel ml_store_load_serial,%sp@-
    movel ml_store_load_pending_id,%sp@-
    movel %a2,%sp@-
    jsr ml_store_publish
    lea.l %sp@(12),%sp
    tstl %d0
    beq .Lram_free
    movel %d0,%sp@-
    jsr ml_store_retire
    addql #4,%sp
    moveq #1,%d0
    movel %d0,ml_store_load_ready
    bra .Lram_done
.Lram_free:
    movel %a2,%sp@-
    jsr ml_store_retire
    addql #4,%sp
.Lram_done:
    moveml %sp@,%d2/%a2
    addql #8,%sp
    rts
    .endif

| Diagnostic : adopter la table déjà éditée après un vrai Save natif réussi.
| self/slot sont ceux du Save ; identité relue sur le projet actif. Aucune
| lecture sidecar, aucune table vidée, aucune notification Load inventée.
    .ifdef ML_SAVE_FIRST
    .text
    .data
    .balign 4
    .globl ml_store_bind_error
ml_store_bind_error: .long 0
    .text
    .globl ml_store_bind_save
ml_store_bind_save:
    lea %sp@(-16),%sp
    moveml %d2-%d3/%a2-%a3,%sp@
    moveq #1,%d0
    movel %d0,ml_store_bind_error
    movew %sr,%d0
    andil #0x700,%d0
    bne .Lbind_fail
    tstl ml_store_load_serial
    bne .Lbind_fail
    tstl ml_store_load_active
    bne .Lbind_fail
    tstl ml_store_io_busy
    bne .Lbind_fail
    tstl ml_store_io_poison
    bne .Lbind_fail
    movel %sp@(24),%d3
    cmpil #95,%d3
    bhi .Lbind_fail
    moveal ml_bank_table,%a2
    tstl %a2
    beq .Lbind_fail
    moveq #2,%d0
    movel %d0,ml_store_bind_error
    movel %sp@(20),%sp@-
    jsr 0x4000eae2
    addql #4,%sp
    movel %d0,%d2
    beq .Lbind_fail
    jsr 0x400cf866
    tstl %d0
    beq .Lbind_fail
    movel %d0,%sp@-
    jsr 0x4000eae2
    addql #4,%sp
    cmpl %d2,%d0
    bne .Lbind_fail
    moveq #3,%d0
    movel %d0,ml_store_bind_error
    tstl ml_store_owner_id
    beq .Lbind_owner_ok
    cmpl ml_store_owner_id,%d2
    bne .Lbind_fail
.Lbind_owner_ok:
    moveq #4,%d0
    movel %d0,ml_store_bind_error
    jsr ml_store_prepare
    tstl %d0
    beq .Lbind_fail
    moveq #5,%d0
    movel %d0,ml_store_bind_error
    jsr 0x400cf866
    tstl %d0
    beq .Lbind_fail
    movel %d0,%sp@-
    jsr 0x4000eae2
    addql #4,%sp
    cmpl %d2,%d0
    bne .Lbind_fail
    movew %sr,%d1
    movel %d1,%sp@-
    movew #0x2700,%sr
    tstl ml_store_load_serial
    bne .Lbind_stale
    cmpal ml_bank_table,%a2
    bne .Lbind_stale
    movel %d2,ml_store_owner_id
    movel %d2,ml_store_load_pending_id
    movel %d3,ml_store_load_pending_slot
    moveq #1,%d0
    movel %d0,ml_store_load_serial
    movel %d0,.Lseen
    movel %d0,ml_store_load_ready
    movel %d0,ml_store_load_status
    clrl ml_store_load_error
    clrl ml_store_ram_only
    clrl ml_store_bind_error
    movel %sp@+,%d1
    movew %d1,%sr
    bra .Lbind_out
.Lbind_stale:
    movel %sp@+,%d1
    movew %d1,%sr
.Lbind_fail:
    moveq #0,%d0
.Lbind_out:
    moveml %sp@,%d2-%d3/%a2-%a3
    lea %sp@(16),%sp
    rts
    .endif
