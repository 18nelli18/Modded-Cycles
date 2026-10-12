| Arp B privé, dérivé de tools/machines/arp/arp.c (projet MIT).
| État32 : count/last/pos/dir/seed (longs), puis 12 notes dans l'ordre de jeu.
| init(state), held(state,note,down), next(state,mode,octaves) -> note ou -1.
| Le propriétaire sérialise sous IPL7. next travaille sur une candidature :
| publier son état seulement si le Note On et sa réserve Off sont acceptés.
| Aucun appel natif/audio/MIDI, aucune allocation, boucles bornées à 48 notes.
    .text
    .globl ml_arp_init,ml_arp_held,ml_arp_next,ml_arp_bank_init,ml_arp_bank_reset
| Initialiser la banque UI avant publication au service ; aucun pointeur global.
ml_arp_bank_init:
    lea.l %sp@(-8),%sp
    movem.l %d2/%a2,%sp@
    moveal %sp@(12),%a2
    moveq #5,%d2
.Larp_bank_lane:
    moveq #5,%d0
    movel %d0,%a2@
    moveq #1,%d0
    movel %d0,%a2@(4)
    pea %a2@(8)
    jsr ml_arp_init
    addql #4,%sp
    lea.l %a2@(40),%a2
    subql #1,%d2
    bpl .Larp_bank_lane
    moveq #1,%d0
    movem.l %sp@,%d2/%a2
    addql #8,%sp
    rts
| Effacer les notes/progression au changement de pattern sans changer mode/Oct.
ml_arp_bank_reset:
    lea.l %sp@(-8),%sp
    movem.l %d2/%a2,%sp@
    moveal %sp@(12),%a2
    moveq #5,%d2
.Larp_bank_reset_lane:
    pea %a2@(8)
    jsr ml_arp_init
    addql #4,%sp
    lea.l %a2@(40),%a2
    subql #1,%d2
    bpl .Larp_bank_reset_lane
    moveq #1,%d0
    movem.l %sp@,%d2/%a2
    addql #8,%sp
    rts
ml_arp_init:
    moveal %sp@(4),%a0
    clrl %a0@
    clrl %a0@(4)
    clrl %a0@(8)
    moveq #1,%d0
    movel %d0,%a0@(12)
    movel #0x2545f491,%d1
    movel %d1,%a0@(16)
    clrl %a0@(20)
    clrl %a0@(24)
    clrl %a0@(28)
    rts
ml_arp_held:
    moveal %sp@(4),%a0
    movel %sp@(8),%d0
    cmpil #127,%d0
    bhi .Lheld_bad
    movel %a0@,%d1
    cmpil #12,%d1
    bhi .Lheld_bad
    movel %d2,%sp@-
    moveq #0,%d2
.Lheld_find:
    cmpl %d1,%d2
    beq .Lheld_absent
    cmpb %a0@(20,%d2:l),%d0
    beq .Lheld_found
    addql #1,%d2
    bra .Lheld_find
.Lheld_absent:
    tstl %sp@(16)
    beq .Lheld_ok
    cmpil #12,%d1
    beq .Lheld_full
    moveb %d0,%a0@(20,%d1:l)
    tstl %d1
    bne .Lheld_append
    movel %d0,%a0@(4)
    clrl %a0@(8)
    moveq #1,%d0
    movel %d0,%a0@(12)
.Lheld_append:
    addql #1,%d1
    movel %d1,%a0@
    bra .Lheld_ok
.Lheld_found:
    tstl %sp@(16)
    bne .Lheld_ok
    subql #1,%d1
    movel %d1,%a0@
.Lheld_shift:
    cmpl %d1,%d2
    beq .Lheld_clear
    moveb %a0@(21,%d2:l),%d0
    moveb %d0,%a0@(20,%d2:l)
    addql #1,%d2
    bra .Lheld_shift
.Lheld_clear:
    clrb %a0@(20,%d1:l)
.Lheld_ok:
    moveq #1,%d0
    movel %sp@+,%d2
    rts
.Lheld_full:
    movel %sp@+,%d2
.Lheld_bad:
    moveq #0,%d0
    rts

ml_arp_next:
    lea.l %sp@(-32),%sp
    movem.l %d2-%d7/%a2,%sp@
    moveal %sp@(36),%a2
    movel %sp@(40),%d6
    cmpil #5,%d6
    bhi .Larp_bad
    movel %sp@(44),%d7
    subql #1,%d7
    cmpil #3,%d7
    bhi .Larp_bad
    addql #1,%d7
    movel %a2@,%d2
    subql #1,%d2
    cmpil #11,%d2
    bhi .Larp_bad
    addql #1,%d2
    moveq #0,%d0
