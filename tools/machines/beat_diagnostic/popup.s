| Note 100 : popup natif court ; meme gestion des chaines que le support commun.
.text
.globl br_popup
br_popup:
    linkw   %fp,#-28
    moveml  %d2-%d3/%a2,%sp@
    movel   0x40fe4178,%d0
    beqw    br_popup_out                | UI pas encore disponible
    lea.l   0x400802e0,%a2        | allocation native
    movel   %fp,%d2
    addil   #-12,%d2
    pea     %fp@(-13)
    movel   %fp@(8),%sp@-         | texte de division
    movel   %d2,%sp@-
    jsr     0x400f980c
    lea.l   %sp@(12),%sp
    pea     0x9c
    jsr     %a2@
    addql   #4,%sp
    movel   %d0,%d3
    movel   %d2,%sp@-
    movel   %d3,%sp@-
    jsr     0x400747c0
    addql   #8,%sp
br_popup_std:
    movel   %d3,%fp@(-8)
    clrl    %fp@(-4)
    pea     0x10
    jsr     %a2@
    addql   #4,%sp
    movea.l %d0,%a0
    moveq   #1,%d0
    movel   %d0,%a0@(4)
    movel   #0x400fbf40,%a0@
    movel   %d0,%a0@(8)
    movel   %d3,%a0@(12)
    movel   %a0,%fp@(-4)
    jsr     0x400d0974
    movel   %d0,%sp@-
    jsr     0x400060d8
    addql   #4,%sp
    clrl    %sp@-
    pea     %fp@(-8)
    movel   %d0,%sp@-
    jsr     0x4007700e
    lea.l   %sp@(12),%sp
    pea     %fp@(-4)
    jsr     0x400cf23c
    addql   #4,%sp
    movel   %d2,%sp@-
    jsr     0x400f7d5c
    addql   #4,%sp
br_popup_out:
    moveml  %fp@(-28),%d2-%d3/%a2
    unlk    %fp
    rts
