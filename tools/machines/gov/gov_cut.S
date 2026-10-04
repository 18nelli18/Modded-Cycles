| Régulateur de charge, décision (notes/36) : appelé par audio_end.S quand la charge soutenue dépasse STEAL ou que le
| pic qui dure dépasse PEAK. Entrée : a1 = GB, d2 = période du bloc (ticks), d4 = charge soutenue, d5 = pic qui dure.
| Temps à libérer : revenir à TARGET (charge soutenue) ou sous PEAK - GOV_MARGIN (pic), le plus grand des deux, moins
| le coût des voix en fondu et de celles éteintes depuis moins de RECENT blocs, que les moyennes n'ont pas encore vues
| partir. Puis deux voix au plus, parmi celles qu'on peut éteindre (comme le code C : ni arrêtée, ni en fondu, ni
| restée faible ; note d'au moins 16 blocs, 4 en surcharge sévère ; avec Model-TG, ni le Sampler ni une piste
| protégée) : la MOINS AUDIBLE dans le mix (gov_key.S), à égalité la plus ancienne. Fondu de 8 blocs, 2 en surcharge
| sévère (pic qui dure au-dessus de SEVERE). Préserve d2-d7/a2-a6.
        .text
        .globl  govern
govern:
        lea     -64(%sp), %sp           | registres (40 o), puis les 6 clés
        movem.l %d2-%d7/%a2-%a5, (%sp)
        movea.l %a1, %a5
        lsr.l   #8, %d2                 | ticks pour 1/256 de bloc
        moveq   #0, %d3                 | d3 = temps à libérer (ticks)
        cmp.l   #STEAL, %d4
        bcs.s   1f
        move.l  %d4, %d3
        sub.l   #TARGET, %d3
        muls.l  %d2, %d3
1:      cmp.l   #PEAK, %d5
        bcs.s   2f
        move.l  %d5, %d0
        sub.l   #PEAK_TO, %d0
        muls.l  %d2, %d0
        cmp.l   %d3, %d0
        bls.s   2f
        move.l  %d0, %d3
2:      moveq   #IDLE_BLOCKS, %d7       | d7 : blocs faibles d'une voix qui s'arrête d'elle-même
        tst.l   O_PRESSURE(%a5)
        beq.s   3f
        moveq   #16, %d7
3:      moveq   #8, %d6                 | d6 : fondu (blocs) ; note d'au moins 2 x fondu blocs
        cmp.l   #SEVERE, %d5
        bcs.s   4f
        moveq   #2, %d6
4:      lea     O_COST(%a5), %a4
        lea     O_X_CUT(%a5), %a3
        moveq   #0, %d0                 | pour chaque piste : sa clé, ou -1 si on ne peut pas l'éteindre
10:     moveq   #-1, %d2
        tst.b   O_FADING(%a5, %d0.l)    | en fondu : encore comptée par les moyennes
        bne.s   12f
        tst.b   O_STOLEN(%a5, %d0.l)
        beq.s   13f
        move.l  O_X_BLK(%a5), %d1       | arrêtée : comptée encore RECENT blocs
        sub.l   (%a3, %d0.l*4), %d1
        moveq   #RECENT, %d4
        cmp.l   %d4, %d1
        bcc.s   18f
12:     move.l  (%a4, %d0.l*4), %d1
        sub.l   %d1, %d3
        bhi.s   18f
        bra.w   99f                     | plus rien à libérer
13:     mvz.b   O_QUIET(%a5, %d0.l), %d4
        cmp.l   %d7, %d4                | restée faible : s'arrête d'elle-même
        bcc.s   18f
        mvz.w   O_AGE(%a5, %d0.l*2), %d4
        sub.l   %d6, %d4
        sub.l   %d6, %d4                | note trop récente
        bmi.s   18f
.ifdef TG
        tst.b   O_FREE(%a5, %d0.l)      | Sampler, piste que Model-TG enregistre ou dont il édite les tranches
        bne.s   18f
.endif
        jsr     GOV_KEY
18:     move.l  %d2, 40(%sp, %d0.l*4)
        addq.l  #1, %d0
        moveq   #6, %d1
        cmp.l   %d1, %d0
        bne.s   10b
        moveq   #2, %d5                 | deux voix au plus, puis on remesure au bloc suivant
20:     moveq   #-2, %d2                | meilleure clé (non signée) ; -1 : on ne peut pas l'éteindre
        moveq   #-1, %d1                | sa piste
        suba.l  %a1, %a1                | son âge
        moveq   #0, %d0
21:     move.l  40(%sp, %d0.l*4), %d4
        cmp.l   %d2, %d4
        bcs.s   22f                     | plus faible
        bne.s   23f
        mvz.w   O_AGE(%a5, %d0.l*2), %d4        | à égalité : la plus ancienne
        cmpa.l  %d4, %a1
        bcc.s   23f
        bra.s   24f
22:     move.l  %d4, %d2
        mvz.w   O_AGE(%a5, %d0.l*2), %d4
24:     movea.l %d4, %a1
        move.l  %d0, %d1
23:     addq.l  #1, %d0
        moveq   #6, %d4
        cmp.l   %d4, %d0
        bne.s   21b
        tst.l   %d1
        bmi.s   99f
        move.b  %d6, O_FADING(%a5, %d1.l)       | fondu de d6 blocs
        move.b  %d6, O_FLEN(%a5, %d1.l)
        move.l  O_X_BLK(%a5), %d0
        move.l  %d0, (%a3, %d1.l*4)
        moveq   #-1, %d0
        move.l  %d0, 40(%sp, %d1.l*4)
        move.l  (%a4, %d1.l*4), %d0
        addq.l  #1, %d0
        sub.l   %d0, %d3
        bls.s   99f
        subq.l  #1, %d5
        bne.s   20b
99:     movem.l (%sp), %d2-%d7/%a2-%a5
        lea     64(%sp), %sp
        rts
