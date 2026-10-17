| Note 112 : boucle deux samples, calculs identiques.
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
    movel %sp@(52),%d0
    lea precise_modes(%pc),%a0
    movel %d1,%a0@(0,%d0:l:4)
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
    tstl %d1
    beq .Ldry_sample
.Lsample:
    movel %a1@,%d6
    asrl #4,%d6
    macl %a3,%d6,%acc0
    movel %d5,%d7
    movclr.l %acc0,%d6
    lsll #2,%d6
    moveal %d6,%a5
    macl %d1,%d7,%acc0
    movel #268434432,%d7
    movclr.l %acc0,%d6
    lsll #2,%d6
    negl %d6
    addl %a5,%d6
    cmpl %d7,%d6
    ble .Lin_hi
    movel %d7,%d6
.Lin_hi:
    cmpil #-268434432,%d6
    bge .Lcascade
    movel #-268434432,%d6
.Lcascade:
.macro pole reg,tag
    subl \reg,%d6
    macl %d0,%d6,%acc0
    .if \tag == 1
    movel #134217728,%d7
    .elseif \tag == 2
    movel #134213632,%d7
    .elseif \tag == 3
    moveal #-134213632,%a5
    .elseif \tag == 4
    lea %a1@(4),%a1
    .endif
    movclr.l %acc0,%d6
    addl %d6,\reg
    .if \tag == 1
    cmpl %d7,\reg
    ble .Lhi\tag
    movel %d7,\reg
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
    cmpl %d7,%d6
    ble .Lout_hi
    movel %d7,%d6
.Lout_hi:
    cmpl %a5,%d6
    bge .Lout_lo
    movel %a5,%d6
.Lout_lo:
    lsll #4,%d6
    movel %d6,%a1@(-4)
    cmpal %a2,%a1
    bne .Lsample
    bra .Lfinish
    | Chemin sans feedback choisi une seule fois par bloc ; memes arrondis.
.macro dry_pole reg,prefetch=0,ready=0
    .if !\ready
    subl \reg,%d6
    .endif
    macl %d0,%d6,%acc0
    | Charger/decaler le prochain sample pendant la latence EMAC.
    .if \prefetch == 1
    movel %a1@(4),%d7
    .elseif \prefetch == 2
    asrl #4,%d7
    .elseif \prefetch == 3
    subl %d2,%d7
    .elseif \prefetch == 4
    lea %a1@(4),%a1
    .endif
    movclr.l %acc0,%d6
    addl %d6,\reg
    movel \reg,%d6
.endm
.macro dry_frame prefetch=0,queued=0
    .if \queued
    movel %d7,%d6
    .else
    movel %a1@,%d6
    asrl #4,%d6
    .endif

    dry_pole %d2,\prefetch,\queued
    dry_pole %d3,(\prefetch*2)
    dry_pole %d4,(\prefetch*3)
    dry_pole %d5,(\prefetch*4)
    cmpil #134213632,%d6
    ble .Ldry_hi\@
    movel #134213632,%d6
.Ldry_hi\@:
    cmpil #-134213632,%d6
    bge .Ldry_lo\@
    movel #-134213632,%d6
.Ldry_lo\@:
    lsll #4,%d6
    .if \prefetch
    movel %d6,%a1@(-4)
    .else
    movel %d6,%a1@+
    .endif
.endm
.Ldry_sample:
    dry_frame 1,0
    dry_frame 0,1
    cmpal %a2,%a1
    bne .Ldry_sample
.Lfinish:
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
.balign 4
.globl precise_modes
precise_modes:
    .space 28
precise_end:
