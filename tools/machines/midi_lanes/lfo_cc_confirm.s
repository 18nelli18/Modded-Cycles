| Choix de destination CC en brouillon ; DATA confirme, BACK annule.
| Seule l'UI écrit le brouillon. Le moteur et Save lisent toujours cfg.
    .data
    .balign 4
    .globl mlccp_draft
mlccp_draft: .long -1
mlccp_draft_owner: .long 0,0,0
    .text
    .globl mlccp_confirm_data,mlccp_confirm_cancel,mlccp_confirm_write
mlccp_confirm_cancel:
.Lconfirm_cancel:
    moveq #-1,%d0
    movel %d0,mlccp_draft
    clrl mlccp_edit
    rts
mlccp_confirm_data:
    bsr .Lconfirm_validate
    movel mlccp_row,%d0
    cmpil #4,%d0
    beq .Lconfirm_dest
    moveq #1,%d0
    eorl %d0,mlccp_edit
    rts
.Lconfirm_dest:
    movel mlccp_draft,%d0
    bpl .Lconfirm_commit
    pea 3
    movel mlccp_index,%sp@-
    movel mlccp_track,%sp@-
    movel mlcc_settings,%sp@-
    jsr mlcc_cfg_get
    lea %sp@(16),%sp
    tstl %d0
    bmi .Lconfirm_done
    movel %d0,mlccp_draft
    movel mlcc_settings,%d0
    movel %d0,mlccp_draft_owner
    movel mlccp_track,%d0
    movel %d0,mlccp_draft_owner+4
    movel mlccp_index,%d0
    movel %d0,mlccp_draft_owner+8
    moveq #1,%d0
    movel %d0,mlccp_edit
.Lconfirm_done:
    rts
.Lconfirm_commit:
    movel %d0,%sp@-
    pea 3
    movel mlccp_index,%sp@-
    movel mlccp_track,%sp@-
    movel mlcc_settings,%sp@-
    jsr mlcc_cfg_edit
    lea %sp@(20),%sp
    bra .Lconfirm_cancel
    .section .text.mlccp_confirm_write,"ax"
mlccp_confirm_write:
    jsr mlccp_confirm_validate
    movel %sp@(16),%d0
    cmpil #3,%d0
    bne .Lconfirm_other
    tstl mlccp_draft
    bmi .Lconfirm_other
    movel %sp@(20),%d0
    cmpil #128,%d0
    bhi .Lconfirm_bad
    movel %d0,mlccp_draft
    moveq #1,%d0
    rts
.Lconfirm_bad:
    moveq #0,%d0
    rts
.Lconfirm_other:
    jmp mlcc_cfg_edit

    .section .text.mlccp_confirm_validate,"ax"
    .globl mlccp_confirm_validate
mlccp_confirm_validate:
.Lconfirm_validate:
    tstl mlccp_draft
    bmi .Lvalidate_done
    movel mlcc_settings,%d0
    cmpl mlccp_draft_owner,%d0
    bne .Lconfirm_cancel
    movel mlccp_track,%d0
    cmpl mlccp_draft_owner+4,%d0
    bne .Lconfirm_cancel
    movel mlccp_index,%d0
    cmpl mlccp_draft_owner+8,%d0
    bne .Lconfirm_cancel
.Lvalidate_done:
    rts
