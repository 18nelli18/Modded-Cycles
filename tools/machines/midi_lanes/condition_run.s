| Exécution condition B : run(history96,lane,code,fill,sample) -> bool.
| Décode les choix natifs, lit uniquement les voisins B, puis mémorise le
| résultat explicite sauf PRE/inverse. Aucun effet sur le RNG ou pistes A.
| Appels sérialisés par le scheduler B sous IPL7.
    .text
    .globl ml_condition_run
ml_condition_run:
    lea.l %sp@(-64),%sp
    moveml %d2-%d5/%a2-%a3,%sp@
    moveal %sp,%a3
    moveal %a3@(68),%a2
    tstl %a2
    beq .Lrun_bad
    movel %a2,%d0
    andil #3,%d0
    bne .Lrun_bad
    movel %a3@(72),%d2
    cmpil #5,%d2
    bhi .Lrun_bad
    movel %a3@(84),%d0
    cmpil #99,%d0
    bhi .Lrun_bad
    pea %a3@(24)
    movel %a3@(76),%sp@-
    jsr ml_condition_decode
    addql #8,%sp
    tstl %d0
    beq .Lrun_bad
    movel %a3@(24),%d3
    movel %d2,%sp@-
    movel %a2,%sp@-
    jsr ml_cond_previous
    addql #8,%sp
    movel %d0,%a3@(40)
    movel %d2,%sp@-
    movel %a2,%sp@-
    jsr ml_cond_neighbor
    addql #8,%sp
    movel %d0,%a3@(44)
    moveq #0,%d5
    cmpil #7,%d3
    bcs .Lrun_phase_ready
    cmpil #8,%d3
    bhi .Lrun_ratio
    movel %d2,%sp@-
    movel %a2,%sp@-
    jsr ml_cond_first
    addql #8,%sp
    moveq #1,%d5
    eorl %d0,%d5
    bra .Lrun_phase_ready
.Lrun_ratio:
    movel %a3@(32),%sp@-
    movel %d2,%sp@-
    movel %a2,%sp@-
    jsr ml_cond_phase
    lea.l %sp@(12),%sp
    movel %d0,%d5
.Lrun_phase_ready:
    movel %a3@(84),%sp@-
    movel %a3@(44),%sp@-
    movel %a3@(40),%sp@-
    movel %a3@(80),%sp@-
    movel %d5,%sp@-
    movel %a3@(32),%sp@-
    movel %a3@(28),%sp@-
    movel %d3,%sp@-
    jsr ml_condition_eval
    lea.l %sp@(32),%sp
    movel %d0,%d4
    movel %d4,%sp@-
    movel %d3,%sp@-
    movel %d2,%sp@-
    movel %a2,%sp@-
    jsr ml_cond_remember
    lea.l %sp@(16),%sp
    movel %d4,%d0
    bra .Lrun_done
.Lrun_bad:
    moveq #0,%d0
.Lrun_done:
    moveml %sp@,%d2-%d5/%a2-%a3
    lea.l %sp@(64),%sp
    rts
