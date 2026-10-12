| Note 57 : banque MIDI privée, édition de six voies et 64 pas.
| Construction/rendu adaptés de la page LFO 2, elle-même adaptée de
| Model-TG (TinyGregAudio, MIT), commit 70b39dd ; LICENSE-Model-TG.
| Canaux 7..12 immuables. Contexte fourni séparément, sans voix interne.
    .text
    .globl mlp_open,mlp_dtor0,mlp_dtor1
mlp_open:
    lea.l   mlp_opened,%a0
    clrl    %a0@
    lea.l   %sp@(-24),%sp
    moveml  %d2-%d4/%a2-%a4,%sp@
    moveq   #0,%d0                | uniquement dans la tâche UI, comme loop_toggle
    movew   %sr,%d0
    andil   #0x0700,%d0
    bnew    mlp_o_done
    .ifdef ML_PATTERN_BANKS
    jsr ml_bank_ui_sync
    tstl %d0
    beqw mlp_o_done
    .endif
    tstl ml_runtime
    beqw mlp_o_done
    tstl ml_pattern
    beqw mlp_o_done
    lea.l   mlp_obj,%a0
    tstl    %a0@
    bnew    mlp_o_done             | page déjà ouverte
    tstl    0x40fe4178
    beqw    mlp_o_done             | gestion des vues pas encore initialisée
    | groupe vtable privé, reconstruit depuis celui de l’OS
    lea.l   0x40117918,%a0
    lea.l   mlp_vt,%a1
    moveq   #(0xb0/4)-1,%d0
mlp_o_cp:
    movel   %a0@+,%a1@+
    subql   #1,%d0
    bplw    mlp_o_cp
    | DrumSelect n'hérite pas de LedHandler. Ajouter une vraie base dédiée,
    | reconnue par le dynamic_cast du gestionnaire ; conserver MidiHandler +8.
    lea.l mlp_vt,%a0
    movel #mlp_typeinfo,%d0
    movel %d0,%a0@(4)
    movel %d0,%a0@(0x54)
    movel %d0,%a0@(0x68)
    movel %d0,%a0@(0x7c)
    movel %d0,%a0@(0x90)
    movel %d0,%a0@(0xa4)
    lea.l   mlp_vt,%a1
    movel   #mlp_dtor0,%d0
    movel   %d0,%a1@(0x08)
    movel   #mlp_dtor1,%d0
    movel   %d0,%a1@(0x0c)
    movel   #mlp_menu_key,%d0
    movel   %d0,%a1@(0x10)
    movel   #mlp_render,%d0
    movel   %d0,%a1@(0x18)
    movel   #mlp_enc,%d0
    movel   %d0,%a1@(0x4c)
    movel   #mlp_enc_th,%d0
    movel   %d0,%a1@(0x60)
    movel #mlp_pad,%d0
    movel %d0,%a1@(0x9c)
    jmp mlp_o_allocate
    .section .text.mlp_open_allocate,"ax"
mlp_o_allocate:
    | Même sélection de piste que le menu LFO natif, sans la modifier.
    jsr 0x400cf866
    tstl %d0
    beq mlp_o_default_track
    movel %d0,%sp@-
    jsr 0x4000eb90
    movel %d0,%sp@-
    jsr 0x40012412
    addql #8,%sp
    cmpil #5,%d0
    bls mlp_o_track_ready
mlp_o_default_track:
    moveq #0,%d0
mlp_o_track_ready:
    movel %d0,mlp_track
    lea.l   0x400802e0,%a3        | operator new
    pea     0x510
    jsr     %a3@
    addql   #4,%sp
    tstl    %d0
    beqw    mlp_o_done
    movea.l %d0,%a4
    movel   %a4,%sp@-
    jsr     0x400a22b0            | constructeur OS de la page MACHINES
    addql   #4,%sp
    lea.l   mlp_vt,%a1
    lea.l   %a1@(8),%a0
    movel   %a0,%a4@              | vptr principal
    lea.l   %a1@(0x58),%a0
    movel   %a0,%a4@(4)           | base +4 (événements encodeur)
    lea.l mlp_led_vt+8,%a0
    movel %a0,%a4@(0x500)
    clrl %a4@(0x504)
    clrl %a4@(0x508)
    lea.l mlp_vt+0x94,%a0
    movel %a0,%a4@(16)
    pea     0x10                  | détenteur de référence, comme l’ouverture OS
    jsr     %a3@                  | construite à 0x4001ca40
    addql   #4,%sp
    tstl %d0
    bnew mlp_o_holder
    movel %a4,%sp@-
    jsr 0x400f4486
    addql #4,%sp
    braw mlp_o_done
