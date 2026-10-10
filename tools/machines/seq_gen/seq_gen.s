| Générateur de notes : aucune écriture dans le pattern avant validation.
| sg_generate(a0=config, a1=sortie 64 octets) -> d0=nombre de trigs, -1 si invalide.
| config : 7 longs BE {longueur, densité, note_min, note_max, gamme, tonalité, graine}.
| Gammes identiques à Model-TG : OFF (chromatique), MAJ, MIN, DOR, PENTA.
| Sortie : note MIDI ou 255 (repos). Seuls longueur octets sont écrits.
| Garde d2-d7/a2-a6 ; d0-d1/a0-a1 détruits. Aucun appel OS, aucun état global.
| La graine n'est avancée que si la configuration est valide.
    .section .text.sg_generate,"ax"
    .globl sg_generate
sg_generate:
    lea.l %sp@(-168),%sp
    movem.l %d2-%d7/%a2-%a5,%sp@
    movea.l %a0,%a2
    movea.l %a1,%a3
    moveq #-1,%d0
    movel %a2@,%d2
    cmpil #1,%d2
    bltw sg_exit
    cmpil #64,%d2
    bgtw sg_exit
    movel %a2@(4),%d1
    cmpil #100,%d1
    bhiw sg_exit
    movel %a2@(8),%d3
    cmpil #127,%d3
    bhiw sg_exit
    movel %a2@(12),%d4
    cmpil #127,%d4
    bhiw sg_exit
    cmpl %d3,%d4
    bltw sg_exit
    movel %a2@(16),%d1
    cmpil #4,%d1
    bhiw sg_exit
    movel %a2@(20),%d1
    cmpil #11,%d1
    bhiw sg_exit
    lea.l %sp@(40),%a4
    moveq #0,%d5
    lea.l sg_masks,%a0
    movel %a2@(16),%d1
    movel %a0@(0,%d1:l:4),%d6
sg_notes:
    movel %d3,%d0
    addil #12,%d0
    subl %a2@(20),%d0
    divuw #12,%d0
    swap %d0
    andil #65535,%d0
    btst %d0,%d6
    beqs sg_next_note
    moveb %d3,%a4@(0,%d5:l)
    addql #1,%d5
sg_next_note:
    addql #1,%d3
    cmpl %d4,%d3
    bles sg_notes
    moveq #-1,%d0
    tstl %d5
    beqs sg_exit
    movel %a2@(24),%d7
    bnes sg_seed_ok
    movel #0x6d2b79f5,%d7
sg_seed_ok:
    moveq #0,%d3
    moveq #0,%d4
sg_steps:
    bsrw sg_random
    divuw #100,%d0
    swap %d0
    andil #65535,%d0
    moveq #-1,%d1
    cmpl %a2@(4),%d0
    bccs sg_store
    bsrw sg_random
    divuw %d5,%d0
    swap %d0
    andil #65535,%d0
    moveq #0,%d1
    moveb %a4@(0,%d0:l),%d1
    addql #1,%d4
sg_store:
    moveb %d1,%a3@(0,%d3:l)
    addql #1,%d3
    cmpl %d2,%d3
    blts sg_steps
    movel %d7,%a2@(24)
    movel %d4,%d0
sg_exit:
    movem.l %sp@,%d2-%d7/%a2-%a5
    lea.l %sp@(168),%sp
    rts

    .section .text.sg_random,"ax"
sg_random:
    movel %d7,%d0
    moveq #13,%d1
    lsll %d1,%d0
    eorl %d0,%d7
    movel %d7,%d0
    moveq #17,%d1
    lsrl %d1,%d0
    eorl %d0,%d7
    movel %d7,%d0
    lsll #5,%d0
    eorl %d0,%d7
    movel %d7,%d0
    andil #32767,%d0
    rts

    .section .rodata.sg_masks,"a"
sg_masks:
    .long 0xfff,0xab5,0x5ad,0x6ad,0x295
