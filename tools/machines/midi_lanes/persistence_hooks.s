| Note 98 : ABI stock rejouee, aucune E/S depuis notification Load ou IRQ.
    .text
    .globl mp_save_entry_hook,mp_save_exit_hook,mp_load_hook,mp_drain
    .globl mp_disk_read_hook,mp_disk_write_hook
mp_save_entry_hook:
    lea %sp@(-20),%sp
    moveml %d0-%d1/%a0-%a1,%sp@
    movew %sr,%d0
    movel %d0,%sp@(16)
    jsr mp_save_enter
    movel %sp@(16),%d0
    movew %d0,%sr
    moveml %sp@,%d0-%d1/%a0-%a1
    lea %sp@(20),%sp
    lea %sp@(-52),%sp
    moveml %d2-%d4/%a2-%fp,%sp@
    jmp 0x4000f76a
mp_save_exit_hook:
    tstb %d0
    beq .Lsave_done
    lea %sp@(-20),%sp
    moveml %d0-%d1/%a0-%a1,%sp@
    movew %sr,%d0
    movel %d0,%sp@(16)
    movel %d3,%sp@-
    movel %a4,%sp@-
    jsr mp_save_finish
    addql #8,%sp
    movel %sp@(16),%d0
    movew %d0,%sr
    moveml %sp@,%d0-%d1/%a0-%a1
    lea %sp@(20),%sp
.Lsave_done:
    moveml %sp@,%d2-%d4/%a2-%fp
    lea %sp@(52),%sp
    rts
mp_load_hook:
    lea %sp@(-20),%sp
    moveml %d0-%d1/%a0-%a1,%sp@
    movew %sr,%d1
    movel %d1,%sp@(16)
    tstb %d0
    beq .Lload_done
    tstl %d2
    beq .Lload_done
    moveal %d2,%a0
    movel %d3,%sp@-
    movel %a0@(8),%sp@-
    jsr mp_load_notice
    addql #8,%sp
.Lload_done:
    movel %sp@(16),%d0
    movew %d0,%sr
    moveml %sp@,%d0-%d1/%a0-%a1
    lea %sp@(20),%sp
    jmp 0xf0010096
mp_drain:
    jsr mp_ui
    moveal mp_api+68,%a0
    jmp %a0@
| Observer seulement nos erreurs ; ne jamais bloquer les sauvegardes natives A.
mp_disk_read_hook:
    movel %sp@(12),%sp@-
    movel %sp@(12),%sp@-
    movel %sp@(12),%sp@-
    bsr .Lnative_read
    lea %sp@(12),%sp
    bra .Ldisk_result
mp_disk_write_hook:
    movel %sp@(12),%sp@-
    movel %sp@(12),%sp@-
    movel %sp@(12),%sp@-
    bsr .Lnative_write
    lea %sp@(12),%sp
.Ldisk_result:
    tstl %d0
    beq .Ldisk_done
    tstl mp_busy
    beq .Ldisk_done
    moveq #1,%d1
    movel %d1,mp_poison
.Ldisk_done:
    rts
.Lnative_read:
    lea %sp@(-20),%sp
    moveml %d2-%d5/%a2,%sp@
    jmp 0x4008b252
.Lnative_write:
    lea %sp@(-20),%sp
    moveml %d2-%d5/%a2,%sp@
    jmp 0x4008b3fe
