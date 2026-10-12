| Note 57 : lecture d'un enregistrement annexe vers un tampon de staging.
| ml_store_read(path,staging,taille=1616) -> 1 si lecture/fermeture complètes.
| Aucune donnée musicale active modifiée ; le décodeur valide ensuite.
| Refuse IPL>0 avant tout appel fichier. Aucun raccordement au flasher.
    .ifdef ML_STORAGE3
    .equ ML_DATA_BYTES,4992
    .equ ML_RECORD_BYTES,5024
    .else
    .ifdef ML_STORAGE2
    .equ ML_DATA_BYTES,4896
    .equ ML_RECORD_BYTES,4928
    .else
    .equ ML_DATA_BYTES,1584
    .equ ML_RECORD_BYTES,1616
    .endif
    .endif
    .text
    .globl ml_store_read
ml_store_read:
    lea.l %sp@(-40),%sp
    movem.l %d2-%d4/%a2,%sp@
    moveq #0,%d4
    movew %sr,%d0
    andil #0x0700,%d0
    bne .Lread_out
    moveal %sp@(44),%a0
    tstl %a0
    beq .Lread_out
    movel %sp@(48),%d2
    beq .Lread_out
    movel %sp@(52),%d0
    cmpil #ML_RECORD_BYTES,%d0
    bne .Lread_out
    lea.l %sp@(16),%a2
    clrl %a2@
    clrl %a2@(4)
    clrl %a2@(8)
    clrl %a2@(12)
    movel %a2,%sp@-
    pea .Lread_mode
    movel %a0,%sp@-
    jsr 0x4007bc5e
    lea.l %sp@(12),%sp
    tstl %d0
    bne .Lread_out
    movel %a2,%sp@-
    movel %d2,%sp@-
    pea ML_RECORD_BYTES
    jsr 0x4007baaa
    lea.l %sp@(12),%sp
    movel %d0,%d3
    movel %a2,%sp@-
    jsr 0x4007bc1c
    addql #4,%sp
    tstl %d0
    bne .Lread_out
    .ifdef ML_STORAGE3
    cmpil #4928,%d3
    bne .Lread_full
    moveal %d2,%a0
    movel %a0@,%d0
    cmpil #0x4d424b32,%d0
    bne .Lread_out
    movel %a0@(4),%d0
    cmpil #2,%d0
    bne .Lread_out
    bra .Lread_success
.Lread_full:
    .endif
    cmpil #ML_RECORD_BYTES,%d3
    bne .Lread_out
.Lread_success:
    moveq #1,%d4
.Lread_out:
    movel %d4,%d0
    movem.l %sp@,%d2-%d4/%a2
    lea.l %sp@(40),%sp
    rts
    .section .rodata
.Lread_mode: .asciz "r"

    .text
    .globl ml_store_write
| ml_store_write(path,record,ML_RECORD_BYTES) -> 1 seulement après toutes les étapes.
| Chemin annexe déjà préparé, copie inactive seulement. Ne crée pas de dossier.
| Finalisation native != garantie de durabilité ; aucun raccordement Save.
ml_store_write:
    lea.l %sp@(-40),%sp
    movem.l %d2-%d4/%a2,%sp@
    moveq #0,%d4
    movew %sr,%d0
    andil #0x700,%d0
    bne .Lwrite_out
    moveal %sp@(44),%a0
    tstl %a0
    beq .Lwrite_out
    movel %sp@(48),%d2
    beq .Lwrite_out
    movel %sp@(52),%d0
    cmpil #ML_RECORD_BYTES,%d0
    bne .Lwrite_out
    lea.l %sp@(16),%a2
    clrl %a2@
    clrl %a2@(4)
    clrl %a2@(8)
    clrl %a2@(12)
    movel %a2,%sp@-
    pea .Lwrite_mode
    movel %a0,%sp@-
    jsr 0x4007bc5e
    lea.l %sp@(12),%sp
    tstl %d0
    bne .Lwrite_out
    pea ML_RECORD_BYTES
    clrl %sp@-
    movel %a2,%sp@-
    jsr 0x4007bb76
    lea.l %sp@(12),%sp
    tstl %d0
    bne .Lwrite_close
    | ABI vérifiée par writer natif : taille, tampon, handle.
    movel %a2,%sp@-
    movel %d2,%sp@-
    pea ML_RECORD_BYTES
    jsr 0x4007bb0a
    lea.l %sp@(12),%sp
    cmpil #ML_RECORD_BYTES,%d0
    bne .Lwrite_close
    movel %a2,%sp@-
    jsr 0x4007e2f6
    addql #4,%sp
    tstl %d0
    bne .Lwrite_close
    moveq #1,%d4
.Lwrite_close:
    movel %a2,%sp@-
    jsr 0x4007bc1c
    addql #4,%sp
    tstl %d0
    beq .Lwrite_out
    moveq #0,%d4
.Lwrite_out:
    movel %d4,%d0
    movem.l %sp@,%d2-%d4/%a2
    lea.l %sp@(40),%sp
    rts
    .section .rodata
.Lwrite_mode: .asciz "w"
