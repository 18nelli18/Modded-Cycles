| Genie B : candidat privé UI, publication au pas zéro de la voie ciblée.
| Aucun objet audio ni p-lock natif ; appels A délégués sans changement.
    .text
    .globl ml_genie_key,ml_genie_settings
| Getter PAGE côté B : SETTINGS local, sans les gardes de vue audio de SG.
ml_genie_key:
    tstl mlp_obj
    beq .Lgk_chain
    cmpal ml_gk_event,%a0
    bne .Lgk_fresh
    movel %a0@(8),%d0
    cmpl ml_gk_time,%d0
    beq .Lgk_eat
.Lgk_fresh:
    movel %a0@(16),%d1
    btst #0,%d1
    bne .Lgk_down
    tstl ml_gk_taken
    beq .Lgk_native
    clrl ml_gk_taken
    bra .Lgk_record
.Lgk_down:
    tstl ml_gk_taken
    bne .Lgk_record
    btst #3,%d1
    bne .Lgk_native
    tstl ml_genie_settings
    beq .Lgk_native
    tstl mlp_func
    bne .Lgk_native
    btst #1,%d1
    bne .Lgk_native
    tstl SG_obj
    bne .Lgk_native
    movew %sr,%d0
    andil #0x700,%d0
    bne .Lgk_native
    moveq #1,%d0
    movel %d0,TG_mod_used
    movel %d0,ml_gk_taken
    movel %a0,%sp@-
    jsr SG_open
    moveal %sp@+,%a0
.Lgk_record:
    movel %a0,ml_gk_event
    movel %a0@(8),%d0
    movel %d0,ml_gk_time
.Lgk_eat:
    movel %a0@(16),%d1
    oril #8,%d1
    movel %d1,%a0@(16)
    moveq #0,%d0
    rts
.Lgk_native:
    jmp ML_original_key
.Lgk_chain:
    jmp ml_key_next
    .globl ml_genie_generate,ml_genie_undo,ml_genie_boundary,ml_genie_pad,ml_genie_service,ml_genie_menu_key
ml_genie_generate:
    bsr ml_genie_is_b
    tstl %d0
    beq .Lgg_audio
    lea.l %sp@(-832),%sp
    movem.l %d2-%d7/%a2-%a5,%sp@
    movew %sr,%d0
    andil #0x700,%d0
    bne .Lgg_error
    .ifdef ML_STORAGE2
    tstl ml_store_load_ready
    beq .Lgg_error
    .endif
    tstl ml_gq_state
    bne .Lgg_error
    moveal ml_pattern,%a2
    movel mlp_track,%d2
    tstl mlp_obj
    bne .Lgg_target_ready
    | L'objet UI peut disparaître sous un overlay : ne jamais tomber vers A.
    moveal ml_genie_b_pattern,%a2
    movel ml_genie_b_track,%d2
    cmpal ml_pattern,%a2
    bne .Lgg_error
.Lgg_target_ready:
    tstl %a2
    beq .Lgg_error
    cmpil #5,%d2
    bhi .Lgg_error
    muluw #264,%d2
    addal %d2,%a2
    moveq #0,%d4
    moveb %a2@(4),%d4
    subql #1,%d4
    cmpil #63,%d4
    bhi .Lgg_error
    addql #1,%d4
    .ifdef ML_GENIE_CHANCE
    jsr ml_repeat_prepare_ui
    jsr ml_gc_capture
    tstl %d0
    beq .Lgg_error
    .endif
    | Copier une image cohérente, pas de génération sous masque IRQ.
    movew %sr,%d3
    movew #0x2700,%sr
    moveal %a2,%a0
    lea.l ml_gq_before,%a1
    bsr .Lgg_copy
    movew %d3,%sr
    lea.l SG_config,%a0
    movel %d4,%a0@
    moveq #0,%d0
    moveb TG_scale_state,%d0
    movel %d0,%a0@(16)
    moveb TG_key_state,%d0
    andil #255,%d0
    movel %d0,%a0@(20)
    lea.l %sp@(40),%a3
    moveal %a3,%a1
    jsr SG_generate
    tstl %d0
    bmi .Lgg_error
    | Façade de lecture 722 octets pour rythme/notes/mutation/Euclide.
    lea.l %sp@(104),%a4
    moveal %a4,%a0
    movel #180,%d0
