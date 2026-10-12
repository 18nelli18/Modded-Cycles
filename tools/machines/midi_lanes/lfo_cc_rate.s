| Limite globale LFO CC : compteur privé4 octets, nul au départ.
| rate_tick(rate) une fois par bloc audio1500Hz, compteur saturant à6.
| rate_service(queue,rate) IPL0 : un CC maximum, six blocs entre retraits.
| 250 messages/s maximum (750 octets DIN/s), sans crédit accumulé au repos.
| Les notes utilisent leur propre file et ne consomment pas ce compteur.
    .text
    .globl mlcc_rate_tick,mlcc_rate_service
mlcc_rate_tick:
    moveq #0,%d0
    moveal %sp@(4),%a0
    tstl %a0
    beq .Lrt_done
    movel %a0,%d1
    andil #3,%d1
    bne .Lrt_done
    movew %sr,%d0
    movew #0x2700,%sr
    movel %a0@,%d1
    cmpil #6,%d1
    bcc .Lrt_restore
    addql #1,%d1
    movel %d1,%a0@
.Lrt_restore:
    movew %d0,%sr
    moveq #1,%d0
.Lrt_done:
    rts
mlcc_rate_service:
    movel %d2,%sp@-
    moveq #0,%d0
    movew %sr,%d2
    movel %d2,%d1
    andil #0x700,%d1
    bne .Lrs_done
    tstl 0x40fe4228
    beq .Lrs_done
    moveal %sp@(12),%a0
    tstl %a0
    beq .Lrs_done
    movel %a0,%d1
    andil #3,%d1
    bne .Lrs_done
    movew #0x2700,%sr
    movel %a0@,%d1
    cmpil #6,%d1
    bcs .Lrs_restore
    clrl %a0@
    movew %d2,%sr
    pea 1
    movel %sp@(12),%sp@-
    jsr mlcc_service
    addql #8,%sp
    bra .Lrs_done
.Lrs_restore:
    movew %d2,%sr
.Lrs_done:
    movel %sp@+,%d2
    rts
