| Première copie A uniquement après deux absences vérifiées. Prototype UI.
| ctx44 : ctx commit32 + parent validé, nomA, nomB. Ne remplace jamais B.
| Garde I/O installée dès boot, dossiers/chemins validés, un seul propriétaire.
    .ifdef ML_STORAGE3
    .equ ML_DATA_BYTES,4992
    .equ ML_RECORD_BYTES,5024
    .else
    .ifdef ML_STORAGE2
    .equ ML_DATA_BYTES,4896
    .equ ML_RECORD_BYTES,4928
    .else
    .equ ML_DATA_BYTES,1584
    .equ ML_RECORD_BYTES,1616
    .endif
    .endif
    .text
    .globl ml_store_initial
ml_store_initial:
    lea.l %sp@(-16),%sp
    moveml %d2/%a2-%a4,%sp@
    movew %sr,%d0
    andil #0x700,%d0
    bne .Lfail
    moveal %sp@(20),%a2
    tstl %a2
    beq .Lfail
    movel %a2,%d0
    andil #3,%d0
    bne .Lfail
    | Refuser un contexte incomplet avant toute lecture fichier.
    moveal %a2,%a0
    moveq #5,%d1
.Lnonnull:
    tstl %a0@+
    beq .Lfail
    subql #1,%d1
    bpl .Lnonnull
    movel %a2@(24),%d0
    cmpil #95,%d0
    bhi .Lfail
    movel %a2@(28),%d0
    cmpil #95,%d0
    bhi .Lfail
    | Quatre régions disjointes : garde conservatriceML_RECORD_BYTES, snapshot compris.
    moveq #8,%d2
.Louter:
    movel %a2@(0,%d2:l),%d0
    movel %d0,%a3
    andil #3,%d0
    bne .Lfail
    movel %a3,%d0
    addil #ML_RECORD_BYTES,%d0
    bcs .Lfail
    movel %d2,%d1
    addql #4,%d1
.Linner:
    cmpil #24,%d1
    bcc .Lnext
    moveal %a2@(0,%d1:l),%a4
    cmpl %a4,%d0
    bls .Ldisjoint
    movel %a4,%a0
    lea.l %a0@(ML_RECORD_BYTES),%a0
    cmpal %a3,%a0
    bhi .Lfail
.Ldisjoint:
    addql #4,%d1
    bra .Linner
.Lnext:
    addql #4,%d2
    cmpil #24,%d2
    bcs .Louter
    | Extension ctx44 : parent, nomA, nomB ; chemin cohérent garanti par caller.
    movel %a2@(32),%d0
    cmpil #2,%d0
    bcs .Lfail
    tstl %a2@(36)
    beq .Lfail
    tstl %a2@(40)
    beq .Lfail
    movel %a2@(8),%sp@-
    movel %a2@(36),%sp@-
    movel %a2@(32),%sp@-
    jsr ml_store_lookup_checked
    lea.l %sp@(12),%sp
    tstl %d0
    bne .Lfail
    movel %a2@(12),%sp@-
    movel %a2@(40),%sp@-
    movel %a2@(32),%sp@-
    jsr ml_store_lookup_checked
    lea.l %sp@(12),%sp
    tstl %d0
    bne .Lfail
    jsr ml_store_io_begin
    tstl %d0
    beq .Lfail
    moveq #0,%d2
    clrl %sp@-
    movel %a2@(28),%sp@-
    movel %a2@(24),%sp@-
    movel %a2@(20),%sp@-
    pea ML_RECORD_BYTES
    movel %a2@(8),%sp@-
    jsr ml_record_encode
    lea.l %sp@(24),%sp
    tstl %d0
    beq .Linitial_end
    pea ML_RECORD_BYTES
    movel %a2@(16),%sp@-
    movel %a2@(8),%sp@-
    movel %a2@,%sp@-
    jsr ml_store_verified
    lea.l %sp@(16),%sp
    movel %d0,%d2
.Linitial_end:
    jsr ml_store_io_end
    andl %d2,%d0
    bra .Ldone
.Lfail:
    moveq #0,%d0
.Ldone:
    moveml %sp@,%d2/%a2-%a4
    lea.l %sp@(16),%sp
    rts
