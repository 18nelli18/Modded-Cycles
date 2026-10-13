| Save CC après Save MIDI réussi : identité/slot/table déjà validés par lui.
| Maps projet144 puis locks9216 des banques visitées. Aucun runtime sauvegardé.
| Erreur CC distincte ; le succès des notes et l'accès B restent inchangés.
    .data
    .balign 4
    .globl mlkcs_save_error
mlkcs_save_error: .long 0
    .text
    .globl mlkcs_save_project
mlkcs_save_project:
    lea %sp@(-24),%sp
    moveml %d2-%d4/%a2-%a4,%sp@
    moveq #1,%d0
    movel %d0,mlkcs_save_error
    movel %sp@(28),%d3
    beq .Lfail
    movel %sp@(32),%d4
    cmpil #95,%d4
    bhi .Lfail
    moveal %sp@(36),%a3
    tstl %a3
    beq .Lfail
    jsr mlkcs_prepare
    moveal %d0,%a2
    tstl %d0
    beq .Lfail
    pea 96
    movel %d4,%sp@-
    movel %d3,%sp@-
    movel %a2,%sp@-
    jsr mlkcs_bind
    lea %sp@(16),%sp
    tstl %d0
    beq .Lfail
    lea mlkc_state,%a0
    moveal %a2@(20),%a1
    moveq #35,%d0
.Lmaps:
    movel %a0@+,%a1@+
    subql #1,%d0
    bpl .Lmaps
    movel %a2,%sp@-
    jsr mlkcs_save
    addql #4,%sp
    tstl %d0
    beq .Lfail
    moveq #0,%d2
.Lpattern:
    moveal %a3@(0,%d2:l:4),%a4
    tstl %a4
    beq .Lnext
    clrl %sp@-
    movel %a4,%sp@-
    jsr mlkc_locks_for
    addql #8,%sp
    tstl %d0
    beq .Lnext
    moveal %d0,%a4
    movel %d2,%sp@-
    movel %d4,%sp@-
    movel %d3,%sp@-
    movel %a2,%sp@-
    jsr mlkcs_bind
    lea %sp@(16),%sp
    tstl %d0
    beq .Lfail
    moveal %a4,%a0
    moveal %a2@(20),%a1
    movel #2303,%d0
.Llocks:
    movel %a0@+,%a1@+
    subql #1,%d0
    bpl .Llocks
    movel %a2,%sp@-
    jsr mlkcs_save
    addql #4,%sp
    tstl %d0
    beq .Lfail
.Lnext:
    addql #1,%d2
    cmpil #96,%d2
    bcs .Lpattern
    clrl mlkcs_save_error
    moveq #1,%d0
    bra .Ldone
.Lfail:
    moveq #0,%d0
.Ldone:
    moveml %sp@,%d2-%d4/%a2-%a4
    lea %sp@(24),%sp
    rts