.Larp_validate:
    tstb %a2@(20,%d0:l)
    bmi .Larp_bad
    addql #1,%d0
    cmpl %d2,%d0
    bne .Larp_validate
    movel %a2@(4),%d0
    cmpil #127,%d0
    bhi .Larp_bad
    cmpil #5,%d6
    beq .Larp_done
    cmpil #3,%d6
    bcc .Larp_position
    moveq #1,%d3
    tstl %d6
    beq .Larp_direction
    moveq #-1,%d3
    cmpil #2,%d6
    bne .Larp_direction
    movel %a2@(12),%d3
    cmpil #1,%d3
    beq .Larp_direction
    cmpil #-1,%d3
    bne .Larp_bad
.Larp_direction:
    movel %a2@(4),%d4
    bsr .Larp_beyond
    tstl %d0
    bpl .Larp_store
    cmpil #2,%d6
    bne .Larp_wrap
    negl %d3
    movel %d3,%a2@(12)
    bsr .Larp_beyond
    tstl %d0
    bpl .Larp_store
    movel %a2@(4),%d0
    bra .Larp_store
.Larp_wrap:
    moveq #-1,%d4
    tstl %d3
    bpl .Larp_wrap_find
    movel #128,%d4
.Larp_wrap_find:
    bsr .Larp_beyond
    bra .Larp_store
.Larp_position:
    movel %d2,%d5
    muluw %d7,%d5
    cmpil #3,%d6
    bne .Larp_play
    movel %a2@(16),%d0
    movel #1103515245,%d1
    mulul %d1,%d0
    addil #12345,%d0
    movel %d0,%a2@(16)
    swap %d0
    andil #65535,%d0
    divuw %d5,%d0
    swap %d0
    andil #65535,%d0
    cmpil #1,%d5
    beq .Larp_pick
    cmpl %a2@(8),%d0
    bne .Larp_pick
    bra .Larp_increment
.Larp_play:
    movel %a2@(8),%d0
    | Pos peut devenir périmée après relâchement : modulo borné 0..47.
    cmpil #47,%d0
    bhi .Larp_bad
.Larp_increment:
    addql #1,%d0
.Larp_mod:
    cmpl %d5,%d0
    bcs .Larp_pick
    subl %d5,%d0
    bra .Larp_mod
.Larp_pick:
    movel %d0,%a2@(8)
    divuw %d2,%d0
    moveq #0,%d1
    movew %d0,%d1
    muluw #12,%d1
    swap %d0
    andil #65535,%d0
    moveq #0,%d4
    moveb %a2@(20,%d0:l),%d4
    addl %d4,%d1
    cmpil #127,%d1
    bls .Larp_pick_valid
    movel %d4,%d1
.Larp_pick_valid:
    movel %d1,%d0
.Larp_store:
    movel %d0,%a2@(4)
    bra .Larp_done
.Larp_bad:
    moveq #-1,%d0
.Larp_done:
    movem.l %sp@,%d2-%d7/%a2
    lea.l %sp@(32),%sp
    rts

| Recherche stricte au-delà de d4 dans le sens d3 ; garde d2/d3/d4/d6/d7.
.Larp_beyond:
    moveq #-1,%d0
    moveq #0,%d5
.Lbeyond_oct:
    moveq #0,%d1
.Lbeyond_note:
    movel %d5,%sp@(32)
    moveb %a2@(20,%d1:l),%d5
    | L'octave est recalculée sans altérer le compteur sauvegardé.
    andil #255,%d5
    movel %d1,%sp@-
    movel %sp@(36),%d1
    muluw #12,%d1
    addl %d1,%d5
    movel %sp@+,%d1
    cmpil #127,%d5
    bhi .Lbeyond_next
    tstl %d3
    bmi .Lbeyond_down
    cmpl %d4,%d5
    ble .Lbeyond_next
    tstl %d0
    bmi .Lbeyond_best
    cmpl %d0,%d5
    bge .Lbeyond_next
    bra .Lbeyond_best
.Lbeyond_down:
    cmpl %d4,%d5
    bge .Lbeyond_next
    cmpl %d0,%d5
    ble .Lbeyond_next
.Lbeyond_best:
    movel %d5,%d0
.Lbeyond_next:
    movel %sp@(32),%d5
    addql #1,%d1
    cmpl %d2,%d1
    bne .Lbeyond_note
    addql #1,%d5
    cmpl %d7,%d5
    bne .Lbeyond_oct
    rts
