| Résultat explicite des sidecars, distinct du succès du Save audio natif.
    .ifdef ML_WORKING
    .equ ML_BOOT_CONTEXT,1
    .endif
    .ifdef ML_SAVE_FIRST
    .equ ML_BOOT_CONTEXT,1
    .endif
    .ifdef ML_STORAGE2
    .data
    .balign 4
    .globl ml_store_save_error
ml_store_save_error: .long 0
    .text
    .globl ml_store_save_feedback,ml_store_load_feedback
ml_store_save_feedback:
    lea .Lsave_failed,%a0
    movel ml_store_save_status,%d0
    subql #1,%d0
    beq .Lfeedback_ok
    tstl ml_store_io_poison
    beq .Lfeedback_stage
    lea .Ldisk,%a0
    bra .Lfeedback_show
.Lfeedback_stage:
    movel ml_store_save_error,%d0
    cmpil #25,%d0
    bhi .Lfeedback_show
    cmpil #17,%d0
    beq .Lwrite_detail
    cmpil #3,%d0
    beq .Lcontext_detail
    lea .Lerrors,%a1
    moveal %a1@(0,%d0:l:4),%a0
    bra .Lfeedback_show
.Lwrite_detail:
    lea .Lwrite_negative,%a0
    tstl ml_store_write_count
    bmi .Lfeedback_show
    lea .Lwrite_zero,%a0
    beq .Lfeedback_show
    lea .Lwrite_short,%a0
    bra .Lfeedback_show
| Contexte absent : distinguer notification, service UI et allocation.
.Lcontext_detail:
    .ifdef ML_SAVE_FIRST
    movel ml_store_bind_error,%d0
    beq .Lcontext_no_save_bind
    cmpil #5,%d0
    bhi .Lcontext_no_save_bind
    lea .Lbind_errors,%a1
    moveal %a1@(0,%d0:l:4),%a0
    bra .Lfeedback_show
.Lcontext_no_save_bind:
    .endif
    lea .Lctx_load,%a0
    tstl ml_store_load_serial
    bne .Lcontext_has_load
    .ifdef ML_BOOT_CONTEXT
    movel ml_store_bootstrap_error,%d0
    beq .Lfeedback_show
    cmpil #4,%d0
    bhi .Lfeedback_show
    lea .Lbootstrap_errors,%a1
    moveal %a1@(0,%d0:l:4),%a0
    .endif
    bra .Lfeedback_show
.Lcontext_has_load:
    lea .Lctx_ui,%a0
    tstl ml_store_ui_seen
    beq .Lfeedback_show
    lea .Lctx_ipl,%a0
    tstl ml_store_ui_ready
    beq .Lfeedback_show
    lea .Lctx_disk,%a0
    tstl ml_store_io_poison
    bne .Lfeedback_show
    lea .Lctx_busy,%a0
    tstl ml_store_io_busy
    bne .Lfeedback_show
    lea .Lctx_ram,%a0
    movel ml_store_load_error,%d0
    subql #1,%d0
    beq .Lfeedback_show
    lea .Lctx_state,%a0
    bra .Lfeedback_show
.Lfeedback_ok:
    .ifdef ML_CC_STORAGE
    tstl mlkcs_save_error
    beq .Lfeedback_cc_ok
    lea .Lcc_save_err,%a0
    bra .Lfeedback_show
.Lfeedback_cc_ok:
    .endif
    lea .Lsave_ok,%a0
    bra .Lfeedback_show
ml_store_load_feedback:
    lea .Lload_failed,%a0
    movel ml_store_load_error,%d0
    cmpil #6,%d0
    bhi .Lfeedback_show
    cmpil #5,%d0
    bne .Lload_general
    tstl ml_store_io_poison
    bne .Lload_disk
    movel ml_store_read_error,%d0
    cmpil #7,%d0
    bhi .Lload_general_read
    lea .Lread_errors,%a1
    moveal %a1@(0,%d0:l:4),%a0
    bra .Lfeedback_show
.Lload_disk:
    lea .Ldisk,%a0
    bra .Lfeedback_show
.Lload_general_read:
    moveq #5,%d0
.Lload_general:
    lea .Lload_errors,%a1
    moveal %a1@(0,%d0:l:4),%a0
.Lfeedback_show:
    movel %a0,%sp@-
    jsr TG_show_popup
    addql #4,%sp
    rts
.Lsave_ok: .asciz "MIDI SAVED"
.Lsave_failed: .asciz "MIDI SAVE ERR"
.Lload_failed: .asciz "MIDI LOAD ERR"
    .balign 4
.Lread_errors:
    .long .Lload_record,.Lread_path,.Lread_lookup,.Lread_guard,.Lread_invalid,.Lread_open,.Lread_size,.Lread_close
