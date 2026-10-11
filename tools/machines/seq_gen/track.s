| Prototype d'édition réversible : le stockage des p-locks n'est jamais effacé.
| sg_track_write(a0=objet piste,a1=notes,d0=longueur,a2=sauvegarde 722 o)
| -> d0=1 si réussi, 0 sinon. Appelé SEULEMENT séquenceur arrêté.
| sg_track_restore(a0=objet piste,a2=sauvegarde) -> d0=1/0.
| Les deux gardent d2-d7/a2-a6 ; aucun état global.
| Les notifications passent par le vrai setter de note 0x40016642, qui
| utilise la même classe d'événement 0x400ff59c que le setter de drapeaux.
    .section .text.sg_track_write,"ax"
    .globl sg_track_write,sg_track_restore
sg_track_write:
    lea.l %sp@(-28),%sp
    movem.l %d2-%d5/%a2-%a4,%sp@
    moveal %a0,%a3
    moveal %a1,%a4
    movel %d0,%d4
    moveq #0,%d0
    tstl 0x40a78874
    bnew stw_out
    tstl 0x40a7883c
    bnew stw_out
    cmpil #1,%d4
    bltw stw_out
    cmpil #64,%d4
    bgtw stw_out
    | Valider toutes les notes AVANT de modifier quoi que ce soit.
    .ifdef SG_ADVANCED
    movel %a3,%sp@-
    moveal %a3@,%a0
    moveal %a0@(40),%a0
    jsr %a0@
    addql #4,%sp
    tstl %d0
    beqw stw_fail
    moveal %d0,%a0
    moveal %a4,%a1
    movel %d4,%d0
    jsr sg_advanced_steps
    .endif
    moveq #0,%d2
stw_check:
    moveq #0,%d1
    moveb %a4@(0,%d2:l),%d1
    .ifdef SG_ADVANCED
    cmpil #254,%d1
    beqs stw_valid
    .endif
    cmpil #255,%d1
    beqs stw_valid
    cmpil #127,%d1
    bhiw stw_out
stw_valid:
    addql #1,%d2
    cmpl %d4,%d2
    blts stw_check
    movel %a3,%sp@-
    jsr 0x40016402
    addql #4,%sp
    cmpl %d4,%d0
    bnew stw_fail
    movel %a3,%sp@-
    moveal %a3@,%a0
    moveal %a0@(40),%a0
    jsr %a0@
    addql #4,%sp
    tstl %d0
    beqw stw_fail
    moveal %d0,%a0
    moveal %a2,%a1
    .ifdef SG_DYNAMICS
    lea.l %sp@(-8),%sp
    movem.l %a0-%a1,%sp@
    jsr sg_dyn_backup
    movem.l %sp@,%a0-%a1
    addql #8,%sp
    tstl %d0
    beqw stw_fail
    movel %a0,%a1@(788)       | identité des données de piste (+996 de la page)
    .endif
    moveq #0,%d2
    .ifdef SG_ADVANCED
    jmp stw_backup
    .section .text.sg_track_apply,"ax"
    .endif
stw_backup:
    moveb %a0@+,%d1
    moveb %d1,%a1@+
    addql #1,%d2
    cmpil #722,%d2
    blts stw_backup
    moveq #0,%d2
stw_step:
    .ifdef SG_ADVANCED
    moveb %a4@(0,%d2:l),%d0
    cmpib #254,%d0
    beqw stw_next
    .endif
    movel %a3,%sp@-
    moveal %a3@,%a0
    moveal %a0@(40),%a0
    jsr %a0@
    addql #4,%sp
    moveal %d0,%a0
    moveq #0,%d3
    moveb %a4@(0,%d2:l),%d3
    moveq #0,%d1
    movew %a0@(0,%d2:l:2),%d1
    .ifdef SG_ADVANCED
    movel sg_advanced+24,%d0
    cmpil #2,%d0
    beqw stw_flags
    .endif
    cmpil #255,%d3
    beqs stw_rest
    andil #65533,%d1           | pas de trigless en même temps qu'un trig note
    oril #513,%d1             | bit 0 note, bit 9 comme le setter stock
    bras stw_flags
stw_rest:
    andil #65534,%d1          | p-locks et trigless existants conservés
    lea.l %a0@(580),%a1
    moveb %a1@(0,%d2:l),%d3
stw_flags:
    movew %d1,%a0@(0,%d2:l:2)
    movel %d3,%sp@-
    movel %d2,%sp@-
    movel %a3,%sp@-
    jsr 0x40016642            | même événement de modification que les flags
    lea.l %sp@(12),%sp
    .ifdef SG_DYNAMICS
    jsr sg_dyn_step
    .endif
stw_next:
    addql #1,%d2
    cmpl %d4,%d2
    bltw stw_step
    moveq #1,%d0
    bras stw_out
stw_fail:
    moveq #0,%d0
stw_out:
    movem.l %sp@,%d2-%d5/%a2-%a4
    lea.l %sp@(28),%sp
    rts

    .section .text.sg_track_restore,"ax"
sg_track_restore:
    lea.l %sp@(-16),%sp
    movem.l %d2-%d3/%a2-%a3,%sp@
    moveal %a0,%a3
    moveq #0,%d0
    tstl 0x40a78874
    bnew str_out
    tstl 0x40a7883c
    bnew str_out
    movel %a3,%sp@-
    jsr 0x40016402
    addql #4,%sp
    movel %d0,%d3
    cmpil #1,%d3
    bltw str_fail
    cmpil #64,%d3
    bgtw str_fail
    .ifdef SG_DYNAMICS
    jsr sg_dyn_validate
    tstl %d0
    beqw str_fail
    .endif
    movel %a3,%sp@-
    moveal %a3@,%a0
    moveal %a0@(40),%a0
    jsr %a0@
    addql #4,%sp
    tstl %d0
    beqw str_fail
    moveal %d0,%a1
    moveal %a2,%a0
    moveq #0,%d2
str_copy:
    moveb %a0@+,%d0
    moveb %d0,%a1@+
    addql #1,%d2
    cmpil #722,%d2
    blts str_copy
    .ifdef SG_DYNAMICS
    jsr sg_dyn_restore
    .endif
    moveq #0,%d2
str_notify:
    moveq #0,%d0
    lea.l %a2@(580),%a1
    moveb %a1@(0,%d2:l),%d0
    movel %d0,%sp@-
    movel %d2,%sp@-
    movel %a3,%sp@-
    jsr 0x40016642
    lea.l %sp@(12),%sp
    addql #1,%d2
    cmpl %d3,%d2
    blts str_notify
    moveq #1,%d0
    bras str_out
str_fail:
    moveq #0,%d0
str_out:
    movem.l %sp@,%d2-%d3/%a2-%a3
    lea.l %sp@(16),%sp
    rts
