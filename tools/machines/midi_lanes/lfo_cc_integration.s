| LFO CC : contexte privé3020o, deux snapshots cfg192+frames952.
| UI écrit seulement le snapshot inactif ; IRQ lit seulement l'actif.
| États384, file148 et cadence4 séparés. Aucun setter de piste audio.
    .data
    .balign 4
    .globl mlcc_context,mlcc_triggers
mlcc_context: .long 0
mlcc_triggers: .long 0
    .text
    .globl mlcc_prepare,mlcc_refresh,mlcc_audio,mlcc_ready,mlcc_worker
mlcc_prepare:
    movel %a2,%sp@-
    movew %sr,%d0
    andil #0x700,%d0
    bne .Lprep_done
    tstl mlcc_context
    bne .Lprep_done
    pea 3020
    jsr 0x400802e0
    addql #4,%sp
    moveal %d0,%a2
    tstl %a2
    beq .Lprep_done
    moveal %a2,%a0
    movel #754,%d0
.Lprep_zero:
    clrl %a0@+
    subql #1,%d0
    bpl .Lprep_zero
    movel %a2,%sp@-
    jsr mlcc_cfg_init
    addql #4,%sp
    movel %a2,mlcc_settings
    movel %a2,mlcc_context
    jsr mlcc_refresh
.Lprep_done:
    movel %sp@+,%a2
    rts
mlcc_refresh:
    lea %sp@(-12),%sp
    moveml %a2-%a4,%sp@
    moveal mlcc_context,%a2
    tstl %a2
    beq .Lrefresh_done
    lea %a2@(192),%a3
    cmpal %a2@(3016),%a3
    bne .Lrefresh_copy
    lea %a2@(1336),%a3
.Lrefresh_copy:
    moveal %a2,%a0
    moveal %a3,%a1
    moveq #47,%d0
.Lrefresh_cfg:
    movel %a0@+,%a1@+
    subql #1,%d0
    bpl .Lrefresh_cfg
    clrl %sp@-
    pea %a3@(192)
    movel %a3,%sp@-
    jsr mlcc_frame_prepare
    lea %sp@(12),%sp
    tstl %d0
    beq .Lrefresh_done
    pea 1
    pea %a3@(668)
    movel %a3,%sp@-
    jsr mlcc_frame_prepare
    lea %sp@(12),%sp
    tstl %d0
    beq .Lrefresh_done
    movel %a3,%a2@(3016)
.Lrefresh_done:
    moveml %sp@,%a2-%a4
    lea %sp@(12),%sp
    rts
| Même ABI trois arguments que l'appel LFO natif ; garder le dispatch LFO2.
mlcc_audio:
    lea %sp@(-32),%sp
    moveml %d2-%d5/%a2-%a5,%sp@
    movel %sp@(44),%sp@-
    movel %sp@(44),%sp@-
    movel %sp@(44),%sp@-
    jsr MLCC_audio_next
    lea %sp@(12),%sp
    moveal mlcc_context,%a2
    tstl %a2
    beq .Laudio_done
    moveal %a2@(3016),%a3
    tstl %a3
    beq .Laudio_done
    moveal ml_play_pattern,%a5
    tstl %a5
    beq .Laudio_done
    movel mlcc_triggers,%d5
    clrl mlcc_triggers
    moveq #0,%d2
.Laudio_lfo:
    movel %d2,%d0
    muluw #476,%d0
    lea %a3@(192),%a4
    addal %d0,%a4
    movel %a4,%sp@-
    jsr mlcc_frame_reset
    addql #4,%sp
    movel %d2,%d0
    muluw #192,%d0
    lea %a2@(2480),%a0
    addal %d0,%a0
    movel %a0,%sp@-
    movel %d5,%sp@-
    movel %sp@(48),%sp@-
    movel %a4,%sp@-
    jsr lf2_update
    lea %sp@(16),%sp
    moveq #0,%d3
.Laudio_lane:
    movel %d2,%d0
    muluw #192,%d0
    lea %a2@(2480),%a0
    addal %d0,%a0
    movel %d3,%sp@-
    movel %a0,%sp@-
    jsr mlcc_value
    addql #8,%sp
    cmpil #127,%d0
    bhi .Laudio_next_lane
    movel %d3,%d1
    lsll #5,%d1
    movel %d2,%d4
    lsll #4,%d4
    addl %d4,%d1
    moveq #0,%d4
    movew %a3@(6,%d1:l),%d4
    movel %d0,%sp@-
    movel %d4,%sp@-
    movel %d2,%sp@-
    movel %d3,%sp@-
    movel %a5,%sp@-
    pea %a2@(2864)
    jsr mlcc_lane_put
    lea %sp@(24),%sp
.Laudio_next_lane:
    addql #1,%d3
    cmpil #6,%d3
    bcs .Laudio_lane
    addql #1,%d2
    cmpil #2,%d2
    bcs .Laudio_lfo
    pea %a2@(3012)
    jsr mlcc_rate_tick
    addql #4,%sp
.Laudio_done:
    moveml %sp@,%d2-%d5/%a2-%a5
    lea %sp@(32),%sp
    rts
mlcc_ready:
    moveq #0,%d0
    moveal mlcc_context,%a0
    tstl %a0
    beq .Lready_done
    movel %a0@(3012),%d1
    cmpil #6,%d1
    bcs .Lready_done
    lea %a0@(2872),%a0
    moveq #11,%d1
.Lready_scan:
    tstl %a0@
    bne .Lready_yes
    lea %a0@(12),%a0
    subql #1,%d1
    bpl .Lready_scan
    bra .Lready_done
.Lready_yes:
    moveq #1,%d0
.Lready_done:
    rts
mlcc_worker:
    lea %sp@(-16),%sp
    moveml %d2-%d3/%a2-%a3,%sp@
    moveal mlcc_context,%a2
    tstl %a2
    beq .Lworker_done
    moveal ml_play_pattern,%a3
    tstl %a3
    beq .Lworker_done
    moveq #0,%d2
.Lworker_prune:
    tstb %a3@
    beq .Lworker_cancel
    tstb %a3@(1)
    bne .Lworker_cancel
    movel %d2,%d0
    muluw #24,%d0
    lea %a2@(2864),%a0
    addal %d0,%a0
    moveq #0,%d3
.Lworker_slot:
    tstl %a0@(8)
    beq .Lworker_next_slot
    moveq #0,%d0
    moveb %a3@(2),%d0
    oril #0xb0,%d0
    cmpb %a0@,%d0
    bne .Lworker_cancel
    moveq #0,%d0
    moveb %a3@(3),%d0
    cmpb %a0@(3),%d0
    bne .Lworker_cancel
.Lworker_next_slot:
    lea %a0@(12),%a0
    addql #1,%d3
    cmpil #2,%d3
    bcs .Lworker_slot
    bra .Lworker_next_lane
.Lworker_cancel:
    movel %d2,%sp@-
    pea %a2@(2864)
    jsr mlcc_lane_cancel
    addql #8,%sp
.Lworker_next_lane:
    lea %a3@(264),%a3
    addql #1,%d2
    cmpil #6,%d2
    bcs .Lworker_prune
    pea %a2@(3012)
    pea %a2@(2864)
    jsr mlcc_rate_service
    addql #8,%sp
.Lworker_done:
    moveml %sp@,%d2-%d3/%a2-%a3
    lea %sp@(16),%sp
    rts
