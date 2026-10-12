| MBK3 : six LFO2 audio par pattern, réglages seuls à +4896 (96 octets).
| Les phases et buffers restent privés ; aucun accès disque ni setter natif.
    .ifdef ML_STORAGE3
    .data
    .balign 4
    .globl ml_audio_lfo_owner
ml_audio_lfo_owner: .long 0
    .text
    .globl ml_audio_lfo_init,ml_audio_lfo_sync,ml_audio_lfo_capture,ml_audio_lfo_reset
ml_audio_lfo_init:
    moveal %sp@(4),%a0
    moveq #5,%d0
.Linit:
    movel #0x40000900,%a0@+
    movel #0x40007f00,%a0@+
    clrl %a0@+
    movel #0x00004000,%a0@+
    subql #1,%d0
    bpl .Linit
    moveq #1,%d0
    rts

ml_audio_lfo_capture:
    movew %sr,%d0
    andil #0x700,%d0
    bne .Lcapture_done
    moveal ml_audio_lfo_owner,%a1
    tstl %a1
    beq .Lcapture_done
    moveal LF2_context,%a0
    tstl %a0
    beq .Lcapture_done
    lea %a0@(192),%a0
    lea %a1@(4896),%a1
    moveq #23,%d0
.Lcapture:
    movel %a0@+,%d1
    movel %d1,%a1@+
    subql #1,%d0
    bpl .Lcapture
.Lcapture_done:
    rts

| Le Load retire les anciennes banques après cet appel : oublier leur adresse.
ml_audio_lfo_reset:
    movew %sr,%d0
    andil #0x700,%d0
    bne .Lreset_done
    clrl ml_audio_lfo_owner
    moveal LF2_context,%a0
    tstl %a0
    beq .Lreset_done
    movew %sr,%d0
    movel %d0,%sp@-
    movew #0x2700,%sr
    pea %a0@(192)
    jsr ml_audio_lfo_init
    addql #4,%sp
    movel %sp@+,%d0
    movew %d0,%sr
.Lreset_done:
    rts

ml_audio_lfo_sync:
    lea %sp@(-12),%sp
    moveml %a2-%a3/%d2,%sp@
    movew %sr,%d0
    andil #0x700,%d0
    bne .Lsync_done
    moveal ml_pattern,%a2
    tstl %a2
    beq .Lsync_done
    cmpal ml_audio_lfo_owner,%a2
    beq .Lsync_done
    jsr ml_audio_lfo_capture
    pea 0x8000100c
    jsr LF2_prepare
    addql #4,%sp
    tstl %d0
    beq .Lsync_done
    moveal LF2_context,%a3
    tstl %a3
    beq .Lsync_done
    movew %sr,%d2
    movew #0x2700,%sr
    moveal %a3,%a0
    moveq #47,%d0
.Lphase_clear:
    clrl %a0@+
    subql #1,%d0
    bpl .Lphase_clear
    lea %a2@(4896),%a1
    moveq #23,%d0
.Lrestore:
    movel %a1@+,%d1
    movel %d1,%a0@+
    subql #1,%d0
    bpl .Lrestore
    movel %a2,ml_audio_lfo_owner
    movew %d2,%sr
.Lsync_done:
    moveml %sp@,%a2-%a3/%d2
    lea %sp@(12),%sp
    rts
    .endif
