| Résultat explicite des sidecars, distinct du succès du Save audio natif.
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
    cmpil #23,%d0
    bhi .Lfeedback_show
    cmpil #3,%d0
    beq .Lcontext_detail
    lea .Lerrors,%a1
    moveal %a1@(0,%d0:l:4),%a0
    bra .Lfeedback_show
| Contexte absent : distinguer notification, service UI et allocation.
.Lcontext_detail:
    lea .Lctx_load,%a0
    tstl ml_store_load_serial
    beq .Lfeedback_show
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
    lea .Lsave_ok,%a0
    bra .Lfeedback_show
ml_store_load_feedback:
    lea .Lload_failed,%a0
    movel ml_store_load_error,%d0
    cmpil #6,%d0
    bhi .Lfeedback_show
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
.Lload_errors:
    .long .Lload_failed,.Lload_context,.Lload_identity,.Lload_slot
    .long .Lload_table,.Lload_record,.Lload_publish
.Lerrors:
    .long .Lsave_failed,.Lirq,.Lbusy,.Lcontext,.Lowner,.Lsync
    .long .Lbank,.Lslot,.Lpath,.Lroot,.Ldir,.Lsnapshot
    .long .Lcommit,.Linitial,.Ldata,.Lopen,.Lallocate,.Lwrite,.Lflush,.Lclose
    .long .Lbuffers,.Llookup_a,.Llookup_b,.Lguard
.Lctx_load: .asciz "CTX: NO LOAD"
.Lctx_ui: .asciz "CTX: NO UI"
.Lctx_ipl: .asciz "CTX: UI IPL"
.Lctx_disk: .asciz "CTX: DISK"
.Lctx_busy: .asciz "CTX: BUSY"
.Lctx_ram: .asciz "CTX: RAM"
.Lctx_state: .asciz "CTX: STATE"
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
.Lflush: .asciz "MIDI: FLUSH"
.Lclose: .asciz "MIDI: CLOSE"
    .balign 2
    .endif
