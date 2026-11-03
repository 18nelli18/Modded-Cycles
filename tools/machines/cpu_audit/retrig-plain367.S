/* Plateau repeat : memes lectures/ecritures dans le meme ordre, y compris
 * lorsque capture et lecture se recouvrent. Constantes gardees en registres.
 * Aucun EMAC, nouvel etat, changement d'enveloppe ou de cadence historique. */
    .text
    .globl rr_plain367
rr_plain367:
    lea -24(%sp),%sp
    movem.l %d2-%d6/%a2,(%sp)
    move.l 28(%sp),%a0
    move.l 32(%sp),%a1
    move.l 36(%sp),%a2
    moveq #15,%d2
    moveq #23,%d3
    move.l #-32767,%d4
    move.l #32767,%d5
    moveq #8,%d6
    tst.l 40(%sp)
    beq .Lread
    .macro full
    move.l (%a0),%d0
    move.l %d0,%d1
    asr.l %d2,%d1
    cmp.l %d4,%d1
    bge.s .Llower_ok\@
    move.l %d4,%d1
.Llower_ok\@:
    cmp.l %d5,%d1
    ble.s .Lupper_ok\@
    move.l %d5,%d1
.Lupper_ok\@:
    move.w %d1,(%a1)+
    lsl.l %d3,%d0
    asr.l %d3,%d0
    mvs.w (%a2)+,%d1
    lsl.l %d2,%d1
    add.l %d1,%d0
    move.l %d0,(%a0)+
    .endm
.Lfull:
    .rept 4
    full
    .endr
    subq.l #1,%d6
    bne .Lfull
    bra .Ldone
.Lread:
    .rept 4
    move.l (%a0),%d0
    lsl.l %d3,%d0
    asr.l %d3,%d0
    mvs.w (%a2)+,%d1
    lsl.l %d2,%d1
    add.l %d1,%d0
    move.l %d0,(%a0)+
    .endr
    subq.l #1,%d6
    bne .Lread
.Ldone:
    movem.l (%sp),%d2-%d6/%a2
    lea 24(%sp),%sp
    rts
