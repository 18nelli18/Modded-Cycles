| Note 57 : résolution des banques privées par identité native de pattern.
| ML_PATTERN_BANKS active le raccordement expérimental ; absent du flasher.
| ml_bank_for(base,index) -> banque de 1584 octets ou NULL (96 patterns).
| ml_active_pattern_id() -> identité audio 0..95 ou -1 si indisponible.
    .text
    .globl ml_bank_for,ml_active_pattern_id
ml_bank_for:
    movel %sp@(4),%d0
    beq .Lbank_return
    movel %sp@(8),%d1
    cmpil #95,%d1
    bhi .Lbank_invalid
    muluw #1584,%d1
    addl %d1,%d0
.Lbank_return:
    rts

    .data
    .balign 4
    .globl ml_bank_table,ml_bank_empty,ml_play_pattern
ml_bank_table: .long 0
ml_bank_empty: .long 0
ml_play_pattern: .long 0
    .text

| UI seulement : allocation paresseuse d'un bloc par pattern visité.
| Publication d'un pointeur aligné après initialisation ; jamais depuis IRQ.
    .globl ml_bank_ui_sync,ml_bank_follow
ml_bank_ui_sync:
    .ifdef ML_PATTERN_BANKS
    lea.l %sp@(-16),%sp
    movem.l %d2/%a2-%a3,%sp@
    movew %sr,%d0
    movel %d0,%sp@(12)
    andil #0x0700,%d0
    bne .Lsync_fail
    moveal ml_bank_table,%a2
    tstl %a2
    beq .Lsync_fail
    jsr ml_active_pattern_id
    cmpil #95,%d0
    bhi .Lsync_ready
    lsll #2,%d0
    addal %d0,%a2
    moveal %a2@,%a3
    tstl %a3
    bne .Lsync_publish
    pea 1584
    jsr 0x400802e0
    addql #4,%sp
    moveal %d0,%a3
    tstl %a3
    beq .Lsync_fail
    movel %a3,%sp@-
    jsr ml_init
    addql #4,%sp
    movel %a3,%a2@
.Lsync_publish:
    cmpal ml_pattern,%a3
    beq .Lsync_ready
    movel %a3,ml_pattern
    clrl mlp_held
    clrl mlp_remove
    clrl mlp_changed
    moveal mlp_obj,%a0
    tstl %a0
    beq .Lsync_ready
    movel %a0,%sp@-
    jsr mlp_redraw
    addql #4,%sp
.Lsync_ready:
    moveq #1,%d2
    bra .Lsync_out
.Lsync_fail:
    moveq #0,%d2
.Lsync_out:
    movel %sp@(12),%d0
    movew %d0,%sr
    movel %d2,%d0
    movem.l %sp@,%d2/%a2-%a3
    lea.l %sp@(16),%sp
    rts
    .else
    moveq #1,%d0
    rts
    .endif

| Audio : aucune allocation. Pattern non visité = banque vide immuable.
ml_bank_follow:
    .ifdef ML_PATTERN_BANKS
    lea.l %sp@(-8),%sp
    movem.l %a2-%a3,%sp@
    moveal ml_bank_table,%a2
    tstl %a2
    beq .Lfollow_done
    jsr ml_active_pattern_id
    cmpil #95,%d0
    bhi .Lfollow_done
    lsll #2,%d0
    moveal %a2@(0,%d0:l),%a3
    tstl %a3
    bne .Lfollow_activate
    moveal ml_bank_empty,%a3
.Lfollow_activate:
    movel %a3,%sp@-
    movel ml_clock_state,%sp@-
    movel ml_runtime,%sp@-
    pea ml_play_pattern
    jsr ml_bank_activate
    lea.l %sp@(16),%sp
.Lfollow_done:
    movem.l %sp@,%a2-%a3
    addql #8,%sp
    rts
    .else
    rts
    .endif
.Lbank_invalid:
    moveq #0,%d0
    rts
ml_active_pattern_id:
    moveal 0x40a7887c,%a0
    tstl %a0
    beq .Lid_invalid
    movel %a0@(30706),%d0
    cmpil #95,%d0
    bhi .Lid_invalid
    rts
.Lid_invalid:
    moveq #-1,%d0
    rts

| ml_bank_activate(slot,runtime,clock,nouvelle_banque) -> 1 si changement.
| slot est indépendant du pointeur d'édition. Sous IPL7 : annuler les
| note-on en attente, libérer les six notes, remettre la phase à zéro,
| publier la banque. Aucun writer physique, allocation ou attente.
    .globl ml_bank_activate
ml_bank_activate:
    lea.l %sp@(-24),%sp
    movem.l %d2-%d3/%a2-%a4,%sp@
    movew %sr,%d0
    movel %d0,%sp@(20)
    moveal %sp@(28),%a4
    moveal %sp@(32),%a2
    moveal %sp@(36),%a3
    movel %sp@(40),%d3
    moveq #0,%d2
    tstl %d3
    beq .Lactivate_out
    movew #0x2700,%sr
    cmpl %a4@,%d3
    beq .Lactivate_out
    movel %a2@,%d0
    movel %a2@(4),%d1
    lea.l %a2@(16),%a0
.Lactivate_scan:
    tstl %d0
    beq .Lactivate_release
    lea.l %a0@(0,%d1:l:4),%a1
    moveq #0,%d2
    moveb %a1@,%d2
    cmpil #0x96,%d2
    bcs .Lactivate_next
    cmpil #0x9b,%d2
    bhi .Lactivate_next
    movel %a1@,%d2
    andil #0xefff00ff,%d2
    movel %d2,%a1@
.Lactivate_next:
    addql #1,%d1
    andil #63,%d1
    subql #1,%d0
    bra .Lactivate_scan
.Lactivate_release:
    moveq #0,%d2
.Lactivate_release_loop:
    movel %d2,%sp@-
    movel %a2,%sp@-
    jsr ml_stop
    addql #8,%sp
    addql #1,%d2
    cmpil #6,%d2
    bcs .Lactivate_release_loop
    moveq #12,%d0
.Lactivate_clock:
    clrl %a3@+
    subql #1,%d0
    bpl .Lactivate_clock
    movel %d3,%a4@
    moveq #1,%d2
.Lactivate_out:
    movel %sp@(20),%d0
    movew %d0,%sr
    movel %d2,%d0
    movem.l %sp@,%d2-%d3/%a2-%a4
    lea.l %sp@(24),%sp
    rts
