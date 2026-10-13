| Slides CC B, comportement cible de Model-TG (TinyGregAudio, MIT).
| État privé par voie64o : propriétaire,horloge,durée,masque,12x{CC,from,to,last}.
| arm(pattern,voie,pas) n'alloue pas et n'appelle aucune sortie MIDI.
| Les réglages sont figés à l'armement, sans retenir un pointeur de locks.
    .data
    .balign 4
    .globl mlkc_slide_states
mlkc_slide_states: .space 384
    .text
    .globl mlkc_slide_arm,mlkc_slide_cancel
mlkc_slide_cancel:
    movew %sr,%d0
    movel %d0,%sp@-
    movew #0x2700,%sr
    lea mlkc_slide_states,%a0
    moveq #5,%d1
.Lcancel_slide:
    clrl %a0@(12)
    clrl %a0@
    lea %a0@(64),%a0
    subql #1,%d1
    bpl .Lcancel_slide
    movel %sp@+,%d0
    movew %d0,%sr
    rts
mlkc_slide_arm:
    lea %sp@(-48),%sp
    moveml %d2-%d7/%a2-%a6,%sp@
    moveal %sp@(52),%a2
    movel %sp@(56),%d2
    cmpil #5,%d2
    bhi .Larm_done
    movel %d2,%d0
    lsll #6,%d0
    lea mlkc_slide_states,%a4
    addal %d0,%a4
    clrl %a4@(12)
    clrl %a4@
    movel %sp@(60),%d3
    movel %d3,%sp@-
    movel %d2,%sp@-
    movel %a2,%sp@-
    jsr mlkc_slide_find
    lea %sp@(12),%sp
    tstl %d0
    bmi .Larm_done
    movel %d0,%d4
    movel %d2,%d1
    muluw #264,%d1
    lea %a2@(0,%d1:l),%a3
    moveq #0,%d1
    moveb %a3@(5),%d1
    cmpil #6,%d1
    bhi .Larm_done
    lea .Lslide_ticks,%a0
    movel %a0@(0,%d1:l:4),%d5
    lsrl #8,%d0
    muluw %d0,%d5
    movel #450000,%d0
    mulsl %d0,%d5
    movel 0x40149310,%d0
    beq .Larm_done
    divul %d0,%d5
    tstl %d5
    beq .Larm_done
    cmpil #200000,%d5
    bls .Larm_duration
    movel #200000,%d5
.Larm_duration:
    clrl %sp@-
    movel %a2,%sp@-
    jsr mlkc_locks_for
    addql #8,%sp
    moveal %d0,%a5
    moveal %d0,%a6
    tstl %a5
    beq .Larm_no_locks
    movel %d2,%d0
    muluw #1536,%d0
    addal %d0,%a5
    addal %d0,%a6
    movel %d3,%d0
    muluw #24,%d0
    addal %d0,%a5
    movel %d4,%d0
    andil #255,%d0
    muluw #24,%d0
    addal %d0,%a6
.Larm_no_locks:
    movel %d2,%d0
    muluw #24,%d0
    lea mlkc_state,%a0
    addal %d0,%a0
    movel %a0,%sp@(44)
    moveq #0,%d6
    moveq #0,%d7
.Larm_knob:
    moveal %sp@(44),%a0
    moveq #0,%d0
    movew %a0@,%d0
    moveq #0,%d1
    movew %a0@,%d1
    tstl %a5
    beq .Larm_values
    movew %a5@+,%d3
    cmpiw #-1,%d3
    beq .Larm_target
    movew %d3,%d0
.Larm_target:
    movew %a6@+,%d3
    cmpiw #-1,%d3
    beq .Larm_values
    movew %d3,%d1
.Larm_values:
    | Numéro identique valide : les destinations différentes sautent.
    cmpil #0x7f7f,%d0
    bhi .Larm_next
    cmpil #0x7f7f,%d1
    bhi .Larm_next
    btst #7,%d0
    bne .Larm_next
    btst #7,%d1
    bne .Larm_next
    movel %d0,%d3
    lsrl #8,%d3
    movel %d1,%d4
    lsrl #8,%d4
    cmpl %d3,%d4
    bne .Larm_next
    cmpb %d0,%d1
    beq .Larm_next
    lea %a4@(16,%d6:l:4),%a0
    moveb %d3,%a0@
    moveb %d0,%a0@(1)
    moveb %d1,%a0@(2)
    moveb %d0,%a0@(3)
    bset %d6,%d7
.Larm_next:
    addql #2,%sp@(44)
    addql #1,%d6
    cmpil #12,%d6
    bcs .Larm_knob
    movel %a2,%a4@
    movel TG_blk_clk,%d0
    movel %d0,%a4@(4)
    movel %d5,%a4@(8)
    moveq #0,%d0
    moveb %a3@(2),%d0
    lsll #8,%d0
    moveb %a3@(3),%d0
    swap %d0
    orl %d0,%d7
    movel %d7,%a4@(12)          | canal/port figés +12bits actifs, publiés en dernier
.Larm_done:
    moveml %sp@,%d2-%d7/%a2-%a6
    lea %sp@(48),%sp
    rts
.Lslide_ticks: .long 24,12,6,4,3,2,1
