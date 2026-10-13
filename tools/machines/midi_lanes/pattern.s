| Note 57 : données d'édition séparées des six pistes sonores.
| Six voies de 264 octets : enabled/mute/fixed-channel/port/length/speed/2 réservés,
| puis 64 pas note/velocity/gate/enabled. Pas de stockage natif revendiqué.
| ml_pattern_tick(runtime,pattern,lane,step) : appelé une fois par pas de voie.
| ml_edit(pattern,lane,step,field,value), ml_config(pattern,lane,field,value).
| Valeurs hors domaine refusées sans écriture ; setters atomiques sur un octet.
    .text
    .globl ml_pattern_tick,ml_edit,ml_config,ml_init
ml_pattern_tick:
    lea.l %sp@(-20),%sp
    movem.l %d2-%d3/%a2-%a3,%sp@
    movew %sr,%d0
    movel %d0,%sp@(16)
    moveal %sp@(24),%a2
    moveal %sp@(28),%a3
    movel %sp@(32),%d2
    cmpil #5,%d2
    bhi .Ltick_bad
    movel %d2,%d0
    muluw #264,%d0
    addal %d0,%a3
    .ifdef ML_GENIE
    moveal %a3,%a0
    movel %d2,%d0
    movel %sp@(36),%d1
    jsr ml_genie_boundary
    .endif
    tstb %a3@
    beq .Ltick_stop
    tstb %a3@(1)
    bne .Ltick_stop
    moveq #0,%d0
    moveb %a3@(4),%d0
    subql #1,%d0
    cmpil #63,%d0
    bhi .Ltick_stop
    movel %sp@(36),%d3
    cmpl %d0,%d3
    bhi .Ltick_stop
    | Canal propre à la voie B, indépendant des pistes audio.
    moveq #0,%d0
    moveb %a3@(2),%d0
    cmpil #15,%d0
    bhi .Ltick_stop
    moveq #0,%d1
    moveb %a3@(3),%d1
    subql #2,%d1
    cmpil #2,%d1
    bhi .Ltick_stop
    lsll #2,%d3
    lea.l %a3@(8,%d3:l),%a0
    moveq #0,%d3
    btst #0,%a0@(3)
    beq .Ltick_rest
    moveb %a0@(2),%d3
    btst #1,%a0@(3)
    beq .Ltick_packet
    bset #31,%d3
.Ltick_packet:
    movel %a0@,%d1
    andil #0xffff0000,%d1
    lsrl #8,%d1
    oril #0x90,%d0
    swap %d0
    lsll #8,%d0
    orl %d1,%d0
    moveq #0,%d1
    moveb %a3@(3),%d1
    orl %d1,%d0
    bra .Ltick_run
.Ltick_rest:
    moveq #0,%d0
.Ltick_run:
    .ifdef ML_REPEAT
    movel %sp@(36),%sp@-
    .endif
    movel %d3,%sp@-
    movel %d0,%sp@-
    movel %d2,%sp@-
    movel %a2,%sp@-
    .ifdef ML_REPEAT
    jsr ml_repeat_locked_step
    lea.l %sp@(20),%sp
    .else
    jsr ml_step
    lea.l %sp@(16),%sp
    .endif
    tstl %d0
    beq .Ltick_done
    tstl %d3
    beq .Ltick_done
    .ifdef ML_LFO_CC
    movel mlcc_triggers,%d1
    bset %d2,%d1
    movel %d1,mlcc_triggers
    .endif
    lea.l ml_pad_serial,%a0
    addql #1,%a0@(0,%d2:l:4)
    bra .Ltick_done
.Ltick_stop:
    movel %d2,%sp@-
    movel %a2,%sp@-
    jsr ml_stop
    addql #8,%sp
.Ltick_bad:
    moveq #0,%d0
.Ltick_done:
    movel %sp@(16),%d1
    movew %d1,%sr
    movem.l %sp@,%d2-%d3/%a2-%a3
    lea.l %sp@(20),%sp
    rts
