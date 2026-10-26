| Note 58 : adaptateur privé vers le vrai rendu 0x400423e4.
| Le constructeur MACHINES garde ses 0x500 octets ; la présentation privée
| occupe les 0x600 suivants. Aucun champ du menu LFO primaire n'est modifié.
    .section .text.lp2l_init,"ax"
    .globl lp2l_init
lp2l_init:
    moveal %sp@(4),%a0
    lea.l %a0@(0x500),%a0
    moveal %a0,%a1
    movel #383,%d0
.Lclear:
    clrl %a1@+
    subql #1,%d0
    bpl .Lclear
    movel #lp2l_vt,%d0
    movel %d0,%a0@
    movel #lp2l_title,%d0
    movel %d0,%a0@(148)
    movel #0x40fe3758,%d0
    movel %d0,%a0@(152)
    | +160 attend le descripteur brut, pas un wrapper Font (vptr/data).
    | Mesure 0x40072204 et dessin 0x4007199c lisent ses champs directement.
    movel 0x40ea14d0,%d0
    movel %d0,%a0@(160)
    movel #lp2l_empty,%d0
    movel %d0,%a0@(556)
    rts

    .section .text.lp2l_render,"ax"
    .globl lp2_render
lp2_render:
    lea.l %sp@(-12),%sp
    movem.l %d2/%a2-%a3,%sp@
    moveal %sp@(16),%a2
    lea.l %a2@(0x500),%a2
    movel lf2p_row,%d0
    lea.l lp2l_inverse,%a0
    movel %a0@(0,%d0:l:4),%d2
    subql #1,%d2
    bpl .Lnonnegative
    moveq #0,%d2
.Lnonnegative:
    cmpil #6,%d2
    bls .Lscroll
    moveq #6,%d2
.Lscroll:
    movel %d2,%a2@(20)
    movel %a0@(0,%d0:l:4),%d0
    subl %d2,%d0
    movel %d0,%a2@(24)
    movel lf2p_edit,%d0
    moveb %d0,%a2@(560)
    lea.l %a2@(0x250),%a3
    moveq #0,%d2
    jmp lp2l_widgets
    .section .text.lp2l_widgets,"ax"
lp2l_widgets:
    lea.l lp2l_order,%a0
    movel %a0@(0,%d2:l:4),%d1
    movel %d1,%a3@(12)
    moveq #1,%d0
    movel %d0,%a3@(20)
    lea.l lp2l_label_callbacks,%a0
    movel %a0@(0,%d1:l:4),%d0
    movel %d0,%a3@(24)
    movel %d1,%a3@(44)
    moveq #1,%d0
    movel %d0,%a3@(52)
    movel #lp2_value,%d0
    movel %d0,%a3@(56)
    moveq #0,%d0
    cmpl lf2p_row,%d1
    bne .Lunselected
    movel lf2p_edit,%d0
.Lunselected:
    moveb %d0,%a3@(80)
    lea.l %a3@(84),%a3
    addql #1,%d2
    cmpil #10,%d2
    bcs lp2l_widgets
    movel %sp@(20),%sp@-
    movel %a2,%sp@-
    jsr 0x400423e4
    addql #8,%sp
    movem.l %sp@,%d2/%a2-%a3
    lea.l %sp@(12),%sp
    rts

    .section .text.lp2l_callbacks,"ax"
lp2l_count:
    moveq #10,%d0
    rts
lp2l_visible:
    moveq #4,%d0
    rts
lp2l_widget:
    moveal %sp@(4),%a1
    movel %sp@(8),%d0
    muluw #84,%d0
    lea.l %a1@(0x250),%a1
    addal %d0,%a1
    movel %a1,%a0@
    clrl %a0@(4)
    rts
lp2l_label:
    | Retour std::string possédé : le renderer détruit ce résultat.
    | Un pointeur statique provoquerait le trap du heap à 0x40080282.
    subql #4,%sp
    moveal %sp@(8),%a1
    movel %a1@,%d0
    lea.l lp2l_labels,%a1
    pea %sp@(3)
    movel %a1@(0,%d0:l:4),%sp@-
    movel %a0,%sp@-
    jsr 0x400f980c
    lea.l %sp@(16),%sp
    rts
lp2l_value:
    lea.l %sp@(-16),%sp
    movem.l %d2/%d4/%d6/%a2,%sp@
    moveal %sp@(20),%a0
    movel %a0@,%d2
    movel %sp@(28),%d6
    movel %sp@(36),%d4
    jmp lf2l_value_start

    .section .rodata.lp2l_vt,"a"
    .balign 4
lp2l_vt:
    .long 0,0,0,lp2l_count,lp2l_widget,0,0,0,0,0,0,0,0,0
    .long 0x4007273a,0x40072744,lp2l_visible
    .section .rodata.lp2l_order,"a"
    .balign 4
    .globl lp2l_order,lp2l_inverse
lp2l_order: .long 5,2,4,8,1,3,6,7,0,9
lp2l_inverse: .long 8,4,1,5,2,0,6,7,3,9
lp2l_label_callbacks: .long lp2l_label,lp2l_label,0x40024c7a,lp2l_label,0x40024ca2,0x40024c52,lp2l_label,lp2l_label,0x40024cca,lp2l_label
lp2l_labels: .long lp2l_trk,lp2l_spd,lp2l_mul,lp2l_fad,lp2l_dst,lp2l_wav,lp2l_sph,lp2l_rst,lp2l_dep,lp2l_pol
    .section .rodata.lp2l_strings,"a"
    .balign 4
    .long 5,5,-1
lp2l_title: .asciz "LFO 2"
    .balign 4
    .long 0,0,-1
lp2l_empty: .asciz ""
    .macro label name,text
    .balign 4
    .long 3,3,-1
\name: .asciz "\text"
    .endm
    label lp2l_trk,Trk
    label lp2l_spd,Spd
    label lp2l_mul,Mul
    label lp2l_fad,Fad
    label lp2l_dst,Dst
    label lp2l_wav,Wav
    label lp2l_sph,SPH
#ifdef LFO_WAVE_SAFE
    .balign 4
    .long 4,4,-1
lp2l_rst: .asciz "Mode"
#else
    label lp2l_rst,Rst
#endif
    label lp2l_dep,Dep

.balign 4
.long 4,4,-1
lp2l_pol: .asciz "Pol."