.Lgg_zero:
    clrl %a0@+
    subql #1,%d0
    bpl .Lgg_zero
    moveq #0,%d2
    lea.l ml_gq_before+8,%a5
.Lgg_facade:
    moveq #0,%d0
    moveb %a5@(3),%d0
    andil #1,%d0
    movew %d0,%a4@(0,%d2:l:2)
    lea.l %a4@(580),%a0
    moveb %a5@,%a0@(0,%d2:l)
    lea.l %a5@(4),%a5
    addql #1,%d2
    cmpl %d4,%d2
    bcs .Lgg_facade
    moveal %a4,%a0
    moveal %a3,%a1
    movel %d4,%d0
    jsr SG_advanced_steps
    pea ml_gq_after
    movel %d4,%sp@-
    movel %a3,%sp@-
    pea ml_gq_before
    jsr ml_genie_notes
    lea.l %sp@(16),%sp
    tstl %d0
    beq .Lgg_error
    tstl SG_options
    beq .Lgg_publish
    | Vélocité seulement ; pan/decay n'existent pas dans le format MIDI B.
    movel SG_config+24,%d7
    lea.l ml_gq_after+8,%a5
    moveq #0,%d2
.Lgg_velocity:
    moveq #0,%d0
    moveb %a3@(0,%d2:l),%d0
    cmpil #254,%d0
    beq .Lgg_velocity_next
    btst #0,%a5@(3)
    beq .Lgg_velocity_next
    jsr SG_random
    lea.l SG_advanced,%a0
    jsr SG_random_range
    tstl %d0
    ble .Lgg_error
    cmpil #127,%d0
    bhi .Lgg_error
    moveb %d0,%a5@(1)
.Lgg_velocity_next:
    lea.l %a5@(4),%a5
    addql #1,%d2
    cmpl %d4,%d2
    bcs .Lgg_velocity
    movel %d7,SG_config+24
.Lgg_publish:
    movel %a2,ml_gq_lane
    movel ml_pattern,%d0
    movel %d0,ml_gq_pattern
    movel mlp_track,%d0
    movel %d0,ml_gq_track
    moveq #1,%d0
    movel %d0,ml_gq_kind
    | Publier l'état en dernier : IRQ ne voit jamais un candidat incomplet.
    movel %d0,ml_gq_state
    movel %d0,SG_undo_valid
    clrl SG_error
    tstl 0x40a7883c
    bne .Lgg_done
    movew %sr,%d3
    movew #0x2700,%sr
    moveal %a2,%a0
    bsr .Lgb_commit
    movew %d3,%sr
    bra .Lgg_done
.Lgg_error:
    moveq #1,%d0
    movel %d0,SG_error
.Lgg_done:
    movem.l %sp@,%d2-%d7/%a2-%a5
    lea.l %sp@(832),%sp
    rts
.Lgg_audio:
    jmp SG_action_generate

| UI : Stop applique une demande en attente ; changer de pattern l'annule.
ml_genie_service:
    movel %d2,%sp@-
    movew %sr,%d2
    movel %d2,%d0
    andil #0x700,%d0
    bne .Lgs_return
    tstl ml_gq_state
    beq .Lgs_done
    movel ml_pattern,%d0
    cmpl ml_gq_pattern,%d0
    beq .Lgs_same
    clrl ml_gq_state
    bra .Lgs_done
.Lgs_same:
    tstl 0x40a7883c
    bne .Lgs_done
    movew #0x2700,%sr
    moveal ml_gq_lane,%a0
    bsr .Lgb_commit
    movew %d2,%sr
.Lgs_done:
    tstl mlp_obj
    beq .Lgs_return
    movel ml_gq_state,%d0
    bne .Lgs_availability
    tstl ml_gu_valid
    beq .Lgs_availability
    movel ml_pattern,%d1
    cmpl ml_gu_pattern,%d1
    bne .Lgs_availability
    movel mlp_track,%d1
    cmpl ml_gu_track,%d1
    bne .Lgs_availability
    moveq #1,%d0
.Lgs_availability:
    cmpl SG_undo_valid,%d0
    beq .Lgs_return
    movel %d0,SG_undo_valid
    tstl SG_obj
    beq .Lgs_return
    movel SG_obj,%sp@-
    jsr 0x40076082
    addql #4,%sp
