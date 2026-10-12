| Note 57 : callback LedHandler de la vue privée (sous-objet +8).
| Écrit uniquement les 16 LED des pas via le writer natif first-wins.
| Aucun port MIDI, aucune allocation et aucune sélection audio modifiée.
    .text
    .globl mlp_led
mlp_led:
    lea.l %sp@(-24),%sp
    movem.l %d2-%d5/%a2-%a3,%sp@
    moveal %sp@(28),%a0
    subql #8,%a0
    cmpal mlp_obj,%a0
    bne .Lled_done
    moveal ml_pattern,%a2
    tstl %a2
    beq .Lled_done
    movel mlp_track,%d0
    cmpil #5,%d0
    bhi .Lled_done
    muluw #264,%d0
    addal %d0,%a2
    movel mlp_step,%d0
    andil #48,%d0
    lsll #2,%d0
    lea.l %a2@(8),%a2
    addal %d0,%a2
    jsr 0x400cfaf4
    tstl %d0
    beq .Lled_done
    moveal %d0,%a3
    moveq #0,%d2
.Lled_loop:
    movel %d2,%sp@-
    jsr 0x4000608c
    addql #4,%sp
    movel %d0,%d3
    cmpil #53,%d3
    bhi .Lled_next
    movel %d3,%d0
    lsrl #5,%d0
    lsll #2,%d0
    moveal %sp@(36),%a0
    addal %d0,%a0
    movel %d3,%d1
    andil #31,%d1
    moveq #1,%d0
    lsll %d1,%d0
    orl %d0,%a0@
    moveq #1,%d4
    tstb %a2@(3)
    beq .Lled_write
    moveq #2,%d4
.Lled_write:
    pea 0x404a8cb8
    movel %d4,%sp@-
    movel %d3,%sp@-
    movel %a3,%sp@-
    jsr 0x40005f86
    lea.l %sp@(16),%sp
.Lled_next:
    addql #4,%a2
    addql #1,%d2
    cmpil #16,%d2
    bcs .Lled_loop
.Lled_done:
    moveq #1,%d0
    movem.l %sp@,%d2-%d5/%a2-%a3
    lea.l %sp@(24),%sp
    rts
