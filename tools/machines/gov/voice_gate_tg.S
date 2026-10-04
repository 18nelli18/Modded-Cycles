| voice_gate(piste, trig, entrée) avec Model-TG (notes/36) : à la place du code compilé de bridge_engines.c (TG_FIRST),
| à la même adresse, même résultat (d0 = 1 : ne pas calculer la voix, sortie à zéro). Appelé par le détour de la
| boucle des voix (gen_syntakt_engines.dispatch_tg_asm) avant update/render. gov_st (voix d'un moteur du Syntakt)
| n'est plus tenu : seul le compteur des firmwares de diagnostic s'en servait, et eux gardent le code compilé.
| Préserve d2-d7/a2-a6.
        .text
        .globl  voice_gate
voice_gate:
        move.l  %d2, -(%sp)
        lea     GB, %a1
        move.l  8(%sp), %d0             | piste
        moveq   #6, %d1                 | libre : le Sampler...
        cmp.l   16(%sp), %d1
        beq.s   3f
        tst.l   TG_RS_STATE             | ...la piste que Model-TG enregistre...
        beq.s   2f
        cmp.l   TG_RS_SRC, %d0
        beq.s   3f
2:      tst.l   TG_SLE_RUN              | ...ou dont il édite les tranches
        beq.s   4f
        cmp.l   TG_SLE_TRK, %d0
        bne.s   4f
3:      moveq   #1, %d2                 | jamais éteinte
        clr.b   O_FADING(%a1, %d0.l)
        clr.b   O_STOLEN(%a1, %d0.l)
        bra.s   5f
4:      moveq   #0, %d2
5:      move.b  %d2, O_FREE(%a1, %d0.l)
        tst.l   12(%sp)
        beq.s   6f
        clr.b   O_FADING(%a1, %d0.l)    | trig : la voix repart
        clr.b   O_STOLEN(%a1, %d0.l)
        clr.b   O_QUIET(%a1, %d0.l)
        clr.w   O_AGE(%a1, %d0.l*2)
        bra.s   8f
6:      mvz.w   O_AGE(%a1, %d0.l*2), %d1
        addq.l  #1, %d1
        cmp.l   #0xffff, %d1            | 0xffff au plus
        bhi.s   7f
        move.w  %d1, O_AGE(%a1, %d0.l*2)
7:      tst.l   %d2
        bne.s   8f
        tst.b   O_STOLEN(%a1, %d0.l)    | éteinte par le régulateur
        bne.s   9f
        mvz.b   O_QUIET(%a1, %d0.l), %d1
        moveq   #IDLE_BLOCKS, %d2
        tst.l   O_PRESSURE(%a1)
        beq.s   71f
        moveq   #16, %d2
71:     cmp.l   %d2, %d1                | restée faible assez longtemps
        bcc.s   9f
8:      moveq   #1, %d0
        move.l  %d0, O_RAN(%a1)
        move.l  TIMER, %d0
        move.l  %d0, O_X_VT0(%a1)
        moveq   #0, %d0
        move.l  (%sp)+, %d2
        rts
9:      moveq   #1, %d0
        move.l  (%sp)+, %d2
        rts
