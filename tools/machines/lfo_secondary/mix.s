| Prototype note 58 : out, base non modulée, taille en mots, banque 1, banque 2.
| Somme des contributions aux 12 destinations, puis saturation unique.
| Pile bornée 140 octets, aucune allocation ni API. Intégration audio à prouver.
    .text
    .globl lf2_mix
lf2_mix:
    lea.l %sp@(-140),%sp
    movem.l %d2-%d7/%a2-%fp,%sp@
    moveal %sp@(144),%a2
    moveal %sp@(148),%a3
    movel %sp@(152),%d7
    moveal %sp@(156),%a4
    lea.l %sp@(44),%a5
    lea.l %sp@(92),%fp
    moveal %a2,%a0
    moveal %a3,%a1
    movel %d7,%d0
    beq .Lcopy_done
.Lcopy:
    movew %a1@+,%d1
    movew %d1,%a0@+
    subql #1,%d0
    bne .Lcopy
.Lcopy_done:
    moveq #0,%d6
    moveq #0,%d5
    moveq #0,%d4
.Ltarget:
    movel %a4@(16),%d0
    bmi .Lnext
    cmpil #32,%d0
    bhi .Lnext
    movel %d4,%d1
    muluw #33,%d1
    addql #7,%d1
    addl %d1,%d0
    cmpl %d7,%d0
    bcc .Lnext
    moveq #0,%d3
.Lfind:
    cmpl %d6,%d3
    beq .Lnew
    cmpl %a5@(0,%d3:l:4),%d0
    beq .Ladd
    addql #1,%d3
    bra .Lfind
.Lnew:
    movel %d0,%a5@(0,%d3:l:4)
    moveq #0,%d2
    movew %a3@(0,%d0:l:2),%d2
    movel %d2,%fp@(0,%d3:l:4)
    addql #1,%d6
.Ladd:
    movel %fp@(0,%d3:l:4),%d2
    addl %a4@(20),%d2
    movel %d2,%fp@(0,%d3:l:4)
.Lnext:
    lea.l %a4@(32),%a4
    addql #1,%d4
    addql #1,%d5
    cmpil #6,%d5
    bne .Llast
    moveq #0,%d4
    moveal %sp@(160),%a4
.Llast:
    cmpil #12,%d5
    bne .Ltarget
    moveq #0,%d3
.Lapply:
    cmpl %d6,%d3
    beq .Ldone
    movel %fp@(0,%d3:l:4),%d0
    bpl .Lpositive
    moveq #0,%d0
.Lpositive:
    cmpil #32512,%d0
    ble .Lwrite
    movel #32512,%d0
.Lwrite:
    movel %a5@(0,%d3:l:4),%d1
    movew %d0,%a2@(0,%d1:l:2)
    addql #1,%d3
    bra .Lapply
.Ldone:
    movem.l %sp@,%d2-%d7/%a2-%fp
    lea.l %sp@(140),%sp
    rts
