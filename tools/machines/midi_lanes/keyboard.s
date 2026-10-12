| Note 57 : clavier MIDI monophonique par voie, file indépendante du pattern.
| mlp_keyboard(code,flags) -> 1 si consommé, 0 pour le chemin édition REC.
| Les releases mémorisées précèdent la lecture du mode REC : changement de
| mode/piste ne perd jamais le propriétaire du note-off. Aucun writer UI.
    .text
    .globl mlp_keyboard,mlp_keyboard_cancel
mlp_keyboard:
    lea.l %sp@(-24),%sp
    movem.l %d2-%d4/%a2-%a4,%sp@
    movel %sp@(28),%d2
    subil #16,%d2
    cmpil #15,%d2
    bhi .Lkb_grid
    movel %sp@(32),%d3
    btst #0,%d3
    beq .Lkb_up
    movel mlp_live_held,%d0
    btst %d2,%d0
    bne .Lkb_used
    | Même getter que KeyboardView stock ; aucun changement du mode natif.
    jsr 0x400cf9a8
    tstl %d0
    beq .Lkb_grid
    movel %d0,%sp@-
    jsr 0x4006b978
    addql #4,%sp
    .ifdef ML_LFO_CC
    tstl mlccp_obj
    bne .Lkb_live_menu
    .endif
    tstb %d0
    bne .Lkb_grid
.Lkb_live_menu:
    tstl mlp_setup
    bne .Lkb_used
    andil #11,%d3
    cmpil #1,%d3
    bne .Lkb_used
    tstl mlp_func
    bne .Lkb_used
    tstl TG_set_held
    bne .Lkb_grid
    movel mlp_track,%d4
    cmpil #5,%d4
    bhi .Lkb_used
    movel %d4,%d0
    muluw #264,%d0
    moveal ml_pattern,%a2
    addal %d0,%a2
    tstb %a2@
    beq .Lkb_used
    | Même décalage clavier que KeyboardView : touche + 52 + octave stock.
    moveq #0,%d0
    moveb %a2@(6),%d0
    extbl %d0
    addl %d2,%d0
    addil #52,%d0
    jsr mlp_scale_note
    cmpil #127,%d0
    bhi .Lkb_used
    movel %d0,%d3
    lsll #8,%d3
    moveq #100,%d0
    orl %d0,%d3
    lsll #8,%d3
    moveq #0,%d0
    moveb %a2@(3),%d0
    orl %d0,%d3
    movel %d4,%d0
    addil #0x96,%d0
    swap %d0
    lsll #8,%d0
    orl %d0,%d3
    pea 64
    movel %d3,%sp@-
    movel %d4,%sp@-
    pea ml_live_runtime
    jsr ml_step
    lea.l %sp@(16),%sp
    tstl %d0
    beq .Lkb_used
    movel mlp_live_pad_held,%d0
    bclr %d4,%d0
    movel %d0,mlp_live_pad_held
    lea.l mlp_live_owner,%a0
    moveb %d4,%a0@(0,%d2:l)
    lea.l mlp_live_key,%a0
    movel %d2,%d0
    addql #1,%d0
    moveb %d0,%a0@(0,%d4:l)
    movel mlp_live_held,%d0
    bset %d2,%d0
    movel %d0,mlp_live_held
    bra .Lkb_used
.Lkb_up:
    movel mlp_live_held,%d0
    btst %d2,%d0
    beq .Lkb_grid
    bclr %d2,%d0
    movel %d0,mlp_live_held
    lea.l mlp_live_owner,%a0
    moveq #0,%d4
    moveb %a0@(0,%d2:l),%d4
    lea.l mlp_live_key,%a0
    moveq #0,%d0
    moveb %a0@(0,%d4:l),%d0
    addql #1,%d2
    cmpl %d2,%d0
    bne .Lkb_used
    clrb %a0@(0,%d4:l)
    movel %d4,%sp@-
    pea ml_live_runtime
    jsr ml_quiet
    addql #8,%sp
.Lkb_used:
    .ifdef ML_WORKER
    jsr ml_worker_kick
    .endif
    moveq #1,%d0
    bra .Lkb_done
.Lkb_grid:
    moveq #0,%d0
.Lkb_done:
    movem.l %sp@,%d2-%d4/%a2-%a4
    lea.l %sp@(24),%sp
    rts
| Réutiliser exactement le pliage Model-TG actif, tonalité comprise.
| Le helper TG travaille en d3 et détruit d5/d6 ; préserver l'ABI C ici.
    .globl mlp_scale_note
mlp_scale_note:
    lea.l %sp@(-12),%sp
    movem.l %d3/%d5-%d6,%sp@
    movel %d0,%d3
    jsr TG_snap_note
    movel %d3,%d0
    movem.l %sp@,%d3/%d5-%d6
    lea.l %sp@(12),%sp
    rts
mlp_keyboard_cancel:
    movel %d2,%sp@-
    moveq #0,%d2
.Lkbc_lane:
    movel %d2,%sp@-
    pea ml_live_runtime
    jsr ml_quiet
    addql #8,%sp
    addql #1,%d2
    cmpil #6,%d2
    bcs .Lkbc_lane
    clrl mlp_live_pad_held
    clrl mlp_live_held
    lea.l mlp_live_key,%a0
    clrl %a0@
    clrw %a0@(4)
    movel %sp@+,%d2
    rts
    .data
    .balign 4
    .globl mlp_live_held
mlp_live_held: .long 0
mlp_live_owner: .space 16
    .globl mlp_live_key
mlp_live_key: .space 6