mlp_o_holder:
    movea.l %d0,%a0
    movel %a4,mlp_obj
    clrl mlp_row
    clrl mlp_edit
    clrl mlp_func
    moveq #1,%d0
    movel %d0,mlp_func_inherited
    clrl mlp_pads
    clrl mlp_held
    clrl mlp_remove
    clrl mlp_changed
    clrl mlp_setup
    moveq   #1,%d1
    movel   #0x401000c4,%d0
    movel   %d0,%a0@
    movel   %d1,%a0@(4)
    movel   %d1,%a0@(8)
    movel   %a4,%a0@(12)
    movel   %a0,%sp@-             | {page, détenteur} sur la pile, détenteur au sommet
    movel   %a4,%sp@-
    jsr     0x400d0974
    movel   %d0,%sp@-
    jsr     0x400060d8
    addql   #4,%sp
    movea.l %sp,%a0
    clrl    %sp@-
    movel   %a0,%sp@-
    movel   %d0,%sp@-
    jsr     0x4007700e            | présenter
    lea.l   %sp@(12),%sp
    pea     %sp@(4)               | libérer notre référence au détenteur
    jsr     0x400cf23c
    lea.l   %sp@(12),%sp          | le pea et la paire
    lea.l   mlp_opened,%a0
    moveq   #1,%d0
    movel   %d0,%a0@
mlp_o_done:
    movel mlp_opened,%d0
    moveml  %sp@,%d2-%d4/%a2-%a4
    lea.l   %sp@(24),%sp
    rts

    .section .text.mlp_dtor,"ax"
| ---- destructeurs : oublier la page, puis appeler ceux de l’OS ----
mlp_dtor0:
    jsr mlp_keyboard_cancel
    .ifdef ML_CONDITIONS
    clrl ml_cond_fill
    .endif
    clrl mlp_held
    clrl mlp_func
    clrl mlp_pads
    lea.l   mlp_obj,%a0
    clrl    %a0@
    jmp     0x400f43ca
mlp_dtor1:
    jsr mlp_keyboard_cancel
    .ifdef ML_CONDITIONS
    clrl ml_cond_fill
    .endif
    clrl mlp_held
    clrl mlp_func
    clrl mlp_pads
    lea.l   mlp_obj,%a0
    clrl    %a0@
    jmp     0x400f4486


    .text
    .globl mlp_render
    .globl mlp_menu_key,mlp_enc,mlp_enc_th,mlp_pad
mlp_menu_key:
    lea.l %sp@(-12),%sp
    movem.l %d2-%d3/%a2,%sp@
    .ifdef ML_PATTERN_BANKS
    jsr ml_bank_ui_sync
    tstl %d0
    beq .Lmk_used
    .endif
    moveal %sp@(16),%a2
    moveal %sp@(20),%a0
    movel %a0@(12),%d2
    movel %a0@(16),%d3
    .ifdef ML_CONDITIONS
    cmpil #15,%d2
    bne .Lmk_fill_done
    movel %d3,%d0
    andil #1,%d0
    movel %d0,ml_cond_fill
.Lmk_fill_done:
    .endif
    .ifdef ML_CLIPBOARD
    movel %d3,%sp@-
    movel %d2,%sp@-
    jsr mlp_clip_key
    addql #8,%sp
    tstl %d0
    bne .Lmk_used
    .endif
    .ifdef ML_GENIE
    | Cette vue lit les événements bruts, sans forcément appeler le getter.
    cmpil #13,%d2
    bne .Lmk_settings_done
    btst #5,%d3
    bne .Lmk_settings_done
    movel %d3,%d0
    andil #1,%d0
    movel %d0,ml_genie_settings
.Lmk_settings_done:
    .endif
    cmpil #1,%d2
    beq .Lmk_func
    cmpil #10,%d2
    beq .Lmk_transport
    cmpil #11,%d2
    beq .Lmk_transport
    cmpil #32,%d2
    beq .Lmk_data
    | Ces touches gardent leurs handlers globaux, appuis et relâchements.
    cmpil #3,%d2
    beq .Lmk_global
    cmpil #8,%d2
    .ifdef ML_LFO_CC
    beq .Lmk_cc_lfo
    .else
    beq .Lmk_global
    .endif
    cmpil #9,%d2
    beq .Lmk_global
    cmpil #13,%d2
    beq .Lmk_global
    | Relâchement des trigs traité avant le filtre des appuis.
    cmpil #16,%d2
    bcs .Lmk_nontrig
    cmpil #31,%d2
    bhi .Lmk_nontrig
    movel %d3,%sp@-
    movel %d2,%sp@-
    jsr mlp_keyboard
    addql #8,%sp
    tstl %d0
    bne .Lmk_used
    btst #0,%d3
    beq .Lmk_trig_release
.Lmk_nontrig:
    movel %d3,%d0
    andil #9,%d0
    cmpil #1,%d0
    bne .Lmk_used
    cmpil #2,%d2
    beq .Lmk_track_setup
    .ifdef ML_REPEAT
    cmpil #4,%d2
    beq .Lmk_retrigger_setup
    .endif
    cmpil #12,%d2
    beq .Lmk_close
    cmpil #15,%d2
    beq .Lmk_page
    tstl mlp_func
    bne .Lmk_used
    subil #16,%d2
    cmpil #15,%d2
    bhi .Lmk_used
    movel mlp_held,%d0
    btst %d2,%d0
    bne .Lmk_used
    bset %d2,%d0
    movel %d0,mlp_held
    movel mlp_step,%d0
    andil #48,%d0
    addl %d2,%d0
    movel %d0,mlp_step
    tstl TG_set_held
    bne .Lmk_slide
    moveq #6,%d2
    movel %d2,mlp_row
    clrl mlp_edit
    jsr mlp_raw_value
    tstl %d0
    beq .Lmk_trig_new
    | d2 est la ligne 6 : retrouver l'index physique depuis le pas.
    movel mlp_step,%d1
    andil #15,%d1
    movel mlp_remove,%d0
    bset %d1,%d0
    movel %d0,mlp_remove
    bra .Lmk_trig_note
