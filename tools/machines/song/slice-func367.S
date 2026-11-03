/* L'editeur peut s'ouvrir alors que FUNC est deja tenu : lire l'etat natif
 * plutot que le seul cache des evenements arrives depuis son ouverture.
 * TST d'origine : tous les registres restent intacts, seuls les CCR changent. */
    .text
    .globl slice_func367
slice_func367:
    lea -16(%sp),%sp
    movem.l %d0-%d1/%a0-%a1,(%sp)
    pea 1
    jsr 0x4007faf4
    addq.l #4,%sp
    tst.l %d0
    movem.l (%sp),%d0-%d1/%a0-%a1
    lea 16(%sp),%sp
    rts
