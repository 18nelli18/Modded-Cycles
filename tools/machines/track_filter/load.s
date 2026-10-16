| Note 105 : meme ladder Q27 ; seuls les checks de bornes redondants sont retires.
| Meme coefficient/courbe/feedback ; acc0 est vide a l'entree depuis Volume+Dist,
| et rendu vide a la sortie. MACSR et registres non volatils preserves.
.text
.globl precise_filter,precise_end
precise_filter:
    movel %sp@(8),%d0
    lea GFLT_F,%a0
    tstl %a0@(0,%d0:l:4)
    beq .Lreturn
    moveal %sp@(4),%a0
    moveq #31,%d1
.Lquiet_samples:
    tstl %a0@+
    bne .Lactive
    subql #1,%d1
    bpl .Lquiet_samples
    movel %sp@(8),%d0
    lsll #2,%d0
    lea GFLT_Y1,%a0
    addal %d0,%a0
    moveq #3,%d1
.Lquiet_states:
    movel %a0@,%d0
    bpl .Lquiet_abs
    negl %d0
.Lquiet_abs:
    cmpil #1024,%d0
    bgt .Lactive
    lea %a0@(28),%a0
    subql #1,%d1
    bpl .Lquiet_states
    lea %a0@(-112),%a0
    moveq #3,%d1
.Lquiet_clear:
    clrl %a0@
    lea %a0@(28),%a0
    subql #1,%d1
    bpl .Lquiet_clear
    rts
.Lactive:
    lea %sp@(-44),%sp
    moveml %d2-%d7/%a2-%a5,%sp@
    movel %macsr,%d1
    movel %d1,%sp@(40)
    movel #0xb0,%macsr
    movel #0,%acc0
    movel %sp@(52),%d7
    lsll #2,%d7
    lea GFLT_F,%a0
    movel %a0@(0,%d7:l),%d0
    moveq #19,%d6
    lsll %d6,%d0
    lea GFLT_Q,%a0
    movel %a0@(0,%d7:l),%d1
    moveq #17,%d6
    lsll %d6,%d1
    lea GFLT_MK,%a0
    movel %a0@(0,%d7:l),%d6
    moveq #17,%d2
    lsll %d2,%d6
    moveal %d6,%a3
    lea GFLT_Y1,%a4
    addal %d7,%a4
    movel %a4@,%d2
    movel %a4@(28),%d3
    movel %a4@(56),%d4
    movel %a4@(84),%d5
    moveal %sp@(48),%a1
    lea %a1@(128),%a2
.Lsample:
    movel %a1@,%d6
    asrl #4,%d6
    tstl %d1
    beq .Lcascade
    macl %a3,%d6,%acc0
    movclr.l %acc0,%d6
    lsll #2,%d6
    moveal %d6,%a5
    movel %d5,%d6
    macl %d1,%d6,%acc0
    movclr.l %acc0,%d6
    lsll #2,%d6
    negl %d6
    addl %a5,%d6
    cmpil #268434432,%d6
    ble .Lin_hi
    movel #268434432,%d6
.Lin_hi:
    cmpil #-268434432,%d6
    bge .Lcascade
    movel #-268434432,%d6
.Lcascade:
.macro pole reg,tag
    subl \reg,%d6
    macl %d0,%d6,%acc0
    movclr.l %acc0,%d6
    addl %d6,\reg
    .if \tag == 1
    | Sans feedback, entree et etat sont deja bornes : interpolation convexe.
    tstl %d1
    beq .Llo\tag
    cmpil #134217728,\reg
    ble .Lhi\tag
    movel #134217728,\reg
.Lhi\tag:
    cmpil #-134217728,\reg
    bge .Llo\tag
    movel #-134217728,\reg
    .endif
.Llo\tag:
    movel \reg,%d6
.endm
    pole %d2,1
    pole %d3,2
    pole %d4,3
    pole %d5,4
    cmpil #134213632,%d6
    ble .Lout_hi
    movel #134213632,%d6
.Lout_hi:
    cmpil #-134213632,%d6
    bge .Lout_lo
    movel #-134213632,%d6
.Lout_lo:
    lsll #4,%d6
    movel %d6,%a1@+
    cmpal %a2,%a1
    bne .Lsample
    movel %d2,%a4@
    movel %d3,%a4@(28)
    movel %d4,%a4@(56)
    movel %d5,%a4@(84)
    movel %sp@(40),%d0
    movel %d0,%macsr
    moveml %sp@,%d2-%d7/%a2-%a5
    lea %sp@(44),%sp
.Lreturn:
    rts
precise_end:
