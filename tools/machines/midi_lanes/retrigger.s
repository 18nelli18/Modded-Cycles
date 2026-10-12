| Prototype retrigger B : état privé de 20 octets par voie.
| active/deadline/interval/end/packet. Aucun accès aux pistes audio.
| ml_repeat_tick(runtime,état,voie,now) : au plus une répétition par appel.
| L'appelant publie l'état sous IPL7 et l'annule sur stop/mute/pattern.
| Intervalle 1..0x3fffffff, durée < 0x40000000 : comparaison modulo 32 bits.
| active=2 : Len INF, annulé explicitement au lieu de comparer end.
| Un retard saute les répétitions manquées ; aucun rattrapage en rafale.
    .text
    .globl ml_repeat_tick,ml_repeat_cancel
ml_repeat_tick:
    lea.l %sp@(-28),%sp
    movem.l %d2-%d4/%a2-%a3,%sp@
    movew %sr,%d0
    movel %d0,%sp@(20)
    movew #0x2700,%sr
    moveal %sp@(32),%a2
    moveal %sp@(36),%a3
    movel %sp@(40),%d2
    movel %sp@(44),%d3
    moveq #0,%d4
    cmpil #5,%d2
    bhi .Lrepeat_done
    tstl %a3@
    beq .Lrepeat_done
    movel %a3@(8),%d0
    subql #1,%d0
    cmpil #0x3ffffffe,%d0
    bhi .Lrepeat_expire
    movel %a3@,%d0
    cmpil #2,%d0
    beq .Lrepeat_deadline
    movel %d3,%d0
    subl %a3@(12),%d0
    bpl .Lrepeat_expire
.Lrepeat_deadline:
    movel %d3,%d0
    subl %a3@(4),%d0
    bmi .Lrepeat_done
    | Réutiliser la file qui réserve chaque Note Off avant d'accepter un On.
    pea 1
    movel %a3@(16),%sp@-
    movel %d2,%sp@-
    movel %a2,%sp@-
    jsr ml_step
    lea.l %sp@(16),%sp
    movel %d0,%d4
    movel %a3@(4),%d0
    addl %a3@(8),%d0
    movel %d3,%d1
    subl %d0,%d1
    bmi .Lrepeat_next
    movel %d3,%d0
    addl %a3@(8),%d0
.Lrepeat_next:
    movel %d0,%a3@(4)
    bra .Lrepeat_done
.Lrepeat_expire:
    clrl %a3@
    movel %d2,%sp@-
    movel %a2,%sp@-
    jsr ml_stop
    addql #8,%sp
.Lrepeat_done:
    movel %d4,%d0
    movel %sp@(20),%d1
    movew %d1,%sr
    movem.l %sp@,%d2-%d4/%a2-%a3
    lea.l %sp@(28),%sp
    rts
ml_repeat_cancel:
    movew %sr,%d0
    movel %d0,%sp@-
    movew #0x2700,%sr
    moveal %sp@(12),%a0
    clrl %a0@
    movel %sp@(16),%sp@-
    movel %sp@(12),%sp@-
    jsr ml_stop
    addql #8,%sp
    movel %sp@+,%d1
    movew %d1,%sr
    rts

| ml_repeat_arm(runtime,état,voie,now,packet,rate,durée) -> 1 si accepté.
| Table Rte native : 17 valeurs de 1/1 à 1/80, en unités musicales stock.
| La première note et sa réserve Off précèdent la publication de active.
| Aucun état partiellement armé en cas d'argument invalide ou file pleine.
    .globl ml_repeat_arm
ml_repeat_arm:
    lea.l %sp@(-32),%sp
    movem.l %d2-%d5/%a2-%a3,%sp@
    movew %sr,%d0
    movel %d0,%sp@(24)
    moveal %sp@(36),%a2
    moveal %sp@(40),%a3
    movel %sp@(44),%d2
    cmpil #5,%d2
    bhi .Larm_bad
    movel %sp@(56),%d0
    cmpil #16,%d0
    bhi .Larm_bad
    movel %sp@(52),%d0
    andil #0xf0808000,%d0
    cmpil #0x90000000,%d0
    bne .Larm_bad
    movel %sp@(52),%d0
    andil #0x00007f00,%d0
    beq .Larm_bad
    movel %sp@(52),%d0
    andil #255,%d0
    subql #2,%d0
    cmpil #2,%d0
    bhi .Larm_bad
    movel %sp@(56),%d0
    lea.l 0x4010ce4c,%a0
    movel %a0@(0,%d0:l:4),%d4
    movel %sp@(60),%d5
    cmpil #-1,%d5
    beq .Larm_duration_valid
    subql #1,%d5
    cmpil #0x3ffffffe,%d5
    bhi .Larm_bad
    addql #1,%d5
.Larm_duration_valid:
    movel %sp@(48),%d3
    movew #0x2700,%sr
    pea 1
    movel %sp@(56),%sp@-
    movel %d2,%sp@-
    movel %a2,%sp@-
    jsr ml_step
    lea.l %sp@(16),%sp
    tstl %d0
    beq .Larm_failed
    clrl %a3@
    movel %d4,%a3@(8)
    addl %d3,%d4
    movel %d4,%a3@(4)
    addl %d3,%d5
    movel %d5,%a3@(12)
    movel %sp@(52),%d0
    movel %d0,%a3@(16)
    moveq #1,%d0
    movel %sp@(60),%d1
    cmpil #-1,%d1
    bne .Larm_publish
    moveq #2,%d0
.Larm_publish:
    movel %d0,%a3@
    moveq #1,%d0
    bra .Larm_done
.Larm_failed:
    clrl %a3@
.Larm_bad:
    moveq #0,%d0
.Larm_done:
    movel %sp@(24),%d1
    movew %d1,%sr
    movem.l %sp@,%d2-%d5/%a2-%a3
    lea.l %sp@(32),%sp
    rts

| Len stock confirmé par audit_midi_retrigger_length.py. Retour durée B,
| 0 si invalide/hors horizon sûr, -1 pour INF127. Aucune constante OS copiée.
| ml_repeat_duration(length,gate_remaining,latency_half).
    .globl ml_repeat_duration
ml_repeat_duration:
    movel %sp@(4),%d0
    cmpil #127,%d0
    bhi .Lduration_bad
    cmpil #127,%d0
    beq .Lduration_infinite
    moveal #0x4010d814,%a0
    movel %a0@(4,%d0:l:4),%d1
    movel %sp@(8),%d0
    cmpil #0x3fffffff,%d0
    bhi .Lduration_bad
    lsrl #1,%d0
    addl %d1,%d0
    bcs .Lduration_bad
    movel %sp@(12),%d1
    subl %d1,%d0
    bcs .Lduration_bad
    tstl %d0
    beq .Lduration_bad
    cmpil #0x1fffffff,%d0
    bhi .Lduration_bad
    addl %d0,%d0
    rts
.Lduration_infinite:
    moveq #-1,%d0
    rts
.Lduration_bad:
    moveq #0,%d0
    rts
