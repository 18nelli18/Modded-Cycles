| Garde I/O persistante : toute erreur disque interdit les saves annexes
| jusqu'au reboot. Le cache OS peut conserver des octets périmés valides.
| MBK2 intercepte les entrées physiques read/write, y compris la finalisation
| native qui ignore les erreurs. Après erreur, aucune écriture physique ne passe.
| Ne jamais réinitialiser poison à begin().
    .data
    .balign 4
    .globl ml_store_io_poison,ml_store_io_busy
ml_store_io_poison: .long 0
ml_store_io_busy: .long 0
    .text
    .globl ml_store_disk_read,ml_store_io_begin,ml_store_io_end
ml_store_disk_read:
    | Conserver exactement l'ABI native (sector,taille,destination).
    movel %sp@(12),%sp@-
    movel %sp@(12),%sp@-
    movel %sp@(12),%sp@-
    .ifdef ML_STORAGE2
    jsr ml_store_disk_read_native
    .else
    jsr 0x4008b24a
    .endif
    lea.l %sp@(12),%sp
    tstl %d0
    beq .Ldisk_ok
    moveq #1,%d1
    movel %d1,ml_store_io_poison
.Ldisk_ok:
    rts
    .ifdef ML_STORAGE2
    .globl ml_store_disk_write
ml_store_disk_write:
    tstl ml_store_io_poison
    bne .Lwrite_blocked
    movel %sp@(12),%sp@-
    movel %sp@(12),%sp@-
    movel %sp@(12),%sp@-
    jsr ml_store_disk_write_native
    lea.l %sp@(12),%sp
    tstl %d0
    beq .Lwrite_done
    moveq #1,%d1
    movel %d1,ml_store_io_poison
.Lwrite_done:
    rts
.Lwrite_blocked:
    moveq #-1,%d0
    rts
| Rejouer le prologue natif avant la continuation, sans récursion du hook.
ml_store_disk_read_native:
    lea.l %sp@(-20),%sp
    moveml %d2-%d5/%a2,%sp@
    jmp 0x4008b252
ml_store_disk_write_native:
    lea.l %sp@(-20),%sp
    moveml %d2-%d5/%a2,%sp@
    jmp 0x4008b3fe
    .endif
ml_store_io_begin:
    moveq #0,%d0
    movew %sr,%d1
    andil #0x700,%d1
    bne .Lbegin_out
    tstl ml_store_io_poison
    bne .Lbegin_out
    tstl ml_store_io_busy
    bne .Lbegin_out
    moveq #1,%d0
    movel %d0,ml_store_io_busy
.Lbegin_out:
    rts
ml_store_io_end:
    moveq #0,%d0
    tstl ml_store_io_busy
    beq .Lend_out
    clrl ml_store_io_busy
    tstl ml_store_io_poison
    bne .Lend_out
    moveq #1,%d0
.Lend_out:
    rts
