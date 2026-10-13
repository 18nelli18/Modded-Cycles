| SCRAMBLE B : seulement les CC assignés de la voie MIDI sélectionnée.
| Aucun appel sc_run, aucune écriture piste audio ni changement de destination.
    .text
    .globl mlkc_scramble
mlkc_scramble:
    lea %sp@(-24),%sp
    moveml %d2-%d4/%a2-%a3,%sp@
    movew %sr,%d0
    andil #0x700,%d0
    bne .Lscr_done
    movel mlp_track,%d2
    cmpil #5,%d2
    bhi .Lscr_done
    moveal ml_pattern,%a2
    tstl %a2
    beq .Lscr_done
    tstl 0x40fe4228
    beq .Lscr_done
    movel %d2,%d0
    muluw #264,%d0
    addal %d0,%a2
    tstb %a2@
    beq .Lscr_done
    tstb %a2@(1)
    bne .Lscr_done
    moveq #0,%d0
    moveb %a2@(2),%d0
    cmpil #15,%d0
    bhi .Lscr_done
    moveq #0,%d0
    moveb %a2@(3),%d0
    subql #2,%d0
    cmpil #2,%d0
    bhi .Lscr_done
    movel %d2,%d0
    muluw #24,%d0
    lea mlkc_state,%a3
    addal %d0,%a3
    moveq #11,%d3
.Lscr_loop:
    moveq #0,%d4
    moveb %a3@,%d4
    cmpil #127,%d4
    bhi .Lscr_next
    jsr SG_random
    andil #127,%d0
    moveb %d0,%a3@(1)
    lsll #8,%d0
    swap %d4
    orl %d4,%d0
    moveq #0,%d4
    moveb %a2@(2),%d4
    oril #0xb0,%d4
    lsll #8,%d4
    swap %d4
    orl %d4,%d0
    moveq #0,%d4
    moveb %a2@(3),%d4
    orl %d4,%d0
    movel %d0,%sp@(20)
    lea %sp@(20),%a0
    movel %d4,%sp@-
    movel %a0,%sp@-
    pea 3
    jsr 0x400826b0
    lea %sp@(12),%sp
.Lscr_next:
    addql #2,%a3
    subql #1,%d3
    bpl .Lscr_loop
    pea .Lscr_text
    jsr TG_show_popup
    addql #4,%sp
.Lscr_done:
    moveml %sp@,%d2-%d4/%a2-%a3
    lea %sp@(24),%sp
    rts
.Lscr_text: .asciz "SCRAMBLE"
    .balign 4