.Lmk_trig_new:
    | Nouveau trig : C5 (MIDI72), même après suppression d’une autre note.
    moveq #7,%d2
    moveq #72,%d0
    jsr mlp_store
    moveq #6,%d2
    moveq #1,%d0
    jsr mlp_store
.Lmk_trig_note:
    clrl mlp_setup
    moveq #7,%d0
    movel %d0,mlp_row
    moveq #1,%d0
    movel %d0,mlp_edit
    bra .Lmk_redraw
.Lmk_slide:
    | SETTINGS + TRIG bascule le legato et garde un vrai trig note.
    movel mlp_track,%d0
    muluw #264,%d0
    moveal ml_pattern,%a0
    addal %d0,%a0
    movel mlp_step,%d0
    lsll #2,%d0
    lea.l %a0@(8,%d0:l),%a0
    moveq #0,%d0
    moveb %a0@(3),%d0
    moveq #2,%d1
    eorl %d1,%d0
    oril #1,%d0
    movel %d0,%sp@-
    pea 3
    movel mlp_step,%sp@-
    movel mlp_track,%sp@-
    movel ml_pattern,%sp@-
    jsr ml_edit
    lea.l %sp@(20),%sp
    moveq #1,%d0
    movel %d0,TG_mod_used
    movel mlp_changed,%d0
    bset %d2,%d0
    movel %d0,mlp_changed
    bra .Lmk_trig_note
.Lmk_trig_release:
    subil #16,%d2
    movel mlp_held,%d0
    btst %d2,%d0
    beq .Lmk_used
    bclr %d2,%d0
    movel %d0,mlp_held
    movel mlp_remove,%d0
    btst %d2,%d0
    beq .Lmk_trig_clear
    movel mlp_changed,%d1
    btst %d2,%d1
    bne .Lmk_trig_clear
    movel mlp_step,%sp@-
    movel mlp_step,%d0
    andil #48,%d0
    addl %d2,%d0
    movel %d0,mlp_step
    movel %d2,%sp@-
    moveq #6,%d2
    moveq #0,%d0
    jsr mlp_store
    .ifdef ML_REPEAT
    jsr ml_repeat_delete_selected
    .endif
    movel %sp@+,%d2
    movel %sp@+,mlp_step
.Lmk_trig_clear:
    movel mlp_remove,%d0
    bclr %d2,%d0
    movel %d0,mlp_remove
    movel mlp_changed,%d0
    bclr %d2,%d0
    movel %d0,mlp_changed
    .ifdef ML_CONDITIONS
    tstl mlp_held
    bne .Lmk_redraw
    movel mlp_setup,%d0
    subql #5,%d0
    bne .Lmk_redraw
    clrl mlp_setup
    .endif
    bra .Lmk_redraw
.Lmk_track_setup:
    tstl mlp_func
    beq .Lmk_used
    tstl TG_set_held
    bne .Lmk_used
    jsr mlp_track_setup_open
    bra .Lmk_redraw
    .ifdef ML_REPEAT
.Lmk_retrigger_setup:
    tstl TG_set_held
    bne .Lmk_used
    tstl mlp_func
    bne .Lmk_retrigger_open
    tstl mlp_held
    beq .Lmk_used
    movel mlp_setup,%d0
    cmpil #4,%d0
    bne .Lmk_retrigger_open
    | Second appui RETRIG avec trig maintenu : activation privée du pas.
    jsr mlp_retrigger_toggle_step
    bra .Lmk_redraw
.Lmk_retrigger_open:
    jsr mlp_retrigger_open
    bra .Lmk_redraw
    .endif
.Lmk_page:
    .ifdef ML_GENIE
    tstl ml_genie_settings
    beq .Lmk_page_normal
    tstl mlp_func
    bne .Lmk_page_normal
    btst #1,%d3
    bne .Lmk_page_normal
    moveq #1,%d0
    movel %d0,TG_mod_used
    jsr SG_open
    bra .Lmk_used
.Lmk_page_normal:
    .endif
    tstl mlp_held
    bne .Lmk_used
    movel mlp_setup,%d0
    cmpil #2,%d0
    beq .Lmk_scale_page
    tstl mlp_func
    bne .Lmk_length
    btst #1,%d3
    bne .Lmk_length
    | PAGE parcourt uniquement les pages de la longueur de la voie.
    movel mlp_step,%d3
    andil #48,%d3
    addil #16,%d3
    moveq #3,%d2
    jsr mlp_raw_value
    cmpl %d0,%d3
    bcs .Lmk_page_set
    moveq #0,%d3
.Lmk_page_set:
    movel %d3,mlp_step
    bra .Lmk_redraw
.Lmk_scale_page:
    | PAGE dans Scale Setup avance Len au multiple de seize suivant.
    moveq #3,%d2
    jsr mlp_raw_value
    addil #16,%d0
    andil #112,%d0
    cmpil #64,%d0
    bls .Lmk_scale_store
    moveq #16,%d0
