| Note116 : affichage Oct = octaves ajoutees, stockage historique inchange.
    .text
    .globl octave_draw
octave_draw:
    cmpil #5,%d2
    bne .Lcompare
    subql #1,%d0
.Lcompare:
    cmpil #2,%d2
    rts
