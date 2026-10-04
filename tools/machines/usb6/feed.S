| Envoi à l'USB à heure fixe (notes/35).
| L'OS envoie chaque bloc à l'USB (0x40002912(source, trames)) juste après l'avoir calculé : l'instant dépend du
| temps de calcul, qui varie avec Model-TG ou les moteurs du Syntakt (pistes au repos, mutes, effets éteints), alors
| que la file USB ne tolère qu'un écart limité (0,2 ms avec le ring du mod 6 canaux d'origine). Ici, les deux envois
| de l'interruption de rendu (0x40059392, et 0x400593ce quand le son est coupé) sont notés, puis faits au début de
| l'interruption suivante, avant tout calcul : toujours au même instant du bloc, avec un bloc de plus de latence
| (0,67 ms). Les mêmes octets servent en stéréo (ring de 16 cases) et en 6 canaux (ring de 9) : la cible de la file
| est tirée de la profondeur du ring, lue dans le code de l'OS.
        .equ    FEED, 0x40002912
        .equ    RESTART, 0x404a062c             | mis par le démarrage du flux, effacé par le 1er envoi
        .equ    STREAM, 0x404a0644              | flux lancé (la 1re case amorcée est partie)
        .equ    DROP, 0x404a0620                | trames que l'envoi saute d'abord
        .equ    POOL, 0x80008000                | les 32 dTD du point d'accès IN, 64 o chacun
        .equ    RING_LAST, 0x400029b9           | moveq #<dernière case>,%d5 de l'envoi : 15 (origine), 8 (6ch-usbup)
        .text
        .globl  feed_isr, feed_note, feed_pend
| à la place de `movel #32,%macsr` (0x40058ca0), au début de l'interruption de rendu ; garde tout sauf d0-d1/a0-a1
feed_isr:
        movel   #32,%macsr
        movel   %a2,%sp@-
        lea     feed_pend,%a2
        tstl    %a2@(4)
        beqs    9f
        tstl    RESTART                         | 1er envoi d'un nouveau flux : la file, alignée ici
        beqs    1f
        tstl    STREAM
        beqs    1f
        bsr     align
1:      movel   %a2@(4),%sp@-
        movel   %a2@,%sp@-
        clrl    %a2@(4)
        jsr     FEED
        addql   #8,%sp
        tstl    %a2@(12)
        beqs    9f
        movel   %a2@(12),%sp@-
        movel   %a2@(8),%sp@-
        clrl    %a2@(12)
        jsr     FEED
        addql   #8,%sp
9:      movel   %sp@+,%a2
        rts
| align : trames à sauter pour que la file compte 16 + 3 x (cases du ring) trames juste après cet envoi de 32 (64 en
| stéréo, 43 avec le ring de 9 cases ; notes/35 §4). L'OS les tire de l'heure de départ de la 1re case, qui suppose
| l'envoi après le calcul du bloc ; ici l'envoi est au début du bloc suivant, et un départ tout près du début d'un
| bloc décale d'un bloc entier. On compte donc les cases encore en file (bit Active du dTD, effacé par le contrôleur
| quand elle part), 6 trames chacune (silence d'amorçage).
align:
        lea     POOL+7,%a0
        moveq   #31,%d1
        moveq   #0,%d0
2:      btst    #7,%a0@
        beqs    3f
        addql   #6,%d0
3:      lea     %a0@(64),%a0
        subql   #1,%d1
        bpls    2b
        mvzb    RING_LAST,%d1
        addql   #1,%d1                          | cases du ring
        mulu.w  #3,%d1
        subil   #16,%d1                         | cible - 32
        subl    %d1,%d0
        bpls    4f
        moveq   #0,%d0
4:      moveq   #31,%d1
        cmpl    %d1,%d0
        bles    5f
        movel   %d1,%d0
5:      movel   %d0,DROP
        rts
| à la place des deux `jsr 0x40002912` de l'interruption de rendu : (source, trames) noté pour la suivante
feed_note:
        lea     feed_pend,%a0
        tstl    %a0@(4)
        beqs    1f
        addql   #8,%a0
        tstl    %a0@(4)
        bnes    2f
1:      movel   %sp@(4),%a0@
        movel   %sp@(8),%a0@(4)
        rts
2:      jmp     FEED                    | (jamais : deux envois au plus par bloc) envoi immédiat, comme l'OS
        .balign 4
feed_pend:
        .long   0, 0, 0, 0              | deux envois notés : (source, trames), trames = 0 si vide
