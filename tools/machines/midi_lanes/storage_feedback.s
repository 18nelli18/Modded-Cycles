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
    lea .Lerrors,%a1
    moveal %a1@(0,%d0:l:4),%a0
    bra .Lfeedback_show
.Lfeedback_ok:
    lea .Lsave_ok,%a0
    bra .Lfeedback_show
ml_store_load_feedback:
    lea .Lload_failed,%a0
.Lfeedback_show:
    movel %a0,%sp@-
    jsr TG_show_popup
    addql #4,%sp
    rts
.Lsave_ok: .asciz "MIDI SAVED"
.Lsave_failed: .asciz "MIDI SAVE ERR"
.Lload_failed: .asciz "MIDI LOAD ERR"
    .balign 4
.Lerrors:
    .long .Lsave_failed,.Lirq,.Lbusy,.Lcontext,.Lowner,.Lsync
    .long .Lbank,.Lslot,.Lpath,.Lroot,.Ldir,.Lsnapshot
    .long .Lcommit,.Linitial,.Ldata,.Lopen,.Lallocate,.Lwrite,.Lflush,.Lclose
    .long .Lbuffers,.Llookup_a,.Llookup_b,.Lguard
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
