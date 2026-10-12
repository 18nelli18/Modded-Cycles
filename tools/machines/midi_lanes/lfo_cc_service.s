| Consommateur CC séparé : service(ctx,budget) -> messages transmis, max8.
| IPL0, singleton routeur nécessaire avant tout retrait ; pas d'appel depuis IRQ.
| Prototype non raccordé. L'appelant garantit contexte privé initialisé.
    .text
    .globl mlcc_service
mlcc_service:
    lea.l %sp@(-24),%sp
    moveml %d2-%d4/%a2,%sp@
    moveq #0,%d2
    movew %sr,%d4
    movel %d4,%d0
    andil #0x700,%d0
    bne .Ldone
    tstl 0x40fe4228
    beq .Ldone
    moveal %sp@(28),%a2
    movel %sp@(32),%d3
    cmpil #8,%d3
    bls .Lloop
    moveq #8,%d3
.Lloop:
    cmpl %d3,%d2
    beq .Ldone
    movel %a2,%sp@-
    jsr mlcc_take
    addql #4,%sp
    tstl %d0
    beq .Ldone
    movel %d0,%sp@(16)
    andil #255,%d0
    lea.l %sp@(16),%a0
    movel %d0,%sp@-
    movel %a0,%sp@-
    pea 3
    jsr 0x400826b0
    lea.l %sp@(12),%sp
    addql #1,%d2
    bra .Lloop
.Ldone:
    movel %d2,%d0
    movew %d4,%sr
    moveml %sp@,%d2-%d4/%a2
    lea.l %sp@(24),%sp
    rts
