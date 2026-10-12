| Prototype UI B : lire les modes live-rec/quantification natifs, sans écriture.
| mode() -> 0 inactif/refus, 1 quantifié, 2 non quantifié. Aucun hook publié.
| UI0 seulement ; les getters natifs restent propriétaires des raccourcis.
    .text
    .globl mllr_mode
mllr_mode:
    movew %sr,%d0
    andil #0x700,%d0
    bne .Llr_inactive
    tstl mlp_obj
    beq .Llr_inactive
    jsr 0x400cf9a8
    tstl %d0
    beq .Llr_inactive
    movel %d0,%sp@-
    jsr 0x4006ba76
    addql #4,%sp
    tstb %d0
    beq .Llr_inactive
    jsr 0x400cf866
    tstl %d0
    beq .Llr_inactive
    movel %d0,%sp@-
    jsr 0x4000eb90
    addql #4,%sp
    tstl %d0
    beq .Llr_inactive
    movel %d0,%sp@-
    jsr 0x4001334c
    addql #4,%sp
    tstb %d0
    beq .Llr_unquantized
    moveq #1,%d0
    rts
.Llr_unquantized:
    moveq #2,%d0
    rts
.Llr_inactive:
    moveq #0,%d0
    rts
