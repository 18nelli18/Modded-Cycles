| voice_after(piste, sortie) avec Model-TG (notes/36) : à la place du code compilé de bridge_engines.c, à la même
| adresse, appelé par voice_done (compilé) pour les pistes que voice_gate a laissé calculer. Comme le code C : coût
| de la voix (moyenne 1/4), fondu éventuel, compteur de blocs faibles ; mais la voix est faible quand tous ses
| échantillons sont dans [-seuil, seuil[, testé par OU(x + seuil) < 2 seuil (non signé), 3 instructions par
| échantillon : exactement le test du code C (OU des valeurs absolues à un bit près, sous un seuil puissance de 2).
| La crête (gov_peak) n'est plus calculée : le régulateur classe les voix sur la sortie des pistes (gov_key.S).
| Préserve d2-d7/a2-a6.
        .text
        .globl  voice_after
voice_after:
        move.l  TIMER, %d1
        lea     -16(%sp), %sp
        movem.l %d2-%d4/%a2, (%sp)
        lea     GB, %a1
        move.l  20(%sp), %d0            | piste
        movea.l 24(%sp), %a0            | sortie (32 x int32)
        sub.l   O_X_VT0(%a1), %d1       | coût d'update + render
        lea     O_COST(%a1), %a2
        move.l  (%a2, %d0.l*4), %d2
        sub.l   %d2, %d1
        asr.l   #2, %d1
        add.l   %d2, %d1
        move.l  %d1, (%a2, %d0.l*4)
        mvz.b   O_FADING(%a1, %d0.l), %d2
        tst.l   %d2
        bne.w   20f
1:      tst.b   O_FREE(%a1, %d0.l)      | Sampler, piste protégée : jamais éteinte
        bne.s   9f
        move.l  #IDLE_THR, %d3
        tst.l   O_PRESSURE(%a1)
        beq.s   2f
        move.l  #0x100000, %d3          | -66 dB sous forte charge
2:      moveq   #0, %d2
        moveq   #7, %d4
3:      move.l  (%a0)+, %d1
        add.l   %d3, %d1
        or.l    %d1, %d2
        move.l  (%a0)+, %d1
        add.l   %d3, %d1
        or.l    %d1, %d2
        move.l  (%a0)+, %d1
        add.l   %d3, %d1
        or.l    %d1, %d2
        move.l  (%a0)+, %d1
        add.l   %d3, %d1
        or.l    %d1, %d2
        subq.l  #1, %d4
        bpl.s   3b
        add.l   %d3, %d3
        cmp.l   %d3, %d2
        bcc.s   5f
        mvz.b   O_QUIET(%a1, %d0.l), %d1        | faible : un bloc de plus (255 au plus)
        addq.l  #1, %d1
        tst.b   %d1
        beq.s   9f
        move.b  %d1, O_QUIET(%a1, %d0.l)
        bra.s   9f
5:      clr.b   O_QUIET(%a1, %d0.l)
9:      movem.l (%sp), %d2-%d4/%a2
        lea     16(%sp), %sp
        rts
20:     mvz.b   O_FLEN(%a1, %d0.l), %d3 | fondu linéaire de flen blocs, comme le code C
        move.l  %d3, %d4
        lsl.l   #5, %d4                 | n = 32 flen échantillons
        move.l  #65536, %d1
        divu.l  %d4, %d1                | pas
        sub.l   %d2, %d3
        lsl.l   #5, %d3                 | p = position dans le fondu
        sub.l   %d3, %d4
        muls.l  %d1, %d4                | (n - p) x pas
        movea.l %a0, %a2
        moveq   #31, %d3
21:     mvs.w   (%a2), %d0              | x >> 16
        muls.l  %d4, %d0
        move.l  %d0, (%a2)+
        sub.l   %d1, %d4
        subq.l  #1, %d3
        bpl.s   21b
        move.l  20(%sp), %d0
        subq.l  #1, %d2
        move.b  %d2, O_FADING(%a1, %d0.l)
        bne.w   1b
        moveq   #1, %d1                 | fondu fini : éteinte jusqu'à son prochain trig
        move.b  %d1, O_STOLEN(%a1, %d0.l)
        bra.w   1b
