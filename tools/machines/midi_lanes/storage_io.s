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
    .ifdef ML_CC_STORAGE
    beq .Lread_size_ok
    cmpil #176,%d0
    beq .Lread_size_ok
    cmpil #9248,%d0
    .endif
    bne .Lread_out
.Lread_size_ok:
    lea.l %sp@(16),%a2
    clrl %a2@
    clrl %a2@(4)
    clrl %a2@(8)
    clrl %a2@(12)
    .ifdef ML_STORAGE2
    moveq #5,%d0
    movel %d0,ml_store_file_error
    .endif
    movel %a2,%sp@-
    pea .Lread_mode
    movel %a0,%sp@-
    jsr 0x4007bc5e
    lea.l %sp@(12),%sp
    tstl %d0
    bne .Lread_out
    movel %a2,%sp@-
    .ifdef ML_CC_STORAGE
    movel %sp@(56),%sp@-
    .else
    pea ML_RECORD_BYTES
    .endif
    movel %d2,%sp@-
    jsr 0x4007baaa
    lea.l %sp@(12),%sp
    movel %d0,%d3
    .ifdef ML_STORAGE2
    movel %d0,ml_store_file_count
    moveq #7,%d0
    movel %d0,ml_store_file_error
    .endif
    movel %a2,%sp@-
    jsr 0x4007bc1c
    addql #4,%sp
    tstl %d0
    bne .Lread_out
    .ifdef ML_STORAGE2
    moveq #6,%d0
    movel %d0,ml_store_file_error
    .endif
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
    .ifdef ML_CC_STORAGE
    cmpl %sp@(52),%d3
    .else
    cmpil #ML_RECORD_BYTES,%d3
    .endif
    bne .Lread_out
.Lread_success:
    .ifdef ML_STORAGE2
    clrl ml_store_file_error
    .endif
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
    .ifdef ML_STORAGE2
    movel %d0,%sp@-
    moveq #15,%d0
    movel %d0,ml_store_save_error
    movel %sp@+,%d0
    .endif
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
    .ifdef ML_CC_STORAGE
    beq .Lwrite_size_ok
    cmpil #176,%d0
    beq .Lwrite_size_ok
    cmpil #9248,%d0
    .endif
    bne .Lwrite_out
.Lwrite_size_ok:
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
    .ifdef ML_STORAGE2
    movel %d0,%sp@-
    moveq #16,%d0
    movel %d0,ml_store_save_error
    movel %sp@+,%d0
    .endif
    .ifdef ML_CC_STORAGE
    movel %sp@(52),%sp@-
    .else
    pea ML_RECORD_BYTES
    .endif
    clrl %sp@-
    movel %a2,%sp@-
    jsr 0x4007bb76
    lea.l %sp@(12),%sp
    tstl %d0
    bne .Lwrite_close
    | ABI des appelants OS/TG : tampon, taille, handle.
    .ifdef ML_STORAGE2
    movel %d0,%sp@-
    moveq #17,%d0
    movel %d0,ml_store_save_error
    movel %sp@+,%d0
    .endif
    | Écrire par petits blocs ; une écriture partielle positive avance le handle
    | natif. Zéro/erreur interrompt sans boucle infinie ; relecture entière ensuite.
    .ifdef ML_CC_STORAGE
    movel %sp@(52),%d3
    .else
    movel #ML_RECORD_BYTES,%d3
    .endif
.Lwrite_chunk:
    movel %d3,%d0
    cmpil #512,%d0
    bls .Lwrite_chunk_ready
    movel #512,%d0
.Lwrite_chunk_ready:
    movel %d0,%sp@(32)
    movel %a2,%sp@-
    movel %d0,%sp@-
    movel %d2,%sp@-
    jsr 0x4007bb0a
    lea.l %sp@(12),%sp
    .ifdef ML_STORAGE2
    movel %d0,ml_store_write_count
    .endif
    tstl %d0
    ble .Lwrite_close
    cmpl %sp@(32),%d0
    bhi .Lwrite_close
    addl %d0,%d2
    subl %d0,%d3
    bne .Lwrite_chunk
    .ifdef ML_STORAGE2
    movel %d0,%sp@-
    moveq #18,%d0
    movel %d0,ml_store_save_error
    movel %sp@+,%d0
    .endif
    movel %a2,%sp@-
    jsr 0x4007e2f6
    addql #4,%sp
    tstl %d0
    bne .Lwrite_close
    moveq #1,%d4
.Lwrite_close:
    .ifdef ML_STORAGE2
    movel ml_store_save_error,%sp@-
    movel %d0,%sp@-
    moveq #19,%d0
    movel %d0,ml_store_save_error
    movel %sp@+,%d0
    .endif
    movel %a2,%sp@-
    jsr 0x4007bc1c
    addql #4,%sp
    .ifdef ML_STORAGE2
    moveal %sp@+,%a0
    tstl %d0
    bne .Lwrite_close_failed
    movel %a0,ml_store_save_error
.Lwrite_close_failed:
    .endif
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

    .ifdef ML_STORAGE2
    .data
    .balign 4
    .globl ml_store_file_error,ml_store_file_count,ml_store_write_count
ml_store_file_error: .long 0
ml_store_file_count: .long 0
ml_store_write_count: .long 0
    .endif
