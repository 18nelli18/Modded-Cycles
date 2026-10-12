| Prototype CC pour deux LFO par voie B : contexte privé148 octets, initialement nul.
| 12 cases {paquet en attente,dernier retiré,dirty}, curseur à144.
| put(ctx,slot0..11,canal0..15,cc0..127,valeur0..127,port2..4) -> accepté.
| Coalescer par LFO : la modulation rapide ne remplit pas la file de notes.
| take(ctx) -> paquet [status,CC,valeur,port], exclusivement IPL0.
| Aucun appel MIDI, allocation ou attente ; non raccordé au firmware.
    .text
    .globl mlcc_put,mlcc_take
mlcc_put:
    lea.l %sp@(-16),%sp
    moveml %d2-%d4/%a2,%sp@
    moveq #0,%d0
    moveal %sp@(20),%a2
    tstl %a2
    beq .Lput_done
    movel %a2,%d1
    andil #3,%d1
    bne .Lput_done
    movel %sp@(24),%d1
    cmpil #11,%d1
    bhi .Lput_done
    movel %d1,%d2
    lsll #3,%d1
    lsll #2,%d2
    addl %d2,%d1
    addal %d1,%a2
    movel %sp@(28),%d2
    cmpil #15,%d2
    bhi .Lput_done
    oril #0xb0,%d2
    lsll #8,%d2
    movel %sp@(32),%d1
    cmpil #127,%d1
    bhi .Lput_done
    orl %d1,%d2
    lsll #8,%d2
    movel %sp@(36),%d1
    cmpil #127,%d1
    bhi .Lput_done
    orl %d1,%d2
    lsll #8,%d2
    movel %sp@(40),%d1
    cmpil #2,%d1
    bcs .Lput_done
    cmpil #4,%d1
    bhi .Lput_done
    orl %d1,%d2
    movew %sr,%d4
    movew #0x2700,%sr
    movel %d2,%a2@
    cmpl %a2@(4),%d2
    seq %d3
    andil #1,%d3
    eoril #1,%d3
    movel %d3,%a2@(8)
    movew %d4,%sr
    moveq #1,%d0
.Lput_done:
    moveml %sp@,%d2-%d4/%a2
    lea.l %sp@(16),%sp
    rts
mlcc_take:
    lea.l %sp@(-16),%sp
    moveml %d2-%d3/%a2-%a3,%sp@
    moveq #0,%d0
    movew %sr,%d3
    movel %d3,%d1
    andil #0x700,%d1
    bne .Ltake_done
    moveal %sp@(20),%a2
    tstl %a2
    beq .Ltake_done
    movel %a2,%d1
    andil #3,%d1
    bne .Ltake_done
    movel %a2@(144),%d2
    cmpil #11,%d2
    bhi .Ltake_done
    movew #0x2700,%sr
    moveq #11,%d1
.Lscan:
    movel %d2,%d0
    lsll #3,%d0
    moveal %d0,%a3
    movel %d2,%d0
    lsll #2,%d0
    addal %d0,%a3
    addal %a2,%a3
    addql #1,%d2
    cmpil #12,%d2
    bcs .Lcursor
    moveq #0,%d2
.Lcursor:
    tstl %a3@(8)
    bne .Lfound
    subql #1,%d1
    bpl .Lscan
    moveq #0,%d0
    bra .Lrestore
.Lfound:
    movel %a3@,%d0
    movel %d0,%a3@(4)
    clrl %a3@(8)
    movel %d2,%a2@(144)
.Lrestore:
    movew %d3,%sr
.Ltake_done:
    moveml %sp@,%d2-%d3/%a2-%a3
    lea.l %sp@(16),%sp
    rts
