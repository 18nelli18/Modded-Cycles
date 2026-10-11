    .ifdef SG_DYNAMICS
    .globl sg_dyn_backup,sg_dyn_step,sg_dyn_restore,sg_dyn_validate
    .endif
| Variation par trig, arrêt obligatoire déjà contrôlé par sg_track_write.
| Stockage fixe OS : 6 pistes × 4385 octets, 64 × 34 mots et 33 indicateurs.
| Sauvegarde uniquement la piste visée, pointeur et index gardés dans la page.
    .ifdef SG_DYNAMICS
    .section .text.sg_dyn_backup,"ax"
sg_dyn_backup:
    lea.l %sp@(-12),%sp
    movem.l %d2/%a2-%a3,%sp@
    moveal sg_obj,%a2
    movel sg_options+4,%d0
    orl sg_options+8,%d0
    beqw sdb_none
    moveal %a3@(44),%a0
    tstl %a0
    beqw sdb_fail
    movel %a3@(56),%d2
    cmpil #5,%d2
    bhiw sdb_fail
    movel %a0,%sp@-
    moveal %a0@,%a1
    moveal %a1@(40),%a1
    jsr %a1@
    addql #4,%sp
    tstl %d0
    beqw sdb_fail
    muluw #4385,%d2
    moveal %d0,%a0
    addal %d2,%a0
    movel %a0,%a2@(1000)
    movel %a3@(44),%a2@(1004)
    lea.l %a2@(1008),%a1
    jsr sg_dyn_copy
    bras sdb_ok
sdb_none:
    clrl %a2@(1000)
sdb_ok:
    moveq #1,%d0
    bras sdb_out
sdb_fail:
    moveq #0,%d0
sdb_out:
    movem.l %sp@,%d2/%a2-%a3
    lea.l %sp@(12),%sp
    rts

| Un changement de pattern ne doit jamais recevoir le snapshot précédent.
sg_dyn_validate:
    lea.l %sp@(-12),%sp
    movem.l %d2/%a2-%a3,%sp@
    moveal sg_obj,%a2
    movel %a3,%sp@-
    moveal %a3@,%a0
    moveal %a0@(40),%a0
    jsr %a0@
    addql #4,%sp
    cmpl %a2@(996),%d0
    bnew sdb_fail
    tstl %a2@(1000)
    beqw sdb_ok
    moveal %a3@(44),%a0
    cmpal %a2@(1004),%a0
    bnew sdb_fail
    movel %a3@(56),%d2
    cmpil #5,%d2
    bhiw sdb_fail
    movel %a0,%sp@-
    moveal %a0@,%a1
    moveal %a1@(40),%a1
    jsr %a1@
    addql #4,%sp
    tstl %d0
    beqw sdb_fail
    muluw #4385,%d2
    addl %d2,%d0
    cmpl %a2@(1000),%d0
    beqw sdb_ok
    braw sdb_fail

    .section .text.sg_dyn_restore,"ax"
sg_dyn_restore:
    lea.l %sp@(-8),%sp
    movem.l %a2-%a3,%sp@
    moveal sg_obj,%a2
    moveal %a2@(1000),%a1
    tstl %a1
    beqw sdr_out
    lea.l %a2@(1008),%a0
    jsr sg_dyn_copy
    moveal %a2@(1004),%a0
    moveal %a0@,%a1
    clrl %sp@-
    movel %a0,%sp@-
    moveal %a1@(16),%a1
    jsr %a1@                  | modification globale du pool, observer OS
    addql #8,%sp
sdr_out:
    movem.l %sp@,%a2-%a3
    addql #8,%sp
    rts
sg_dyn_copy:
    movel #4384,%d0
sdc_loop:
    moveb %a0@+,%d1
    moveb %d1,%a1@+
    subql #1,%d0
    bplw sdc_loop
    rts

    .section .text.sg_dyn_step,"ax"
sg_dyn_step:
    moveb %a4@(0,%d2:l),%d0
    cmpib #255,%d0
    beqw sds_done
    lea.l %sp@(-20),%sp
    movem.l %d2-%d3/%d7/%a2-%a3,%sp@
    movel sg_config+24,%d7
    tstl sg_options
    beqw sds_decay
    jsr sg_random
    .ifdef SG_ADVANCED
    lea.l sg_advanced,%a0
    jsr sg_random_range
    .else
    divuw #127,%d0
    swap %d0
    andil #65535,%d0
    addql #1,%d0
    .endif
    movel %d0,%sp@-
    movel %d2,%sp@-
    movel %a3,%sp@-
    jsr 0x400166c2            | velocity : octet par pas et notification OS
    lea.l %sp@(12),%sp
sds_decay:
    tstl sg_options+4
    beqw sds_pan
    moveq #18,%d3            | slot Amp Decay, commun à toutes les machines
    jsr sg_dyn_lock
sds_pan:
    tstl sg_options+8
    beqw sds_out
    moveq #22,%d3            | slot Pan, centre = 64
    jsr sg_dyn_lock
sds_out:
    movel %d7,sg_config+24
    movem.l %sp@,%d2-%d3/%d7/%a2-%a3
    lea.l %sp@(20),%sp
sds_done:
    rts
sg_dyn_lock:
    jsr sg_random
    .ifdef SG_ADVANCED
    lea.l sg_advanced+8,%a0
    cmpil #18,%d3
    beqs sds_range
    addql #8,%a0
sds_range:
    jsr sg_random_range
    .else
    andil #127,%d0
    .endif
    lsll #8,%d0
    movel %d0,%sp@-
    movel %d3,%sp@-
    movel %d2,%sp@-
    movel %a3,%sp@-
    jsr 0x4001646a            | vrai setter p-lock : valeur, compte et indicateur
    lea.l %sp@(16),%sp
    rts
    .endif