.Lload_errors:
    .long .Lload_failed,.Lload_context,.Lload_identity,.Lload_slot
    .long .Lload_table,.Lload_record,.Lload_publish
.Lerrors:
    .long .Lsave_failed,.Lirq,.Lbusy,.Lcontext,.Lowner,.Lsync
    .long .Lbank,.Lslot,.Lpath,.Lroot,.Ldir,.Lsnapshot
    .long .Lcommit,.Linitial,.Ldata,.Lopen,.Lallocate,.Lwrite,.Lflush,.Lclose
    .long .Lbuffers,.Llookup_a,.Llookup_b,.Lguard,.Lram_only,.Lverify
    .ifdef ML_BOOT_CONTEXT
    .balign 4
.Lbootstrap_errors:
    .long .Lctx_load,.Lboot_project,.Lboot_id,.Lboot_slot,.Lboot_changed
.Lboot_project: .asciz "CTX: PROJECT"
.Lboot_id: .asciz "CTX: ID"
.Lboot_slot: .asciz "CTX: SLOT"
.Lboot_changed: .asciz "CTX: CHANGED"
    .endif
    .ifdef ML_SAVE_FIRST
    .balign 4
.Lbind_errors:
    .long .Lctx_load,.Lbind_state,.Lbind_id,.Lbind_owner,.Lbind_ram,.Lbind_changed
.Lbind_state: .asciz "CTX: SAVE STATE"
.Lbind_id: .asciz "CTX: SAVE ID"
.Lbind_owner: .asciz "CTX: SAVE OWNER"
.Lbind_ram: .asciz "CTX: SAVE RAM"
.Lbind_changed: .asciz "CTX: SAVE CHANGED"
    .endif
.Lverify: .asciz "MIDI: VERIFY"
.Lram_only: .asciz "MIDI: RAM ONLY"
.Lctx_load: .asciz "CTX: NO LOAD"
.Lctx_ui: .asciz "CTX: NO UI"
.Lctx_ipl: .asciz "CTX: UI IPL"
.Lctx_disk: .asciz "CTX: DISK"
    .ifdef ML_CC_STORAGE
.Lcc_save_err: .asciz "CC SAVE ERR"
    .endif
.Lctx_busy: .asciz "CTX: BUSY"
.Lctx_ram: .asciz "CTX: RAM"
.Lctx_state: .asciz "CTX: STATE"
.Lread_path: .asciz "MIDI LOAD: PATH"
.Lread_lookup: .asciz "MIDI LOAD: LOOKUP"
.Lread_guard: .asciz "MIDI LOAD: BUSY"
.Lread_invalid: .asciz "MIDI LOAD: FORMAT"
.Lread_open: .asciz "MIDI LOAD: OPEN"
.Lread_size: .asciz "MIDI LOAD: SIZE"
.Lread_close: .asciz "MIDI LOAD: CLOSE"
.Lload_context: .asciz "MIDI LOAD: RAM"
.Lload_identity: .asciz "MIDI LOAD: ID"
.Lload_slot: .asciz "MIDI LOAD: SLOT"
.Lload_table: .asciz "MIDI LOAD: TABLE"
.Lload_record: .asciz "MIDI LOAD: READ"
.Lload_publish: .asciz "MIDI LOAD: APPLY"
.Ldisk: .asciz "MIDI: DISK"
.Lbuffers: .asciz "MIDI: BUFFERS"
.Llookup_a: .asciz "MIDI: LOOKUP A"
.Llookup_b: .asciz "MIDI: LOOKUP B"
.Lguard: .asciz "MIDI: GUARD"
.Lirq: .asciz "MIDI: IRQ"
.Lbusy: .asciz "MIDI: LOADING"
.Lbank: .asciz "MIDI: BANK"
.Lslot: .asciz "MIDI: SLOT"
.Lcontext: .asciz "MIDI: CONTEXT"
.Lowner: .asciz "MIDI: OWNER"
.Lsync: .asciz "MIDI: SYNC"
.Lpath: .asciz "MIDI: PATH"
.Lroot: .asciz "MIDI: ROOT"
.Ldir: .asciz "MIDI: DIR"
.Lsnapshot: .asciz "MIDI: SNAP"
.Lcommit: .asciz "MIDI: COMMIT"
.Linitial: .asciz "MIDI: CREATE"
.Ldata: .asciz "MIDI: DATA"
.Lopen: .asciz "MIDI: OPEN"
.Lallocate: .asciz "MIDI: ALLOC"
.Lwrite: .asciz "MIDI: WRITE"
.Lwrite_negative: .asciz "WRITE: FAIL"
.Lwrite_zero: .asciz "WRITE: ZERO"
.Lwrite_short: .asciz "WRITE: SHORT"
.Lflush: .asciz "MIDI: FLUSH"
.Lclose: .asciz "MIDI: CLOSE"
    .balign 2
    .endif
