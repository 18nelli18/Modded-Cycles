| Routage d'un résultat LFO B vers les paramètres MIDI de sa voie.
| mlcc_lane_put(ctx,pattern,lane0..5,lfo0..1,cc0..127,value0..127).
| Aucun setter audio ; le calcul de forme d'onde reste distinct, non raccordé.
    .text
    .globl mlcc_lane_put
mlcc_lane_put:
    lea.l %sp@(-16),%sp
    moveml %d2-%d3/%a2-%a3,%sp@
    moveq #0,%d0
    moveal %sp@(20),%a2
    tstl %a2
    beq .Llane_done
    movel %a2,%d1
    andil #3,%d1
    bne .Llane_done
    moveal %sp@(24),%a3
    tstl %a3
    beq .Llane_done
    movel %a3,%d1
    andil #3,%d1
    bne .Llane_done
    movel %sp@(28),%d2
    cmpil #5,%d2
    bhi .Llane_done
    movel %sp@(32),%d3
    cmpil #1,%d3
    bhi .Llane_done
    movel %d2,%d1
    muluw #264,%d1
    addal %d1,%a3
    moveq #0,%d1
    moveb %a3@,%d1
    cmpil #1,%d1
    bne .Llane_done
    tstb %a3@(1)
    bne .Llane_done
    addl %d2,%d2
    addl %d3,%d2
    moveq #0,%d1
    moveb %a3@(3),%d1
    movel %d1,%sp@-
    movel %sp@(44),%sp@-
    movel %sp@(44),%sp@-
    moveq #0,%d1
    moveb %a3@(2),%d1
    movel %d1,%sp@-
    movel %d2,%sp@-
    movel %a2,%sp@-
    jsr mlcc_put
    lea.l %sp@(24),%sp
.Llane_done:
    moveml %sp@,%d2-%d3/%a2-%a3
    lea.l %sp@(16),%sp
    rts

| mlcc_lane_cancel(ctx,lane) : purger les deux LFO lors d'un mute/changement
| canal/port/projet. Réinitialiser le dernier CC autorise la reprise identique.
| L'appelant sérialise publication/cancel ; masque seulement six longwords.
    .globl mlcc_lane_cancel
mlcc_lane_cancel:
    moveq #0,%d0
    moveal %sp@(4),%a0
    tstl %a0
    beq .Lcancel_done
    movel %a0,%d1
    andil #3,%d1
    bne .Lcancel_done
    movel %sp@(8),%d1
    cmpil #5,%d1
    bhi .Lcancel_done
    muluw #24,%d1
    addal %d1,%a0
    movew %sr,%d1
    movew #0x2700,%sr
    clrl %a0@
    clrl %a0@(4)
    clrl %a0@(8)
    clrl %a0@(12)
    clrl %a0@(16)
    clrl %a0@(20)
    movew %d1,%sr
    moveq #1,%d0
.Lcancel_done:
    rts
