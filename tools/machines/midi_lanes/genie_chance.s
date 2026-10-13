| Genie B : les conditions de pas sont remises à l'héritage à chaque Generate.
| Snapshot/Undo privés ; aucune allocation, E/S ni modification des défauts de voie.
    .ifdef ML_GENIE_CHANCE
    .data
    .balign 4
ml_gc_pointer: .long 0
ml_gc_before: .space 64
ml_gc_after: .space 64
ml_gc_undo: .space 64
    .text
    .globl ml_gc_capture,ml_gc_validate,ml_gc_save_undo,ml_gc_restore_candidate,ml_gc_apply
ml_gc_capture:
    moveal ml_repeat_edit_settings,%a0
    tstl %a0
    beq .Lgc_bad
    movel mlp_track,%d0
    cmpil #5,%d0
    bhi .Lgc_bad
    muluw #520,%d0
    lea.l %a0@(15,%d0:l),%a0
    movel %a0,ml_gc_pointer
    lea.l ml_gc_before,%a1
    moveq #63,%d0
.Lgc_capture:
    moveb %a0@,%a1@+
    addql #8,%a0
    subql #1,%d0
    bpl .Lgc_capture
    lea.l ml_gc_after,%a0
    moveq #15,%d0
.Lgc_zero:
    clrl %a0@+
    subql #1,%d0
    bpl .Lgc_zero
    moveq #1,%d0
    rts
.Lgc_bad:
    moveq #0,%d0
    rts
ml_gc_validate:
    movel ml_gq_pattern,%sp@-
    jsr ml_repeat_pattern_lookup
    addql #4,%sp
    tstl %d0
    beq .Lgc_bad
    moveal %d0,%a0
    movel ml_gq_track,%d0
    muluw #520,%d0
    lea.l %a0@(15,%d0:l),%a0
    cmpal ml_gc_pointer,%a0
    bne .Lgc_bad
    lea.l ml_gc_before,%a1
    moveq #63,%d0
.Lgc_compare:
    moveb %a0@,%d1
    cmpb %a1@+,%d1
    bne .Lgc_bad
    addql #8,%a0
    subql #1,%d0
    bpl .Lgc_compare
    moveq #1,%d0
    rts
ml_gc_save_undo:
    lea.l ml_gc_before,%a0
    lea.l ml_gc_undo,%a1
    bra .Lgc_copy
ml_gc_restore_candidate:
    lea.l ml_gc_undo,%a0
    lea.l ml_gc_after,%a1
.Lgc_copy:
    moveq #15,%d0
.Lgc_copy_loop:
    movel %a0@+,%a1@+
    subql #1,%d0
    bpl .Lgc_copy_loop
    rts
ml_gc_apply:
    moveal ml_gc_pointer,%a0
    lea.l ml_gc_after,%a1
    moveq #63,%d0
.Lgc_apply:
    moveb %a1@+,%a0@
    addql #8,%a0
    subql #1,%d0
    bpl .Lgc_apply
    rts
    .endif
