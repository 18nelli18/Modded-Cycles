| Note 58 : lf2_prepare(frame), allocation unique dans la tâche UI.
| Le pointeur audio reste nul jusqu'à la fin de lf2_init. Un rappel
| réentrant refuse l'ouverture ; un contexte publié n'est jamais réinitialisé.
| Aucune allocation ni libération depuis lf2_dispatch.
    .data
    .globl lf2_preparing
lf2_preparing: .long 0
    .text
    .globl lf2_prepare
lf2_prepare:
    lea.l %sp@(-8),%sp
    movem.l %a2-%a3,%sp@
    movew %sr,%d0
    andil #0x0700,%d0
    bne .Lprepare_refuse
    moveal %sp@(12),%a3
    tstl %a3
    beq .Lprepare_refuse
    tstl lf2_context
    bne .Lprepare_ready
    tstl lf2_preparing
    bne .Lprepare_refuse
    moveq #1,%d0
    movel %d0,lf2_preparing
    pea 1240
    jsr 0x400802e0
    addql #4,%sp
    moveal %d0,%a2
    tstl %a2
    beq .Lprepare_failed
    movel %a3,%sp@-
    movel %a2,%sp@-
    jsr lf2_init
    addql #8,%sp
    tstl %d0
    beq .Lprepare_free
    | Publication d'un seul long aligné, après tous les réglages et buffers.
    movel %a2,lf2_context
    clrl lf2_preparing
.Lprepare_ready:
    moveq #1,%d0
    bra .Lprepare_done
.Lprepare_free:
    movel %a2,%sp@-
    jsr 0x400802ec
    addql #4,%sp
.Lprepare_failed:
    clrl lf2_preparing
.Lprepare_refuse:
    moveq #0,%d0
.Lprepare_done:
    movem.l %sp@,%a2-%a3
    addql #8,%sp
    rts
