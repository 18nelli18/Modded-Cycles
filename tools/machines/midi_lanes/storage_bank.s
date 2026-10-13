| Banque MBK2 : notes1584 + réglages/locks3120 + douze configs LFO192.
| Initialisation UI seulement ; aucune phase, file ou adresse sérialisée.
    .ifdef ML_STORAGE2
    .text
    .globl ml_store_bank_init
ml_store_bank_init:
    lea.l %sp@(-12),%sp
    moveml %d2/%a2-%a3,%sp@
    movew %sr,%d0
    andil #0x700,%d0
    bne .Lbank_init_fail
    moveal %sp@(16),%a2
    tstl %a2
    beq .Lbank_init_fail
    movel %a2,%d0
    andil #3,%d0
    bne .Lbank_init_fail
    movel %a2,%sp@-
    jsr ml_init
    addql #4,%sp
    lea.l %a2@(1584),%a3
    moveq #5,%d2
.Lbank_init_lane:
    movel #0x00082e00,%d0
    movel %d0,%a3@
    movel #0x05010000,%d0
    movel %d0,%a3@(4)
    pea %a3@(8)
    jsr ml_repeat_locks_init
    addql #4,%sp
    lea.l %a3@(520),%a3
    subql #1,%d2
    bpl .Lbank_init_lane
    pea %a2@(4704)
    jsr mlcc_cfg_init
    addql #4,%sp
    .ifdef ML_STORAGE3
    pea %a2@(4896)
    jsr ml_audio_lfo_init
    addql #4,%sp
    .endif
    bra .Lbank_init_done
.Lbank_init_fail:
    moveq #0,%d0
.Lbank_init_done:
    moveml %sp@,%d2/%a2-%a3
    lea.l %sp@(12),%sp
    rts
    .endif
