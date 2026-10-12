| Publication UI d'une table candidate complète, après annulation des touches
| tenues, du Genie et de l'undo par le demandeur. Aucun free ni I/O ici.
| publish(table,id,serial) -> ancienne table à retirer,0 refus sans mutation.
| Le demandeur garde les banques anciennes jusqu'au retour et ne libère pas
| le contexte initial ni sa table embarquée. Les pointeurs candidate sont privés.
    .text
    .globl ml_store_publish
ml_store_publish:
    lea.l %sp@(-24),%sp
    moveml %d2-%d4/%a2-%a3,%sp@
    movew %sr,%d0
    movel %d0,%sp@(20)
    andil #0x700,%d0
    bne .Lpub_fail
    moveal %sp@(28),%a2
    movel %sp@(32),%d3
    movel %sp@(36),%d4
    tstl %a2
    beq .Lpub_fail
    movel %a2,%d0
    andil #3,%d0
    bne .Lpub_fail
    tstl %d3
    beq .Lpub_fail
    tstl ml_bank_empty
    beq .Lpub_fail
    tstl ml_runtime
    beq .Lpub_fail
    tstl ml_clock_state
    beq .Lpub_fail
    moveal ml_bank_table,%a3
    tstl %a3
    beq .Lpub_fail
    cmpal %a3,%a2
    beq .Lpub_fail
    jsr 0x400cf866
    tstl %d0
    beq .Lpub_fail
    movel %d0,%sp@-
    jsr 0x4000eae2
    addql #4,%sp
    cmpl %d3,%d0
    bne .Lpub_fail
    movew #0x2700,%sr
    cmpl ml_store_load_serial,%d4
    bne .Lpub_fail
    cmpl ml_store_load_pending_id,%d3
    bne .Lpub_fail
    | L'IRQ ne peut plus conserver une référence à la banque ancienne.
    movel ml_bank_empty,%sp@-
    movel ml_clock_state,%sp@-
    movel ml_runtime,%sp@-
    pea ml_play_pattern
    jsr ml_bank_activate
    lea.l %sp@(16),%sp
    movel ml_bank_empty,%d0
    movel %d0,ml_pattern
    movel %a2,ml_bank_table
    movel %d3,ml_store_owner_id
    movel %a3,%d0
    bra .Lpub_out
.Lpub_fail:
    moveq #0,%d0
.Lpub_out:
    movel %sp@(20),%d1
    movew %d1,%sr
    moveml %sp@,%d2-%d4/%a2-%a3
    lea.l %sp@(24),%sp
    rts