.Lgs_return:
    movel %sp@+,%d2
    rts

ml_genie_undo:
    bsr ml_genie_is_b
    tstl %d0
    beq .Lgu_audio
    movew %sr,%d0
    andil #0x700,%d0
    bne .Lgu_done
    | Undo d'une demande encore en attente = annulation, sans toucher la voie.
    tstl ml_gq_state
    beq .Lgu_restore
    clrl ml_gq_state
    movel ml_gu_valid,%d0
    movel %d0,SG_undo_valid
    clrl SG_error
    rts
.Lgu_restore:
    tstl ml_gu_valid
    beq .Lgu_done
    movel ml_pattern,%d0
    cmpl ml_gu_pattern,%d0
    bne .Lgu_done
    movel mlp_track,%d0
    cmpl ml_gu_track,%d0
    bne .Lgu_done
    .ifdef ML_GENIE_CHANCE
    jsr ml_repeat_prepare_ui
    jsr ml_gc_capture
    tstl %d0
    beq .Lgu_done
    jsr ml_gc_restore_candidate
    .endif
    lea.l %sp@(-12),%sp
    movem.l %d2-%d3/%a2,%sp@
    movew %sr,%d2
    andil #0x700,%d2
    bne .Lgu_out
    moveal ml_gu_lane,%a2
    movew %sr,%d3
    movew #0x2700,%sr
    moveal %a2,%a0
    lea.l ml_gq_before,%a1
    bsr .Lgg_copy
    movew %d3,%sr
    lea.l ml_gu_data,%a0
    lea.l ml_gq_after,%a1
    bsr .Lgg_copy
    movel %a2,ml_gq_lane
    movel ml_pattern,%d0
    movel %d0,ml_gq_pattern
    movel mlp_track,%d0
    movel %d0,ml_gq_track
    clrl ml_gq_kind
    moveq #1,%d0
    movel %d0,ml_gq_state
    tstl 0x40a7883c
    bne .Lgu_out
    movew #0x2700,%sr
    moveal %a2,%a0
    bsr .Lgb_commit
    movew %d3,%sr
.Lgu_out:
    movem.l %sp@,%d2-%d3/%a2
    lea.l %sp@(12),%sp
.Lgu_done:
    rts
.Lgu_audio:
    jmp SG_action_undo

| a0=voie, d0=index, d1=pas. Appelé avant de lire les données du pas zéro.
ml_genie_boundary:
    tstl %d1
    bne .Lgb_done
    tstl ml_gq_state
    beq .Lgb_done
    cmpl ml_gq_track,%d0
    bne .Lgb_done
    cmpal ml_gq_lane,%a0
    bne .Lgb_done
.Lgb_commit:
    lea.l %sp@(-20),%sp
    movem.l %d2/%a2-%a5,%sp@
    moveal %a0,%a2
    moveal %a0,%a3
    lea.l ml_gq_before,%a4
    moveq #65,%d2
.Lgb_compare:
    movel %a3@+,%d0
    cmpl %a4@+,%d0
    bne .Lgb_cancel
    subql #1,%d2
    bpl .Lgb_compare
    .ifdef ML_GENIE_CHANCE
    jsr ml_gc_validate
    tstl %d0
    beq .Lgb_cancel
    .endif
    tstl ml_gq_kind
    beq .Lgb_restore
    moveal %a2,%a0
    lea.l ml_gu_data,%a1
    bsr .Lgg_copy
    movel %a2,ml_gu_lane
    movel ml_gq_pattern,%d0
    movel %d0,ml_gu_pattern
    movel ml_gq_track,%d0
    movel %d0,ml_gu_track
    moveq #1,%d0
    movel %d0,ml_gu_valid
    .ifdef ML_GENIE_CHANCE
    jsr ml_gc_save_undo
    .endif
    bra .Lgb_write
.Lgb_restore:
    clrl ml_gu_valid
.Lgb_write:
    .ifdef ML_GENIE_CHANCE
    jsr ml_gc_apply
    .endif
    lea.l ml_gq_after,%a0
    moveal %a2,%a1
    bsr .Lgg_copy
.Lgb_cancel:
    clrl ml_gq_state
    movem.l %sp@,%d2/%a2-%a5
    lea.l %sp@(20),%sp
