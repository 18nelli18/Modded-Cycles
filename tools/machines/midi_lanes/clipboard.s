| Presse-papiers B privé. REC9 copy / PLAY10 clear / STOP11 paste.
| Longueur/vitesse et64 pas copiés ; canal/port/mute/enable destination gardés.
| Deuxième clear/paste même lane : undo. Aucune donnée audio ni clipboard stock.
    .data
    .balign 4
mlp_step_clip_ready: .long 0
mlp_step_clip: .space 12
mlp_clip_ready: .long 0
mlp_clip_keys: .long 0
mlp_clip_undo_op: .long 0
mlp_clip_undo_lane: .long 0
mlp_clip_buffer: .space 264
mlp_clip_undo: .space 264
    .text
    .globl mlp_clip_key
mlp_clip_key:
    lea.l %sp@(-24),%sp
    moveml %d2-%d4/%a2-%a3,%sp@
    movew %sr,%d0
    movel %d0,%sp@(20)
    andil #0x700,%d0
    bne .Lclip_pass
    movel %sp@(28),%d2
    subql #8,%d2
    subql #1,%d2
    cmpil #2,%d2
    bhi .Lclip_pass
    movel %sp@(32),%d3
    btst #0,%d3
    bne .Lclip_down
    movel mlp_clip_keys,%d0
    btst %d2,%d0
    beq .Lclip_pass
    bclr %d2,%d0
    movel %d0,mlp_clip_keys
    bra .Lclip_used
.Lclip_down:
    movel mlp_clip_keys,%d0
    btst %d2,%d0
    bne .Lclip_used
    tstl mlp_held
    beq .Lclip_track
    jmp .Lclip_step
.Lclip_track:
    tstl mlp_func
    beq .Lclip_pass
    btst #5,%d3
    bne .Lclip_used
    bset %d2,%d0
    movel %d0,mlp_clip_keys
    movel mlp_track,%d4
    cmpil #5,%d4
    bhi .Lclip_used
    moveal ml_pattern,%a2
    tstl %a2
    beq .Lclip_used
    movel %d4,%d0
    muluw #264,%d0
    addal %d0,%a2
    .ifdef ML_REPEAT
    jsr ml_repeat_prepare_ui
    tstl ml_repeat_edit_settings
    beq .Lclip_used
    jsr ml_repeat_clip_prepare
    tstl %d0
    beq .Lclip_used
    .endif
    tstl %d2
    beq .Lclip_copy
    cmpil #2,%d2
    bne .Lclip_mutate
    tstl mlp_clip_ready
    beq .Lclip_used
.Lclip_mutate:
    jsr mlp_keyboard_cancel
    movel %d4,%sp@-
    movel ml_runtime,%sp@-
    jsr ml_stop
    addql #8,%sp
    movew #0x2700,%sr
    lea mlp_clip_undo,%a3
    cmpal mlp_clip_undo_lane,%a2
    bne .Lclip_new_undo
    cmpl mlp_clip_undo_op,%d2
    bne .Lclip_new_undo
    clrl mlp_clip_undo_op
    clrl mlp_clip_undo_lane
    .ifdef ML_REPEAT
    moveq #2,%d0
    jsr ml_repeat_clip
    .endif
    bra .Lclip_apply
.Lclip_new_undo:
    .ifdef ML_REPEAT
    moveq #1,%d0
    jsr ml_repeat_clip
    .endif
    movel %a2,mlp_clip_undo_lane
    movel %d2,mlp_clip_undo_op
    moveal %a2,%a0
    moveal %a3,%a1
    moveq #65,%d0
.Lclip_snapshot:
    movel %a0@+,%a1@+
    subql #1,%d0
    bpl .Lclip_snapshot
    cmpil #1,%d2
    beq .Lclip_clear
    lea mlp_clip_buffer,%a3
    .ifdef ML_REPEAT
    moveq #3,%d0
    jsr ml_repeat_clip
    .endif
.Lclip_apply:
    movew %a3@(4),%d0
    movew %d0,%a2@(4)
    lea %a3@(8),%a0
    lea %a2@(8),%a1
    moveq #63,%d0
.Lclip_apply_loop:
    movel %a0@+,%a1@+
    subql #1,%d0
    bpl .Lclip_apply_loop
    bra .Lclip_changed
.Lclip_clear:
    .ifdef ML_REPEAT
    moveq #4,%d0
    jsr ml_repeat_clip
    .endif
    lea %a2@(8),%a0
    moveq #63,%d0
    movel #0x48640100,%d1
.Lclip_clear_loop:
    movel %d1,%a0@+
    subql #1,%d0
    bpl .Lclip_clear_loop
.Lclip_changed:
    clrl mlp_held
    clrl mlp_remove
    clrl mlp_changed
    movel %sp@(20),%d0
    movew %d0,%sr
    movel mlp_obj,%sp@-
    jsr mlp_redraw
    addql #4,%sp
    bra .Lclip_used
