| Adaptateur privé vers le moteur LFO natif : cfg192 -> frame476, LFO0/1.
| frame_prepare(cfg,frame,lfo) exclusivement IPL0 ; zones alignées4/disjointes.
| Vérifier les six jeux avant écriture. Le CC n'est JAMAIS une cible audio :
| cible native fictive11 dans le frame privé, ou OFF127 pour CC128.
| value(state192,lane) : 0..127 depuis delta signé natif, -1 si OFF/invalide.
    .text
    .globl mlcc_frame_prepare,mlcc_value
mlcc_frame_prepare:
    lea.l %sp@(-24),%sp
    moveml %d2-%d5/%a2-%a3,%sp@
    moveq #0,%d0
    movew %sr,%d1
    andil #0x700,%d1
    bne .Lframe_done
    moveal %sp@(28),%a2
    moveal %sp@(32),%a3
    tstl %a2
    beq .Lframe_done
    tstl %a3
    beq .Lframe_done
    movel %a2,%d1
    movel %a3,%d2
    orl %d2,%d1
    andil #3,%d1
    bne .Lframe_done
    movel %a2,%d1
    addil #192,%d1
    bcs .Lframe_done
    movel %a3,%d2
    addil #476,%d2
    bcs .Lframe_done
    cmpl %a3,%d1
    bls .Lframe_disjoint
    cmpl %a2,%d2
    bhi .Lframe_done
.Lframe_disjoint:
    movel %sp@(36),%d5
    cmpil #1,%d5
    bhi .Lframe_done
    lsll #4,%d5
    moveal %a2,%a0
    addal %d5,%a0
    moveq #5,%d3
.Lvalidate_lane:
    lea .Lframe_max,%a1
    moveq #0,%d4
.Lvalidate_field:
    moveq #0,%d1
    movew %a0@(0,%d4:l:2),%d1
    moveq #0,%d2
    movew %a1@(0,%d4:l:2),%d2
    cmpl %d2,%d1
    bhi .Lframe_done
    addql #1,%d4
    cmpil #8,%d4
    bne .Lvalidate_field
    lea %a0@(32),%a0
    subql #1,%d3
    bpl .Lvalidate_lane
    moveal %a3,%a0
    moveq #118,%d1
.Lframe_zero:
    clrl %a0@+
    subql #1,%d1
    bpl .Lframe_zero
    addal %d5,%a2
    lea %a3@(16),%a3
    moveq #5,%d3
.Lframe_lane:
    moveq #0,%d4
.Lframe_field:
    moveq #0,%d1
    movew %a2@(0,%d4:l:2),%d1
    cmpil #3,%d4
    beq .Lframe_cc
    cmpil #1,%d4
    beq .Lframe_enum
    cmpil #4,%d4
    beq .Lframe_enum
    cmpil #6,%d4
    bne .Lframe_word
.Lframe_enum:
    lsll #8,%d1
    bra .Lframe_word
.Lframe_cc:
    cmpil #128,%d1
    beq .Lframe_off
    movel #0x0b00,%d1
    bra .Lframe_word
.Lframe_off:
    movel #0x7f00,%d1
.Lframe_word:
    movew %d1,%a3@(0,%d4:l:2)
    addql #1,%d4
    cmpil #8,%d4
    bne .Lframe_field
    movel #16384,%d1
    movew %d1,%a3@(20)
    lea %a2@(32),%a2
    lea %a3@(66),%a3
    subql #1,%d3
    bpl .Lframe_lane
    moveq #1,%d0
.Lframe_done:
    moveml %sp@,%d2-%d5/%a2-%a3
    lea.l %sp@(24),%sp
    rts
mlcc_value:
    moveq #-1,%d0
    moveal %sp@(4),%a0
    tstl %a0
    beq .Lvalue_done
    movel %a0,%d1
    andil #3,%d1
    bne .Lvalue_done
    movel %sp@(8),%d1
    cmpil #5,%d1
    bhi .Lvalue_done
    lsll #5,%d1
    addal %d1,%a0
    movel %a0@(16),%d1
    cmpil #11,%d1
    bne .Lvalue_done
    movel %a0@(20),%d0
    | Le delta natif est signé ; borner avant addition évite tout overflow.
    cmpil #-16384,%d0
    bge .Lvalue_high
    moveq #0,%d0
    rts
.Lvalue_high:
    cmpil #16128,%d0
    ble .Lvalue_center
    moveq #127,%d0
    rts
.Lvalue_center:
    addil #16384,%d0
    lsrl #8,%d0
.Lvalue_done:
    rts
    .balign 2
.Lframe_max: .word 32767,23,32767,128,6,32767,4,32767

| Réamorcer seulement les six cibles fictives avant chaque bloc natif.
| Le moteur écrit son résultat dans ces mots ; sans remise à zéro, la
| modulation s'accumulerait. Appel IRQ borné, aucune allocation ni MIDI.
| mlcc_frame_reset(frame476) : d0=1 si pointeur aligné et sans débordement.
    .text
    .globl mlcc_frame_reset
mlcc_frame_reset:
    moveq #0,%d0
    moveal %sp@(4),%a0
    tstl %a0
    beq .Lreset_done
    movel %a0,%d1
    andil #3,%d1
    bne .Lreset_done
    movel %a0,%d1
    addil #476,%d1
    bcs .Lreset_done
    movew #16384,%a0@(36)
    movew #16384,%a0@(102)
    movew #16384,%a0@(168)
    movew #16384,%a0@(234)
    movew #16384,%a0@(300)
    movew #16384,%a0@(366)
    moveq #1,%d0
.Lreset_done:
    rts
