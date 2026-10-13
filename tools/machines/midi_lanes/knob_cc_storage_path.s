| Réutiliser les chemins projet validés ; namespaces CCM (maps) et CCL (locks).
| path(out,cap,id,pattern0..96,copie0..1,slot0..95) -> bool.
| pattern96 désigne les assignations globales, nom CCM-00-A/B.
    .text
    .globl mlkcs_path
mlkcs_path:
    lea %sp@(-8),%sp
    moveml %d2/%a2,%sp@
    movel %sp@(24),%d2
    cmpil #96,%d2
    bhi .Lbad
    movel %d2,%d0
    cmpil #96,%d0
    bne .Lpattern
    moveq #0,%d0
.Lpattern:
    moveal %sp@(12),%a2
    movel %sp@(32),%sp@-
    clrl %sp@-
    movel %sp@(36),%sp@-
    movel %d0,%sp@-
    movel %sp@(36),%sp@-
    movel %sp@(36),%sp@-
    movel %a2,%sp@-
    jsr ml_store_path
    lea %sp@(28),%sp
    tstl %d0
    beq .Ldone
    moveb #67,%a2@(26)
    moveb #67,%a2@(27)
    moveb #76,%a2@(28)
    cmpil #96,%d2
    bne .Ldone
    moveb #77,%a2@(28)
    bra .Ldone
.Lbad:
    moveq #0,%d0
.Ldone:
    moveml %sp@,%d2/%a2
    addql #8,%sp
    rts
