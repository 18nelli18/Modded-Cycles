| Note 107 : somme de trois voix (0, 3, 6), niveau non compense.
.text
.globl swarm_lite_sum
swarm_lite_sum:
    clrl %d1
.Lsample:
    movel %a0@+,%d0
    addl %a0@(872),%d0
    addl %a0@(1748),%d0
    movel %d0,%a4@(0,%d1:l)
    addql #4,%d1
    cmpil #128,%d1
    bne.s .Lsample
.rept (44-(.-swarm_lite_sum))/2
    .word 0x4e71
.endr
