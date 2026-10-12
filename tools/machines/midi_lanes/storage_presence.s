| Distinguer une absence vérifiée de deux fichiers illisibles/corrompus.
| presence(ctx) ->0 aucun fichier,1 au moins un présent,-1 erreur.
| Aucun mkdir ni écriture fichier ; scratch privé du contexte.
    .ifdef ML_STORAGE2
    .text
    .globl ml_store_presence
ml_store_presence:
    lea.l %sp@(-16),%sp
    moveml %d2/%a2-%a4,%sp@
    moveal %sp@(20),%a2
    moveal %a2@(16),%a4
    movel %a4,%sp@-
    pea .Lpresence_root
    pea 2
    jsr ml_store_lookup_checked
    lea.l %sp@(12),%sp
    tstl %d0
    ble .Lpresence_done
    movew %a4@(4),%d0
    cmpiw #1,%d0
    bne .Lpresence_error
    movel %a4@,%d2
    cmpil #2,%d2
    bcs .Lpresence_error
    moveal %a2@,%a3
    clrb %a3@(25)
    movel %a4,%sp@-
    pea %a3@(14)
    movel %d2,%sp@-
    jsr ml_store_lookup_checked
    lea.l %sp@(12),%sp
    moveb #47,%a3@(25)
    tstl %d0
    ble .Lpresence_done
    movew %a4@(4),%d0
    cmpiw #1,%d0
    bne .Lpresence_error
    movel %a4@,%d2
    cmpil #2,%d2
    bcs .Lpresence_error
    movel %a4,%sp@-
    pea %a3@(26)
    movel %d2,%sp@-
    jsr ml_store_lookup_checked
    lea.l %sp@(12),%sp
    tstl %d0
    bne .Lpresence_done
    moveal %a2@(4),%a3
    movel %a4,%sp@-
    pea %a3@(26)
    movel %d2,%sp@-
    jsr ml_store_lookup_checked
    lea.l %sp@(12),%sp
    bra .Lpresence_done
.Lpresence_error:
    moveq #-1,%d0
.Lpresence_done:
    moveml %sp@,%d2/%a2-%a4
    lea.l %sp@(16),%sp
    rts
.Lpresence_root: .asciz "ModdedCycles"
    .balign 2
    .endif
