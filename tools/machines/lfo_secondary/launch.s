| Note 58 : callback du deuxième appui LFO, ABI (vue parente) -> ouvert.
| Prépare le contexte avant la page ; refus de préparation/page = retour 0,
| l'adaptateur key.s conserve alors le comportement de fermeture natif.
| 0x8000100c est le frame 476 octets produit par 0x40058474.
    .text
    .globl lf2_launch
lf2_launch:
    tstl 0x40fe4178
    beq .Llaunch_refuse
    tstl lf2p_obj
    bne .Llaunch_refuse
    pea 0x8000100c
    jsr lf2_prepare
    addql #4,%sp
    tstl %d0
    beq .Llaunch_refuse
    jmp lf2p_open
.Llaunch_refuse:
    moveq #0,%d0
    rts
