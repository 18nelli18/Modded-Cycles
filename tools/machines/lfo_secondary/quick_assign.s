| Geste LFO2 + potard : même table de boutons et delta que le LFO natif.
| lf2p_quick_assign(index0..11, delta) -> 1 accepté. Aucun réglage LFO1 écrit.
    .section .text.lf2p_quick_map,"ax"
    .globl lf2p_quick_assign
lf2p_quick_assign:
    lea.l %sp@(-12),%sp
    moveml %d2-%d4,%sp@
    movel %sp@(16),%d2
    cmpil #11,%d2
    bhi .Lqa_fail
    tstl lf2_context
    beq .Lqa_fail
    pea 1
    jsr 0x4004df5c
    addql #4,%sp
    moveal %d0,%a0
    movel %a0@(8,%d2:l:4),%sp@-
    jsr 0x4005a4e8
    addql #4,%sp
    movel %d0,%d4
    cmpil #32,%d4
    bhi .Lqa_fail
    moveal lf2_context,%a0
    movel lf2p_track,%d2
    cmpil #5,%d2
    bhi .Lqa_fail
    lsll #4,%d2
    lea.l %a0@(192),%a0
    addal %d2,%a0
    moveq #0,%d0
    movew %a0@(6),%d0
    lsrl #8,%d0
    cmpl %d4,%d0
    beq .Lqa_depth
    movel %d4,%sp@-
    pea 3
    bra .Lqa_write
    .section .text.lf2p_quick_depth,"ax"
.Lqa_depth:
    moveq #0,%d0
    movew %a0@(14),%d0
    movel %sp@(20),%d3
    cmpil #32767,%d3
    bgt .Lqa_max
    cmpil #-32768,%d3
    blt .Lqa_min
    lsll #8,%d3
    addl %d3,%d0
    bmi .Lqa_min
    cmpil #32767,%d0
    ble .Lqa_value
.Lqa_max:
    movel #32767,%d0
    bra .Lqa_value
.Lqa_min:
    moveq #0,%d0
.Lqa_value:
    movel %d0,%sp@-
    pea 7
.Lqa_write:
    movel lf2p_track,%sp@-
    movel lf2_context,%sp@-
    jsr lf2_edit
    lea.l %sp@(16),%sp
    tstl %d0
    beq .Lqa_fail
    moveq #1,%d0
    movel %d0,lf2p_assigned
    moveq #8,%d1
    movel %d1,lf2p_row
    bra .Lqa_out
.Lqa_fail:
    moveq #0,%d0
.Lqa_out:
    moveml %sp@,%d2-%d4
    lea.l %sp@(12),%sp
    rts
