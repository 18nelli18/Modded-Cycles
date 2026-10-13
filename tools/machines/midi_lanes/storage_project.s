| Raccordement Save -> toutes les banques visitées du projet propriétaire.
| Prototype : contexte/table/propriétaire initialisés par futur raccordement Load.
| Aucune allocation ici. Refuse identité différente au lieu d'écrire de vieux
| patterns sous un nouveau projet. Save As avec identité renouvelée à traiter.
    .data
    .balign 4
    .globl ml_store_project_ctx,ml_store_owner_id,ml_store_save_status
ml_store_project_ctx: .long 0
ml_store_owner_id: .long 0
ml_store_save_status: .long 0
    .text
    .globl ml_store_save_notice
ml_store_save_notice:
    lea.l %sp@(-20),%sp
    moveml %d2-%d4/%a2-%a3,%sp@
    clrl ml_store_save_status
    .ifdef ML_STORAGE2
    movel %d0,%sp@-
    moveq #1,%d0
    movel %d0,ml_store_save_error
    movel %sp@+,%d0
    .endif
    movew %sr,%d0
    andil #0x700,%d0
    bne .Lproject_done
    .ifdef ML_STORAGE
    .ifdef ML_STORAGE2
    moveq #2,%d0
    movel %d0,ml_store_save_error
    .endif
    tstl ml_store_load_active
    bne .Lproject_done
    .ifdef ML_STORAGE2
    tstl ml_store_load_ready
    beq .Lproject_done
    .endif
    .endif
    .ifdef ML_STORAGE2
    moveq #3,%d0
    movel %d0,ml_store_save_error
    .endif
    moveal ml_store_project_ctx,%a2
    tstl %a2
    beq .Lproject_done
    .ifdef ML_STORAGE2
    moveq #6,%d0
    movel %d0,ml_store_save_error
    .endif
    moveal ml_bank_table,%a3
    tstl %a3
    beq .Lproject_done
    .ifdef ML_STORAGE2
    moveq #7,%d0
    movel %d0,ml_store_save_error
    .endif
    movel %sp@(28),%d3
    .ifdef ML_WORKING
    cmpil #96,%d3
    .else
    cmpil #95,%d3
    .endif
    bhi .Lproject_done
    movel %sp@(24),%sp@-
    .ifdef ML_STORAGE2
    movel %d0,%sp@-
    moveq #4,%d0
    movel %d0,ml_store_save_error
    movel %sp@+,%d0
    .endif
    jsr 0x4000eae2
    addql #4,%sp
    tstl %d0
    beq .Lproject_done
    cmpl ml_store_owner_id,%d0
    bne .Lproject_done
    movel %d0,%d4
    .ifdef ML_WORKING
    clrl ml_store_namespace
    cmpil #96,%d3
    bne .Lproject_namespace_ready
    movel %d3,%sp@-
    movel %d4,%sp@-
    jsr ml_store_resolve_slot
    addql #8,%sp
    tstl %d0
    bmi .Lproject_done
    movel %d0,%d3
    moveq #2,%d0
    movel %d0,ml_store_namespace
.Lproject_namespace_ready:
    .endif
    .ifdef ML_STORAGE3
    movel %d0,%sp@-
    moveq #5,%d0
    movel %d0,ml_store_save_error
    movel %sp@+,%d0
    jsr ml_bank_ui_sync
    tstl %d0
    beq .Lproject_done
    jsr ml_audio_lfo_capture
    .endif
    moveq #0,%d2
.Lproject_next:
    movel %a3@(0,%d2:l:4),%d0
    beq .Lproject_skip
    movel %d0,%sp@-
    movel %d2,%sp@-
    movel %d3,%sp@-
    movel %d4,%sp@-
    movel %a2,%sp@-
    jsr ml_store_session_save
    lea.l %sp@(20),%sp
    tstl %d0
    beq .Lproject_done
.Lproject_skip:
    addql #1,%d2
    cmpil #96,%d2
    bcs .Lproject_next
    moveq #1,%d0
    movel %d0,ml_store_save_status
    .ifdef ML_STORAGE2
    clrl ml_store_save_error
    .endif
.Lproject_done:
    moveml %sp@,%d2-%d4/%a2-%a3
    lea.l %sp@(20),%sp
    rts
