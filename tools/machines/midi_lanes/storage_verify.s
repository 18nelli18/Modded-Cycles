| Copie inactive uniquement : écriture puis relecture et comparaison intégrale.
| ml_store_verified(path,record,scratch,1616) -> 1 si identiques.
| Scratch privé, disjoint ; aucune publication de génération ni hook Save.
    .ifdef ML_STORAGE3
    .equ ML_DATA_BYTES,4992
    .equ ML_RECORD_BYTES,5024
    .else
    .ifdef ML_STORAGE2
    .equ ML_DATA_BYTES,4896
    .equ ML_RECORD_BYTES,4928
    .else
    .equ ML_DATA_BYTES,1584
    .equ ML_RECORD_BYTES,1616
    .endif
    .endif
    .text
    .globl ml_store_verified
ml_store_verified:
    lea.l %sp@(-16),%sp
    moveml %d2/%a2-%a4,%sp@
    moveq #0,%d2
    movew %sr,%d0
    andil #0x700,%d0
    bne .Ldone
    moveal %sp@(20),%a4
    tstl %a4
    beq .Ldone
    moveal %sp@(24),%a2
    tstl %a2
    beq .Ldone
    moveal %sp@(28),%a3
    tstl %a3
    beq .Ldone
    movel %sp@(32),%d0
    cmpil #ML_RECORD_BYTES,%d0
    bne .Ldone
    movel %a2,%d0
    addil #ML_RECORD_BYTES,%d0
    bcs .Ldone
    movel %a3,%d1
    addil #ML_RECORD_BYTES,%d1
    bcs .Ldone
    cmpl %a3,%d0
    bls .Ldisjoint
    cmpl %a2,%d1
    bhi .Ldone
.Ldisjoint:
    pea ML_RECORD_BYTES
    movel %a2,%sp@-
    movel %a4,%sp@-
    jsr ml_store_write
    lea.l %sp@(12),%sp
    tstl %d0
    beq .Ldone
    pea ML_RECORD_BYTES
    movel %a3,%sp@-
    movel %a4,%sp@-
    jsr ml_store_read
    lea.l %sp@(12),%sp
    tstl %d0
    beq .Ldone
    movel #1615,%d1
.Lcompare:
    moveb %a2@+,%d0
    cmpb %a3@+,%d0
    bne .Ldone
    subql #1,%d1
    bpl .Lcompare
    moveq #1,%d2
.Ldone:
    movel %d2,%d0
    moveml %sp@,%d2/%a2-%a4
    lea.l %sp@(16),%sp
    rts
