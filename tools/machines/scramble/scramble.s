| SCRAMBLE indépendant : pas de page, pas de snapshot, quatre contrôles machine.
| Paramètres OS via Project::setParameter, jamais le setter groupé du prototype.
    .section .data.sc_state,"aw"
    .globl sc_taken,sc_event,sc_time,sc_seed,sc_result
sc_taken: .long 0
sc_event: .long 0
sc_time: .long 0
sc_seed: .long 0x6d2b79f5
sc_result: .long 0
    .section .text.sc_key,"ax"
    .globl sc_key
sc_key:
    moveal %sp@(4),%a0
    movel %a0@(12),%d0
    cmpil #2,%d0
    bnew sc_pass
    movel %a0@(16),%d1
    btst #0,%d1
    beqw sc_release
    tstl sc_taken
    beqw sc_fresh
    cmpal sc_event,%a0
    bnew sc_fresh
    movel %a0@(8),%d0
    cmpl sc_time,%d0
    beqw sc_eat
sc_fresh:
    tstl TG_set_held
    beqw sc_pass
    andil #10,%d1
    bnew sc_pass
    tstl TG_mm_obj
    bnew sc_pass
    tstl TG_rtg_on
    bnew sc_pass
    tstl TG_sle_on
    bnew sc_pass
    moveq #0,%d0
    movew %sr,%d0
    andil #0x700,%d0
    bnew sc_pass
    movel %a0,sc_event
    movel %a0@(8),%d0
    movel %d0,sc_time
    moveq #1,%d0
    movel %d0,sc_taken
    movel %d0,TG_mod_used
    movel %a0,%sp@-
    .ifdef SC_STEPS
    jsr sc_steps_toggle
    tstl %d0
    bnes sc_skip_run
    .endif
    jsr sc_run
    .ifdef SC_STEPS
sc_skip_run:
    .endif
    moveal %sp@+,%a0
    braw sc_eat
sc_release:
    tstl sc_taken
    beqw sc_pass
    clrl sc_taken
    movel %a0,sc_event
    movel %a0@(8),%d0
    movel %d0,sc_time
    braw sc_eat
sc_pass:
    jmp SC_NEXT
sc_eat:
    movel %a0@(16),%d1
    oril #8,%d1
    movel %d1,%a0@(16)
    moveq #0,%d0
    rts

    .section .text.sc_run,"ax"
    .globl sc_run
sc_run:
    lea.l %sp@(-88),%sp
    movem.l %d2-%d7/%a2-%a5,%sp@
    clrl sc_result
    jsr 0x400cf866
    tstl %d0
    beqw sc_out
    moveal %d0,%a2
    pea %a2@(48)
    jsr 0x40012412
    addql #4,%sp
    cmpil #5,%d0
    bhiw sc_out
    movel %d0,%d5
    muluw #68,%d0
    lea.l %a2@(212),%a0
    addal %d0,%a0
    movel %a0,%sp@-
    moveal %a0@,%a1
    movel %a1,%d0
    beqw sc_no_get
    moveal %a1@(40),%a1
    movel %a1,%d0
    beqw sc_no_get
    jsr %a1@
    addql #4,%sp
    tstl %d0
    beqw sc_out
    moveal %d0,%a3
    moveq #0,%d6
    moveb %a3@(38),%d6
    cmpil #6,%d6
    beqw sc_out               | Sampler : sample/modes ne sont pas des contrôles synthèse.
    moveq #0,%d2
    lea.l %sp@(40),%a4        | quatre paires {descripteur, valeur}.
    jmp sc_prepare
sc_no_get:
    addql #4,%sp
    braw sc_out
    .section .text.sc_prepare,"ax"
sc_prepare:
    movel %d2,%d3
    addil #11,%d3
    movel %d6,%sp@-
    movel %d3,%sp@-
    jsr 0x4005a692
    addql #8,%sp
    tstl %d0
    beqw sc_out
    movel %d0,%a4@
    movel %d0,%sp@-
    lea.l %sp@(76),%a0        | résultat caché à sp d'entrée de run +72.
    jsr 0x4005a65a
    addql #4,%sp
    movel %sp@(72),%d3
    movel %sp@(76),%d4
    tstl %d3
    bmiw sc_out
    cmpil #32512,%d4
    bgtw sc_out
    cmpl %d3,%d4
    bltw sc_out
    addil #255,%d3
    lsrl #8,%d3
    lsrl #8,%d4
    subl %d3,%d4
    addql #1,%d4
    jsr sc_random
    andil #65535,%d0
    divuw %d4,%d0
    swap %d0
    andil #65535,%d0
    addl %d3,%d0
    movel %d0,%a4@(4)
    movel %a4@,%sp@-
    jsr 0x4005a7f8            | descripteur -> CC, valeur MIDI entière.
    addql #4,%sp
    tstl %d0
    bmiw sc_out
    cmpil #127,%d0
    bhiw sc_out
    movel %d0,%d3
    movel %d3,%sp@-
    movel %d6,%sp@-
    movel %d5,%sp@-
    jsr 0x4005a8ce            | vérifier le mapping inverse avant toute écriture.
    lea.l %sp@(12),%sp
    cmpl %a4@,%d0
    bnew sc_out
    movel %d3,%a4@
    addql #8,%a4
    addql #1,%d2
    cmpil #4,%d2
    bltw sc_prepare
    moveq #0,%d2
    lea.l %sp@(40),%a4
    jmp sc_apply
    .section .text.sc_apply,"ax"
sc_apply:
    clrl %sp@-               | pas de renvoi MIDI demandé.
    movel %d5,%sp@-
    movel %a4@(4),%sp@-
    movel %a4@,%sp@-
    movel %a2,%sp@-
    jsr 0x4000f2a2
    lea.l %sp@(20),%sp
    addql #8,%a4
    addql #1,%d2
    cmpil #4,%d2
    bltw sc_apply
    moveq #1,%d0
    movel %d0,sc_result
    pea sc_text
    jsr TG_show_popup
    addql #4,%sp
sc_out:
    movem.l %sp@,%d2-%d7/%a2-%a5
    lea.l %sp@(88),%sp
    rts
    .section .text.sc_random,"ax"
sc_random:
    movel sc_seed,%d0
    movel TG_blk_clk,%d1
    eorl %d1,%d0
    bnes sc_rng_seed
    movel #0x6d2b79f5,%d0
sc_rng_seed:
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
    movel %d0,sc_seed
    movel %d0,%d1
    rts
    .section .rodata.sc_text,"a"
    .ifdef SC_STEPS
sc_text: .asciz " SCRAMBLE "
    .else
sc_text: .asciz "SCRAMBLE"
    .endif
