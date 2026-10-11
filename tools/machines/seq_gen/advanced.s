| Extension expérimentale, notes/54. Aucune exécution dans l'interruption audio.
    .ifdef SG_ADVANCED
    .globl sg_advanced_edit,sg_advanced_value,sg_advanced_steps,sg_random_range
    .section .text.sg_advanced_edit,"ax"
sg_advanced_edit:
    movel %d2,%d0
    subql #5,%d0
    lea.l sg_fields,%a1
    lsll #4,%d0
    addal %d0,%a1
    moveal %a1@,%a0
    movel %a0@,%d0
    addl %d3,%d0
    cmpl %a1@(4),%d0
    bltw sme_out
    cmpl %a1@(8),%d0
    bgtw sme_out
    movel %a1@(12),%d1
    beqs sae_store
    moveal %d1,%a1
    | Les minima sont aux lignes paires 6, 9, 12 (trois paires).
    cmpil #6,%d2
    beqs sae_min
    cmpil #9,%d2
    beqs sae_min
    cmpil #12,%d2
    beqs sae_min
    cmpl %a1@,%d0
    bltw sme_out
    bras sae_store
sae_min:
    cmpl %a1@,%d0
    bgtw sme_out
sae_store:
    movel %d0,%a0@
    braw sme_redraw

    .section .text.sg_advanced_value,"ax"
sg_advanced_value:
    movel %d3,%d0
    subql #5,%d0
    lsll #4,%d0
    lea.l sg_fields,%a0
    moveal %a0@(0,%d0:l),%a0
    movel %a0@,%d0
    cmpil #5,%d3
    beqs sav_bool
    cmpil #8,%d3
    beqs sav_bool
    cmpil #11,%d3
    beqs sav_bool
    cmpil #14,%d3
    beqs sav_target
    cmpil #16,%d3
    beqs sav_rhythm
    braw smr_num
sav_bool:
    lea.l sg_bool_names,%a0
    bras sav_string
sav_target:
    lea.l sg_target_names,%a0
    bras sav_string
sav_rhythm:
    lea.l sg_rhythm_names,%a0
sav_string:
    moveal %a0@(0,%d0:l:4),%a2
    braw smr_string

    .section .rodata.sg_fields,"a"
sg_fields:
    .long sg_options,0,1,0
    .long sg_advanced,1,127,sg_advanced+4
    .long sg_advanced+4,1,127,sg_advanced
    .long sg_options+4,0,1,0
    .long sg_advanced+8,0,127,sg_advanced+12
    .long sg_advanced+12,0,127,sg_advanced+8
    .long sg_options+8,0,1,0
    .long sg_advanced+16,0,127,sg_advanced+20
    .long sg_advanced+20,0,127,sg_advanced+16
    .long sg_advanced+24,0,2,0
    .long sg_advanced+28,0,100,0
    .long sg_advanced+32,0,1,0
    .long sg_advanced+36,0,64,0
    .long sg_advanced+40,0,63,0
    .long sg_advanced+44,0,100,0

    .section .rodata.sg_enums,"a"
sg_bool_names: .long sg_off,sg_on
sg_target_names: .long sg_both,sg_rhythm_only,sg_notes_only
sg_rhythm_names: .long sg_random_text,sg_euclid
sg_both: .asciz "Both"
sg_rhythm_only: .asciz "Rhythm"
sg_notes_only: .asciz "Notes"
sg_random_text: .asciz "Random"
sg_euclid: .asciz "Euclid"

    .section .text.sg_random_range,"ax"
| d0=aléa 0..32767, a0={min,max}, résultat inclusif.
sg_random_range:
    movel %a0@(4),%d1
    subl %a0@,%d1
    addql #1,%d1
    divuw %d1,%d0
    swap %d0
    andil #65535,%d0
    addl %a0@,%d0
    rts

    .section .text.sg_advanced_steps,"ax"
| a0=données OS, a1=candidats, d0=longueur ; 254 signifie conserver le pas.
| Préserve d2-d7/a2-a4. Ne modifie que les candidats et la graine.
sg_advanced_steps:
    lea.l %sp@(-36),%sp
    movem.l %d2-%d7/%a2-%a4,%sp@
    moveal %a0,%a2
    moveal %a1,%a3
    movel %d0,%d4
    moveq #0,%d2
    movel sg_config+24,%d7
sas_loop:
    jsr sg_random
    divuw #100,%d0
    swap %d0
    andil #65535,%d0
    cmpl sg_advanced+28,%d0
    bccw sas_keep
    moveq #0,%d3
    moveb %a3@(0,%d2:l),%d3
    movew %a2@(0,%d2:l:2),%d5
    movel sg_advanced+24,%d1
    cmpil #2,%d1
    beqw sas_notes
    tstl sg_advanced+32
    beqw sas_rhythm
    jmp sas_euclid
    .section .text.sg_euclid,"ax"
sas_euclid:
    movel sg_advanced+36,%d6
    cmpl %d4,%d6
    bles sas_hits
    movel %d4,%d6
sas_hits:
    movel sg_advanced+40,%d0
    divuw %d4,%d0
    swap %d0
    andil #65535,%d0
    movel %d2,%d1
    addl %d4,%d1
    subl %d0,%d1
    muluw %d6,%d1
    divuw %d4,%d1
    swap %d1
    andil #65535,%d1
    cmpl %d6,%d1
    bcsw sas_rhythm
    movel #255,%d3
sas_rhythm:
    movel sg_advanced+24,%d1
    cmpil #1,%d1
    bnew sas_store
    btst #0,%d5
    beqw sas_store
    cmpil #255,%d3
    beqw sas_store
    moveq #0,%d3
    lea.l %a2@(580),%a0
    moveb %a0@(0,%d2:l),%d3
    braw sas_store
sas_notes:
    btst #0,%d5
    beqw sas_keep
    braw sas_store
sas_keep:
    movel #254,%d3
sas_store:
    moveb %d3,%a3@(0,%d2:l)
    addql #1,%d2
    cmpl %d4,%d2
    bltw sas_loop
    movel %d7,sg_config+24
    movem.l %sp@,%d2-%d7/%a2-%a4
    lea.l %sp@(36),%sp
    rts
    .endif