.Lclip_copy:
    movew #0x2700,%sr
    .ifdef ML_REPEAT
    moveq #0,%d0
    jsr ml_repeat_clip
    .endif
    moveal %a2,%a0
    lea mlp_clip_buffer,%a1
    moveq #65,%d0
.Lclip_copy_loop:
    movel %a0@+,%a1@+
    subql #1,%d0
    bpl .Lclip_copy_loop
    moveq #1,%d0
    movel %d0,mlp_clip_ready
    movel %sp@(20),%d0
    movew %d0,%sr
| TRIG maintenu + REC/STOP : un pas et ses locks privés, jamais le transport.
    .section .text.ml_step_clip_a,"ax"
.Lclip_step:
    cmpil #1,%d2
    bne.s .Lstep_far1
    jmp .Lclip_pass
.Lstep_far1:
    btst #5,%d3
    beq.s .Lstep_far2
    jmp .Lclip_used
.Lstep_far2:
    bset %d2,%d0
    movel %d0,mlp_clip_keys
    movel mlp_track,%d4
    cmpil #5,%d4
    bls.s .Lstep_far3
    jmp .Lclip_used
.Lstep_far3:
    movel mlp_step,%d3
    cmpil #63,%d3
    bls.s .Lstep_far4
    jmp .Lclip_used
.Lstep_far4:
    moveal ml_pattern,%a2
    tstl %a2
    bne.s .Lstep_far5
    jmp .Lclip_used
.Lstep_far5:
    movel %d4,%d0
    muluw #264,%d0
    addal %d0,%a2
    movel %d3,%d0
    lsll #2,%d0
    addal %d0,%a2
    addql #8,%a2
    jmp .Lclip_step_locks
    .section .text.ml_step_clip_c,"ax"
.Lclip_step_locks:
    .ifdef ML_REPEAT
    jsr ml_repeat_prepare_ui
    moveal ml_repeat_edit_settings,%a3
    tstl %a3
    bne.s .Lstep_far6
    jmp .Lclip_used
.Lstep_far6:
    movel %d4,%d0
    muluw #520,%d0
    addal %d0,%a3
    movel %d3,%d0
    lsll #3,%d0
    addal %d0,%a3
    addql #8,%a3
    .endif
    tstl %d2
    bne.s .Lstep_far7
    jmp .Lclip_step_copy
.Lstep_far7:
    tstl mlp_step_clip_ready
    bne.s .Lstep_far8
    jmp .Lclip_used
.Lstep_far8:
    jsr mlp_keyboard_cancel
    movel %d4,%sp@-
    movel ml_runtime,%sp@-
    jsr ml_stop
    addql #8,%sp
    .ifdef ML_REPEAT
    jsr ml_repeat_delete_selected
    .endif
    movew #0x2700,%sr
    movel mlp_step_clip,%d0
    movel %d0,%a2@
    .ifdef ML_REPEAT
    movel mlp_step_clip+4,%d0
    movel %d0,%a3@
    movel mlp_step_clip+8,%d0
    movel %d0,%a3@(4)
    .endif
    jmp .Lclip_step_changed
    .section .text.ml_step_clip_b,"ax"
.Lclip_step_copy:
    movew #0x2700,%sr
    movel %a2@,%d0
    movel %d0,mlp_step_clip
    .ifdef ML_REPEAT
    movel %a3@,%d0
    movel %d0,mlp_step_clip+4
    movel %a3@(4),%d0
    movel %d0,mlp_step_clip+8
    .endif
    moveq #1,%d0
    movel %d0,mlp_step_clip_ready
.Lclip_step_changed:
    | La libération du trig ne doit pas effacer le pas copié/collé.
    movel mlp_held,%d0
    orl %d0,mlp_changed
    movel %sp@(20),%d0
    movew %d0,%sr
    movel mlp_obj,%sp@-
    jsr mlp_redraw
    addql #4,%sp
    movel %d2,%sp@-
    jsr mlp_step_clip_popup
    addql #4,%sp
    jmp .Lclip_used

    .text
.Lclip_used:
    moveq #1,%d0
    bra .Lclip_out
.Lclip_pass:
    moveq #0,%d0
.Lclip_out:
    moveml %sp@,%d2-%d4/%a2-%a3
    lea.l %sp@(24),%sp
    rts

| Projet remplacé : copie privée conservée, undo ancien pointeur invalidé.
| Garder les releases consommés évite leur fuite vers le transport natif.
    .section .text.ml_step_clip_d,"ax"
    .globl mlp_clip_invalidate
mlp_clip_invalidate:
    clrl mlp_clip_undo_op
    clrl mlp_clip_undo_lane
    rts

| Confirmation via la fenêtre native utilisée par Model-TG.
    .section .text.ml_step_clip_d,"ax"
mlp_step_clip_popup:
    lea .Lstep_copy_text,%a0
    tstl %sp@(4)
    beq .Lstep_popup_show
    lea .Lstep_paste_text,%a0
.Lstep_popup_show:
    movel %a0,%sp@-
    jsr TG_show_popup
    addql #4,%sp
    rts
.Lstep_copy_text: .asciz "COPY"
.Lstep_paste_text: .asciz "PASTE"
    .balign 2
