| Noyau interpolation CC, non raccordé au firmware : aucune émission MIDI.
| value(départ,cible,écoulé,durée) ->0..127 ou-1 si domaine invalide.
| Durée1..200000, écoulé non signé32bits ; quotient borné127, aucune division à zéro.
    .text
    .globl mlkc_slide_value
mlkc_slide_value:
    lea %sp@(-12),%sp
    moveml %d2-%d4,%sp@
    moveq #-1,%d0
    movel %sp@(16),%d2
    cmpil #127,%d2
    bhi .Lsv_done
    movel %sp@(20),%d3
    cmpil #127,%d3
    bhi .Lsv_done
    movel %sp@(24),%d4
    movel %sp@(28),%d1
    beq .Lsv_done
    cmpil #200000,%d1
    bhi .Lsv_done
    cmpl %d1,%d4
    bcc .Lsv_target
    movel %d3,%d0
    subl %d2,%d0
    bpl .Lsv_up
    negl %d0
    mulsl %d4,%d0
    divul %d1,%d0
    subl %d0,%d2
    movel %d2,%d0
    bra .Lsv_done
.Lsv_up:
    mulsl %d4,%d0
    divul %d1,%d0
    addl %d2,%d0
    bra .Lsv_done
.Lsv_target:
    movel %d3,%d0
.Lsv_done:
    moveml %sp@,%d2-%d4
    lea %sp@(12),%sp
    rts
