| Note 58 : adaptateur privé vers le vrai rendu 0x400423e4.
| Le constructeur MACHINES garde ses 0x500 octets ; la présentation privée
| occupe les 0x600 suivants. Aucun champ du menu LFO primaire n'est modifié.
    .section .text.lf2l_init,"ax"
    .globl lf2l_init
lf2l_init:
    moveal %sp@(4),%a0
    lea.l %a0@(0x500),%a0
    moveal %a0,%a1
    movel #383,%d0
.Lclear:
    clrl %a1@+
    subql #1,%d0
    bpl .Lclear
    movel #lf2l_vt,%d0
    movel %d0,%a0@
    movel #lf2l_title,%d0
    movel %d0,%a0@(148)
    movel #0x40fe3758,%d0
    movel %d0,%a0@(152)
    lea.l %a0@(512),%a1
    movel %a1,%a0@(160)
    movel #0x401117e0,%d0
    movel %d0,%a1@
    movel 0x40ea14d0,%d0
    movel %d0,%a1@(4)
    movel #lf2l_empty,%d0
    movel %d0,%a0@(556)
    rts

    .section .text.lf2l_render,"ax"
    .globl lf2p_render
lf2p_render:
    lea.l %sp@(-12),%sp
    movem.l %d2/%a2-%a3,%sp@
    moveal %sp@(16),%a2
    lea.l %a2@(0x500),%a2
    movel lf2p_row,%d0
    lea.l lf2l_inverse,%a0
    movel %a0@(0,%d0:l:4),%d2
    subql #1,%d2
    bpl .Lnonnegative
    moveq #0,%d2
.Lnonnegative:
    cmpil #5,%d2
    bls .Lscroll
    moveq #5,%d2
.Lscroll:
    movel %d2,%a2@(20)
    movel %a0@(0,%d0:l:4),%d0
    subl %d2,%d0
    movel %d0,%a2@(24)
    movel lf2p_edit,%d0
    moveb %d0,%a2@(560)
    lea.l %a2@(0x250),%a3
    moveq #0,%d2
    jmp lf2l_widgets
    .section .text.lf2l_widgets,"ax"
lf2l_widgets:
    lea.l lf2l_order,%a0
    movel %a0@(0,%d2:l:4),%d1
    movel %d1,%a3@(12)
    moveq #1,%d0
    movel %d0,%a3@(20)
    movel #lf2l_label,%d0
    movel %d0,%a3@(24)
    movel %d1,%a3@(44)
    moveq #1,%d0
    movel %d0,%a3@(52)
    movel #lf2l_value,%d0
    movel %d0,%a3@(56)
    moveq #0,%d0
    cmpl lf2p_row,%d1
    bne .Lunselected
    movel lf2p_edit,%d0
.Lunselected:
    moveb %d0,%a3@(80)
    lea.l %a3@(84),%a3
    addql #1,%d2
    cmpil #9,%d2
    bcs lf2l_widgets
    movel %sp@(20),%sp@-
    movel %a2,%sp@-
    jsr 0x400423e4
    addql #8,%sp
    movem.l %sp@,%d2/%a2-%a3
    lea.l %sp@(12),%sp
    rts

    .section .text.lf2l_callbacks,"ax"
lf2l_count:
    moveq #9,%d0
    rts
lf2l_visible:
    moveq #4,%d0
    rts
lf2l_widget:
    moveal %sp@(4),%a1
    movel %sp@(8),%d0
    muluw #84,%d0
    lea.l %a1@(0x250),%a1
    addal %d0,%a1
    movel %a1,%a0@
    clrl %a0@(4)
    rts
lf2l_label:
    moveal %sp@(4),%a1
    movel %a1@,%d0
    lea.l lf2l_labels,%a1
    movel %a1@(0,%d0:l:4),%a0@
    rts
lf2l_value:
    lea.l %sp@(-16),%sp
    movem.l %d2/%d4/%d6/%a2,%sp@
    moveal %sp@(20),%a0
    movel %a0@,%d2
    movel %sp@(28),%d6
    movel %sp@(36),%d4
    jmp lf2l_value_start

    .section .rodata.lf2l_vt,"a"
    .balign 4
lf2l_vt:
    .long 0,0,0,lf2l_count,lf2l_widget,0,0,0,0,0,0,0,0,0
    .long 0x4007273a,0x40072744,lf2l_visible
    .section .rodata.lf2l_order,"a"
    .balign 4
    .globl lf2l_order,lf2l_inverse
lf2l_order: .long 5,2,4,8,1,3,6,7,0
lf2l_inverse: .long 8,4,1,5,2,0,6,7,3
lf2l_labels: .long lf2l_trk,lf2l_spd,lf2l_mul,lf2l_fad,lf2l_dst,lf2l_wav,lf2l_sph,lf2l_rst,lf2l_dep
    .section .rodata.lf2l_strings,"a"
    .balign 4
    .long 5,5,-1
lf2l_title: .asciz "LFO 2"
    .balign 4
    .long 0,0,-1
lf2l_empty: .asciz ""
    .macro label name,text
    .balign 4
    .long 3,3,-1
\name: .asciz "\text"
    .endm
    label lf2l_trk,Trk
    label lf2l_spd,Spd
    label lf2l_mul,Mul
    label lf2l_fad,Fad
    label lf2l_dst,Dst
    label lf2l_wav,Wav
    label lf2l_sph,SPH
    label lf2l_rst,Rst
    label lf2l_dep,Dep