.Lmk_scale_store:
    jsr mlp_store
    bra .Lmk_redraw
.Lmk_length:
    | Vue Scale Setup privée, distincte du menu général de la banque.
    moveq #2,%d0
    movel %d0,mlp_setup
    moveq #1,%d0
    movel %d0,mlp_edit
    moveq #3,%d0
    movel %d0,mlp_row
    bra .Lmk_redraw
.Lmk_func:
    andil #1,%d3
    movel %d3,mlp_func
    | Consommer FUNC dans B : sinon QuickMuteMenu recouvre la banque et
    | les pads suivants coupent les pistes audio avant notre callback.
    tstl %d3
    bne .Lmk_func_down
    tstl mlp_func_inherited
    beq .Lmk_used
    | Seul le release du FUNC déjà pressé en A avant l'entrée est transmis.
    clrl mlp_func_inherited
    moveq #0,%d0
    bra .Lmk_return
.Lmk_func_down:
    clrl mlp_func_inherited
    bra .Lmk_used
    .ifdef ML_LFO_CC
.Lmk_cc_lfo:
    movel %d3,%d0
    andil #3,%d0
    bne .Lmk_used
    jsr mlp_keyboard_cancel
    clrl mlccp_index
    jsr mlccp_open
    bra .Lmk_used
    .endif
.Lmk_global:
    | Une page native peut capter les releases suivantes : couper le clavier
    | avant TEMPO/LFO/REC, sans toucher aux notes du séquenceur.
    btst #0,%d3
    beq .Lmk_global_done
    cmpil #13,%d2
    beq .Lmk_global_done
    jsr mlp_keyboard_cancel
    .ifdef ML_WORKER
    jsr ml_worker_kick
    .endif
.Lmk_global_done:
    moveq #0,%d0
    bra .Lmk_return
.Lmk_data:
    btst #4,%d3
    beq .Lmk_used
    tstl mlp_setup
    bne .Lmk_data_setup
    tstl mlp_held
    beq .Lmk_used
    | Clic tenu : Note -> Vel -> Len -> Note ; aucune écriture au clic.
    movel mlp_row,%d0
    addql #1,%d0
    cmpil #9,%d0
    bls .Lmk_data_step_row
    moveq #7,%d0
.Lmk_data_step_row:
    movel %d0,mlp_row
    bra .Lmk_redraw
.Lmk_data_setup:
    movel mlp_row,%d2
    cmpil #6,%d2
    beq .Lmk_toggle
    cmpil #10,%d2
    beq .Lmk_toggle
    moveq #1,%d0
    eorl %d0,mlp_edit
    bra .Lmk_redraw
.Lmk_toggle:
    jsr mlp_raw_value
    moveq #1,%d1
    eorl %d1,%d0
    jsr mlp_store
    bra .Lmk_redraw
.Lmk_close:
    tstl mlp_setup
    beq .Lmk_close_page
    clrl mlp_setup
    bra .Lmk_redraw
.Lmk_close_page:
    moveal %a2@,%a0
    moveal %a0@(0x28),%a0
    movel %a2,%sp@-
    jsr %a0@
    addql #4,%sp
    bra .Lmk_used
.Lmk_transport:
    btst #1,%d3
    bne .Lmk_used
    moveq #0,%d0
    bra .Lmk_return
.Lmk_redraw:
    movel %a2,%sp@-
    jsr mlp_redraw
    addql #4,%sp
.Lmk_used:
    moveq #1,%d0
.Lmk_return:
    movem.l %sp@,%d2-%d3/%a2
    lea.l %sp@(12),%sp
    rts

mlp_pad:
    lea.l %sp@(-12),%sp
    movem.l %d2/%a2-%a3,%sp@
    .ifdef ML_PATTERN_BANKS
    jsr ml_bank_ui_sync
    tstl %d0
    beq .Lmp_done
    .endif
    moveal %sp@(16),%a3
    lea.l %a3@(-16),%a3
    moveal %sp@(20),%a2
    movel %a2@(20),%d2
    subql #1,%d2
    cmpil #5,%d2
    bhi .Lmp_done
    movel mlp_pads,%d1
    tstl %a2@(16)
    beq .Lmp_release
    movel %a2@(16),%d0
    cmpil #1,%d0
    bne .Lmp_done
    btst %d2,%d1
    bne .Lmp_done
    bset %d2,%d1
    movel %d1,mlp_pads
    tstl mlp_func
    bne .Lmp_output
    tstl mlp_held
    bne .Lmp_done
    movel %d2,mlp_track
    pea 1
    movel %d2,%sp@-
    jsr mlp_pad_note
    addql #8,%sp
    bra .Lmp_redraw
.Lmp_output:
    movel %d2,%d0
    muluw #264,%d0
    moveal ml_pattern,%a0
    moveq #0,%d1
    moveb %a0@(0,%d0:l),%d1
    moveq #1,%d0
    eorl %d0,%d1
    movel %d1,%sp@-
    pea 0
    movel %d2,%sp@-
    movel %a0,%sp@-
    jsr ml_config
    lea.l %sp@(16),%sp
    movel %d2,%d0
    muluw #264,%d0
    moveal ml_pattern,%a0
    tstb %a0@(0,%d0:l)
    bne .Lmp_redraw
    movel %d2,%sp@-
    movel ml_runtime,%sp@-
    jsr ml_quiet
    addql #8,%sp
    movel %d2,%sp@-
    pea ml_live_runtime
    jsr ml_quiet
    addql #8,%sp
    .ifdef ML_WORKER
    jsr ml_worker_kick
    .endif
