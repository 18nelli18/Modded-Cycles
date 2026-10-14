| Release UI d'un trig existant, appel spécifique 40022dd0(objet,pas,0).
| Le clear natif libère tous les slots de locks et réinitialise les champs.
| Retirer ensuite tous les flags résiduels, notamment SCRAMBLE bit6/slide.
| Note setter natif = même notification de pas que l'OS. Aucun état global.
    .text
    .globl sc_step_delete
sc_step_delete:
    lea %sp@(-12),%sp
    moveml %d2/%a2,%sp@
    moveal %sp@(16),%a2
    movel %sp@(20),%d2
    movel %sp@(24),%sp@-
    movel %d2,%sp@-
    movel %a2,%sp@-
    jsr 0x40017c4e
    lea %sp@(12),%sp
    movel %d0,%sp@(8)
    cmpil #63,%d2
    bhi .Lsd_done
    movel %a2,%sp@-
    jsr 0x40016402
    addql #4,%sp
    cmpl %d2,%d0
    ble .Lsd_done
    movel %a2,%sp@-
    moveal %a2@,%a0
    moveal %a0@(40),%a0
    jsr %a0@
    addql #4,%sp
    tstl %d0
    beq .Lsd_done
    moveal %d0,%a0
    clrw %a0@(0,%d2:l:2)
    pea -1
    movel %d2,%sp@-
    movel %a2,%sp@-
    jsr 0x40016642
    lea %sp@(12),%sp
.Lsd_done:
    movel %sp@(8),%d0
    moveml %sp@,%d2/%a2
    lea %sp@(12),%sp
    rts
