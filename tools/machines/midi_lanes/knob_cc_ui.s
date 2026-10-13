| Potards gris B : SETTINGS choisit le CC, mouvement normal transmet sa valeur.
| État RAM global par voie ; aucun paramètre A ni fichier modifié ici.
    .data
    .balign 4
    .globl mlkc_state,mlkc_selected,mlkc_show,mlkc_time,mlkc_locked_value
mlkc_state:
    .rept 72
    .byte 255,64
    .endr
mlkc_selected: .long 0
mlkc_show: .long 0
mlkc_time: .long 0
mlkc_locked_value: .long -1
    .text
    .globl mlkc_enc
mlkc_enc:
    lea %sp@(-24),%sp
    moveml %d2-%d4/%a2-%a3,%sp@
    moveq #0,%d0
    moveal %sp@(28),%a3
    movel %a3@(12),%d2
    subql #2,%d2
    cmpil #11,%d2
    bhi .Lku_done
    movel mlp_track,%d3
    cmpil #5,%d3
    bhi .Lku_done
    moveal ml_pattern,%a2
    tstl %a2
    beq .Lku_done
    movel %d3,%d1
    muluw #264,%d1
    addal %d1,%a2
    movel %d3,%d1
    muluw #24,%d1
    addl %d2,%d1
    addl %d2,%d1
    lea mlkc_state,%a0
    addal %d1,%a0
    tstl TG_set_held
    beq .Lku_not_assigning
    | Un geste d'assignation, même delta nul, consomme SETTINGS.
    moveq #1,%d1
    movel %d1,TG_mod_used
    .ifdef ML_KNOB_LOCKS
    | Aucun ancien CC provisoire ne doit sortir après changement de numéro.
    jsr mlkcq_reset
    .endif
    bra .Lku_read_delta
.Lku_not_assigning:
    moveq #0,%d1
    moveb %a0@,%d1
    cmpil #255,%d1
    beq .Lku_done
    tstb %a2@(1)
    bne .Lku_used
    tstb %a2@
    beq .Lku_used
.Lku_read_delta:
    pea 1
    pea 1
    movel %a3,%sp@-
    jsr 0x4006f73a
    lea %sp@(12),%sp
    movel %d0,%d4
    beq .Lku_used
    movel %d2,mlkc_selected
    .ifdef ML_KNOB_LOCKS
    moveq #-1,%d0
    movel %d0,mlkc_locked_value
    tstl TG_set_held
    bne .Lku_lock_done
    tstl mlp_held
    beq .Lku_lock_done
    movel %d4,%sp@-
    movel %d2,%sp@-
    movel %d3,%sp@-
    movel ml_pattern,%sp@-
    jsr mlkc_edit_held
    lea %sp@(16),%sp
    tstl %d0
    bmi .Lku_used
    movel %d0,mlkc_locked_value
    moveq #2,%d0
    movel %d0,mlkc_show
    movel TG_blk_clk,%d0
    movel %d0,mlkc_time
    bra .Lku_used
.Lku_lock_done:
    .endif
    moveq #0,%d0
    moveb %a2@(3),%d0
    movel %d0,%sp@-
    moveb %a2@(2),%d0
    andil #255,%d0
    movel %d0,%sp@-
    movel TG_set_held,%sp@-
    movel %d4,%sp@-
    movel %d2,%sp@-
    movel %d3,%sp@-
    pea mlkc_state
    jsr mlkc_edit
    lea %sp@(28),%sp
    movel %d0,%sp@(20)
    tstl TG_set_held
    beq .Lku_send
    moveq #1,%d0
    movel %d0,mlkc_show
    movel %d0,TG_mod_used
    bra .Lku_used
.Lku_send:
    moveq #2,%d1
    movel %d1,mlkc_show
    movel TG_blk_clk,%d1
    movel %d1,mlkc_time
    tstl %d0
    beq .Lku_used
    tstl 0x40fe4228
    beq .Lku_used
    andil #255,%d0
    lea %sp@(20),%a0
    movel %d0,%sp@-
    movel %a0,%sp@-
    pea 3
    jsr 0x400826b0
    lea %sp@(12),%sp
.Lku_used:
    moveq #1,%d0
.Lku_done:
    moveml %sp@,%d2-%d4/%a2-%a3
    lea %sp@(24),%sp
    rts

| Fenêtre dessinée avec les primitives/polices stock ; B reste la vue propriétaire.
| render(self,canvas). Le relâchement SETTINGS rend immédiatement la vue B.
    .globl mlkc_render
mlkc_render:
    lea %sp@(-16),%sp
    moveml %d2-%d3/%a2-%a3,%sp@
    moveal %sp@(24),%a3
    clrl %sp@-
    pea 63
    pea 127
    clrl %sp@-
    clrl %sp@-
    movel %a3,%sp@-
    jsr 0x40070dea
    lea %sp@(24),%sp
    pea .Lku_cc
    pea .Lku_s
    pea 0x10
    pea 35
    pea 11
    pea 0x40ea14cc
    movel %a3,%sp@-
    jsr 0x40071a04
    lea %sp@(28),%sp
    .ifdef ML_KNOB_LOCKS
    tstl mlp_held
    beq .Lku_no_lock_label
    pea .Lku_lock
    pea .Lku_s
    pea 0x10
    pea 13
    pea 7
    pea 0x40ea14cc
    movel %a3,%sp@-
    jsr 0x40071a04
    lea %sp@(28),%sp
.Lku_no_lock_label:
    .endif
    pea -1
    pea 63
    pea 39
    clrl %sp@-
    clrl %sp@-
    movel %a3,%sp@-
    jsr 0x40070dea
    lea %sp@(24),%sp
    movel mlp_track,%d2
    muluw #24,%d2
    movel mlkc_selected,%d3
    addl %d3,%d2
    addl %d3,%d2
    lea mlkc_state,%a2
    addal %d2,%a2
    moveq #0,%d0
    moveb %a2@,%d0
    cmpil #255,%d0
    bne .Lku_name
    movel #128,%d0
.Lku_name:
    movel %d0,%sp@-
    jsr mlcc_name
    addql #4,%sp
    movel %d0,%sp@-
    jsr mlkc_window
    addql #4,%sp
    movel %d0,%sp@-
    pea .Lku_s
    pea 0x10
    pea 43
    pea 43
    pea 0x40ea14cc
    movel %a3,%sp@-
    jsr 0x40071a04
    lea %sp@(28),%sp
    moveq #0,%d0
    moveb %a2@(1),%d0
    .ifdef ML_KNOB_LOCKS
    tstl mlp_held
    beq .Lku_render_value
    tstl mlkc_locked_value
    bmi .Lku_render_value
    movel mlkc_locked_value,%d0
.Lku_render_value:
    .endif
    movel %d0,%sp@-
    pea .Lku_value
    pea 0x10
    pea 27
    pea 43
    pea 0x40ea14cc
    movel %a3,%sp@-
    jsr 0x40071a04
    lea %sp@(28),%sp
    addql #1,%d3
    movel %d3,%sp@-
    pea .Lku_knob
    pea 0x10
    pea 11
    pea 43
    pea 0x40ea14cc
    movel %a3,%sp@-
    jsr 0x40071a04
    lea %sp@(28),%sp
    moveml %sp@,%d2-%d3/%a2-%a3
    lea %sp@(16),%sp
    rts
    .section .rodata
.Lku_lock: .asciz "LOCK"
.Lku_cc: .asciz "CC"
.Lku_s: .asciz "%s"
.Lku_value: .asciz "Val %d"
.Lku_knob: .asciz "Knob %d"
    .balign 4
