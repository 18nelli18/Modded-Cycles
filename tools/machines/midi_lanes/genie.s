| Adaptateur de données Sequence Genie vers une voie B privée.
| ml_genie_notes(source,notes,longueur,candidat) -> 1/0.
| Aucun objet piste audio, p-lock natif, file MIDI ou appel OS.
| Préparer hors IRQ ; publier/undo/queue seront raccordés séparément.
    .text
    .globl ml_genie_notes
ml_genie_notes:
    lea.l %sp@(-20),%sp
    movem.l %d2-%d4/%a2-%a3,%sp@
    moveq #0,%d0
    movew %sr,%d1
    andil #0x0700,%d1
    bne .Lg_done
    moveal %sp@(24),%a2
    tstl %a2
    beq .Lg_done
    moveal %sp@(28),%a3
    tstl %a3
    beq .Lg_done
    movel %sp@(32),%d2
    subql #1,%d2
    cmpil #63,%d2
    bhi .Lg_done
    addql #1,%d2
    moveal %sp@(36),%a1
    tstl %a1
    beq .Lg_done
    cmpal %a2,%a1
    beq .Lg_done
    | Tampons distincts : aucun chevauchement avec la voie ni les notes.
    movel %a1,%d1
    subl %a2,%d1
    cmpil #264,%d1
    bcs .Lg_done
    movel %a2,%d1
    subl %a1,%d1
    cmpil #264,%d1
    bcs .Lg_done
    movel %a3,%d1
    subl %a1,%d1
    cmpil #264,%d1
    bcs .Lg_done
    movel %a1,%d1
    subl %a3,%d1
    cmpl %d2,%d1
    bcs .Lg_done
    moveq #0,%d1
    moveb %a2@(4),%d1
    cmpl %d2,%d1
    bne .Lg_done
    moveq #0,%d3
.Lg_validate:
    moveq #0,%d1
    moveb %a3@(0,%d3:l),%d1
    cmpil #254,%d1
    bcc .Lg_valid
    cmpil #36,%d1
    bcs .Lg_done
    cmpil #96,%d1
    bhi .Lg_done
.Lg_valid:
    addql #1,%d3
    cmpl %d2,%d3
    bcs .Lg_validate
    moveal %a2,%a0
    moveal %a1,%a2
    moveq #65,%d3
.Lg_copy:
    movel %a0@+,%a1@+
    subql #1,%d3
    bpl .Lg_copy
    lea.l %a2@(8),%a0
    moveq #0,%d3
.Lg_step:
    moveq #0,%d1
    moveb %a3@(0,%d3:l),%d1
    cmpil #254,%d1
    beq .Lg_next
    cmpil #255,%d1
    beq .Lg_rest
    moveb %d1,%a0@
    moveb %a0@(3),%d1
    andil #2,%d1
    oril #1,%d1
    moveb %d1,%a0@(3)
    moveq #0,%d1
    moveb %a0@(1),%d1
    subql #1,%d1
    cmpil #126,%d1
    bls .Lg_gate
    moveb #100,%a0@(1)
.Lg_gate:
    moveq #0,%d1
    moveb %a0@(2),%d1
    subql #1,%d1
    cmpil #63,%d1
    bls .Lg_next
    moveb #1,%a0@(2)
    bra .Lg_next
.Lg_rest:
    clrb %a0@(3)
.Lg_next:
    addql #4,%a0
    addql #1,%d3
    cmpl %d2,%d3
    bcs .Lg_step
    moveq #1,%d0
.Lg_done:
    movem.l %sp@,%d2-%d4/%a2-%a3
    lea.l %sp@(20),%sp
    rts
