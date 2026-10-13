| Journal CC UI : ctx48 cheminsA/B,recordsA/B,scratch,payload,slot,pattern,
| parent,nomsA/B,identité. Tampons privés disjoints >=9248 (payload>=9216).
| load ->1/2 copie choisie dans scratch,3 absence vérifiée,0 erreur.
| save ->1 après relecture intégrale de la copie inactive, sinon0.
| Le demandeur a déjà validé propriétaire/slot et créé le dossier via Save MIDI.
    .text
    .globl mlkcs_load,mlkcs_save
mlkcs_load:
    lea %sp@(-24),%sp
    moveml %d2-%d5/%a2-%a3,%sp@
    moveal %sp@(28),%a2
    bsr .Lctx
    tstl %d0
    beq .Lfail
    movel %a2,%sp@-
    jsr ml_store_presence
    addql #4,%sp
    tstl %d0
    bmi .Lfail
    beq .Labsent
    moveq #0,%d4
    moveq #0,%d5
    movel %d3,%sp@-
    movel %a2@(8),%sp@-
    movel %a2@,%sp@-
    jsr ml_store_read_checked
    lea %sp@(12),%sp
    tstl %d0
    beq .Lread_b
    moveal %a2@(8),%a3
    bsr .Ldecode
    movel %d0,%d4
.Lread_b:
    movel %d3,%sp@-
    movel %a2@(12),%sp@-
    movel %a2@(4),%sp@-
    jsr ml_store_read_checked
    lea %sp@(12),%sp
    tstl %d0
    beq .Lchoose
    moveal %a2@(12),%a3
    bsr .Ldecode
    movel %d0,%d5
.Lchoose:
    tstl %d4
    beq .Lonly_b
    tstl %d5
    beq .Lchoose_a
    moveal %a2@(8),%a0
    moveal %a2@(12),%a1
    movel %a0@(20),%d0
    subl %a1@(20),%d0
    | Égalité choisit A ; écart demi-cycle ambigu refusé.
    cmpil #0x80000000,%d0
    beq .Lfail
    tstl %d0
    bpl .Lchoose_a
.Lonly_b:
    tstl %d5
    beq .Lfail
    moveal %a2@(12),%a3
    moveq #2,%d4
    bra .Lselected
.Lchoose_a:
    moveal %a2@(8),%a3
    moveq #1,%d4
.Lselected:
    bsr .Ldecode
    tstl %d0
    beq .Lfail
    movel %d4,%d0
    bra .Lout
.Labsent:
    moveq #3,%d0
    bra .Lout
.Lfail:
    moveq #0,%d0
.Lout:
    moveml %sp@,%d2-%d5/%a2-%a3
    lea %sp@(24),%sp
    rts
mlkcs_save:
    lea %sp@(-24),%sp
    moveml %d2-%d5/%a2-%a3,%sp@
    moveal %sp@(28),%a2
    bsr .Lctx
    tstl %d0
    beq .Lfail
    movel %a2,%sp@-
    jsr mlkcs_load
    addql #4,%sp
    tstl %d0
    beq .Lfail
    cmpil #3,%d0
    beq .Linitial
    cmpil #1,%d0
    bne .Lfrom_b
    moveal %a2@(8),%a0
    movel %a0@(20),%d4
    moveal %a2@(12),%a3
    movel %a2@(4),%d5
    bra .Ladvance
.Lfrom_b:
    moveal %a2@(12),%a0
    movel %a0@(20),%d4
    moveal %a2@(8),%a3
    movel %a2@,%d5
    bra .Ladvance
.Linitial:
    moveq #0,%d4
    moveal %a2@(8),%a3
    movel %a2@,%d5
.Ladvance:
    addql #1,%d4
    movel %d4,%sp@-
    movel %a2@(28),%sp@-
    movel %a2@(24),%sp@-
    movel %a2@(44),%sp@-
    movel %d2,%sp@-
    movel %a2@(20),%sp@-
    movel %d3,%sp@-
    movel %a3,%sp@-
    jsr mlkcs_encode
    lea %sp@(32),%sp
    tstl %d0
    beq .Lfail
    jsr ml_store_io_begin
    tstl %d0
    beq .Lfail
    movel %d3,%sp@-
    movel %a2@(16),%sp@-
    movel %a3,%sp@-
    movel %d5,%sp@-
    jsr mlkcs_verified
    lea %sp@(16),%sp
    movel %d0,%d4
    jsr ml_store_io_end
    andl %d4,%d0
    bra .Lout
.Ldecode:
    movel %a2@(28),%sp@-
    movel %a2@(24),%sp@-
    movel %a2@(44),%sp@-
    movel %d3,%sp@-
    movel %a3,%sp@-
    movel %a2@(16),%sp@-
    jsr mlkcs_decode
    lea %sp@(24),%sp
    rts
.Lctx:
    moveq #0,%d0
    movew %sr,%d1
    andil #0x700,%d1
    bne .Lctx_out
    tstl %a2
    beq .Lctx_out
    movel %a2,%d1
    andil #3,%d1
    bne .Lctx_out
    moveal %a2,%a0
    moveq #5,%d1
.Lctx_ptr:
    movel %a0@+,%d0
    beq .Lctx_bad
    subql #1,%d1
    bpl .Lctx_ptr
    moveq #0,%d0
    tstl %a2@(44)
    beq .Lctx_out
    movel %a2@(24),%d1
    cmpil #95,%d1
    bhi .Lctx_out
    movel %a2@(28),%d1
    cmpil #96,%d1
    bhi .Lctx_out
    movel #9216,%d2
    cmpil #96,%d1
    bne .Lctx_size
    movel #144,%d2
.Lctx_size:
    movel %d2,%d3
    addil #32,%d3
    | Quatre tampons privés ; refuser un alias avant toute E/S ou décodage.
    moveq #8,%d4
.Lctx_outer:
    moveal %a2@(0,%d4:l),%a0
    movel %a0,%d0
    andil #3,%d0
    bne .Lctx_bad
    movel %a0,%d0
    addl %d3,%d0
    bcs .Lctx_bad
    movel %d4,%d5
    addql #4,%d5
.Lctx_inner:
    cmpil #24,%d5
    bcc .Lctx_next
    moveal %a2@(0,%d5:l),%a1
    cmpl %a1,%d0
    bls .Lctx_disjoint
    movel %a1,%d1
    addl %d3,%d1
    bcs .Lctx_bad
    cmpl %a0,%d1
    bhi .Lctx_bad
.Lctx_disjoint:
    addql #4,%d5
    bra .Lctx_inner
.Lctx_next:
    addql #4,%d4
    cmpil #24,%d4
    bcs .Lctx_outer
    moveq #1,%d0
.Lctx_out:
    rts
.Lctx_bad:
    moveq #0,%d0
    rts
