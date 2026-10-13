| Candidature CC privée parallèle aux96 étapes de restauration MIDI.
| step(banqueOu0,index,id,slot), apply(table) seulement après publication MIDI.
| Un fichier CC absent = défaut, corrompu = erreur CC non fatale pour les notes.
    .data
    .balign 4
    .globl mlkcs_load_error
mlkcs_load_error: .long 0
.Lmaps: .space 144
.Llocks: .space 384
    .text
    .globl mlkcs_candidate_reset,mlkcs_candidate_step,mlkcs_candidate_apply
mlkcs_candidate_reset:
    lea %sp@(-12),%sp
    moveml %d2/%a2-%a3,%sp@
    lea .Llocks,%a2
    moveq #95,%d2
.Lfree:
    moveal %a2@,%a3
    clrl %a2@+
    tstl %a3
    beq .Lfree_next
    movel %a3,%sp@-
    jsr 0x400802ec
    addql #4,%sp
.Lfree_next:
    subql #1,%d2
    bpl .Lfree
    lea .Lmaps,%a0
    moveq #35,%d0
    movel #0xff40ff40,%d1
.Ldefaults:
    movel %d1,%a0@+
    subql #1,%d0
    bpl .Ldefaults
    clrl mlkcs_load_error
    moveml %sp@,%d2/%a2-%a3
    lea %sp@(12),%sp
    rts
mlkcs_candidate_step:
    lea %sp@(-20),%sp
    moveml %d2-%d4/%a2-%a3,%sp@
    movel %sp@(28),%d2
    cmpil #95,%d2
    bhi .Lerror
    jsr mlkcs_prepare
    moveal %d0,%a2
    tstl %d0
    beq .Lerror
    moveal %sp@(24),%a3
    tstl %d2
    bne .Llock
    pea 96
    movel %sp@(40),%sp@-
    movel %sp@(40),%sp@-
    movel %a2,%sp@-
    jsr mlkcs_bind
    lea %sp@(16),%sp
    tstl %d0
    beq .Lerror
    movel %a2,%sp@-
    jsr mlkcs_load
    addql #4,%sp
    tstl %d0
    beq .Lmap_error
    cmpil #3,%d0
    beq .Llock
    moveal %a2@(16),%a0
    lea .Lmaps,%a1
    moveq #35,%d0
.Lcopy_map:
    movel %a0@+,%a1@+
    subql #1,%d0
    bpl .Lcopy_map
    bra .Llock
.Lmap_error:
    moveq #1,%d0
    movel %d0,mlkcs_load_error
.Llock:
    tstl %a3
    beq .Lstep_done
    movel %d2,%sp@-
    movel %sp@(40),%sp@-
    movel %sp@(40),%sp@-
    movel %a2,%sp@-
    jsr mlkcs_bind
    lea %sp@(16),%sp
    tstl %d0
    beq .Lerror
    movel %a2,%sp@-
    jsr mlkcs_load
    addql #4,%sp
    tstl %d0
    beq .Lerror
    cmpil #3,%d0
    beq .Lstep_done
    pea 9216
    jsr 0x400802e0
    addql #4,%sp
    tstl %d0
    beq .Lerror
    moveal %d0,%a1
    lea .Llocks,%a0
    movel %d0,%a0@(0,%d2:l:4)
    moveal %a2@(16),%a0
    movel #2303,%d0
.Lcopy_lock:
    movel %a0@+,%a1@+
    subql #1,%d0
    bpl .Lcopy_lock
    bra .Lstep_done
.Lerror:
    moveq #1,%d0
    movel %d0,mlkcs_load_error
.Lstep_done:
    moveml %sp@,%d2-%d4/%a2-%a3
    lea %sp@(20),%sp
    rts
mlkcs_candidate_apply:
    lea %sp@(-12),%sp
    moveml %d2/%a2-%a3,%sp@
    moveal %sp@(16),%a2
    lea .Lmaps,%a0
    lea mlkc_state,%a1
    moveq #35,%d0
.Lapply_map:
    movel %a0@+,%a1@+
    subql #1,%d0
    bpl .Lapply_map
    lea .Llocks,%a3
    moveq #0,%d2
.Ladopt:
    movel %a3@(0,%d2:l:4),%d0
    beq .Ladopt_next
    movel %d0,%sp@-
    movel %a2@(0,%d2:l:4),%sp@-
    jsr mlkc_locks_adopt
    addql #8,%sp
    tstl %d0
    beq .Ladopt_error
    clrl %a3@(0,%d2:l:4)
    bra .Ladopt_next
.Ladopt_error:
    moveq #1,%d0
    movel %d0,mlkcs_load_error
.Ladopt_next:
    addql #1,%d2
    cmpil #96,%d2
    bcs .Ladopt
    | Libérer uniquement les candidatures qui n'ont pas pu être adoptées.
    moveq #95,%d2
.Lleftovers:
    movel %a3@,%d0
    clrl %a3@+
    tstl %d0
    beq .Lleftover_next
    movel %d0,%sp@-
    jsr 0x400802ec
    addql #4,%sp
.Lleftover_next:
    subql #1,%d2
    bpl .Lleftovers
    moveml %sp@,%d2/%a2-%a3
    lea %sp@(12),%sp
    rts