.Lmp_redraw:
    movel %a3,%sp@-
    jsr mlp_redraw
    addql #4,%sp
    bra .Lmp_done
.Lmp_release:
    bclr %d2,%d1
    movel %d1,mlp_pads
    clrl %sp@-
    movel %d2,%sp@-
    jsr mlp_pad_note
    addql #8,%sp
.Lmp_done:
    moveq #1,%d0
    movem.l %sp@,%d2/%a2-%a3
    lea.l %sp@(12),%sp
    rts

mlp_enc_th:
    subql #4,%sp@(4)
mlp_enc:
    lea.l %sp@(-16),%sp
    movem.l %d2-%d4/%a2,%sp@
    .ifdef ML_PATTERN_BANKS
    jsr ml_bank_ui_sync
    tstl %d0
    beq .Lme_out
    .endif
    moveal %sp@(20),%a2
    moveal %sp@(24),%a0
    movel %a0@(12),%d0
    .ifdef ML_CONDITIONS
    cmpil #13,%d0
    beq .Lme_chance_knob
    .endif
    cmpil #1,%d0
    bne .Lme_out
    pea 1
    pea 1
    movel %a0,%sp@-
    jsr 0x4006f73a
    lea.l %sp@(12),%sp
    tstl %d0
    beq .Lme_out
    moveq #1,%d3
    tstl %d0
    bpl .Lme_sign
    moveq #-1,%d3
.Lme_sign:
    movel mlp_setup,%d0
    .ifdef ML_CONDITIONS
    cmpil #5,%d0
    beq .Lme_chance_delta
    .endif
    .ifdef ML_REPEAT
    cmpil #4,%d0
    bne .Lme_not_retrigger
    movel %d3,%sp@-
    jsr mlp_retrigger_enc
    addql #4,%sp
    bra .Lme_redraw
.Lme_not_retrigger:
    .endif
    cmpil #3,%d0
    bne .Lme_not_track_setup
    movel %d3,%sp@-
    jsr mlp_track_setup_enc
    addql #4,%sp
    bra .Lme_redraw
.Lme_not_track_setup:
    tstl mlp_held
    bne .Lme_held
    tstl mlp_setup
    bne .Lme_setup
    movel mlp_step,%d0
    addl %d3,%d0
    cmpil #63,%d0
    bhi .Lme_out
    movel %d0,mlp_step
    bra .Lme_redraw
.Lme_setup:
    movel mlp_row,%d2
    tstl mlp_edit
    bne .Lme_value
    addl %d3,%d2
    cmpil #10,%d2
    bhi .Lme_out
.Lme_store_row:
    movel %d2,mlp_row
    bra .Lme_redraw
.Lme_value:
    jsr mlp_raw_value
    addl %d3,%d0
    lea.l mlp_min,%a0
    moveq #0,%d1
    moveb %a0@(0,%d2:l),%d1
    cmpl %d1,%d0
    bge .Lme_min_ok
    movel %d1,%d0
.Lme_min_ok:
    lea.l mlp_max,%a0
    moveq #0,%d1
    moveb %a0@(0,%d2:l),%d1
    cmpl %d1,%d0
    ble .Lme_max_ok
    movel %d1,%d0
.Lme_max_ok:
    jsr mlp_store
    bra .Lme_redraw
.Lme_held:
    | DATA édite Note/Vel/Len des pas tenus, sans toucher aux pistes audio.
    movel mlp_step,%sp@-
    moveq #0,%d4
    movel mlp_row,%d2
    cmpil #7,%d2
    bcs .Lme_held_note
    cmpil #9,%d2
    bls .Lme_held_loop
.Lme_held_note:
    moveq #7,%d2
.Lme_held_loop:
    movel mlp_held,%d0
    btst %d4,%d0
    beq .Lme_held_next
    movel %sp@,%d0
    andil #48,%d0
    addl %d4,%d0
    movel %d0,mlp_step
    jsr mlp_raw_value
    addl %d3,%d0
    lea.l mlp_min,%a0
    moveq #0,%d1
    moveb %a0@(0,%d2:l),%d1
    cmpl %d1,%d0
    bge .Lme_held_min
    movel %d1,%d0
.Lme_held_min:
    lea.l mlp_max,%a0
    moveq #0,%d1
    moveb %a0@(0,%d2:l),%d1
    cmpl %d1,%d0
    ble .Lme_held_max
    movel %d1,%d0
.Lme_held_max:
    jsr mlp_store
    movel mlp_changed,%d0
    bset %d4,%d0
    movel %d0,mlp_changed
.Lme_held_next:
    addql #1,%d4
    cmpil #16,%d4
    bcs .Lme_held_loop
    movel %sp@+,mlp_step
.Lme_redraw:
    movel %a2,%sp@-
    jsr mlp_redraw
    addql #4,%sp
.Lme_out:
    moveq #1,%d0
    movem.l %sp@,%d2-%d4/%a2
    lea.l %sp@(16),%sp
    rts

