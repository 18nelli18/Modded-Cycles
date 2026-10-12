| Note 57 : adaptateurs de contexte publié. Aucun accès MIDI depuis l'audio.
| ml_audio_tick(now, playing) garde SR et les registres préservés par l'ABI.
    .text
    .globl ml_audio_tick,ml_ui_drain
ml_audio_tick:
    lea.l %sp@(-8),%sp
    movew %sr,%d0
    movel %d0,%sp@
    movel %a2,%sp@(4)
    moveal ml_context,%a2
    tstl %a2
    beq .Lat_done
    .ifdef ML_PATTERN_BANKS
    jsr ml_bank_follow
    .endif
    .ifdef ML_REPEAT
    | Service infra-pas avant le pas suivant ; nouveau pattern annule l'ancien.
    movel %sp@(16),%sp@-
    movel %sp@(16),%sp@-
    .ifdef ML_PATTERN_BANKS
    movel ml_play_pattern,%sp@-
    .else
    movel %a2,%sp@-
    .endif
    pea %a2@(1584)
    jsr ml_repeat_audio
    lea.l %sp@(16),%sp
    .endif
    movel %sp@(16),%sp@-
    movel %sp@(16),%sp@-
    pea %a2@(1904)
    .ifdef ML_PATTERN_BANKS
    movel ml_play_pattern,%sp@-
    .else
    movel %a2,%sp@-
    .endif
    pea %a2@(1584)
    jsr ml_clock
    lea.l %sp@(20),%sp
    .ifdef ML_WORKER
    jsr ml_worker_kick
    .endif
.Lat_done:
    movel %sp@(4),%a2
    movel %sp@,%d1
    movew %d1,%sr
    lea.l %sp@(8),%sp
    rts
ml_ui_drain:
    subql #4,%sp
    movew %sr,%d0
    movel %d0,%sp@
    movew %sr,%d0
    andil #0x0700,%d0
    bne .Lud_done
    moveal ml_context,%a0
    tstl %a0
    bne .Lud_ready
    | Préparer dès le premier service UI, avant la première ouverture.
    | Les voies vides peuvent ainsi garder leur phase pendant la lecture.
    jsr ml_prepare
    moveal ml_context,%a0
    tstl %a0
    beq .Lud_done
.Lud_ready:
    .ifdef ML_STORAGE
    jsr ml_store_service
    .endif
    .ifdef ML_LFO_CC
    jsr mlcc_prepare
    jsr mlcc_refresh
    jsr mlccp_tick
    .endif
    .ifdef ML_PATTERN_BANKS
    jsr ml_bank_ui_sync
    moveal ml_context,%a0
    .endif
    .ifdef ML_REPEAT
    jsr ml_repeat_prepare_ui
    moveal ml_context,%a0
    .endif
    .ifdef ML_GENIE
    jsr ml_genie_service
    moveal ml_context,%a0
    .endif
    .ifdef ML_WORKER
    .ifdef ML_MERGE
    jsr mm_prepare
    .endif
    jsr ml_worker_prepare
    jsr ml_worker_kick
    .else
    pea 8
    pea %a0@(1584)
    jsr ml_service
    addql #8,%sp
    pea 8
    pea ml_live_runtime
    jsr ml_service
    addql #8,%sp
    .endif
    jsr mlp_led_poll
.Lud_done:
    movel %sp@,%d1
    movew %d1,%sr
    lea.l %sp@(4),%sp
    rts
