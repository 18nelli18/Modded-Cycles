| Hook expérimental épilogue0x4000f850, remplace4cd77c1c4fef0034 par JMP/NOP.
| Notification seulement après succès du Save natif ; aucune I/O ici.
| Callback futur ml_store_save_notice(self,slot) : tâche UI, slot0..95.
    .text
    .globl ml_store_save_hook
ml_store_save_hook:
    tstb %d0
    beq .Lsave_restore
    .ifdef ML_WORKING
    cmpil #96,%d3
    .else
    cmpil #95,%d3
    .endif
    bhi .Lsave_restore
    movel %d0,%sp@-
    moveq #0,%d0
    movew %sr,%d0
    andil #0x700,%d0
    bne .Lsave_result
    movel %d3,%sp@-
    movel %a4,%sp@-
    jsr ml_store_save_notice
    addql #8,%sp
    .ifdef ML_STORAGE2
    .ifdef ML_WORKING
    cmpil #96,%d3
    beq .Lsave_result
    .endif
    jsr ml_store_save_feedback
    .endif
.Lsave_result:
    movel %sp@+,%d0
.Lsave_restore:
    .ifdef ML_SAVE_FIRST
    clrl .Lentry_valid
    .endif
    moveml %sp@,%d2-%d4/%a2-%fp
    lea.l %sp@(52),%sp
    rts

    .ifdef ML_SAVE_FIRST
| Capture avant Save natif : seuls self/table/série inchangés autorisent Save As.
| Le trampoline conserve les registres volatils et rejoue le prologue déplacé.
    .data
    .balign 4
.Lentry_valid: .long 0
.Lentry_self: .long 0
.Lentry_table: .long 0
.Lentry_serial: .long 0
.Lentry_owner: .long 0
.Lentry_slot: .long 0
    .text
    .globl ml_store_save_entry,ml_store_adopt_saved
ml_store_save_entry:
    lea %sp@(-16),%sp
    moveml %d0-%d1/%a0-%a1,%sp@
    clrl .Lentry_valid
    movew %sr,%d0
    andil #0x700,%d0
    bne .Lentry_done
    tstl ml_store_load_active
    bne .Lentry_done
    tstl ml_store_load_ready
    beq .Lentry_done
    movel %sp@(24),%d0
    cmpil #95,%d0
    bhi .Lentry_done
    movel %d0,.Lentry_slot
    movel %sp@(20),%d1
    movel %d1,.Lentry_self
    movel ml_bank_table,%d1
    movel %d1,.Lentry_table
    beq .Lentry_done
    movel ml_store_load_serial,%d1
    movel %d1,.Lentry_serial
    movel ml_store_owner_id,%d1
    movel %d1,.Lentry_owner
    beq .Lentry_done
    movel %sp@(20),%sp@-
    jsr 0x4000eae2
    addql #4,%sp
    cmpl .Lentry_owner,%d0
    bne .Lentry_done
    jsr 0x400cf866
    tstl %d0
    beq .Lentry_done
    movel %d0,%sp@-
    jsr 0x4000eae2
    addql #4,%sp
    cmpl .Lentry_owner,%d0
    bne .Lentry_done
    moveq #1,%d0
    movel %d0,.Lentry_valid
.Lentry_done:
    moveml %sp@,%d0-%d1/%a0-%a1
    lea %sp@(16),%sp
    lea %sp@(-52),%sp
    moveml %d2-%d4/%a2-%fp,%sp@
    jmp 0x4000f76a

| Arguments self,slot,id : identité issue du Save réussi, jamais d'un Load.
ml_store_adopt_saved:
    moveq #0,%d0
    tstl .Lentry_valid
    beq .Ladopt_done
    clrl .Lentry_valid
    movel %sp@(4),%d1
    cmpl .Lentry_self,%d1
    bne .Ladopt_done
    movel %sp@(8),%d1
    cmpl .Lentry_slot,%d1
    bne .Ladopt_done
    movel ml_bank_table,%d1
    cmpl .Lentry_table,%d1
    bne .Ladopt_done
    movel ml_store_load_serial,%d1
    cmpl .Lentry_serial,%d1
    bne .Ladopt_done
    movel ml_store_owner_id,%d1
    cmpl .Lentry_owner,%d1
    bne .Ladopt_done
    tstl ml_store_load_active
    bne .Ladopt_done
    jsr 0x400cf866
    tstl %d0
    beq .Ladopt_done
    movel %d0,%sp@-
    jsr 0x4000eae2
    addql #4,%sp
    cmpl %sp@(12),%d0
    bne .Ladopt_fail
    tstl %d0
    beq .Ladopt_done
    movel %d0,ml_store_owner_id
    movel %d0,ml_store_load_pending_id
    movel %sp@(8),%d1
    movel %d1,ml_store_load_pending_slot
    moveq #1,%d0
    rts
.Ladopt_fail:
    moveq #0,%d0
.Ladopt_done:
    rts
    .endif
