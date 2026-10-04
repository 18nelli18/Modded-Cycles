| Régulateur de charge, partie de chaque bloc (notes/36) : à la place du audio_end() compilé de bridge_engines.c, à
| la même adresse, appelé de même par la sonde de la fonction audio (gen_syntakt_engines.probe_asm). En-tête écrit
| par tools/gov_asm.py : GB = base des variables de la passerelle, O_* = leurs décalages, seuils de GOV.
| Mêmes mesures que le code C (charge du bloc, moyenne rapide 1/8 et l'arrêt anticipé qu'elle commande, période), une
| moyenne lente (1/2^GOV_SLOW) qui monte vraiment, puis :
|  - charge soutenue = la plus basse des deux moyennes : une fois des voix éteintes, la moyenne rapide redescend en
|    quelques blocs, la lente en centaines ; le code C continuait d'éteindre tant que la lente restait haute ;
|  - pic = le plus bas des deux derniers blocs : un bloc isolé au-dessus du seuil (un pas chargé, les caches vidés
|    par l'interface) est déjà passé, éteindre une voix ne le rattraperait pas ;
|  - au-dessus d'un seuil, gov_cut.S décide (rare). Préserve d2-d7/a2-a6 (convention C).
        .text
        .globl  audio_end
audio_end:
        move.l  TIMER, %d1
        lea     -16(%sp), %sp
        movem.l %d2-%d5, (%sp)
        lea     GB, %a1
        addq.l  #1, O_X_BLK(%a1)
        move.l  O_T0_AUDIO(%a1), %d0
        move.l  %d0, %d2
        sub.l   O_X_LAST_T0(%a1), %d2   | période : depuis le début du bloc précédent
        move.l  %d0, O_X_LAST_T0(%a1)
        sub.l   %d0, %d1                | durée de la fonction audio
        tst.l   %d2
        beq.w   9f                      | (premier bloc : période nulle ; après une pause, la charge du bloc est faible)
        lsl.l   #8, %d1
        divu.l  %d2, %d1                | d1 = charge du bloc, en 1/256
        move.l  %d1, O_LOAD(%a1)
        move.l  O_AVG(%a1), %d3
        move.l  %d1, %d0
        sub.l   %d3, %d0
        asr.l   #3, %d0
        add.l   %d0, %d3                | d3 = moyenne rapide (environ 5 ms)
        move.l  %d3, O_AVG(%a1)
        moveq   #0, %d0
        cmp.l   #PRESSURE, %d3
        bcs.s   2f
        moveq   #1, %d0
2:      move.l  %d0, O_PRESSURE(%a1)
        move.l  O_X_FAST(%a1), %d3      | moyenne rapide précise, en 1/2048 de bloc : celle du code C (gov_avg, gardée
        move.l  %d3, %d0                | pour l'arrêt anticipé des fins de notes) reste jusqu'à 7/256 sous la charge
        lsr.l   #3, %d0                 | quand elle monte (l'écart / 8 tombe à 0)
        sub.l   %d0, %d3
        add.l   %d1, %d3
        move.l  %d3, O_X_FAST(%a1)
        lsr.l   #3, %d3                 | d3 = moyenne rapide (environ 5 ms)
        move.l  O_X_SLOW(%a1), %d4      | moyenne lente précise, en 1/65536 de bloc : dans le code C (en 1/256),
        move.l  %d4, %d0                | l'écart / 256 était presque toujours 0 et elle ne montait pas
        lsr.l   #SLOW_SH, %d0
        sub.l   %d0, %d4
        add.l   %d1, %d4
        move.l  %d4, O_X_SLOW(%a1)
        lsr.l   #SLOW_SH, %d4           | d4 = moyenne lente (environ 170 ms), en 1/256 dans gov_slow
        move.l  %d4, O_SLOW(%a1)
        cmp.l   %d3, %d4
        bls.s   3f
        move.l  %d3, %d4                | d4 = charge soutenue
3:      move.l  O_X_PREV_LOAD(%a1), %d5
        move.l  %d1, O_X_PREV_LOAD(%a1)
        cmp.l   %d1, %d5
        bls.s   4f
        move.l  %d1, %d5                | d5 = pic qui dure
4:      cmp.l   #STEAL, %d4
        bcc.s   5f
        cmp.l   #PEAK, %d5
        bcs.s   9f
5:      jsr     GOV_CUT                 | (a1 base, d2 période, d4 charge soutenue, d5 pic qui dure)
9:      movem.l (%sp), %d2-%d5
        lea     16(%sp), %sp
        rts
