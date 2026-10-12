| Dossier annexe réservé : parent validé, nom simple, chemin absolu cohérent.
| ml_store_directory(parent,name,path,entry276) -> inode ou0.
| Contrat : seule tâche UI propriétaire de ces chemins, garde disque au boot.
| Ne jamais créer après une absence accompagnée d'une erreur physique.
    .text
    .globl ml_store_directory
ml_store_directory:
    lea.l %sp@(-20),%sp
    moveml %d2/%a2-%a5,%sp@
    moveq #0,%d2
    movel %sp@(24),%d0
    cmpil #2,%d0
    bcs .Ldir_out
    moveal %sp@(28),%a2
    moveal %sp@(32),%a3
    moveal %sp@(36),%a4
    tstl %a2
    beq .Ldir_out
    tstl %a3
    beq .Ldir_out
    tstl %a4
    beq .Ldir_out
    movel %a4,%d0
    andil #3,%d0
    bne .Ldir_out
    jsr ml_store_io_begin
    tstl %d0
    beq .Ldir_out
    movel %a4,%sp@-
    movel %a2,%sp@-
    movel %sp@(32),%sp@-
    jsr 0x4007ad86
    lea.l %sp@(12),%sp
    tstl ml_store_io_poison
    bne .Ldir_end
    cmpil #1,%d0
    beq .Ldir_validate
    tstl %d0
    bne .Ldir_end
    movel %a3,%sp@-
    jsr 0x4007ac46
    addql #4,%sp
    tstl %d0
    bne .Ldir_end
    tstl ml_store_io_poison
    bne .Ldir_end
    movel %a4,%sp@-
    movel %a2,%sp@-
    movel %sp@(32),%sp@-
    jsr 0x4007ad86
    lea.l %sp@(12),%sp
    cmpil #1,%d0
    bne .Ldir_end
.Ldir_validate:
    | Type1 = dossier, établi dans le résolveur natif 0x4007d5a6.
    moveq #0,%d0
    movew %a4@(4),%d0
    cmpil #1,%d0
    bne .Ldir_end
    movel %a4@,%d0
    cmpil #2,%d0
    bcs .Ldir_end
    movel %d0,%d2
.Ldir_end:
    jsr ml_store_io_end
    tstl %d0
    bne .Ldir_out
    moveq #0,%d2
.Ldir_out:
    movel %d2,%d0
    moveml %sp@,%d2/%a2-%a5
    lea.l %sp@(20),%sp
    rts
