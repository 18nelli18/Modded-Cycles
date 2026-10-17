| Note 112 : (phase & 0xffffff) >> 16 == (phase >> 16) & 255.
| d3 est recharge par la table avant son prochain usage ; CCR ecrase par AND d6.
.text
.globl native_index
native_index:
 movel %acc1,%d2
 swap %d2
 andil #255,%d2

| Deuxieme boucle : (phase >> 14) & 1020 == ((phase >> 16) & 255)*4.
| SWAP + masque remplace le shift ; l index x4 est porte par les deux EA.
| Le moveq14 est retire, le compteur suivant lit seulement les 6 bits bas
| de d6, fixes a15 par moveb avant usage. d6 entier est ensuite recharge.
| Les fins des fonctions et branches sont recalees a -2 ; NOP apres RTS.
