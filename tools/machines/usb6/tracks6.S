| Copie des 6 pistes vers le ring USB, déroulée (notes/34), à la place du stub tracks6 de ms-multi-output.
| Même contrat, mêmes octets écrits, mêmes registres et mêmes indicateurs à la sortie : entrée d0 = mots longs
| (trames x 2, échelle stéréo de l'OS), d1 = case du ring, d3 = trame de départ dans le bloc (modulo 32) ; chaque
| trame = les 6 pistes (0x80001858, 128 o chacune), octets inversés (USB petit-boutiste) ; sortie 0x40002a26.
| Le stub d'origine fait une boucle de 6 par trame (43 instructions et un branchement mal prédit) : ici 23.
        .equ    TRACK_BASE, 0x80001858
        .equ    REJOIN, 0x40002a26
        .text
        .globl  tracks6
tracks6:
        lea     %sp@(-28),%sp
        moveml  %d0/%d2/%d4/%d6/%a0-%a2,%sp@
        movea.l %d1,%a1
        lsrl    #1,%d0
        bles    9f
        moveq   #31,%d4
        movel   %d3,%d6
        lea     TRACK_BASE,%a0
1:      andl    %d4,%d6
        lea     %a0@(0,%d6:l:4),%a2
        movel   %a2@,%d2
        byterev %d2
        movel   %d2,%a1@+
        movel   %a2@(128),%d2
        byterev %d2
        movel   %d2,%a1@+
        movel   %a2@(256),%d2
        byterev %d2
        movel   %d2,%a1@+
        movel   %a2@(384),%d2
        byterev %d2
        movel   %d2,%a1@+
        movel   %a2@(512),%d2
        byterev %d2
        movel   %d2,%a1@+
        movel   %a2@(640),%d2
        byterev %d2
        movel   %d2,%a1@+
        addql   #1,%d6
        subql   #1,%d0
        bgts    1b
9:      moveml  %sp@,%d0/%d2/%d4/%d6/%a0-%a2
        lea     %sp@(28),%sp
        jmp     REJOIN
