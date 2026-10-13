| Annexe MCC1 : header32, puis mappings144 (pattern96) ou locks9216.
| Identité projet/slot/pattern, génération, CRC payload et header séparés.
| Aucun pointeur/runtime sérialisé. Validation complète avant écriture.
| encode(out,cap,payload,len,id,slot,pattern,generation) -> bool.
| decode(out,record,total,id,slot,pattern) -> bool.
    .text
    .globl mlkcs_encode,mlkcs_decode
mlkcs_encode:
    lea %sp@(-24),%sp
    moveml %d2-%d4/%a2-%a4,%sp@
    moveal %sp@(28),%a2
    moveal %sp@(36),%a3
    movel %sp@(40),%d2
    movel %sp@(44),%d3
    movel %sp@(52),%d4
    tstl %d3
    beq .Lfail
    movel %sp@(48),%d0
    cmpil #95,%d0
    bhi .Lfail
    bsr .Lsize
    tstl %d0
    beq .Lfail
    movel %d2,%d0
    addil #32,%d0
    cmpl %sp@(32),%d0
    bne .Lfail
    bsr .Lbuffers
    tstl %d0
    beq .Lfail
    moveal %a3,%a0
    bsr .Lvalues
    tstl %d0
    beq .Lfail
    movel #0x4d434331,%a2@
    movel %d2,%a2@(4)
    movel %d3,%a2@(8)
    movel %sp@(48),%a2@(12)
    movel %d4,%a2@(16)
    movel %sp@(56),%a2@(20)
    moveal %a3,%a0
    lea %a2@(32),%a1
    bsr .Lcopy
    movel %d2,%sp@-
    pea %a2@(32)
    jsr ml_record_crc
    addql #8,%sp
    movel %d0,%a2@(24)
    pea 28
    movel %a2,%sp@-
    jsr ml_record_crc
    addql #8,%sp
    movel %d0,%a2@(28)
    bra .Lok
mlkcs_decode:
    lea %sp@(-24),%sp
    moveml %d2-%d4/%a2-%a4,%sp@
    moveal %sp@(32),%a2
    moveal %sp@(28),%a3
    movel %sp@(36),%d0
    cmpil #176,%d0
    beq .Ldec_len
    cmpil #9248,%d0
    bne .Lfail
.Ldec_len:
    subil #32,%d0
    movel %d0,%d2
    movel %sp@(40),%d3
    beq .Lfail
    movel %sp@(44),%d0
    cmpil #95,%d0
    bhi .Lfail
    movel %sp@(48),%d4
    bsr .Lsize
    tstl %d0
    beq .Lfail
    bsr .Lbuffers
    tstl %d0
    beq .Lfail
    movel %a2@,%d0
    cmpil #0x4d434331,%d0
    bne .Lfail
    cmpl %a2@(4),%d2
    bne .Lfail
    cmpl %a2@(8),%d3
    bne .Lfail
    movel %sp@(44),%d0
    cmpl %a2@(12),%d0
    bne .Lfail
    cmpl %a2@(16),%d4
    bne .Lfail
    pea 28
    movel %a2,%sp@-
    jsr ml_record_crc
    addql #8,%sp
    cmpl %a2@(28),%d0
    bne .Lfail
    movel %d2,%sp@-
    pea %a2@(32)
    jsr ml_record_crc
    addql #8,%sp
    cmpl %a2@(24),%d0
    bne .Lfail
    lea %a2@(32),%a0
    bsr .Lvalues
    tstl %d0
    beq .Lfail
    lea %a2@(32),%a0
    moveal %a3,%a1
    bsr .Lcopy
.Lok:
    moveq #1,%d0
    bra .Ldone
.Lfail:
    moveq #0,%d0
.Ldone:
    moveml %sp@,%d2-%d4/%a2-%a4
    lea %sp@(24),%sp
    rts
| Les deux tampons privés sont disjoints et alignés ; jamais en IRQ.
.Lbuffers:
    movew %sr,%d0
    andil #0x700,%d0
    bne .Lbad
    movel %a2,%d0
    beq .Lbad
    movel %a3,%d1
    beq .Lbad
    orl %d1,%d0
    andil #3,%d0
    bne .Lbad
    movel %a2,%d0
    addil #32,%d0
    addl %d2,%d0
    bcs .Lbad
    movel %a3,%d1
    addl %d2,%d1
    bcs .Lbad
    cmpl %a3,%d0
    bls .Lgood
    cmpl %a2,%d1
    bhi .Lbad
.Lgood:
    moveq #1,%d0
    rts
.Lbad:
    moveq #0,%d0
    rts
.Lsize:
    cmpil #96,%d4
    bhi .Lbad
    beq .Lmap_size
    cmpil #9216,%d2
    bne .Lbad
    bra .Lgood
.Lmap_size:
    cmpil #144,%d2
    bne .Lbad
    bra .Lgood
.Lvalues:
    movel %d2,%d1
    lsrl #1,%d1
    subql #1,%d1
.Lvalue_loop:
    moveq #0,%d0
    movew %a0@+,%d0
    cmpil #96,%d4
    beq .Lmap_value
    cmpil #65535,%d0
    beq .Lvalue_next
.Lmap_value:
    | OFF255 conserve une valeur de base0..127 ; lock absent = ffff.
    cmpil #96,%d4
    bne .Lpair
    cmpil #0xff00,%d0
    bcs .Lpair
    cmpil #0xff7f,%d0
    bhi .Lbad
    bra .Lvalue_next
.Lpair:
    andil #0x8080,%d0
    bne .Lbad
.Lvalue_next:
    subql #1,%d1
    bpl .Lvalue_loop
    bra .Lgood
.Lcopy:
    movel %d2,%d1
    lsrl #2,%d1
    subql #1,%d1
.Lcopy_loop:
    movel %a0@+,%a1@+
    subql #1,%d1
    bpl .Lcopy_loop
    rts
