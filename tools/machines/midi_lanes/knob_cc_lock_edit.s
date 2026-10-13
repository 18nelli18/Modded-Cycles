| edit_held(pattern,voie,potard,delta) -> valeur0..127 ou-1.
| Tous les TRIG maintenus de la page reçoivent le même CC/valeur, sans envoi.
    .text
    .globl mlkc_edit_held,mlkc_clear_selected
mlkc_edit_held:
    lea %sp@(-32),%sp
    moveml %d2-%d6/%a2-%a4,%sp@
    movel %sp@(40),%d2
    cmpil #5,%d2
    bhi .Lhe_bad
    movel %sp@(44),%d3
    cmpil #11,%d3
    bhi .Lhe_bad
    tstl mlp_held
    beq .Lhe_bad
    movel %d2,%d0
    muluw #24,%d0
    addl %d3,%d0
    addl %d3,%d0
    lea mlkc_state,%a2
    addal %d0,%a2
    moveq #0,%d4
    moveb %a2@,%d4
    cmpil #127,%d4
    bhi .Lhe_bad
    pea 1
    movel %sp@(40),%sp@-
    jsr mlkc_locks_for
    addql #8,%sp
    tstl %d0
    beq .Lhe_bad
    moveal %d0,%a3
    movel %d3,%sp@-
    movel mlp_step,%sp@-
    movel %d2,%sp@-
    movel %a3,%sp@-
    jsr mlkc_lock_get
    lea %sp@(16),%sp
    movel %d0,%d5
    lsrl #8,%d0
    cmpl %d4,%d0
    beq .Lhe_existing
    moveq #0,%d5
    moveb %a2@(1),%d5
.Lhe_existing:
    andil #255,%d5
    addl %sp@(48),%d5
    bpl .Lhe_min
    moveq #0,%d5
.Lhe_min:
    cmpil #127,%d5
    ble .Lhe_max
    moveq #127,%d5
.Lhe_max:
    movel mlp_held,%d6
    moveq #0,%d3
.Lhe_loop:
    btst %d3,%d6
    beq .Lhe_next
    movel mlp_step,%d0
    andil #48,%d0
    addl %d3,%d0
    movel %d5,%sp@-
    movel %d4,%sp@-
    movel %sp@(52),%sp@-
    movel %d0,%sp@-
    movel %d2,%sp@-
    movel %a3,%sp@-
    jsr mlkc_lock_set
    lea %sp@(24),%sp
.Lhe_next:
    addql #1,%d3
    cmpil #16,%d3
    bcs .Lhe_loop
    movel mlp_changed,%d0
    orl %d6,%d0
    movel %d0,mlp_changed
    movel %d5,%d0
    bra .Lhe_done
.Lhe_bad:
    moveq #-1,%d0
.Lhe_done:
    moveml %sp@,%d2-%d6/%a2-%a4
    lea %sp@(32),%sp
    rts
mlkc_clear_selected:
    clrl %sp@-
    movel ml_pattern,%sp@-
    jsr mlkc_locks_for
    addql #8,%sp
    tstl %d0
    beq .Lcs_done
    movel mlp_step,%sp@-
    movel mlp_track,%sp@-
    movel %d0,%sp@-
    jsr mlkc_lock_clear
    lea %sp@(12),%sp
.Lcs_done:
    rts
