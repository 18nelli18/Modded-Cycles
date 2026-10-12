| Notification après ProjectCache::load réussi ; aucun I/O ni publication ici.
| Épilogue0x4006a660 remplace4cd7040c4fef0020 par JMP/NOP.
| Slot96 transmis au service UI, qui vérifie son association avant lecture.
    .data
    .balign 4
    .globl ml_store_load_pending_id,ml_store_load_pending_slot,ml_store_load_serial
ml_store_load_pending_id: .long 0
ml_store_load_pending_slot: .long 0
ml_store_load_serial: .long 0
    .text
    .globl ml_store_load_hook
ml_store_load_hook:
    .ifdef ML_REPEAT
    jsr ml_repeat_project_notice
    .endif
    tstb %d0
    beq .Lload_restore
    cmpil #96,%d3
    bhi .Lload_restore
    tstl %d2
    beq .Lload_restore
    movel %d0,%sp@-
    movel %a0,%sp@-
    movew %sr,%d0
    andil #0x700,%d0
    bne .Lload_result
    moveal %d2,%a0
    movel %a0@(8),%d0
    beq .Lload_result
    movel %d0,ml_store_load_pending_id
    movel %d3,ml_store_load_pending_slot
    addql #1,ml_store_load_serial
.Lload_result:
    movel %sp@+,%a0
    movel %sp@+,%d0
.Lload_restore:
    moveml %sp@,%d2-%d3/%a2
    lea.l %sp@(32),%sp
    rts
