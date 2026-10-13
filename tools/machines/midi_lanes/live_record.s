| Live-rec B : notes/clavier/pads, horloge privée de chaque voie.
| on(lane,paquet) ; off(lane). UI uniquement ; aucun appel MIDI/disque.
| flags du pas : bits0/1 trig/slide, bits2..7 retard0..63/64 de pas.
| Pending24 par voie : propriétaire,pas,heure,durée,paquet,note attendue.
    .data
    .balign 4
.Lpending: .space 144
    .text
    .globl mllr_on,mllr_off,mllr_cancel
mllr_on:
    lea %sp@(-32),%sp
    moveml %d2-%d5/%a2-%a5,%sp@
    movew %sr,%d0
    andil #0x700,%d0
    bne .Lon_done
    movel %sp@(36),%d2
    cmpil #5,%d2
    bhi .Lon_done
    movel %sp@(40),%d0
    andil #0xf0808000,%d0
    cmpil #0x90000000,%d0
    bne .Lon_done
    movel %sp@(40),%d0
    andil #0x7f00,%d0
    beq .Lon_done
    | Une nouvelle touche termine la durée de la précédente sur cette voie.
    movel %d2,%sp@-
    jsr mllr_off
    addql #4,%sp
    jsr mllr_mode
    tstl %d0
    beq .Lon_done
    movel %d0,%d5
    moveal ml_clock_state,%a0
    tstl %a0
    beq .Lon_done
    moveal ml_pattern,%a2
    tstl %a2
    beq .Lon_done
    cmpal ml_play_pattern,%a2
    bne .Lon_done
    movel %d2,%d0
    muluw #264,%d0
    lea %a2@(0,%d0:l),%a3
    moveq #0,%d0
    moveb %a3@(5),%d0
    cmpil #6,%d0
    bhi .Lon_done
    lea ml_clock_durations,%a1
    movel %a1@(0,%d0:l:4),%d4
    movel %d2,%d0
    lsll #3,%d0
    lea %a0@(4,%d0:l),%a1
    | Snapshot court : deadline/step/heure appartiennent à l'audio.
    movew %sr,%d1
    movel %d1,%sp@-
    movew #0x2700,%sr
    movel %a0@,%d1
    movel %a1@,%d3
    movel %a1@(4),%d0
    movel 0x8000184c,%a4
    movel %sp@+,%a0
    movel %d0,%sp@-
    movel %a0,%d0
    movew %d0,%sr
    movel %sp@+,%d0
    cmpil #1,%d1
    bne .Lon_done
    moveq #0,%d1
    moveb %a3@(4),%d1
    subql #1,%d1
    cmpil #63,%d1
    bhi .Lon_done
    subql #1,%d0
    bpl .Lon_previous
    movel %d1,%d0
.Lon_previous:
    cmpl %d1,%d0
    bhi .Lon_done
    subl %d4,%d3
    movel %a4,%d1
    subl %d3,%d1
    bmi .Lon_done
    cmpl %d4,%d1
    bcs .Lon_phase_ready
    subl %d4,%d1
    addql #1,%d0
    moveq #0,%d3
    moveb %a3@(4),%d3
    cmpl %d3,%d0
    bcs .Lon_phase_bound
    moveq #0,%d0
.Lon_phase_bound:
    cmpl %d4,%d1
    bcc .Lon_done
.Lon_phase_ready:
    cmpil #1,%d5
    bne .Lon_unquantized
    movel %d4,%d3
    lsrl #1,%d3
    cmpl %d3,%d1
    bcs .Lon_quantized
    addql #1,%d0
    moveq #0,%d1
    moveb %a3@(4),%d1
    cmpl %d1,%d0
    bcs .Lon_quantized
    moveq #0,%d0
.Lon_quantized:
    moveq #0,%d3
    bra .Lon_index
.Lon_unquantized:
    lsll #6,%d1
    divul %d4,%d1
    movel %d1,%d3
    lsll #2,%d3
.Lon_index:
    lsll #2,%d0
    lea %a3@(8,%d0:l),%a3
    movel %d2,%d0
    muluw #24,%d0
    lea .Lpending,%a5
    addal %d0,%a5
    movel %sp@(40),%d0
    movel %d0,%a5@(16)
    lsll #8,%d0
    andil #0xffff0000,%d0
    oril #0x101,%d0
    orl %d3,%d0
    | Le nouveau pas complet est publié en une écriture atomique.
    movel %d0,%a3@
    movel %a2,%a5@
    movel %a3,%a5@(4)
    movel %a4,%a5@(8)
    movel %d4,%a5@(12)
    movel %d0,%a5@(20)
.Lon_done:
    moveml %sp@,%d2-%d5/%a2-%a5
    lea %sp@(32),%sp
    rts
mllr_off:
    lea %sp@(-16),%sp
    moveml %d2/%a2-%a4,%sp@
    movew %sr,%d0
    andil #0x700,%d0
    bne .Loff_done
    movel %sp@(20),%d0
    cmpil #5,%d0
    bhi .Loff_done
    muluw #24,%d0
    lea .Lpending,%a2
    addal %d0,%a2
    moveal %a2@,%a3
    clrl %a2@
    tstl %a3
    beq .Loff_done
    cmpal ml_pattern,%a3
    bne .Loff_done
    cmpal ml_play_pattern,%a3
    bne .Loff_done
    moveal ml_clock_state,%a0
    tstl %a0
    beq .Loff_done
    movel %a0@,%d0
    cmpil #1,%d0
    bne .Loff_done
    moveal %a2@(4),%a4
    movel %a4@,%d0
    andil #0xffff00ff,%d0
    movel %a2@(20),%d1
    andil #0xffff00ff,%d1
    cmpl %d1,%d0
    bne .Loff_done
    movel 0x8000184c,%d0
    subl %a2@(8),%d0
    bmi .Loff_done
    movel %a2@(12),%d1
    beq .Loff_done
    addl %d1,%d0
    subql #1,%d0
    divul %d1,%d0
    tstl %d0
    bne .Loff_bound
    moveq #1,%d0
.Loff_bound:
    cmpil #64,%d0
    bls .Loff_store
    moveq #64,%d0
.Loff_store:
    moveb %d0,%a4@(2)
.Loff_done:
    moveml %sp@,%d2/%a2-%a4
    lea %sp@(16),%sp
    rts
mllr_cancel:
    movel %d2,%sp@-
    moveq #0,%d2
.Lcancel:
    movel %d2,%sp@-
    jsr mllr_off
    addql #4,%sp
    addql #1,%d2
    cmpil #6,%d2
    bcs .Lcancel
    movel %sp@+,%d2
    rts
