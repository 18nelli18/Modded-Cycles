| Service retrigger B entre les pas, sans allocation ni accès MIDI physique.
| ml_repeat_service(runtime,pattern,états120,now,playing) -> répétitions acceptées.
| L'appelant fournit le pattern publié ; changement de pattern : annuler avant
| sa publication. Stop/pause, mute, canal/port modifié annulent ici les états.
| Au plus six répétitions par appel. Aucun traitement d'une piste audio.
    .data
    .balign 4
    .globl ml_repeat_states,ml_repeat_arp_bank
ml_repeat_states: .space 120
| Pointeur UI publié après init : six records mode/octaves/arp32 (40 octets).
| Zéro garde le retrigger simple. Les données restent exclusivement B.
ml_repeat_arp_bank: .long 0
    .globl ml_repeat_owner
ml_repeat_owner: .long 0
    .text
    .globl ml_repeat_service,ml_repeat_service_with_arp,ml_repeat_cancel_all,ml_repeat_audio
| Adaptateur audio : détruire l'ancien propriétaire avant tout changement.
| ml_repeat_audio(runtime,pattern,now,playing), utilisé sous ML_REPEAT.
ml_repeat_audio:
    lea.l %sp@(-16),%sp
    movem.l %a2-%a3,%sp@
    movew %sr,%d0
    movel %d0,%sp@(8)
    movew #0x2700,%sr
    moveal %sp@(20),%a2
    moveal %sp@(24),%a3
    cmpal ml_repeat_owner,%a3
    beq .Laudio_same
    pea ml_repeat_states
    movel %a2,%sp@-
    jsr ml_repeat_cancel_all
    addql #8,%sp
    movel ml_repeat_arp_bank,%d0
    beq .Laudio_no_arp
    movel %d0,%sp@-
    jsr ml_arp_bank_reset
    addql #4,%sp
.Laudio_no_arp:
    movel %a3,%sp@-
    jsr ml_repeat_pattern_lookup
    addql #4,%sp
    movel %d0,ml_repeat_play_settings
    movel %a3,ml_repeat_owner
.Laudio_same:
    movel %sp@(32),%sp@-
    movel %sp@(32),%sp@-
    pea ml_repeat_states
    movel %a3,%sp@-
    movel %a2,%sp@-
    jsr ml_repeat_service
    lea.l %sp@(20),%sp
    movel %sp@(8),%d1
    movem.l %sp@,%a2-%a3
    lea.l %sp@(16),%sp
    movew %d1,%sr
    rts
ml_repeat_service:
    | Compatibilité avec l'ordonnanceur de pattern ; état arp publié UI.
    movew %sr,%d0
    movel %d0,%sp@-
    movel ml_repeat_arp_bank,%sp@-
    movel %sp@(28),%sp@-
    movel %sp@(28),%sp@-
    movel %sp@(28),%sp@-
    movel %sp@(28),%sp@-
    movel %sp@(28),%sp@-
    jsr ml_repeat_service_with_arp
    lea.l %sp@(24),%sp
    movel %sp@+,%d1
    movew %d1,%sr
    rts
| Même contrat + sixième argument arpbank ; permet un propriétaire live
| distinct du séquenceur, sans échanger un global sous interruption.
ml_repeat_service_with_arp:
    lea.l %sp@(-40),%sp
    movem.l %d2-%d6/%a2-%a5,%sp@
    movew %sr,%d0
    movel %d0,%sp@(36)
    movew #0x2700,%sr
    moveal %sp@(44),%a2
    moveal %sp@(48),%a3
    moveal %sp@(52),%a4
    movel %sp@(56),%d4
    movel %sp@(60),%d5
    moveq #0,%d2
    moveq #0,%d6
.Lservice_lane:
    tstl %a4@
    beq .Lservice_next
    cmpil #1,%d5
    bne .Lservice_cancel
    tstb %a3@
    beq .Lservice_cancel
    tstb %a3@(1)
    bne .Lservice_cancel
    moveq #0,%d0
    moveb %a3@(4),%d0
    subql #1,%d0
    cmpil #63,%d0
    bhi .Lservice_cancel
    moveq #0,%d0
    moveb %a3@(5),%d0
    cmpil #6,%d0
    bhi .Lservice_cancel
    moveq #0,%d0
    moveb %a3@(2),%d0
    cmpil #15,%d0
    bhi .Lservice_cancel
    oril #0x90,%d0
    moveq #0,%d1
    moveb %a4@(16),%d1
    cmpl %d0,%d1
    bne .Lservice_cancel
    moveq #0,%d0
    moveb %a3@(3),%d0
    moveq #0,%d1
    moveb %a4@(19),%d1
    cmpl %d0,%d1
    bne .Lservice_cancel
    subql #2,%d0
    cmpil #2,%d0
    bhi .Lservice_cancel
    moveal %sp@(64),%a5
    tstl %a5
    beq .Lservice_plain
    movel %d2,%d0
    muluw #40,%d0
    addal %d0,%a5
    movel %a5@,%d0
    cmpil #5,%d0
    bhi .Lservice_cancel
    movel %a5@(4),%d1
    subql #1,%d1
    cmpil #3,%d1
    bhi .Lservice_cancel
    cmpil #5,%d0
    beq .Lservice_plain
    movel %a5@(8),%d0
    cmpil #12,%d0
    bhi .Lservice_cancel
    tstl %d0
    beq .Lservice_plain
    movel %a5@(4),%sp@-
    movel %a5@,%sp@-
    movel %d4,%sp@-
    movel %d2,%sp@-
    pea %a5@(8)
    movel %a4,%sp@-
    movel %a2,%sp@-
    jsr ml_repeat_arp_tick
    lea.l %sp@(28),%sp
    bra .Lservice_count
.Lservice_plain:
    movel %d4,%sp@-
    movel %d2,%sp@-
    movel %a4,%sp@-
    movel %a2,%sp@-
    jsr ml_repeat_tick
    lea.l %sp@(16),%sp
.Lservice_count:
    addl %d0,%d6
    bra .Lservice_next
.Lservice_cancel:
    movel %d2,%sp@-
    movel %a4,%sp@-
    movel %a2,%sp@-
    jsr ml_repeat_cancel
    lea.l %sp@(12),%sp
.Lservice_next:
    lea.l %a3@(264),%a3
    lea.l %a4@(20),%a4
    addql #1,%d2
    cmpil #6,%d2
    bne .Lservice_lane
    movel %d6,%d0
    movel %sp@(36),%d1
    movem.l %sp@,%d2-%d6/%a2-%a5
    lea.l %sp@(40),%sp
    movew %d1,%sr
    rts

| Annuler sous IPL7 avant de publier une autre banque ou restaurer un projet.
| ml_repeat_cancel_all(runtime,états120) ; chaque Off garde son ancien canal.
ml_repeat_cancel_all:
    lea.l %sp@(-20),%sp
    movem.l %d2/%a2-%a3,%sp@
    movew %sr,%d0
    movel %d0,%sp@(12)
    movew #0x2700,%sr
    moveal %sp@(24),%a2
    moveal %sp@(28),%a3
    moveq #0,%d2
.Lcancel_all_lane:
    movel %d2,%sp@-
    movel %a3,%sp@-
    movel %a2,%sp@-
    jsr ml_repeat_cancel
    lea.l %sp@(12),%sp
    lea.l %a3@(20),%a3
    addql #1,%d2
    cmpil #6,%d2
    bne .Lcancel_all_lane
    movel %sp@(12),%d1
    movem.l %sp@,%d2/%a2-%a3
    lea.l %sp@(20),%sp
    movew %d1,%sr
    rts
