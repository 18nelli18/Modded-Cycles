| Nettoyage UI avant retrait des banques ; aucune libération mémoire.
    .text
    .globl ml_store_ui_cancel
ml_store_ui_cancel:
    movew %sr,%d0
    andil #0x700,%d0
    bne .Lcancel_done
    jsr mlp_keyboard_cancel
    subql #4,%sp
    movew %sr,%d0
    movel %d0,%sp@
    movew #0x2700,%sr
    clrl mlp_held
    clrl mlp_remove
    clrl mlp_changed
    .ifdef ML_GENIE
    clrl ml_gq_state
    clrl ml_gu_valid
    clrl SG_undo_valid
    .endif
    .ifdef ML_CLIPBOARD
    jsr mlp_clip_invalidate
    .endif
    movel %sp@,%d0
    movew %d0,%sr
    addql #4,%sp
.Lcancel_done:
    rts
