| Prototype chance B : dernier octet du record retrig8, sans changer le format.
| 0 hérite ; 1..101 représente 0..100 %. Les masques retrig restent inchangés.
| set(table,step,pct), clear(table,step), percent(default8,table512,step),
| accept(default8,table512,step,échantillon0..99). Aucun RNG audio partagé.
| Raccordement Test3 conditionnel ; le build compact conserve seulement le RNG.
    .text
    .ifndef ML_CONDITION_COMPACT
    .globl ml_chance_set,ml_chance_clear,ml_chance_percent,ml_chance_accept
ml_chance_set:
    movel %sp@(12),%d0
    cmpil #100,%d0
    bhi .Lchance_bad
    addql #1,%d0
    bra .Lchance_write
ml_chance_clear:
    moveq #0,%d0
.Lchance_write:
    moveal %sp@(4),%a0
    tstl %a0
    beq .Lchance_bad
    movel %a0,%d1
    andil #3,%d1
    bne .Lchance_bad
    movel %sp@(8),%d1
    cmpil #63,%d1
    bhi .Lchance_bad
    lsll #3,%d1
    moveb %d0,%a0@(7,%d1:l)
    moveq #1,%d0
    rts
.Lchance_bad:
    moveq #0,%d0
    rts
ml_chance_percent:
    moveal %sp@(4),%a0
    moveal %sp@(8),%a1
    tstl %a0
    beq .Lchance_full
    tstl %a1
    beq .Lchance_full
    movel %sp@(12),%d1
    cmpil #63,%d1
    bhi .Lchance_full
    lsll #3,%d1
    moveq #0,%d0
    moveb %a1@(7,%d1:l),%d0
    beq .Lchance_default
    cmpil #101,%d0
    bls .Lchance_decode
.Lchance_default:
    moveb %a0@(7),%d0
    beq .Lchance_full
    cmpil #101,%d0
    bhi .Lchance_full
.Lchance_decode:
    subql #1,%d0
    rts
.Lchance_full:
    moveq #100,%d0
    rts
ml_chance_accept:
    movel %d2,%sp@-
    movel %sp@(20),%d2
    cmpil #99,%d2
    bhi .Lchance_reject
    movel %sp@(16),%sp@-
    movel %sp@(16),%sp@-
    movel %sp@(16),%sp@-
    jsr ml_chance_percent
    lea.l %sp@(12),%sp
    cmpl %d0,%d2
    bcc .Lchance_reject
    moveq #1,%d0
    bra .Lchance_accept_done
.Lchance_reject:
    moveq #0,%d0
.Lchance_accept_done:
    movel %sp@+,%d2
    rts

    .endif

| Tirage privé B : seed32 fourni par voie, sans état global ni RNG audio.
| sample(seed*) -> 0..99, ou -1 si pointeur invalide. Coût borné sans boucle.
    .globl ml_chance_sample
ml_chance_sample:
    moveal %sp@(4),%a0
    tstl %a0
    beq .Lsample_bad
    movel %a0,%d0
    andil #3,%d0
    bne .Lsample_bad
    movel %a0@,%d0
    bne .Lsample_seed
    movel #0x6d2b79f5,%d0
.Lsample_seed:
    movel %d0,%d1
    lsll #8,%d1
    lsll #5,%d1
    eorl %d1,%d0
    movel %d0,%d1
    lsrl #8,%d1
    lsrl #8,%d1
    lsrl #1,%d1
    eorl %d1,%d0
    movel %d0,%d1
    lsll #5,%d1
    eorl %d1,%d0
    movel %d0,%a0@
    swap %d0
    andil #65535,%d0
    muluw #100,%d0
    swap %d0
    andil #65535,%d0
    rts
.Lsample_bad:
    moveq #-1,%d0
    rts
