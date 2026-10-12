| Transaction arp/retrigger : ne publier la progression qu'après On accepté.
| ml_repeat_arp_tick(runtime,repeat20,arp32,lane,now,mode,octaves) -> bool.
| État arp candidat sur pile, aucune allocation, Note Off réservé par ml_step.
| OFF répète le paquet d'origine ; arrêt/échéance utilisent le service normal.
    .text
    .globl ml_repeat_arp_tick
ml_repeat_arp_tick:
    lea.l %sp@(-64),%sp
    movem.l %d2-%d4/%a2-%a5,%sp@
    movew %sr,%d0
    movel %d0,%sp@(28)
    movew #0x2700,%sr
    moveal %sp@(68),%a5
    moveal %sp@(72),%a2
    moveal %sp@(76),%a3
    movel %sp@(80),%d2
    movel %sp@(84),%d3
    cmpil #5,%d2
    bhi .Larp_tick_bad
    movel %sp@(88),%d0
    cmpil #5,%d0
    bhi .Larp_tick_bad
    movel %sp@(92),%d0
    subql #1,%d0
    cmpil #3,%d0
    bhi .Larp_tick_bad
    tstl %a2@
    beq .Larp_tick_plain
    movel %a2@,%d0
    cmpil #2,%d0
    beq .Larp_tick_deadline
    movel %d3,%d0
    subl %a2@(12),%d0
    bpl .Larp_tick_plain
.Larp_tick_deadline:
    movel %d3,%d0
    subl %a2@(4),%d0
    bmi .Larp_tick_plain
    movel %sp@(88),%d0
    cmpil #5,%d0
    beq .Larp_tick_plain
    lea.l %sp@(32),%a4
    moveal %a3,%a0
    moveal %a4,%a1
    moveq #7,%d0
.Larp_tick_copy:
    movel %a0@+,%d1
    movel %d1,%a1@+
    subql #1,%d0
    bpl .Larp_tick_copy
    movel %sp@(92),%sp@-
    movel %sp@(92),%sp@-
    movel %a4,%sp@-
    jsr ml_arp_next
    lea.l %sp@(12),%sp
    tstl %d0
    bmi .Larp_tick_bad
    movel %a2@(16),%d4
    lsll #8,%d0
    lsll #8,%d0
    movel %d4,%d1
    andil #0xff00ffff,%d1
    orl %d1,%d0
    movel %d0,%a2@(16)
    movel %d3,%sp@-
    movel %d2,%sp@-
    movel %a2,%sp@-
    movel %a5,%sp@-
    jsr ml_repeat_tick
    lea.l %sp@(16),%sp
    tstl %d0
    beq .Larp_tick_rejected
    moveal %a4,%a0
    moveal %a3,%a1
    moveq #7,%d1
.Larp_tick_publish:
    movel %a0@+,%d0
    movel %d0,%a1@+
    subql #1,%d1
    bpl .Larp_tick_publish
    moveq #1,%d0
    bra .Larp_tick_done
.Larp_tick_rejected:
    movel %d4,%a2@(16)
    bra .Larp_tick_done
.Larp_tick_plain:
    movel %d3,%sp@-
    movel %d2,%sp@-
    movel %a2,%sp@-
    movel %a5,%sp@-
    jsr ml_repeat_tick
    lea.l %sp@(16),%sp
    bra .Larp_tick_done
.Larp_tick_bad:
    moveq #0,%d0
.Larp_tick_done:
    movel %sp@(28),%d1
    movem.l %sp@,%d2-%d4/%a2-%a5
    lea.l %sp@(64),%sp
    movew %d1,%sr
    rts
