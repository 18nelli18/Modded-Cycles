| Résultat explicite des sidecars, distinct du succès du Save audio natif.
    .ifdef ML_STORAGE2
    .text
    .globl ml_store_save_feedback,ml_store_load_feedback
ml_store_save_feedback:
    lea .Lsave_failed,%a0
    movel ml_store_save_status,%d0
    subql #1,%d0
    bne .Lfeedback_show
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
    .balign 2
    .endif
