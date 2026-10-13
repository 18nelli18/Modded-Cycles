| Chargement annexe UI : lire A/B dans deux tampons privés, valider, choisir.
| ml_store_load(dest,pathA,pathB,recordA,recordB,slot,pattern) -> 0/1/2.
| Dest = staging privé 1584, records = 1616 chacun, alignés et disjoints.
| Jamais de publication dans une banque active ni d'E/S en IRQ.
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
    .globl ml_store_load
ml_store_load:
    lea.l %sp@(-40),%sp
    moveml %d2-%d5/%a2-%fp,%sp@
    moveq #0,%d4
    moveq #0,%d5
    movew %sr,%d0
    andil #0x700,%d0
    bne .Lfail
    moveal %sp@(44),%a2
    moveal %sp@(48),%a5
    moveal %sp@(52),%fp
    moveal %sp@(56),%a3
    moveal %sp@(60),%a4
    movel %sp@(64),%d2
    movel %sp@(68),%d3
    cmpil #95,%d2
    bhi .Lfail
    cmpil #95,%d3
    bhi .Lfail
    tstl %a5
    beq .Lfail
    tstl %fp
    beq .Lfail
    movel %a2,%d0
    movel %a3,%d1
    bsr .Lpair
    tstl %d0
    beq .Lfail
    movel %a2,%d0
    movel %a4,%d1
    bsr .Lpair
    tstl %d0
    beq .Lfail
    movel %a3,%d0
    movel %a4,%d1
    bsr .Lpair
    tstl %d0
    beq .Lfail
    pea ML_RECORD_BYTES
    movel %a3,%sp@-
    movel %a5,%sp@-
    jsr ml_store_read
    lea.l %sp@(12),%sp
    .ifdef ML_STORAGE2
    movel ml_store_file_error,%d1
    movel %d1,.Lfile_error_a
    .endif
    tstl %d0
    beq .Lread_b
    movel #ML_RECORD_BYTES,%d4
.Lread_b:
    pea ML_RECORD_BYTES
    movel %a4,%sp@-
    movel %fp,%sp@-
    jsr ml_store_read
    lea.l %sp@(12),%sp
    tstl %d0
    beq .Lselect
    movel #ML_RECORD_BYTES,%d5
.Lselect:
    .ifdef ML_STORAGE2
    movel %d4,%d0
    orl %d5,%d0
    bne .Lselect_records
    movel .Lfile_error_a,%d0
    cmpil #5,%d0
    bne .Lselect_file_error
    movel ml_store_file_error,%d0
.Lselect_file_error:
    movel %d0,ml_store_read_error
    bra .Lfail
.Lselect_records:
    .endif
    movel %d3,%sp@-
    movel %d2,%sp@-
    movel %d5,%sp@-
    movel %a4,%sp@-
    movel %d4,%sp@-
    movel %a3,%sp@-
    movel %a2,%sp@-
    jsr ml_record_select
    lea.l %sp@(28),%sp
    bra .Ldone
.Lfail:
    moveq #0,%d0
.Ldone:
    moveml %sp@,%d2-%d5/%a2-%fp
    lea.l %sp@(40),%sp
    rts
| Garde conservatrice de deux régionsML_RECORD_BYTES : dest réelML_DATA_BYTES.
.Lpair:
    tstl %d0
    beq .Lpair_bad
    tstl %d1
    beq .Lpair_bad
    movel %d0,%a0
    movel %d1,%a1
    orl %d1,%d0
    andil #3,%d0
    bne .Lpair_bad
    movel %a0,%d0
    addil #ML_RECORD_BYTES,%d0
    bcs .Lpair_bad
    movel %a1,%d1
    addil #ML_RECORD_BYTES,%d1
    bcs .Lpair_bad
    cmpl %a1,%d0
    bls .Lpair_good
    cmpl %a0,%d1
    bhi .Lpair_bad
.Lpair_good:
    moveq #1,%d0
    rts
.Lpair_bad:
    moveq #0,%d0
    rts

    .ifdef ML_STORAGE2
    .data
    .balign 4
.Lfile_error_a: .long 0
    .endif
