| Note 58 : initialisation UI avant publication du pointeur audio.
| lf2_init(context,frame) : clone les huit réglages des six LFO natifs,
| phases/buffers vides ; destination OFF et profondeur neutre pour démarrer.
| Ne jamais appeler sur un contexte déjà publié pendant la lecture.
    .text
    .globl lf2_init
lf2_init:
    subql #8,%sp
    movem.l %a2,%sp@
    movew %sr,%d0
    movel %d0,%sp@(4)
    moveal %sp@(12),%a0
    moveal %sp@(16),%a1
    tstl %a0
    beq .Linit_invalid
    tstl %a1
    beq .Linit_invalid
    moveal %a0,%a2
    movel #309,%d0
    moveq #0,%d1
.Linit_clear:
    movel %d1,%a0@+
    subql #1,%d0
    bpl .Linit_clear
    lea.l %a2@(192),%a0
    lea.l %a1@(16),%a1
    moveq #5,%d0
.Linit_track:
    movel %a1@,%d1
    movel %d1,%a0@
    movel %a1@(4),%d1
    movel %d1,%a0@(4)
    movel %a1@(8),%d1
    movel %d1,%a0@(8)
    movel %a1@(12),%d1
    movel %d1,%a0@(12)
    movel #0x7f00,%d1
    movew %d1,%a0@(6)
    movel #16384,%d1
    movew %d1,%a0@(14)
    lea.l %a0@(16),%a0
    lea.l %a1@(66),%a1
    subql #1,%d0
    bpl .Linit_track
    moveq #1,%d0
    bra .Linit_done
.Linit_invalid:
    moveq #0,%d0
.Linit_done:
    movel %sp@(4),%d1
    moveal %sp@,%a2
    addql #8,%sp
    movew %d1,%sr
    rts
