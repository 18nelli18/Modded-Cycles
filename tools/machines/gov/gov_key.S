| Régulateur de charge (notes/36) : à quel point la piste d0 s'entend dans le mix, pour gov_cut.S. d2 = somme des
| valeurs absolues de ses 32 échantillons du bloc (0x80001858 : après le niveau de piste, ce que reçoit le mixeur)
| x le plus grand de ses 6 gains de mixeur (gov_gains.S) ; ceux d'une piste mutée sont nuls. Non signé, sous 2^32.
| Garde d0, d3, d6, d7 et a2-a6 ; change d1, d2, d4, d5, a0, a1.
        .text
        .globl  gov_key
gov_key:
        move.l  %d0, %d4
        lsl.l   #7, %d4
        lea     TRACK_BASE, %a0
        adda.l  %d4, %a0
        moveq   #0, %d2
        moveq   #31, %d4
1:      move.l  (%a0)+, %d1
        bpl.s   2f
        not.l   %d1
2:      lsr.l   #8, %d1
        add.l   %d1, %d2
        subq.l  #1, %d4
        bpl.s   1b
        lsr.l   #8, %d2
        lsr.l   #4, %d2                 | < 2^16
        move.l  %d0, %d4
        lsl.l   #2, %d4
        lea     GOV_GAINS, %a0
        moveq   #0, %d5
4:      move.l  (%a0)+, %d1
        beq.s   6f
        movea.l %d1, %a1
        move.l  (%a1, %d4.l), %d1
        bpl.s   5f
        neg.l   %d1
5:      cmp.l   %d5, %d1
        bls.s   4b
        move.l  %d1, %d5
        bra.s   4b
6:      lsr.l   #8, %d5
        lsr.l   #8, %d5                 | < 2^16
        mulu.l  %d5, %d2
        rts
