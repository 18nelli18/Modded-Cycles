| Checkpoint WRK UI, jamais dans IRQ. Une banque examinée toutes les150
| trames audio (~100ms), stabilité2s avant écriture ; aucune réécriture
| d'un état identique. Le Save explicite conserve son espace SEQ.
    .ifdef ML_WORKING
    .data
    .balign 4
.Lstate: .long 0
.Lowner: .long 0
.Lserial: .long 0
.Lcursor: .long 0
.Llast: .long 0
    .text
    .globl ml_store_autosave
ml_store_autosave:
    lea %sp@(-24),%sp
    moveml %d2-%d4/%a2-%a4,%sp@
    movew %sr,%d0
    andil #0x700,%d0
    bne .Lauto_done
    tstl ml_store_ram_only
    bne .Lauto_done
    tstl ml_store_load_ready
    beq .Lauto_done
    tstl ml_store_load_active
    bne .Lauto_done
    tstl ml_store_io_busy
    bne .Lauto_done
    tstl ml_store_io_poison
    bne .Lauto_done
    movel TG_blk_clk,%d4
    movel %d4,%d0
    subl .Llast,%d0
    cmpil #150,%d0
    bcs .Lauto_done
    movel %d4,.Llast
    moveal .Lstate,%a2
    tstl %a2
    bne .Lauto_allocated
    pea 1536
    jsr 0x400802e0
    addql #4,%sp
    moveal %d0,%a2
    tstl %a2
    beq .Lauto_done
    movel %a2,.Lstate
    clrl .Lowner
.Lauto_allocated:
    movel ml_store_owner_id,%d2
    beq .Lauto_done
    cmpl .Lowner,%d2
    bne .Lauto_reset
    movel ml_store_load_serial,%d0
    cmpl .Lserial,%d0
    beq .Lauto_scan
.Lauto_reset:
    movel %d2,.Lowner
    movel ml_store_load_serial,%d0
    movel %d0,.Lserial
    moveal %a2,%a0
    movel #383,%d0
.Lauto_zero:
    clrl %a0@+
    subql #1,%d0
    bpl .Lauto_zero
    clrl .Lcursor
.Lauto_scan:
    movel .Lcursor,%d3
    movel %d3,%d0
    addql #1,%d0
    movel %d0,.Lcursor
    cmpil #96,%d0
    bcs .Lauto_index
    clrl .Lcursor
.Lauto_index:
    moveal ml_bank_table,%a0
    tstl %a0
    beq .Lauto_done
    moveal %a0@(0,%d3:l:4),%a3
    tstl %a3
    beq .Lauto_done
    jsr ml_audio_lfo_capture
    pea 4992
    movel %a3,%sp@-
    jsr ml_record_crc
    addql #8,%sp
    movel %d3,%d1
    lsll #4,%d1
    lea %a2@(0,%d1:l),%a4
    tstl %a4@(12)
    beq .Lauto_changed
    cmpl %a4@,%d0
    bne .Lauto_changed
    btst #1,%a4@(15)
    bne .Lauto_done
    movel %d4,%d0
    subl %a4@(4),%d0
    cmpil #3000,%d0
    bcs .Lauto_done
    pea 96
    movel %d2,%sp@-
    jsr ml_store_resolve_slot
    addql #8,%sp
    tstl %d0
    bmi .Lauto_done
    moveq #2,%d1
    movel %d1,ml_store_namespace
    movel %a3,%sp@-
    movel %d3,%sp@-
    movel %d0,%sp@-
    movel %d2,%sp@-
    movel ml_store_project_ctx,%sp@-
    jsr ml_store_session_save
    lea %sp@(20),%sp
    tstl %d0
    beq .Lauto_done
    moveq #3,%d0
    movel %d0,%a4@(12)
    bra .Lauto_done
.Lauto_changed:
    movel %d0,%a4@
    movel %d4,%a4@(4)
    moveq #1,%d0
    movel %d0,%a4@(12)
.Lauto_done:
    moveml %sp@,%d2-%d4/%a2-%a4
    lea %sp@(24),%sp
    rts
    .endif