| d2 = ligne, d0 = valeur brute. Seuls d0/d1/a0/a1 sont modifiés.
mlp_store:
    tstl %d2
    bne .Lms_not_track
    movel %d0,mlp_track
    rts
.Lms_not_track:
    cmpil #5,%d2
    bne .Lms_not_step
    movel %d0,mlp_step
    rts
.Lms_not_step:
    movel %d0,%sp@-
    jsr mlp_raw_value
    cmpl %sp@,%d0
    bne .Lms_changed
    addql #4,%sp
    rts
.Lms_changed:
    cmpil #6,%d2
    bne .Lms_flags_ready
    moveq #0,%d0
    moveb %a0@(3),%d0
    andil #2,%d0
    orl %d0,%sp@
.Lms_flags_ready:
    lea.l mlp_fields,%a0
    moveq #0,%d0
    moveb %a0@(0,%d2:l),%d0
    movel %d0,%sp@-
    cmpil #6,%d2
    bcs .Lms_config
    cmpil #10,%d2
    beq .Lms_config
    movel mlp_step,%sp@-
    movel mlp_track,%sp@-
    movel ml_pattern,%sp@-
    jsr ml_edit
    lea.l %sp@(20),%sp
    rts
.Lms_config:
    movel mlp_track,%sp@-
    movel ml_pattern,%sp@-
    jsr ml_config
    lea.l %sp@(16),%sp
    cmpil #3,%d2
    bne .Lms_not_length
    | Réduire la longueur replace la sélection sur le dernier pas actif.
    | Les pas masqués restent en mémoire pour une extension ultérieure.
    jsr mlp_raw_value
    cmpl mlp_step,%d0
    bhi .Lms_done
    subql #1,%d0
    movel %d0,mlp_step
    bra .Lms_done
.Lms_not_length:
    cmpil #1,%d2
    beq .Lms_channel_release
    cmpil #2,%d2
    beq .Lms_release
    cmpil #10,%d2
    bne .Lms_done
    jsr mlp_raw_value
    tstl %d0
    bne .Lms_done
    movel mlp_track,%sp@-
    movel ml_runtime,%sp@-
    jsr ml_quiet
    addql #8,%sp
    rts
.Lms_channel_release:
    jsr mlp_keyboard_cancel
.Lms_release:
    movel mlp_track,%sp@-
    movel ml_runtime,%sp@-
    jsr ml_stop
    addql #8,%sp
.Lms_done:
    rts

mlp_raw_value:
    .globl mlp_raw_value,mlp_value
    moveq #0,%d0
    moveal ml_pattern,%a0
    tstl %d2
    bne .Lmv_not_track
    movel mlp_track,%d0
    rts
.Lmv_not_track:
    cmpil #5,%d2
    bne .Lmv_data
    movel mlp_step,%d0
    rts
.Lmv_data:
    movel mlp_track,%d1
    muluw #264,%d1
    addal %d1,%a0
    cmpil #6,%d2
    bcs .Lmv_config
    cmpil #10,%d2
    beq .Lmv_config
    movel mlp_step,%d1
    lsll #2,%d1
    lea.l %a0@(8,%d1:l),%a0
.Lmv_config:
    lea.l mlp_fields,%a1
    moveb %a1@(0,%d2:l),%d1
    andil #255,%d1
    moveb %a0@(0,%d1:l),%d0
    cmpil #6,%d2
    bne .Lmv_raw_return
    andil #1,%d0
.Lmv_raw_return:
    rts

| d0 valeur numérique, a0 chaîne si énumération ; d2 ligne conservée.
mlp_value:
    jsr mlp_raw_value
    moveal #0,%a0
    tstl %d2
    beq .Lmv_one_based
    cmpil #1,%d2
    beq .Lmv_one_based
    cmpil #5,%d2
    beq .Lmv_one_based
    cmpil #2,%d2
    beq .Lmv_port
    cmpil #4,%d2
    beq .Lmv_speed
    cmpil #6,%d2
    beq .Lmv_bool
    cmpil #10,%d2
    beq .Lmv_bool
    rts
.Lmv_one_based:
    addql #1,%d0
    rts
.Lmv_port:
    subql #2,%d0
    cmpil #2,%d0
    bhi .Lmv_return
    lea.l mlp_ports,%a0
    bra .Lmv_string
.Lmv_speed:
    cmpil #6,%d0
    bhi .Lmv_return
    lea.l mlp_speeds,%a0
.Lmv_string:
    moveal %a0@(0,%d0:l:4),%a0
.Lmv_return:
    rts
.Lmv_bool:
    lea.l mlp_off,%a0
    tstl %d0
    beq .Lmv_return
    lea.l mlp_on,%a0
    rts

    .ifdef ML_CONDITIONS
.Lme_chance_knob:
    pea 1
    pea 1
    movel %a0,%sp@-
    jsr 0x4006f73a
    lea.l %sp@(12),%sp
    movel %d0,%d3
.Lme_chance_delta:
    movel %d3,%sp@-
    jsr mlp_chance_enc
    addql #4,%sp
    bra .Lme_redraw
    .endif

