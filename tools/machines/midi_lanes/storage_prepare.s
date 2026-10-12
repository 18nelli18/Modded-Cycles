| Allocation UI du contexte sidecar et de ses quatre buffers1616 privés.
| 44 contexte + deux chemins36 + quatre buffers1616 =6580 octets.
| Aucun accès disque ; publication du pointeur seulement après initialisation.
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
    .globl ml_store_prepare
ml_store_prepare:
    subql #4,%sp
    movel %a2,%sp@
    movew %sr,%d0
    andil #0x700,%d0
    bne .Lprepare_fail
    tstl ml_store_project_ctx
    bne .Lprepare_ok
    pea (116+4*ML_RECORD_BYTES)
    jsr 0x400802e0
    addql #4,%sp
    moveal %d0,%a2
    tstl %a2
    beq .Lprepare_fail
    moveal %a2,%a0
    movel #((116+4*ML_RECORD_BYTES)/4-1),%d0
.Lprepare_zero:
    clrl %a0@+
    subql #1,%d0
    bpl .Lprepare_zero
    lea.l %a2@(44),%a0
    movel %a0,%a2@
    lea.l %a2@(80),%a0
    movel %a0,%a2@(4)
    lea.l %a2@(116),%a0
    movel %a0,%a2@(8)
    lea.l %a2@(116+ML_RECORD_BYTES),%a0
    movel %a0,%a2@(12)
    lea.l %a2@(116+2*ML_RECORD_BYTES),%a0
    movel %a0,%a2@(16)
    lea.l %a2@(116+3*ML_RECORD_BYTES),%a0
    movel %a0,%a2@(20)
    movel %a2,ml_store_project_ctx
.Lprepare_ok:
    moveq #1,%d0
    bra .Lprepare_out
.Lprepare_fail:
    moveq #0,%d0
.Lprepare_out:
    movel %sp@,%a2
    addql #4,%sp
    rts