.Lgb_done:
    rts
.Lgg_copy:
    moveq #65,%d0
.Lgg_copy_loop:
    movel %a0@+,%a1@+
    subql #1,%d0
    bpl .Lgg_copy_loop
    rts

ml_genie_pad:
    tstl mlp_obj
    bne .Lgp_b_present
    bsr ml_genie_is_b
    tstl %d0
    beq .Lgp_audio
    | Un overlay B sans objet sous-jacent ne joue jamais les pads audio.
    moveq #1,%d0
    rts
.Lgp_b_present:
    | La vue Genie est au-dessus de B ; utiliser son état FUNC, ses pads B.
    movel SG_func,%d0
    movel %d0,mlp_func
    movel %sp@(8),%sp@-
    movel mlp_obj,%d0
    addil #16,%d0
    movel %d0,%sp@-
    jsr mlp_pad
    addql #8,%sp
    rts
.Lgp_audio:
    jmp SG_pad

| Le release FUNC du menu supérieur doit aussi libérer le modificateur B.
ml_genie_menu_key:
    movel %d2,%sp@-
    movel %sp@(12),%sp@-
    movel %sp@(12),%sp@-
    jsr SG_menu_key
    addql #8,%sp
    movel %d0,%d2
    tstl mlp_obj
    beq .Lgmk_done
    movel SG_func,%d0
    movel %d0,mlp_func
.Lgmk_done:
    movel %d2,%d0
    movel %sp@+,%d2
    rts
    .data
    .balign 4
ml_genie_settings: .long 0
ml_gk_taken: .long 0
ml_gk_event: .long 0
ml_gk_time: .long 0
    .globl ml_gq_state,ml_gq_lane,ml_gq_track,ml_gq_pattern,ml_gq_before,ml_gq_after,ml_gu_valid
ml_gq_state: .long 0
ml_gq_lane: .long 0
ml_gq_track: .long 0
ml_gq_pattern: .long 0
ml_gq_kind: .long 0
ml_gu_valid: .long 0
ml_gu_lane: .long 0
ml_gu_pattern: .long 0
ml_gu_track: .long 0
ml_gq_before: .space 264
ml_gq_after: .space 264
ml_gu_data: .space 264

    .text
    .globl ml_genie_present
| La page MACHINES ferme le groupe 2 à la présentation. En B seulement,
| masquer ce vecteur pendant l'appel natif conserve l'éditeur sous Genie.
| Restaurer immédiatement le vecteur : son allocation appartient à l'OS.
ml_genie_present:
    moveal %sp@(8),%a0
    moveal %a0@,%a0
    cmpal SG_obj,%a0
    bne .Lgpr_native
    clrl ml_genie_b_owner
    tstl mlp_obj
    beq .Lgpr_native
    movel %a0,ml_genie_b_owner
    movel ml_pattern,%d0
    movel %d0,ml_genie_b_pattern
    movel mlp_track,%d0
    movel %d0,ml_genie_b_track
    lea.l %sp@(-8),%sp
    moveml %d2/%a2,%sp@
    moveal %a0,%a2
    movel %a2@(32),%d2
    movel %a2@(28),%d0
    movel %d0,%a2@(32)
    movel %sp@(20),%sp@-
    movel %sp@(20),%sp@-
    movel %sp@(20),%sp@-
    jsr 0x4007700e
    lea.l %sp@(12),%sp
    movel %d2,%a2@(32)
    moveml %sp@,%d2/%a2
    lea.l %sp@(8),%sp
    rts
.Lgpr_native:
    jmp 0x4007700e

| Le contexte appartient à cet objet Genie, jamais à une prochaine ouverture A.
    .globl ml_genie_is_b
ml_genie_is_b:
    moveq #1,%d0
    tstl mlp_obj
    bne .Lgb_yes
    movel SG_obj,%d0
    beq .Lgb_yes
    cmpl ml_genie_b_owner,%d0
    seq %d0
    andil #1,%d0
.Lgb_yes:
    rts
    .data
    .balign 4
    .globl ml_genie_b_owner,ml_genie_b_pattern,ml_genie_b_track
ml_genie_b_owner: .long 0
ml_genie_b_pattern: .long 0
ml_genie_b_track: .long 0
