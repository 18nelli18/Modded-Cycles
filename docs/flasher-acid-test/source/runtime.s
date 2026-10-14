| Prototype note 57. Banque RAM : count/head/tail/held (4 longs), 64 paquets
| de 4 octets (status/note/velocity/port), six voies de 8 octets (off/gate).
| ml_step(bank,index,packet,gate), packet=0 pour silence ; gate en pas 1..64.
| ml_stop(bank,index), ml_take(bank) -> paquet ou 0. Aucune API de sortie/son.
| Réservation d'un emplacement note-off par note acceptée. Sections atomiques
| bornées, registres sauvegardés et SR restauré ; intégration horloge à faire.
    .text
    .globl ml_step,ml_stop,ml_take
ml_step:
    lea.l %sp@(-44),%sp
    movem.l %d2-%d7/%a2-%a5,%sp@
    movew %sr,%d0
    movel %d0,%sp@(40)
    movew #0x2700,%sr
    moveal %sp@(48),%a2
    movel %sp@(52),%d4
    movel %sp@(56),%d2
    movel %sp@(60),%d3
    | Bit 31 interne : legato, nouvelle note avant la fin de l'ancienne.
    andil #0x7fffffff,%d3
    moveq #0,%d6
    moveq #0,%d7
    cmpil #5,%d4
    bhi .Lstep_out
    movel %d4,%d0
    lsll #3,%d0
    lea.l %a2@(272),%a3
    addal %d0,%a3
    tstl %d2
    beq .Lgate
    movel %d2,%d0
    andil #0xf0808000,%d0
    cmpil #0x90000000,%d0
    bne .Lstep_out
    movel %d2,%d0
    andil #0x00007f00,%d0
    beq .Lstep_out
    movel %d2,%d0
    andil #255,%d0
    subql #2,%d0
    cmpil #2,%d0
    bhi .Lstep_out
    cmpil #1,%d3
    bcs .Lstep_out
    cmpil #64,%d3
    bhi .Lstep_out
.Lgate:
    tstl %d2
    beq .Lgate_ready
    | Éviter deux propriétaires du même canal/note, quel que soit le port.
    movel %d2,%d7
    andil #0xefff0000,%d7
    lea.l %a2@(272),%a4
    moveq #0,%d5
.Lcollision:
    cmpl %d4,%d5
    beq .Lcollision_next
    movel %a4@,%d0
    andil #0xffff0000,%d0
    cmpl %d7,%d0
    beq .Lcollision_reject
.Lcollision_next:
    lea.l %a4@(8),%a4
    addql #1,%d5
    cmpil #6,%d5
    bne .Lcollision
    moveq #0,%d7
    bra .Lgate_ready
.Lcollision_reject:
    | Refuser le nouveau On ne suspend jamais le gate de la note tenue.
    moveq #0,%d2
    moveq #-1,%d7
.Lgate_ready:
    tstl %a3@
    beq .Lnew_note
    tstl %d2
    beq .Lgate_countdown
    movel %sp@(60),%d0
    btst #31,%d0
    beq .Lgate_countdown
    movel %d2,%d0
    andil #0xefff0000,%d0
    movel %a3@,%d1
    andil #0xffff0000,%d1
    cmpl %d1,%d0
    beq .Lgate_countdown
    movel %a2@,%d0
    addl %a2@(12),%d0
    addql #2,%d0
    cmpil #64,%d0
    bhi .Lgate_countdown
    | Capacité vérifiée avant le premier message, réserve note-off conservée.
    movel %d2,%d0
    bsr ml_push
    bsr ml_release
    bra .Lnew_hold
.Lgate_countdown:
    movel %a3@(4),%d0
    subql #1,%d0
    movel %d0,%a3@(4)
    beq .Lexpire
    tstl %d2
    beq .Laccepted
.Lexpire:
    bsr ml_release
.Lnew_note:
    tstl %d2
    beq .Laccepted
    movel %a2@,%d0
    addl %a2@(12),%d0
    addql #2,%d0
    cmpil #64,%d0
    bhi .Lstep_out
    movel %d2,%d0
    bsr ml_push
