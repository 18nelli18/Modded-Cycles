| Note 57 : FUNC + SETTINGS + TRACK, avant le getter Sequence Genie/Model-TG.
| Les événements SETTINGS continuent vers la chaîne pour ne jamais bloquer
| TG_set_held. TRACK est consommé jusqu'au relâchement, lectures idempotentes.
| ml_key_next est la cible de chaîne fournie par le futur générateur.
    .data
    .globl ml_key_event,ml_key_time,ml_key_taken
ml_key_event: .long 0
ml_key_time: .long 0
ml_key_taken: .long 0
    .text
    .globl ml_key,ml_toggle
ml_key:
    moveal %sp@(4),%a0
    movel %a0@(12),%d0
    cmpil #2,%d0
    bne .Lchain
    cmpal ml_key_event,%a0
    bne .Lfresh
    movel %a0@(8),%d0
    cmpl ml_key_time,%d0
    beq .Leat
.Lfresh:
    movel %a0@(16),%d1
    btst #0,%d1
    bne .Ldown
    tstl ml_key_taken
    beq .Lchain
    clrl ml_key_taken
    bra .Lrecord
.Ldown:
    tstl ml_key_taken
    bne .Lrecord
    | FUNC consommé par B n'atteint plus le modificateur natif.
    | Utiliser notre état local pour quitter avec le même accord.
    btst #3,%d1
    bne .Lchain
    tstl mlp_obj
    beq .Lnative_modifiers
    tstl mlp_func
    bne .Lsettings_check
.Lnative_modifiers:
    andil #11,%d1
    cmpil #3,%d1
    bne .Lchain
.Lsettings_check:
    tstl TG_set_held
    beq .Lchain
    movew %sr,%d0
    andil #0x0700,%d0
    bne .Lchain
    moveq #1,%d0
    movel %d0,ml_key_taken
    movel %d0,TG_mod_used
    movel %a0,%sp@-
    jsr ml_toggle
    moveal %sp@+,%a0
.Lrecord:
    movel %a0,ml_key_event
    movel %a0@(8),%d0
    movel %d0,ml_key_time
.Leat:
    movel %a0@(16),%d1
    oril #8,%d1
    movel %d1,%a0@(16)
    moveq #0,%d0
    rts
.Lchain:
    jmp ml_key_next
ml_toggle:
    moveal mlp_obj,%a0
    tstl %a0
    bne .Lclose
    jsr ml_prepare
    tstl %d0
    beq .Ltoggle_done
    jmp mlp_open
.Lclose:
    movel %a0,%sp@-
    moveal %a0@,%a1
    moveal %a1@(0x28),%a1
    jsr %a1@
    addql #4,%sp
.Ltoggle_done:
    rts
