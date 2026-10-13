| Contexte CC UI privé : 48 + chemins72 + quatre buffers9248 =37112 octets.
| Aucun disque, aucune mutation des banques musicales. Publication après init.
    .data
    .balign 4
    .globl mlkcs_context
mlkcs_context: .long 0
    .text
    .globl mlkcs_prepare,mlkcs_bind
mlkcs_prepare:
    movel %a2,%sp@-
    moveq #0,%d0
    movew %sr,%d1
    andil #0x700,%d1
    bne .Lprepare_out
    movel mlkcs_context,%d0
    bne .Lprepare_out
    pea 37112
    jsr 0x400802e0
    addql #4,%sp
    tstl %d0
    beq .Lprepare_out
    moveal %d0,%a2
    moveal %a2,%a0
    movel #(37112/4-1),%d1
.Lzero:
    clrl %a0@+
    subql #1,%d1
    bpl .Lzero
    lea %a2@(48),%a0
    movel %a0,%a2@
    lea %a0@(26),%a1
    movel %a1,%a2@(36)
    lea %a2@(84),%a0
    movel %a0,%a2@(4)
    lea %a0@(26),%a1
    movel %a1,%a2@(40)
    lea %a2@(120),%a0
    moveq #8,%d1
.Lbuffers:
    movel %a0,%a2@(0,%d1:l)
    lea %a0@(9248),%a0
    addql #4,%d1
    cmpil #24,%d1
    bcs .Lbuffers
    movel %a2,mlkcs_context
    movel %a2,%d0
.Lprepare_out:
    moveal %sp@+,%a2
    rts
| bind(ctx,id,slot,pattern0..96) ->1. Identité fournie par hooks MIDI validés.
mlkcs_bind:
    lea %sp@(-20),%sp
    moveml %d2-%d4/%a2-%a3,%sp@
    moveq #0,%d0
    movew %sr,%d1
    andil #0x700,%d1
    bne .Lbind_out
    moveal %sp@(24),%a2
    tstl %a2
    beq .Lbind_out
    movel %a2,%d1
    andil #3,%d1
    bne .Lbind_out
    movel %sp@(28),%d3
    beq .Lbind_out
    movel %sp@(32),%d4
    cmpil #95,%d4
    bhi .Lbind_out
    movel %sp@(36),%d2
    cmpil #96,%d2
    bhi .Lbind_out
    moveal %a2@,%a3
    moveq #0,%d1
.Lpath:
    movel %d4,%sp@-
    movel %d1,%sp@-
    movel %d2,%sp@-
    movel %d3,%sp@-
    pea 35
    movel %a3,%sp@-
    jsr mlkcs_path
    lea %sp@(24),%sp
    tstl %d0
    beq .Lbind_out
    cmpal %a2@(4),%a3
    beq .Lbound
    moveal %a2@(4),%a3
    moveq #1,%d1
    bra .Lpath
.Lbound:
    movel %d4,%a2@(24)
    movel %d2,%a2@(28)
    movel %d3,%a2@(44)
    moveq #1,%d0
.Lbind_out:
    moveml %sp@,%d2-%d4/%a2-%a3
    lea %sp@(20),%sp
    rts
