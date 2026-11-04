/* Remplace PEA note puis MOVE piste avant KeyboardView::note_on.
 * D2=evenement,D3=piste,A2=touche,A6=KbT. Les arguments sont construits
 * avant le consommateur natif : son tableau des touches garde la vraie note
 * pour le relachement, meme si FUNC ou la piste change entretemps.
 * Tous les registres sont conserves ; effet pile identique aux deux pushes. */
    .text
    .globl sn_push368
sn_push368:
    lea -24(%sp),%sp
    movem.l %d0-%d1/%a0-%a1,(%sp)
    move.l 24(%sp),20(%sp)
    move.l %d2,-(%sp)
    move.l %d3,-(%sp)
    jsr sn_offset368
    addq.l #8,%sp
    lea 52(%a2,%a6.l),%a0
    adda.l %d0,%a0
    move.l %a0,24(%sp)
    movem.l (%sp),%d0-%d1/%a0-%a1
    move.l 20(%sp),16(%sp)
    move.l %d3,20(%sp)
    lea 16(%sp),%sp
    rts
