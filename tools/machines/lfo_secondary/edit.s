| Note 58 : setter UI des huit réglages LFO 2, représentation native.
| lf2_edit(context,track,field,value) -> 1 accepté, 0 refusé.
| Ordre : speed, multiplier, fade, destination, waveform, start, mode, depth.
| Les enums occupent l'octet haut du mot. Destination 127 = désactivée.
| Écriture alignée unique, aucune API/alloc ; contexte créé hors audio.
    .text
    .globl lf2_edit
lf2_edit:
    lea.l %sp@(-4),%sp
    movew %sr,%d0
    movel %d0,%sp@
    moveal %sp@(8),%a0
    movel %sp@(12),%d0
    cmpil #5,%d0
    bhi .Lrefuse
    lsll #4,%d0
    lea.l %a0@(192),%a0
    addal %d0,%a0
    movel %sp@(16),%d0
    cmpil #7,%d0
    bhi .Lrefuse
    lea.l %a0@(0,%d0:l:2),%a0
    movel %sp@(20),%d1
    cmpil #3,%d0
    bne .Lbounded
    cmpil #127,%d1
    beq .Lenum
.Lbounded:
    lea.l .Lmaximum,%a1
    movew %a1@(0,%d0:l:2),%d0
    andil #65535,%d0
    cmpl %d0,%d1
    bhi .Lrefuse
    movel %sp@(16),%d0
    cmpil #1,%d0
    beq .Lenum
    cmpil #3,%d0
    beq .Lenum
    cmpil #4,%d0
    beq .Lenum
    cmpil #6,%d0
    bne .Lwrite
.Lenum:
    lsll #8,%d1
.Lwrite:
    .ifdef LF2_NATIVE_SOUND
    movel %a0,%sp@-
    movel %d1,%sp@-
    movel %d1,%sp@-
    movel %sp@(28),%sp@-
    movel %sp@(28),%sp@-
    jsr lf2n_write
    lea.l %sp@(12),%sp
    movel %sp@+,%d1
    moveal %sp@+,%a0
    .endif
    movew %d1,%a0@
    moveq #1,%d0
    bra .Ldone
.Lrefuse:
    moveq #0,%d0
.Ldone:
    movel %sp@,%d1
    movew %d1,%sr
    lea.l %sp@(4),%sp
    rts
.Lmaximum:
    .word 32767,23,32767,32,6,32767,4,32767
