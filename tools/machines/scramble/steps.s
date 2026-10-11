| Marque par pas : bit 6 réservé ; valeurs nouvelles dans l'événement seulement.
| UI : trig tenu puis SETTINGS + TRACK ; même geste retire la marque.
    .ifdef SC_STEPS
    .section .text.sc_steps_toggle,"ax"
    .globl sc_steps_toggle
sc_steps_toggle:
    lea.l %sp@(-32),%sp
    movem.l %d2-%d5/%a2-%a5,%sp@
    jsr 0x400cf9a8
    tstl %d0
    beqw scst_none
    moveal %d0,%a3
    movel %a3@(352),%d4
    movel %a3@(348),%d5
    movel %d4,%d0
    orl %d5,%d0
    beqw scst_none
    jsr 0x400cf866
    movel %d0,%sp@-
    jsr 0x4000f23e
    addql #4,%sp
    tstl %d0
    beqw scst_done
    moveal %d0,%a2
    moveq #0,%d2
    jmp scst_loop
scst_none:
    moveq #0,%d0
    bras scst_out
scst_done:
    pea sc_text
    jsr TG_show_popup
    addql #4,%sp
    moveq #1,%d0
scst_out:
    movem.l %sp@,%d2-%d5/%a2-%a5
    lea.l %sp@(32),%sp
    rts
    .section .text.sc_steps_loop,"ax"
scst_loop:
    cmpil #32,%d2
    bnew scst_bit
    movel %d5,%d4
scst_bit:
    btst #0,%d4
    beqw scst_next
    | Neutraliser l'action de relâchement du trig déjà tenu.
    clrl %sp@-
    movel %d2,%sp@-
    movel %a3,%sp@-
    jsr 0x4006b91a
    lea.l %sp@(12),%sp
    pea 64
    movel %d2,%sp@-
    movel %a2,%sp@-
    jsr 0x400157d6
    lea.l %sp@(12),%sp
    moveq #1,%d3
    tstb %d0
    beqw scst_set
    moveq #0,%d3
scst_set:
    movel %d3,%sp@-
    pea 64
    movel %d2,%sp@-
    movel %a2,%sp@-
    jsr 0x400179ce
    lea.l %sp@(16),%sp
scst_next:
    lsrl #1,%d4
    addql #1,%d2
    cmpil #64,%d2
    bltw scst_loop
    jmp scst_done

    .section .text.sc_steps_event,"ax"
    .globl sc_steps_event
| Hook 40054c0e : rejouer locks->event+72 et event->d0 avant épilogue OS.
| Tous registres/SR conservés ; aucune notification, allocation ou API UI.
sc_steps_event:
    movel %fp,%a2@(72)
    movel %a2,%d0
    lea.l %sp@(-96),%sp
    movem.l %d0-%d7/%a0-%a5,%sp@
    movew %sr,%d0
    movel %d0,%sp@(56)
    movel %a2@(40),%d0
    btst #6,%d0
    beqw scse_out
    andil #0xffffffbf,%d0
    movel %d0,%a2@(40)          | marque retirée avant le moteur natif.
    moveal %a2@(44),%a3
    moveal %a2@(72),%a4
    tstl %a3
    beqw scse_out
    tstl %a4
    beqw scse_out
    movel %a4@(8),%d0
    cmpil #33,%d0
    bhiw scse_out
    moveq #0,%d6
    moveb %a3@(38),%d6
    cmpil #6,%d6
    beqw scse_out
    moveq #11,%d2
    lea.l %sp@(64),%a5
    jmp scse_prepare
scse_out:
    movel %sp@(56),%d0
    movew %d0,%sr
    movem.l %sp@,%d0-%d7/%a0-%a5
    lea.l %sp@(96),%sp
    jmp 0x40054c14
    .section .text.sc_steps_prepare,"ax"
scse_prepare:
    movel %d6,%sp@-
    movel %d2,%sp@-
    jsr 0x4005a692
    addql #8,%sp
    tstl %d0
    beqw scse_out
    movel %d0,%sp@-
    lea.l %sp@(84),%a0          | bornes à sp fixe +80/+84.
    jsr 0x4005a65a
    addql #4,%sp
    movel %sp@(80),%d3
    movel %sp@(84),%d4
    tstl %d3
    bmiw scse_out
    cmpil #32512,%d4
    bgtw scse_out
    cmpl %d3,%d4
    bltw scse_out
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
    lsll #8,%d0
    movel %d0,%a5@+
    addql #1,%d2
    cmpil #15,%d2
    bltw scse_prepare
    moveq #11,%d2
    lea.l %sp@(64),%a5
    jmp scse_apply
    .section .text.sc_steps_apply,"ax"
scse_apply:
    movel %a4@(8),%d3
    moveq #0,%d4
    lea.l %a4@(20),%a0
scse_find:
    cmpl %d3,%d4
    beqw scse_append
    moveq #0,%d0
    movew %a0@,%d0
    cmpl %d2,%d0
    beqw scse_write
    addql #8,%a0
    addql #1,%d4
    braw scse_find
scse_append:
    cmpil #33,%d3
    bccw scse_out
    movew %d2,%a0@
    clrl %a0@(4)
    addql #1,%d3
    movel %d3,%a4@(8)
scse_write:
    movel %a5@+,%d0
    movew %d0,%a0@(2)
    addql #1,%d2
    cmpil #15,%d2
    bltw scse_apply
    jmp scse_out
    .endif
