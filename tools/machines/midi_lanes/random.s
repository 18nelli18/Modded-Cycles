| Xorshift privé B : même séquence que le générateur, sans importer son mod.
| d7=état non nul, d0=résultat0..32767, d1 scratch ; état porté par l'appelant.
| Source propre tools/machines/seq_gen/seq_gen.s (MIT).
    .text
    .globl ml_random
ml_random:
    movel %d7,%d0
    moveq #13,%d1
    lsll %d1,%d0
    eorl %d0,%d7
    movel %d7,%d0
    moveq #17,%d1
    lsrl %d1,%d0
    eorl %d0,%d7
    movel %d7,%d0
    lsll #5,%d0
    eorl %d0,%d7
    movel %d7,%d0
    andil #32767,%d0
    rts
