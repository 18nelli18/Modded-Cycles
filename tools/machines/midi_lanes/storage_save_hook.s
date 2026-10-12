| Hook expérimental épilogue0x4000f850, remplace4cd77c1c4fef0034 par JMP/NOP.
| Notification seulement après succès du Save natif ; aucune I/O ici.
| Callback futur ml_store_save_notice(self,slot) : tâche UI, slot0..95.
    .text
    .globl ml_store_save_hook
ml_store_save_hook:
    tstb %d0
    beq .Lsave_restore
    cmpil #95,%d3
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
    jsr ml_store_save_feedback
    .endif
.Lsave_result:
    movel %sp@+,%d0
.Lsave_restore:
    moveml %sp@,%d2-%d4/%a2-%fp
    lea.l %sp@(52),%sp
    rts
