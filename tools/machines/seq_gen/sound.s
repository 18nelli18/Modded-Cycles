| Action distincte : cinq paramètres du son, sans pitch, niveau, FX ou machine.
| Descripteurs actifs consultés via l'OS : bornes de SY BITS/MACRO comprises.
    .ifdef SG_ADVANCED
    .globl sg_sound_generate,sg_sound_undo,sg_sound_valid
    .section .data.sg_sound,"aw"
sg_sound_valid: .long 0
    .section .text.sg_sound_current,"ax"
sg_sound_current:
    jsr 0x400cf866
    moveal %d0,%a2
    pea %a2@(48)
    jsr 0x40012412
    addql #4,%sp
    cmpil #5,%d0
    bhiw ssc_fail
    muluw #68,%d0
    lea.l %a2@(212),%a2
    addal %d0,%a2
    movel %a2,%sp@-
    moveal %a2@,%a0
    moveal %a0@(40),%a0
    jsr %a0@
    addql #4,%sp
    rts
ssc_fail:
    moveq #0,%d0
    rts

    .section .text.sg_sound_generate,"ax"
sg_sound_generate:
    lea.l %sp@(-56),%sp
    movem.l %d2-%d7/%a2-%a5,%sp@
    clrl sg_error
    tstl 0x40a78874
    bnew ssg_fail
    tstl 0x40a7883c
    bnew ssg_fail
    tstl sg_advanced+44
    beqw ssg_out
    jsr sg_sound_current
    tstl %d0
    beqw ssg_fail
    moveal %d0,%a3
    moveq #0,%d6
    moveb %a3@(38),%d6
    cmpil #6,%d6             | Sampler : ne pas toucher au sample et à ses modes
    beqw ssg_fail
    moveal sg_obj,%a4
    lea.l %a4@(5408),%a5
    moveq #0,%d2
    movel sg_config+24,%d7
    jmp ssg_loop
    .section .text.sg_sound_values,"ax"
ssg_loop:
    movel %d2,%d3
    addil #11,%d3
    cmpil #4,%d2
    bnes ssg_slot
    moveq #18,%d3
ssg_slot:
    movel %d6,%sp@-
    movel %d3,%sp@-
    jsr 0x4005a692
    addql #8,%sp
    tstl %d0
    beqw ssg_fail
    movel %d0,%sp@-
    lea.l %sp@(44),%a0       | résultat ABI caché : {min,max,défaut}, scratch 12 o
    jsr 0x4005a65a
    addql #4,%sp
    | Seulement les domaines entiers non négatifs qui tiennent en 7 bits.
    movel %sp@(40),%d4
    movel %sp@(44),%d5
    tstl %d4
    bmiw ssg_fail
    cmpil #32512,%d5
    bgtw ssg_fail
    cmpl %d4,%d5
    bltw ssg_fail
    lsrl #8,%d4
    lsrl #8,%d5
    movel %d4,%sp@(40)
    movel %d5,%sp@(44)
    jsr sg_random
    lea.l %sp@(40),%a0
    jsr sg_random_range
    moveq #0,%d1
    movew %a3@(20,%d3:l:2),%d1
    lsrl #8,%d1
    cmpl %sp@(40),%d1
    bgew ssg_old_min
    movel %sp@(40),%d1
ssg_old_min:
    cmpl %sp@(44),%d1
    blew ssg_old_max
    movel %sp@(44),%d1
ssg_old_max:
    subl %d1,%d0
    movel sg_advanced+44,%d4
    mulsw %d4,%d0
    divsw #100,%d0
    extl %d0
    addl %d1,%d0
    lsll #8,%d0
    movel %d3,%a5@(0,%d2:l:8)
    movew %d0,%a5@(4,%d2:l:8)
    addql #1,%d2
    cmpil #5,%d2
    bltw ssg_loop
    jmp ssg_commit
    .section .text.sg_sound_commit,"ax"
ssg_commit:
    | Toutes les valeurs sont prêtes avant le snapshot et la première écriture.
    moveq #0,%d2
ssg_save:
    movel %a5@(0,%d2:l:8),%d3
    movew %a3@(20,%d3:l:2),%d0
    lea.l %a4@(5456),%a0
    movel %d3,%a0@(0,%d2:l:8)
    movew %d0,%a0@(4,%d2:l:8)
    addql #1,%d2
    cmpil #5,%d2
    blts ssg_save
    movel %a2,%a4@(5500)
    movel %a3,%a4@(5504)
    movel %d6,%a4@(5508)
    moveq #1,%d0
    movel %d0,sg_sound_valid
    movel %d7,sg_config+24
    jsr sg_sound_apply
    bras ssg_out
ssg_fail:
    moveq #1,%d0
    movel %d0,sg_error
ssg_out:
    movem.l %sp@,%d2-%d7/%a2-%a5
    lea.l %sp@(56),%sp
    rts

    .section .text.sg_sound_undo,"ax"
sg_sound_undo:
    lea.l %sp@(-56),%sp
    movem.l %d2-%d7/%a2-%a5,%sp@
    tstl 0x40a78874
    bnew ssg_out
    tstl 0x40a7883c
    bnew ssg_out
    tstl sg_sound_valid
    beqw ssg_out
    jsr sg_sound_current
    moveal sg_obj,%a4
    cmpal %a4@(5500),%a2
    bnew ssg_out
    cmpl %a4@(5504),%d0
    bnew ssg_out
    moveal %d0,%a3
    moveq #0,%d0
    moveb %a3@(38),%d0
    cmpl %a4@(5508),%d0
    bnew ssg_out
    lea.l %a4@(5456),%a5
    jsr sg_sound_apply
    clrl sg_sound_valid
    braw ssg_out

    .section .text.sg_sound_apply,"ax"
sg_sound_apply:
    lea.l %sp@(-12),%sp
    movel %a5,%sp@
    lea.l %a5@(40),%a0
    movel %a0,%sp@(4)
    movel %sp,%a0
    movel %a0,%sp@-
    movel %a2,%sp@-
    jsr 0x4001416c           | vrai setter OS par lot et notification globale
    addql #8,%sp
    lea.l %sp@(12),%sp
    rts
    .endif
