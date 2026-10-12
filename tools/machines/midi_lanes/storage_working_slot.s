| Associer le working slot96 au slot sauvegardé déclaré par l'OS.
| resolve(id,slot) ->0..95 ou-1 ; UI seule, aucune écriture ni recherche devinée.
| Le getter stock40044d74 lit le slot courant signé404e9b4d. Vérifier aussi
| le type projet6 et son identité via les lecteurs utilisés par4000fe3c.
    .text
    .globl ml_store_resolve_slot
ml_store_resolve_slot:
    lea.l %sp@(-12),%sp
    moveml %d2-%d3/%a2,%sp@
    movew %sr,%d0
    andil #0x700,%d0
    bne .Lslot_fail
    movel %sp@(16),%d2
    beq .Lslot_fail
    movel %sp@(20),%d3
    cmpil #95,%d3
    bls .Lslot_ok
    cmpil #96,%d3
    bne .Lslot_fail
    jsr 0x40044d74
    cmpil #95,%d0
    bhi .Lslot_fail
    movel %d0,%d3
    jsr 0x400d0a10
    tstl %d0
    beq .Lslot_fail
    moveal %d0,%a2
    movel %d3,%sp@-
    movel %a2,%sp@-
    jsr 0x4008c2c2
    addql #8,%sp
    cmpil #6,%d0
    bne .Lslot_fail
    movel %d3,%sp@-
    movel %a2,%sp@-
    jsr 0x4008c324
    addql #8,%sp
    cmpl %d2,%d0
    bne .Lslot_fail
.Lslot_ok:
    movel %d3,%d0
    bra .Lslot_done
.Lslot_fail:
    moveq #-1,%d0
.Lslot_done:
    moveml %sp@,%d2-%d3/%a2
    lea.l %sp@(12),%sp
    rts