ml_edit:
    lea.l %sp@(-4),%sp
    movew %sr,%d0
    movel %d0,%sp@
    moveal %sp@(8),%a0
    movel %sp@(12),%d0
    cmpil #5,%d0
    bhi .Ledit_bad
    muluw #264,%d0
    addal %d0,%a0
    movel %sp@(16),%d0
    cmpil #63,%d0
    bhi .Ledit_bad
    lsll #2,%d0
    lea.l %a0@(8,%d0:l),%a0
    movel %sp@(20),%d0
    cmpil #3,%d0
    bhi .Ledit_bad
    movel %sp@(24),%d1
    tstl %d0
    beq .Ledit_note
    cmpil #1,%d0
    beq .Ledit_velocity
    cmpil #2,%d0
    beq .Ledit_gate
    .ifdef ML_LIVE_REC
    cmpil #255,%d1
    .else
    cmpil #3,%d1
    .endif
    bhi .Ledit_bad
    bra .Ledit_write
.Ledit_gate:
    cmpil #1,%d1
    bcs .Ledit_bad
    cmpil #64,%d1
    bhi .Ledit_bad
    bra .Ledit_write
.Ledit_velocity:
    tstl %d1
    beq .Ledit_bad
.Ledit_note:
    cmpil #127,%d1
    bhi .Ledit_bad
.Ledit_write:
    moveb %d1,%a0@(0,%d0:l)
    moveq #1,%d0
    bra .Ledit_return
.Ledit_bad:
    moveq #0,%d0
.Ledit_return:
    movel %sp@,%d1
    movew %d1,%sr
    lea.l %sp@(4),%sp
    rts
ml_config:
    lea.l %sp@(-4),%sp
    movew %sr,%d0
    movel %d0,%sp@
    moveal %sp@(8),%a0
    movel %sp@(12),%d0
    cmpil #5,%d0
    bhi .Ledit_bad
    muluw #264,%d0
    addal %d0,%a0
    movel %sp@(16),%d0
    cmpil #5,%d0
    bhi .Ledit_bad
    movel %sp@(20),%d1
    cmpil #1,%d0
    bls .Lconfig_bool
    cmpil #2,%d0
    beq .Lconfig_channel
    cmpil #3,%d0
    beq .Lconfig_port
    cmpil #4,%d0
    beq .Ledit_gate
    cmpil #6,%d1
    bhi .Ledit_bad
    bra .Ledit_write
.Lconfig_channel:
    cmpil #15,%d1
    bhi .Ledit_bad
    bra .Ledit_write
.Lconfig_bool:
    cmpil #1,%d1
    bhi .Ledit_bad
    bra .Ledit_write
.Lconfig_port:
    cmpil #2,%d1
    bcs .Ledit_bad
    cmpil #4,%d1
    bhi .Ledit_bad
    bra .Ledit_write

| Initialiser une banque vide : MIDI actif, canaux par défaut 7..12, port both.
ml_init:
    lea.l %sp@(-4),%sp
    movew %sr,%d0
    movel %d0,%sp@
    moveal %sp@(8),%a0
    moveq #0,%d0
.Linit_lane:
    movel #0x01000004,%a0@
    movel %d0,%d1
    addql #6,%d1
    moveb %d1,%a0@(2)
    movel #0x10020000,%d1
    movel %d1,%a0@(4)
    lea.l %a0@(8),%a1
    moveq #63,%d1
.Linit_step:
    movel #0x3c640100,%a1@+
    subql #1,%d1
    bpl .Linit_step
    lea.l %a0@(264),%a0
    addql #1,%d0
    cmpil #6,%d0
    bne .Linit_lane
    moveq #1,%d0
    movel %sp@,%d1
    movew %d1,%sr
    lea.l %sp@(4),%sp
    rts

    .data
    .balign 4
    .globl ml_pad_serial
ml_pad_serial: .space 24
