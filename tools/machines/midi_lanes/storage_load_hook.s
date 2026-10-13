| Notification après ProjectCache::load réussi ; aucun I/O ni publication ici.
| Épilogue0x4006a660 remplace4cd7040c4fef0020 par JMP/NOP.
| Slot96 transmis au service UI, qui vérifie son association avant lecture.
    .data
    .balign 4
    .globl ml_store_load_pending_id,ml_store_load_pending_slot,ml_store_load_serial
ml_store_load_pending_id: .long 0
ml_store_load_pending_slot: .long 0
ml_store_load_serial: .long 0
    .globl ml_store_suspend_pending
ml_store_suspend_pending: .long 0
    .ifdef ML_STORAGE2
    .globl ml_store_load_ready
ml_store_load_ready: .long 1
    .endif
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
    movel %d1,%sp@-
    movew %sr,%d1
    movel %d1,%sp@-
    | Publication atomique sans allocation, disque ni callback UI.
    movew #0x2700,%sr
    moveal %d2,%a0
    movel %a0@(8),%d0
    beq .Lload_result
    movel %d0,ml_store_load_pending_id
    movel %d3,ml_store_load_pending_slot
    .ifdef ML_STORAGE2
    clrl ml_store_load_ready
    moveq #1,%d0
    movel %d0,ml_store_suspend_pending
    .endif
    addql #1,ml_store_load_serial
.Lload_result:
    movel %sp@+,%d1
    movew %d1,%sr
    movel %sp@+,%d1
    movel %sp@+,%a0
    movel %sp@+,%d0
.Lload_restore:
    moveml %sp@,%d2-%d3/%a2
    lea.l %sp@(32),%sp
    rts

| Retirer immédiatement l'ancien projet du chemin de lecture, sans I/O.
    .ifdef ML_STORAGE2
    .globl ml_store_suspend
ml_store_suspend:
    clrl ml_store_load_ready
    jsr ml_store_ui_cancel
    tstl ml_runtime
    beq .Lsuspend_done
    tstl ml_clock_state
    beq .Lsuspend_done
    tstl ml_bank_empty
    beq .Lsuspend_done
    movel ml_bank_empty,%sp@-
    movel ml_clock_state,%sp@-
    movel ml_runtime,%sp@-
    pea ml_play_pattern
    jsr ml_bank_activate
    lea.l %sp@(16),%sp
    movel ml_bank_empty,%d0
    movel %d0,ml_pattern
.Lsuspend_done:
    rts
    .endif