mlp_render:
    movel mlp_setup,%d0
    .ifdef ML_CONDITIONS
    cmpil #5,%d0
    beq mlp_chance_render
    .endif
    .ifdef ML_REPEAT
    cmpil #4,%d0
    beq mlp_retrigger_render
    .endif
    cmpil #3,%d0
    beq mlp_track_setup_render
    .ifdef ML_STOCK_DISPLAY
    movel mlp_setup,%d0
    cmpil #2,%d0
    beq mlp_scale_render
    .endif
    tstl mlp_setup
    .ifdef ML_STOCK_DISPLAY
    beq mlp_stock_render
    .else
    beq mlp_overview
    .endif
    lea.l %sp@(-24),%sp
    movem.l %d2-%d6/%a2,%sp@
    movel %sp@(32),%d6
    clrl %sp@-
    pea 63
    pea 127
    clrl %sp@-
    clrl %sp@-
    movel %d6,%sp@-
    jsr 0x40070dea
    lea.l %sp@(24),%sp
    pea mlp_title
    pea mlp_fmt_s
    pea 0x10
    pea 49
    pea 2
    pea 0x40ea14cc
    movel %d6,%sp@-
    jsr 0x40071a04
    lea.l %sp@(28),%sp
    movel mlp_row,%d5
    subql #1,%d5
    bpl .Lpr_nonnegative
    moveq #0,%d5
.Lpr_nonnegative:
    cmpil #8,%d5
    bls .Lpr_start
    moveq #8,%d5
.Lpr_start:
    movel %d5,%d2
    moveq #35,%d4
.Lpr_loop:
    lea.l mlp_labels,%a0
    moveal %a0@(0,%d2:l:4),%a2
    movel %a2,%sp@-
    pea mlp_fmt_s
    pea 0x10
    movel %d4,%sp@-
    pea 2
    pea 0x40ea14cc
    movel %d6,%sp@-
    jsr 0x40071a04
    lea.l %sp@(28),%sp
    jsr mlp_value
    tstl %a0
    beq .Lpr_number
    movel %a0,%sp@-
    pea mlp_fmt_s
    bra .Lpr_value
.Lpr_number:
    movel %d0,%sp@-
    pea mlp_fmt_d
.Lpr_value:
    pea 0x14
    movel %d4,%sp@-
    pea 125
    pea 0x40ea14cc
    movel %d6,%sp@-
    jsr 0x40071a04
    lea.l %sp@(28),%sp
    addql #1,%d2
    subil #14,%d4
    movel %d2,%d0
    subl %d5,%d0
    cmpil #3,%d0
    bcs .Lpr_loop
    movel mlp_row,%d0
    subl %d5,%d0
    muluw #14,%d0
    moveq #48,%d1
    subl %d0,%d1
    pea -1
    movel %d1,%sp@-
    pea 127
    subil #13,%d1
    movel %d1,%sp@-
    moveq #0,%d0
    tstl mlp_edit
    beq .Lpr_cursor
    moveq #64,%d0
.Lpr_cursor:
    movel %d0,%sp@-
    movel %d6,%sp@-
    jsr 0x40070dea
    lea.l %sp@(24),%sp
    movem.l %sp@,%d2-%d6/%a2
    lea.l %sp@(24),%sp
    rts

| Vue musicale : note inversée à gauche, vélocité au centre, voie à droite.
| Vol représente la vélocité du pas, pas un CC ni un niveau du moteur audio.
mlp_overview:
    lea.l %sp@(-24),%sp
    movem.l %d2-%d6/%a2,%sp@
    movel %sp@(32),%d6
    clrl %sp@-
    pea 63
    pea 127
    clrl %sp@-
    clrl %sp@-
    movel %d6,%sp@-
    jsr 0x40070dea
    lea.l %sp@(24),%sp
    moveq #7,%d2
    jsr mlp_raw_value
    moveq #-1,%d4
.Lov_octave:
    addql #1,%d4
    subil #12,%d0
    bpl .Lov_octave
    addil #12,%d0
    subql #1,%d4
    lea.l mlp_note_names,%a0
    movel %d4,%sp@-
    movel %a0@(0,%d0:l:4),%sp@-
    pea mlp_note_fmt
    pea 0x10
    pea 24
    pea 5
    pea 0x40ea14cc
    movel %d6,%sp@-
    jsr 0x40071a04
    lea.l %sp@(32),%sp
    | Inverser après le texte : note blanche dans le rectangle noir.
    pea -1
    pea 43
    pea 42
    pea 15
    pea 1
    movel %d6,%sp@-
    jsr 0x40070dea
    lea.l %sp@(24),%sp
    | Petite routine commune : a0 texte, d0=x, d1=y, d6 cible.
    lea.l mlp_note,%a0
    moveq #5,%d0
    moveq #47,%d1
    bsr mlp_over_text
    lea.l mlp_vol,%a0
    moveq #51,%d0
    moveq #47,%d1
    bsr mlp_over_text
    moveq #8,%d2
    jsr mlp_raw_value
    movel %d0,%sp@-
    pea mlp_fmt_d
    pea 0x10
    pea 24
    pea 54
    pea 0x40ea14cc
    movel %d6,%sp@-
    jsr 0x40071a04
    lea.l %sp@(28),%sp
    moveq #1,%d2
    jsr mlp_raw_value
    movel %d0,%sp@-
    pea mlp_ch_fmt
    pea 0x10
    pea 47
    pea 91
    pea 0x40ea14cc
    movel %d6,%sp@-
    jsr 0x40071a04
    lea.l %sp@(28),%sp
    movel mlp_step,%d0
    addql #1,%d0
    movel %d0,%sp@-
    pea mlp_step_fmt
    pea 0x10
    pea 24
    pea 91
    pea 0x40ea14cc
    movel %d6,%sp@-
    jsr 0x40071a04
    lea.l %sp@(28),%sp
    moveq #10,%d2
    jsr mlp_raw_value
    lea.l mlp_over_off,%a0
    tstl %d0
    beq .Lov_output
    lea.l mlp_over_on,%a0
