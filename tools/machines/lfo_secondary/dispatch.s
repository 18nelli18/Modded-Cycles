| Note 58 : remplacement de l'appel LFO 0x400597c6, même ABI trois arguments.
| Contexte alloué/initialisé par l'UI, jamais ici ; pointeur nul = chemin natif.
| 1240 octets : états 192, réglages 96, base 476, copie LFO 2 476.
    .data
    .globl lf2_context
lf2_context: .long 0
    .text
    .globl lf2_dispatch
lf2_dispatch:
    lea.l %sp@(-28),%sp
    movem.l %d2-%d4/%a2-%a5,%sp@
    movel %sp@(32),%d2
    movel %sp@(36),%d3
    movel %sp@(40),%d4
    moveal lf2_context,%a2
    tstl %a2
    beq .Lnative
    lea.l %a2@(288),%a3
    lea.l %a2@(764),%a4
    moveal %d2,%a0
    moveal %a3,%a1
    .ifdef LF2_NATIVE_SOUND
    jsr lf2n_copy_frame
    .else
    bsr lf2_copy_frame
    .endif
.Lnative:
    movel %d4,%sp@-
    movel %d3,%sp@-
    movel %d2,%sp@-
    jsr 0x40091ab2
    lea.l %sp@(12),%sp
    tstl %a2
    beq .Ldone
    moveal %a3,%a0
    moveal %a4,%a1
    bsr lf2_copy_frame
    lea.l %a2@(192),%a5
    lea.l %a4@(16),%a0
    moveq #5,%d0
.Lsettings:
    movel %a5@+,%d1
    movel %d1,%a0@
    movel %a5@+,%d1
    movel %d1,%a0@(4)
    movel %a5@+,%d1
    movel %d1,%a0@(8)
    movel %a5@+,%d1
    movel %d1,%a0@(12)
    lea.l %a0@(66),%a0
    subql #1,%d0
    bpl .Lsettings
    movel %a2,%sp@-
    movel %d4,%sp@-
    movel %d3,%sp@-
    movel %a4,%sp@-
    jsr lf2_update
    lea.l %sp@(16),%sp
    movel %a2,%sp@-
    pea 0x40fde838
    pea 238
    movel %a3,%sp@-
    movel %d2,%sp@-
    jsr lf2_mix
    lea.l %sp@(20),%sp
.Ldone:
    movem.l %sp@,%d2-%d4/%a2-%a5
    lea.l %sp@(28),%sp
    rts
    .globl lf2_copy_frame
lf2_copy_frame:
    movel #118,%d0
.Lcopy_frame:
    movel %a0@+,%d1
    movel %d1,%a1@+
    subql #1,%d0
    bpl .Lcopy_frame
    rts
