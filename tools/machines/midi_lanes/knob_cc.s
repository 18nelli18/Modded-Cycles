| Assignations CC B : 6 voies x12 potards, couples {CC ou255 OFF,valeur}.
| edit(état144,voie,potard,delta,assigner,canal0..15,port2..4) -> paquet ou0.
| UI seule ; assigner ne transmet jamais. Aucun setter synthé ni accès disque.
    .text
    .globl mlkc_edit
mlkc_edit:
    lea %sp@(-16),%sp
    moveml %d2-%d3/%a2,%sp@
    moveq #0,%d0
    movew %sr,%d1
    andil #0x700,%d1
    bne .Lkc_done
    moveal %sp@(20),%a2
    tstl %a2
    beq .Lkc_done
    movel %sp@(24),%d1
    cmpil #5,%d1
    bhi .Lkc_done
    muluw #24,%d1
    addal %d1,%a2
    movel %sp@(28),%d1
    cmpil #11,%d1
    bhi .Lkc_done
    addl %d1,%d1
    addal %d1,%a2
    movel %sp@(32),%d2
    beq .Lkc_done
    movel %sp@(40),%d1
    cmpil #15,%d1
    bhi .Lkc_done
    movel %sp@(44),%d1
    cmpil #2,%d1
    bcs .Lkc_done
    cmpil #4,%d1
    bhi .Lkc_done
    tstl %sp@(36)
    beq .Lkc_value
    moveq #0,%d1
    moveb %a2@,%d1
    cmpil #255,%d1
    bne .Lkc_assign_ready
    moveq #-1,%d1
.Lkc_assign_ready:
    addl %d2,%d1
    cmpil #-1,%d1
    bge .Lkc_assign_low
    moveq #-1,%d1
.Lkc_assign_low:
    cmpil #127,%d1
    ble .Lkc_assign_high
    moveq #127,%d1
.Lkc_assign_high:
    moveb %d1,%a2@
    bra .Lkc_done
.Lkc_value:
    moveq #0,%d3
    moveb %a2@,%d3
    cmpil #127,%d3
    bhi .Lkc_done
    moveq #0,%d1
    moveb %a2@(1),%d1
    addl %d2,%d1
    bpl .Lkc_value_low
    moveq #0,%d1
.Lkc_value_low:
    cmpil #127,%d1
    ble .Lkc_value_high
    moveq #127,%d1
.Lkc_value_high:
    cmpb %a2@(1),%d1
    beq .Lkc_done
    moveb %d1,%a2@(1)
    movel %sp@(40),%d0
    oril #0xb0,%d0
    lsll #8,%d0
    orl %d3,%d0
    lsll #8,%d0
    orl %d1,%d0
    lsll #8,%d0
    orl %sp@(44),%d0
.Lkc_done:
    moveml %sp@,%d2-%d3/%a2
    lea %sp@(16),%sp
    rts
