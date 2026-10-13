| Écriture CC annexe : réutiliser exactement les adaptateurs natifs validés.
| verified(path,record,scratch,length176ou9248) -> bool. Copie inactive seule.
| Aucun accès sous IRQ, buffers privés disjoints, comparaison intégrale.
    .text
    .globl mlkcs_verified
mlkcs_verified:
    lea %sp@(-20),%sp
    moveml %d2-%d3/%a2-%a4,%sp@
    moveq #0,%d2
    movew %sr,%d0
    andil #0x700,%d0
    bne .Ldone
    moveal %sp@(24),%a4
    tstl %a4
    beq .Ldone
    moveal %sp@(28),%a2
    tstl %a2
    beq .Ldone
    moveal %sp@(32),%a3
    tstl %a3
    beq .Ldone
    movel %sp@(36),%d3
    cmpil #176,%d3
    beq .Llength
    cmpil #9248,%d3
    bne .Ldone
.Llength:
    movel %a2,%d0
    movel %a3,%d1
    orl %d1,%d0
    andil #3,%d0
    bne .Ldone
    movel %a2,%d0
    addl %d3,%d0
    bcs .Ldone
    movel %a3,%d1
    addl %d3,%d1
    bcs .Ldone
    cmpl %a3,%d0
    bls .Ldisjoint
    cmpl %a2,%d1
    bhi .Ldone
.Ldisjoint:
    movel %d3,%sp@-
    movel %a2,%sp@-
    movel %a4,%sp@-
    jsr ml_store_write
    lea %sp@(12),%sp
    tstl %d0
    beq .Ldone
    movel %d3,%sp@-
    movel %a3,%sp@-
    movel %a4,%sp@-
    jsr ml_store_read
    lea %sp@(12),%sp
    tstl %d0
    beq .Ldone
    subql #1,%d3
.Lcompare:
    moveb %a2@+,%d0
    cmpb %a3@+,%d0
    bne .Ldone
    subql #1,%d3
    bpl .Lcompare
    moveq #1,%d2
.Ldone:
    movel %d2,%d0
    moveml %sp@,%d2-%d3/%a2-%a4
    lea %sp@(20),%sp
    rts
