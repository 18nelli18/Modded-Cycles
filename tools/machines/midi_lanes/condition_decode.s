| Adapter l'index condition natif0..63 au moteur B, sans copier la table OS.
| decode(code,out12) -> bool ; sortie kind/a/b, publiée après validation.
| Les noms/valeurs viennent de la table native de l'OS utilisateur à l'exécution.
    .text
    .globl ml_condition_decode
ml_condition_decode:
    movel %sp@(4),%d0
    cmpil #63,%d0
    bhi .Ldecode_bad
    moveal %sp@(8),%a1
    tstl %a1
    beq .Ldecode_bad
    movel %a1,%d1
    andil #3,%d1
    bne .Ldecode_bad
    cmpil #8,%d0
    bcc .Ldecode_number
    addql #1,%d0
    movel %d0,%a1@
    clrl %a1@(4)
    clrl %a1@(8)
    moveq #1,%d0
    rts
.Ldecode_number:
    lea.l 0x40108f54,%a0
    moveal %a0@(0,%d0:l:4),%a0
    cmpil #29,%d0
    bcc .Ldecode_ratio
    moveq #0,%d0
    moveb %a0@+,%d0
    subil #48,%d0
    cmpil #9,%d0
    bhi .Ldecode_bad
    moveq #0,%d1
    moveb %a0@+,%d1
    cmpil #37,%d1
    beq .Ldecode_percent
    subil #48,%d1
    cmpil #9,%d1
    bhi .Ldecode_bad
    muluw #10,%d0
    addl %d1,%d0
    moveq #0,%d1
    moveb %a0@,%d1
    cmpil #37,%d1
    bne .Ldecode_bad
.Ldecode_percent:
    clrl %a1@
    movel %d0,%a1@(4)
    clrl %a1@(8)
    moveq #1,%d0
    rts
.Ldecode_ratio:
    moveq #0,%d0
    moveb %a0@,%d0
    subil #49,%d0
    cmpil #7,%d0
    bhi .Ldecode_bad
    addql #1,%d0
    moveq #0,%d1
    moveb %a0@(1),%d1
    cmpil #58,%d1
    bne .Ldecode_bad
    moveq #0,%d1
    moveb %a0@(2),%d1
    subil #49,%d1
    cmpil #7,%d1
    bhi .Ldecode_bad
    addql #1,%d1
    cmpl %d1,%d0
    bhi .Ldecode_bad
    movel %d0,%a1@(4)
    movel %d1,%a1@(8)
    moveq #9,%d0
    movel %d0,%a1@
    moveq #1,%d0
    rts
.Ldecode_bad:
    moveq #0,%d0
    rts