.Lov_output:
    moveq #2,%d0
    moveq #2,%d1
    bsr mlp_over_text
    movem.l %sp@,%d2-%d6/%a2
    lea.l %sp@(24),%sp
    rts
mlp_over_text:
    movel %a0,%sp@-
    pea mlp_fmt_s
    pea 0x10
    movel %d1,%sp@-
    movel %d0,%sp@-
    pea 0x40ea14cc
    movel %d6,%sp@-
    jsr 0x40071a04
    lea.l %sp@(28),%sp
    rts

    .data
    .balign 4
    .globl ml_pattern,ml_runtime,mlp_obj,mlp_opened,mlp_row,mlp_edit,mlp_track,mlp_step,mlp_func,mlp_pads,mlp_vt,mlp_held,mlp_remove,mlp_changed
ml_pattern: .long 0
ml_runtime: .long 0
mlp_obj: .long 0
mlp_opened: .long 0
mlp_row: .long 0
mlp_edit: .long 0
mlp_track: .long 0
mlp_step: .long 0
mlp_func: .long 0
mlp_func_inherited: .long 0
mlp_pads: .long 0
mlp_held: .long 0
mlp_remove: .long 0
mlp_changed: .long 0
    .globl mlp_setup
mlp_setup: .long 0
mlp_vt: .space 0xb0
    .balign 4
mlp_typeinfo:
    .long 0x40123f20,mlp_typename,0,2
    .long 0x401178f8,2,0x400ff970,0x50002
mlp_typename: .asciz "12MidiBankView"
    .balign 4
mlp_led_vt:
    .long -0x500,mlp_typeinfo,mlp_led_dtor0,mlp_led_dtor1,mlp_led
    .globl mlp_labels
mlp_labels: .long mlp_track_label,mlp_channel,mlp_port,mlp_length,mlp_speed,mlp_step_label,mlp_trig,mlp_note,mlp_velocity,mlp_gate,mlp_output
mlp_ports: .long mlp_usb,mlp_din,mlp_both
mlp_speeds: .long mlp_quarter,mlp_half,mlp_normal,mlp_threehalf,mlp_double,mlp_triple,mlp_four
mlp_min: .byte 0,0,2,1,0,0,0,0,1,1,0
mlp_max: .byte 5,15,4,64,6,63,1,127,127,64,1
mlp_fields: .byte 0,2,3,4,5,0,3,0,1,2,0
mlp_title: .asciz "MIDI BANK"
mlp_track_label: .asciz "Track"
mlp_channel: .asciz "MIDI Ch."
mlp_port: .asciz "Output"
mlp_length: .asciz "Length"
mlp_speed: .asciz "Speed"
mlp_step_label: .asciz "Step"
mlp_trig: .asciz "Trig"
mlp_note: .asciz "Note"
mlp_velocity: .asciz "Velocity"
mlp_gate: .asciz "Gate steps"
mlp_output: .asciz "MIDI OUT"
mlp_on: .asciz "On"
mlp_off: .asciz "Off"
mlp_usb: .asciz "USB"
mlp_din: .asciz "DIN"
mlp_both: .asciz "USB+DIN"
mlp_quarter: .asciz "1/4x"
mlp_half: .asciz "1/2x"
mlp_normal: .asciz "1x"
mlp_threehalf: .asciz "3/2x"
mlp_double: .asciz "2x"
mlp_triple: .asciz "3x"
mlp_four: .asciz "4x"
mlp_fmt_s: .asciz "%s"
mlp_fmt_d: .asciz "%d"
mlp_vol: .asciz "Vol"
mlp_note_fmt: .asciz "%s%d"
mlp_ch_fmt: .asciz "Ch%d"
mlp_step_fmt: .asciz "S%02d"
mlp_over_on: .asciz "MIDI OUT On"
mlp_over_off: .asciz "MIDI OUT Off"
    .balign 4
mlp_note_names: .long mlp_c,mlp_cs,mlp_d,mlp_ds,mlp_e,mlp_f,mlp_fs,mlp_g,mlp_gs,mlp_a,mlp_as,mlp_b
mlp_c: .asciz "C"
mlp_cs: .asciz "C#"
mlp_d: .asciz "D"
mlp_ds: .asciz "D#"
mlp_e: .asciz "E"
mlp_f: .asciz "F"
mlp_fs: .asciz "F#"
mlp_g: .asciz "G"
mlp_gs: .asciz "G#"
mlp_a: .asciz "A"
mlp_as: .asciz "A#"
mlp_b: .asciz "B"

