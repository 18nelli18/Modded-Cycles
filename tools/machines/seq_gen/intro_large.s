| Cartouche 120×56 à coins arrondis, caractères originaux 5×7 agrandis ×2.
    .ifdef SG_SEQUENCE_ONLY
    .globl sg_large_intro
    .section .text.sg_large_intro,"ax"
sg_large_intro:
    lea.l %sp@(-40),%sp
    movem.l %d2-%d7/%a2-%a5,%sp@
    movel %sp@(48),%d2
    clrl %sp@-
    pea 63
    pea 127
    clrl %sp@-
    clrl %sp@-
    movel %d2,%sp@-
    jsr 0x40070dea
    lea.l %sp@(24),%sp
    lea.l sg_round_bands,%a2
    moveq #4,%d3
sgli_band:
    pea -1
    moveq #0,%d0
    moveb %a2@+,%d0
    movel %d0,%sp@-
    moveb %a2@+,%d0
    movel %d0,%sp@-
    moveb %a2@+,%d0
    movel %d0,%sp@-
    moveb %a2@+,%d0
    movel %d0,%sp@-
    movel %d2,%sp@-
    jsr 0x40070dea
    lea.l %sp@(24),%sp
    subql #1,%d3
    bplw sgli_band
    lea.l sg_large_letters,%a2
    lea.l %a2@(56),%a3
    moveal #17,%a4
    moveq #49,%d7
    jsr sgli_line
    lea.l %a2@(35),%a3
    moveal #35,%a4
    moveq #27,%d7
    jsr sgli_line
    movem.l %sp@,%d2-%d7/%a2-%a5
    lea.l %sp@(40),%sp
    rts
    .section .text.sg_large_letters,"ax"
sgli_line:
    moveq #0,%d3
sgli_letter:
    moveq #0,%d4
sgli_row:
    moveq #0,%d5
    moveq #0,%d6
    moveb %a2@+,%d6
sgli_pixel:
    moveq #4,%d0
    subl %d5,%d0
    btst %d0,%d6
    beqw sgli_skip
    movel %d3,%d0
    muluw #12,%d0
    addl %a4,%d0
    movel %d5,%d1
    muluw #2,%d1
    addl %d1,%d0
    movel %d4,%d1
    muluw #2,%d1
    negl %d1
    addl %d7,%d1
    jsr sgli_white
sgli_skip:
    addql #1,%d5
    cmpil #5,%d5
    bltw sgli_pixel
    addql #1,%d4
    cmpil #7,%d4
    bltw sgli_row
    addql #1,%d3
    cmpal %a3,%a2
    bcsw sgli_letter
    rts
    .section .text.sg_large_white,"ax"
sgli_white:
    clrl %sp@-
    addql #1,%d1
    movel %d1,%sp@-
    addql #1,%d0
    movel %d0,%sp@-
    subql #1,%d1
    movel %d1,%sp@-
    subql #1,%d0
    movel %d0,%sp@-
    movel %d2,%sp@-
    jsr 0x40070dea
    lea.l %sp@(24),%sp
    rts
    .section .rodata.sg_large_intro,"a"
| Chaque bande : top, right, bottom, left ; aucun recouvrement inversé.
sg_round_bands:
    .byte 5,119,4,8, 7,121,6,6, 55,123,8,4, 57,121,56,6, 59,119,58,8
sg_large_letters:
    .byte 15,16,16,14,1,1,30
    .byte 31,16,16,30,16,16,31
    .byte 14,17,17,17,21,18,13
    .byte 17,17,17,17,17,17,14
    .byte 31,16,16,30,16,16,31
    .byte 17,25,25,21,19,19,17
    .byte 14,17,16,16,16,17,14
    .byte 31,16,16,30,16,16,31
    .byte 14,17,16,23,17,17,14
    .byte 31,16,16,30,16,16,31
    .byte 17,25,25,21,19,19,17
    .byte 31,4,4,4,4,4,31
    .byte 31,16,16,30,16,16,31
    .endif