.Lnew_hold:
    movel %d2,%d0
    andil #0xefff00ff,%d0
    movel %d0,%a3@
    movel %d3,%a3@(4)
    movel %a2@(12),%d0
    addql #1,%d0
    movel %d0,%a2@(12)
.Laccepted:
    tstl %d7
    bmi .Lstep_out
    moveq #1,%d6
.Lstep_out:
    movel %d6,%d0
    movel %sp@(40),%d1
    movew %d1,%sr
    movem.l %sp@,%d2-%d7/%a2-%a5
    lea.l %sp@(44),%sp
    rts
ml_stop:
    lea.l %sp@(-16),%sp
    movem.l %d2/%a2-%a3,%sp@
    movew %sr,%d0
    movel %d0,%sp@(12)
    movew #0x2700,%sr
    moveal %sp@(20),%a2
    movel %sp@(24),%d0
    cmpil #5,%d0
    bhi .Lstop_out
    lsll #3,%d0
    lea.l %a2@(272),%a3
    addal %d0,%a3
    bsr ml_release
.Lstop_out:
    movel %sp@(12),%d0
    movew %d0,%sr
    movem.l %sp@,%d2/%a2-%a3
    lea.l %sp@(16),%sp
    rts
ml_release:
    movel %a3@,%d0
    beq .Lrelease_done
    bsr ml_push
    clrl %a3@
    clrl %a3@(4)
    movel %a2@(12),%d0
    subql #1,%d0
    movel %d0,%a2@(12)
.Lrelease_done:
    rts
ml_push:
    movel %a2@(8),%d1
    lea.l %a2@(16),%a0
    movel %d0,%a0@(0,%d1:l:4)
    addql #1,%d1
    andil #63,%d1
    movel %d1,%a2@(8)
    movel %a2@,%d1
    addql #1,%d1
    movel %d1,%a2@
    rts
ml_take:
    movew %sr,%d1
    movew #0x2700,%sr
    moveal %sp@(4),%a0
    movel %a0@,%d0
    beq .Ltake_out
    subql #1,%d0
    movel %d0,%a0@
    moveal %a0@(4),%a1
    movel %a1,%d0
    addql #1,%d0
    andil #63,%d0
    movel %d0,%a0@(4)
    lea.l %a0@(16),%a0
    addal %a1,%a1
    addal %a1,%a1
    movel %a0@(0,%a1:l),%d0
.Ltake_out:
    movew %d1,%sr
    rts

| ml_quiet(bank,lane) : annule les note-ons encore en file, puis libère la
| note tenue. Les note-offs, autres canaux et ports sont conservés. Au plus
| 64 paquets inspectés ; aucun appel de sortie sous IPL7.
    .globl ml_quiet
ml_quiet:
    lea.l %sp@(-20),%sp
    movem.l %d2-%d4/%a2,%sp@
    movew %sr,%d0
    movel %d0,%sp@(16)
    movew #0x2700,%sr
    moveal %sp@(24),%a2
    movel %sp@(28),%d4
    cmpil #5,%d4
    bhi .Lquiet_done
    movel %d4,%d2
    addil #0x96,%d2
    movel %a2@,%d3
    movel %a2@(4),%d1
    lea.l %a2@(16),%a0
.Lquiet_scan:
    tstl %d3
    beq .Lquiet_release
    lea.l %a0@(0,%d1:l:4),%a1
    moveq #0,%d0
    moveb %a1@,%d0
    cmpl %d2,%d0
    bne .Lquiet_next
    movel %a1@,%d0
    andil #0xefff00ff,%d0
    movel %d0,%a1@
.Lquiet_next:
    addql #1,%d1
    andil #63,%d1
    subql #1,%d3
    bra .Lquiet_scan
.Lquiet_release:
    movel %d4,%sp@-
    movel %a2,%sp@-
    jsr ml_stop
    addql #8,%sp
    .ifdef ML_WORKER
    jsr ml_worker_kick
    .endif
.Lquiet_done:
    movel %sp@(16),%d0
    movew %d0,%sr
    movem.l %sp@,%d2-%d4/%a2
    lea.l %sp@(20),%sp
    rts

    .data
    .balign 4
    .globl ml_live_runtime
| File et propriétaires clavier séparés de ceux de la lecture du pattern.
ml_live_runtime: .space 320
