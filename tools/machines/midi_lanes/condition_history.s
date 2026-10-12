| Historique conditionnel B privé : six records16, aucun état audio natif.
| record : dernier résultat long, passage après premier long, phases B=1..8.
| init(bank96), advance(bank,lane), remember(bank,lane,kind,result),
| previous(bank,lane), neighbor(bank,lane), phase(bank,lane,B).
| PRE et !PRE ne remplacent jamais le dernier résultat conditionnel.
    .text
    .globl ml_cond_init,ml_cond_advance,ml_cond_remember
    .globl ml_cond_previous,ml_cond_neighbor,ml_cond_phase,ml_cond_first
ml_cond_init:
    moveal %sp@(4),%a0
    tstl %a0
    beq .Lhist_bad
    movel %a0,%d0
    andil #3,%d0
    bne .Lhist_bad
    moveq #23,%d0
.Lhist_zero:
    clrl %a0@+
    subql #1,%d0
    bpl .Lhist_zero
    moveq #1,%d0
    rts
| Validation commune ; d0=voie, a0=record, d1=valide.
.Lhist_record:
    moveal %sp@(8),%a0
    tstl %a0
    beq .Lhist_record_bad
    movel %a0,%d0
    andil #3,%d0
    bne .Lhist_record_bad
    movel %sp@(12),%d0
    cmpil #5,%d0
    bhi .Lhist_record_bad
    lsll #4,%d0
    addal %d0,%a0
    moveq #1,%d1
    rts
.Lhist_record_bad:
    moveq #0,%d1
    rts
ml_cond_advance:
    jsr .Lhist_record
    tstl %d1
    beq .Lhist_bad
    moveq #1,%d0
    movel %d0,%a0@(4)
    addql #8,%a0
    moveq #1,%d1
.Lhist_advance_loop:
    moveq #0,%d0
    moveb %a0@,%d0
    addql #1,%d0
    cmpl %d1,%d0
    bcs .Lhist_advance_write
    moveq #0,%d0
.Lhist_advance_write:
    moveb %d0,%a0@+
    addql #1,%d1
    cmpil #9,%d1
    bcs .Lhist_advance_loop
    moveq #1,%d0
    rts
ml_cond_remember:
    jsr .Lhist_record
    tstl %d1
    beq .Lhist_bad
    movel %sp@(12),%d0
    cmpil #9,%d0
    bhi .Lhist_bad
    cmpil #3,%d0
    beq .Lhist_unchanged
    cmpil #4,%d0
    beq .Lhist_unchanged
    movel %sp@(16),%d0
    cmpil #1,%d0
    bhi .Lhist_bad
    jsr .Lhist_record
    tstl %d1
    beq .Lhist_bad
    movel %sp@(16),%d0
    movel %d0,%a0@
.Lhist_unchanged:
    moveq #1,%d0
    rts
ml_cond_previous:
    jsr .Lhist_record
    tstl %d1
    beq .Lhist_bad
    movel %a0@,%d0
    rts
ml_cond_neighbor:
    jsr .Lhist_record
    tstl %d1
    beq .Lhist_bad
    tstl %sp@(8)
    beq .Lhist_bad
    movel %a0@(-16),%d0
    rts
ml_cond_first:
    jsr .Lhist_record
    tstl %d1
    beq .Lhist_bad
    tstl %a0@(4)
    seq %d0
    andil #1,%d0
    rts
ml_cond_phase:
    jsr .Lhist_record
    tstl %d1
    beq .Lhist_bad
    movel %sp@(12),%d1
    subql #1,%d1
    cmpil #7,%d1
    bhi .Lhist_bad
    moveq #0,%d0
    moveb %a0@(8,%d1:l),%d0
    rts
.Lhist_bad:
    moveq #0,%d0
    rts
