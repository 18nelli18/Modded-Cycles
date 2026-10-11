| Génération différée, note 56. Aucune API OS dans l'interruption.
| Hook 0x400550da : préserver tous registres/SR, rejouer movea.l active,a2.
| Frontière : juste avant la lecture anticipée du pas 0, phase piste 0 = 0.
| Première version : longueur/vitesse communes, sans chaîne de patterns.
    .ifdef SG_QUEUE
    .globl sg_q_state,sg_q_building,sg_q_stage,sg_q_hook,sg_q_service,sg_q_cancel,sg_q_label,sg_q_stop
    .globl sg_action_generate,sg_undo_track,sg_undo_valid,sg_action_undo
    .equ Q_TRACK,5632
    .equ Q_POBJ,5696
    .equ Q_RAW,5720
    .equ Q_POOL,6444
    .equ Q_AUDIO,10832
    .equ Q_OLD_AUDIO,11556
    .section .data.sg_queue,"aw"
sg_q_detail: .asciz "Q mod 00000"
    .balign 4
sg_q_reason: .long 0
sg_q_state: .long 0              | 0 libre, 1 préparé, 2 appliqué, 3 annulé
sg_q_building: .long 0           | UI uniquement, jamais utilisé par l'ISR
sg_q_track: .long 0
sg_q_raw: .long 0
sg_q_pool: .long 0
sg_q_powner: .long 0
sg_q_audio: .long 0
sg_q_pattern: .long 0
sg_q_index: .long 0
sg_q_length: .long 0
sg_q_speed: .long 0
sg_q_vt: .long 0,0,0,0,sg_q_quiet,0,0,0,0,0,sg_q_get
    .section .text.sg_q_helpers,"ax"
sg_q_get:
    moveal %sp@(4),%a0
    movel %a0@(16),%d0
    rts
sg_q_quiet:
    rts
sg_q_cancel:
    clrl sg_q_state
    rts
| d0 octets, a0 source, a1 cible. Accès non alignés admis (MCF54418RM §20.4.8).
sg_q_copy:
    movel %d0,%sp@-
    lsrl #2,%d0
    beqs sqcopy_tail
sqcopy_long:
    movel %a0@+,%d1
    movel %d1,%a1@+
    subql #1,%d0
    bnes sqcopy_long
sqcopy_tail:
    movel %sp@+,%d0
    andil #3,%d0
    beqs sqcopy_done
sqcopy_byte:
    moveb %a0@+,%d1
    moveb %d1,%a1@+
    subql #1,%d0
    bnes sqcopy_byte
sqcopy_done:
    rts
| d0 octets -> d0=0 si égaux, 1 sinon ; borne fixe, pile restaurée.
sg_q_equal:
    movel %d0,%sp@-
    lsrl #2,%d0
    beqs sqequal_tail
sqequal_long:
    movel %a0@+,%d1
    cmpl %a1@+,%d1
    bnes sqequal_no
    subql #1,%d0
    bnes sqequal_long
sqequal_tail:
    movel %sp@,%d0
    andil #3,%d0
    beqs sqequal_yes
sqequal_byte:
    moveb %a0@+,%d1
    cmpb %a1@+,%d1
    bnes sqequal_no
    subql #1,%d0
    bnes sqequal_byte
sqequal_yes:
    addql #4,%sp
    moveq #0,%d0
    rts
sqequal_no:
    addql #4,%sp
    moveq #1,%d0
    rts
sg_q_label:
    cmpil #20,%d3
    bnew sql_state
    tstl sg_error
    beqw sql_state
    movel sg_q_reason,%d0
    beqw sql_state
    moveal %d0,%a2
    rts
sql_state:
    movel sg_q_state,%d0
    cmpil #1,%d0
    bnew sql_done
    cmpil #20,%d3
    bnew sql_undo
    lea.l sg_q_wait,%a2
    rts
sql_undo:
    cmpil #21,%d3
    bnew sql_done
    lea.l sg_q_cancel_text,%a2
sql_done:
    rts
    .section .rodata.sg_queue,"a"
sq_pending: .asciz "Queue pending"
sq_transport: .asciz "Queue: transport"
sq_mode: .asciz "Queue: mode"
sq_chain: .asciz "Queue: chain"
sq_track: .asciz "Queue: track"
sq_audio: .asciz "Queue: audio"
sq_data: .asciz "Queue: data"
sq_pool: .asciz "Queue: locks"
sq_build: .asciz "Queue: build"
sg_q_wait: .asciz "Queued"
sg_q_cancel_text: .asciz "Cancel queue"
    .section .text.sg_q_detail,"ax"
| UI seulement : d0 valeur non signée 16 bits, d1 étiquette de quatre octets.
| Retour d0 inchangé ; d2 préservé ; d1/a0/a1 temporaires.
sg_q_format:
    lea.l %sp@(-8),%sp
    movem.l %d0/%d2,%sp@
    lea.l sg_q_detail,%a0
    movel %d1,%a0@(2)
    movel %a0,sg_q_reason
    lea.l %a0@(11),%a1
    andil #65535,%d0
    moveq #4,%d2
sqf_digit:
    divuw #10,%d0
    movel %d0,%d1
    swap %d1
    addil #48,%d1
    moveb %d1,%a1@-
    andil #65535,%d0
    subql #1,%d2
    bplw sqf_digit
    movem.l %sp@,%d0/%d2
    lea.l %sp@(8),%sp
    rts
    .section .text.sg_q_stage,"ax"
sg_q_stage:
    lea.l %sp@(-32),%sp
    movem.l %d2-%d5/%a2-%a5,%sp@
    lea.l sq_pending,%a0
    movel %a0,sg_q_reason
    tstl sg_q_state
    bnew sqs_fail
    clrl sg_undo_valid
    moveal sg_obj,%a2
    tstl %a2
    beqw sqs_fail
    lea.l sq_transport,%a0
    movel %a0,sg_q_reason
    movel 0x40a7883c,%d0
    cmpil #1,%d0
    bnew sqs_fail
    moveal 0x40a7887c,%a4
    tstl %a4
    beqw sqs_fail
    moveq #0,%d0
    moveb %a4@(30667),%d0
    movel #0x6d6f6420,%d1        | "mod "
    jsr sg_q_format
    tstl %d0                    | modes de longueur par piste refusés
    bnew sqs_fail
    moveq #0,%d2
    movew %a4@(30662),%d2
    movel %d2,%d0
    movel #0x6c656e20,%d1        | "len "
    jsr sg_q_format
    cmpil #1,%d2
    bltw sqs_fail
    cmpil #64,%d2
    bgtw sqs_fail
    movel %d2,sg_q_length
    moveq #0,%d0
    moveb %a4@(30668),%d0
    movel #0x73706420,%d1        | "spd "
    jsr sg_q_format
    cmpil #6,%d0
    bhiw sqs_fail
    movel %d0,sg_q_speed
    movel 0x40a78848,%d0
    movel #0x72756e20,%d1        | "run "
    jsr sg_q_format
    cmpil #1,%d0
    bnew sqs_fail
    lea.l sq_chain,%a0
    movel %a0,sg_q_reason
    jsr sg_q_chain_ok
    tstl %d0
    beqw sqs_fail
    movel %a4,sg_q_pattern
    jmp sqs_identity
    .section .text.sg_q_identity,"ax"
sqs_identity:
    lea.l sq_track,%a0
    movel %a0,sg_q_reason
    jsr 0x400cf866
    movel %d0,%sp@-
    jsr 0x4000f23e
    addql #4,%sp
    tstl %d0
    beqw sqs_fail
    moveal %d0,%a3
    movel %a3,sg_q_track
    movel %a3@(56),%d3
    cmpil #5,%d3
    bhiw sqs_fail
    movel %d3,sg_q_index
    lea.l sq_audio,%a0
    movel %a0,sg_q_reason
    movel %d3,%d0
    muluw #722,%d0
    addl %a4,%d0
    cmpl %a3@(32),%d0            | véritable destination audio de cette piste
    bnew sqs_fail
    movel %d0,sg_q_audio
    lea.l sq_data,%a0
    movel %a0,sg_q_reason
    movel %a3,%sp@-
    moveal %a3@,%a0
    moveal %a0@(40),%a0
    jsr %a0@
    addql #4,%sp
    tstl %d0
    beqw sqs_fail
    cmpl %a3@(16),%d0
    bnew sqs_fail
    movel %d0,sg_q_raw
    | Longueur effective via parent +60 ; +713 peut rester différente en mode commun.
    lea.l sq_pool,%a0
    movel %a0,sg_q_reason
    moveal %a3@(44),%a5
    tstl %a5
    beqw sqs_fail
    movel %a5,sg_q_powner
    movel %a5,%sp@-
    moveal %a5@,%a0
    moveal %a0@(40),%a0
    jsr %a0@
    addql #4,%sp
    tstl %d0
    beqw sqs_fail
    cmpl %a5@(16),%d0
    bnew sqs_fail
    muluw #4385,%d3
    addl %d3,%d0
    movel %d0,sg_q_pool
    jmp sqs_shadow
    .section .text.sg_q_shadow,"ax"
sqs_shadow:
    | Objets privés avec getters réels de données, notifications muettes.
    moveal %a3,%a0
    lea.l %a2@(Q_TRACK),%a1
    moveq #64,%d0
    jsr sg_q_copy
    lea.l %a2@(Q_TRACK),%a0
    movel #sg_q_vt,%a0@
    lea.l %a2@(Q_RAW),%a1
    movel %a1,%a0@(16)
    clrl %a0@(32)
    clrl %a0@(56)
    lea.l %a2@(Q_POBJ),%a1
    movel %a1,%a0@(44)
    movel #sg_q_vt,%a1@
    lea.l %a2@(Q_POOL),%a0
    movel %a0,%a1@(16)
    moveal sg_q_raw,%a0
    lea.l %a2@(Q_RAW),%a1
    movel #722,%d0
    jsr sg_q_copy
    moveal sg_q_pool,%a0
    lea.l %a2@(Q_POOL),%a1
    movel #4385,%d0
    jsr sg_q_copy
    | Le snapshot du pool reste nécessaire même si decay/pan sont désactivés.
    moveal sg_q_pool,%a0
    lea.l %a2@(1008),%a1
    movel #4385,%d0
    jsr sg_q_copy
    moveq #1,%d0
    movel %d0,sg_q_building
    lea.l sq_build,%a0
    movel %a0,sg_q_reason
    jsr sg_action_generate
    clrl sg_q_building
    clrl sg_undo_valid
    tstl sg_error
    bnew sqs_fail
    movel sg_q_track,%d0
    movel %d0,sg_undo_track
    movel sg_q_raw,%d0
    movel %d0,%a2@(996)
    movel sg_q_pool,%d0
    movel %d0,%a2@(1000)
    movel sg_q_powner,%d0
    movel %d0,%a2@(1004)
    jmp sqs_convert
    .section .text.sg_q_convert,"ax"
sqs_convert:
    | Conversion native complète avant publication, jamais dans l'ISR.
    pea -1
    pea -1
    clrl %sp@-
    pea %a2@(Q_RAW)
    pea %a2@(Q_AUDIO)
    jsr 0x4005b642
    lea.l %sp@(20),%sp
    pea -1
    pea -1
    clrl %sp@-
    pea %a2@(208)
    pea %a2@(Q_OLD_AUDIO)
    jsr 0x4005b642
    lea.l %sp@(20),%sp
    moveq #1,%d0
    movel %d0,sg_q_state         | publication atomique après préparation complète
    braw sqs_out
sqs_fail:
    moveq #1,%d0
    movel %d0,sg_error
sqs_out:
    movem.l %sp@,%d2-%d5/%a2-%a5
    lea.l %sp@(32),%sp
    rts
    .section .text.sg_q_chain,"ax"
| a4 = pattern actif ; une chaîne/changement demandé n'est jamais écrasé.
sg_q_chain_ok:
    moveq #0,%d0
    movel 0x40a78638,%d1
    cmpil #1,%d1
    bnew sqc_out
    cmpal 0x40a7863c,%a4
    bnew sqc_out
    tstl 0x40a788f4
    bnew sqc_out
    tstl 0x40a788f8
    bnew sqc_out
    tstb 0x40a788bb
    bnew sqc_out
    moveq #1,%d0
sqc_out:
    rts
    .section .text.sg_q_hook,"ax"
sg_q_hook:
    lea.l %sp@(-36),%sp
    movem.l %d0-%d2/%a0-%a4,%sp@
    movew %sr,%d0
    movel %d0,%sp@(32)
    movel sg_q_state,%d0
    cmpil #1,%d0
    bnew sqh_out
    movel 0x40a7883c,%d0
    cmpil #1,%d0
    bnew sqh_cancel
    moveal sg_obj,%a2
    tstl %a2
    beqw sqh_cancel
    moveal 0x40a7887c,%a4
    cmpal sg_q_pattern,%a4
    bnew sqh_cancel
    jsr sg_q_chain_ok
    tstl %d0
    beqw sqh_cancel
    tstl 0x40a78630              | une seule fois au tick séquenceur
    bnew sqh_out
    tstb 0x40a78860              | prochain pas piste 0
    bnew sqh_out
    tstb 0x40a78866              | avant la première lecture anticipée
    bnew sqh_out
    tstb %a4@(30667)
    bnew sqh_cancel
    jmp sqh_validate
    .section .text.sg_q_validate,"ax"
sqh_validate:
    moveal sg_q_track,%a0
    movel %a0@(16),%d0
    cmpl sg_q_raw,%d0
    bnew sqh_cancel
    movel %a0@(32),%d0
    cmpl sg_q_audio,%d0
    bnew sqh_cancel
    movel %a0@(44),%d0
    cmpl sg_q_powner,%d0
    bnew sqh_cancel
    movel %a0@(56),%d0
    cmpl sg_q_index,%d0
    bnew sqh_cancel
    moveal sg_q_powner,%a1
    movel sg_q_index,%d0
    muluw #4385,%d0
    addl %a1@(16),%d0
    cmpl sg_q_pool,%d0
    bnew sqh_cancel
    moveq #0,%d0
    movew %a4@(30662),%d0
    cmpl sg_q_length,%d0
    bnew sqh_cancel
    moveb %a4@(30668),%d0
    andil #255,%d0
    cmpl sg_q_speed,%d0
    bnew sqh_cancel
    | Annuler si une édition UI/audio a changé depuis le snapshot.
    lea.l %a2@(208),%a0
    moveal sg_q_raw,%a1
    movel #722,%d0
    jsr sg_q_equal
    tstl %d0
    bnew sqh_cancel
    lea.l %a2@(1008),%a0
    moveal sg_q_pool,%a1
    movel #4385,%d0
    jsr sg_q_equal
    tstl %d0
    bnew sqh_cancel
    lea.l %a2@(Q_OLD_AUDIO),%a0
    moveal sg_q_audio,%a1
    movel #722,%d0
    jsr sg_q_equal
    tstl %d0
    bnew sqh_cancel
    | Le pool audio utilise le même format natif étendu, prouvé au lecteur.
    movel sg_q_index,%d2
    muluw #4385,%d2
    lea.l %a4@(4332),%a3
    addal %d2,%a3
    lea.l %a2@(1008),%a0
    moveal %a3,%a1
    movel #4385,%d0
    jsr sg_q_equal
    tstl %d0
    bnew sqh_cancel
    jmp sqh_commit
    .section .text.sg_q_commit,"ax"
sqh_commit:
    movew #0x2700,%sr            | transaction atomique, aucune allocation/API
    lea.l %a2@(Q_RAW),%a0
    moveal sg_q_raw,%a1
    movel #722,%d0
    jsr sg_q_copy
    lea.l %a2@(Q_POOL),%a0
    moveal sg_q_pool,%a1
    movel #4385,%d0
    jsr sg_q_copy
    lea.l %a2@(Q_AUDIO),%a0
    moveal sg_q_audio,%a1
    movel #722,%d0
    jsr sg_q_copy
    lea.l %a2@(Q_POOL),%a0
    moveal %a3,%a1
    movel #4385,%d0
    jsr sg_q_copy
    moveq #1,%d0
    movel %d0,sg_undo_valid
    moveq #2,%d0
    movel %d0,sg_q_state
    braw sqh_out
sqh_cancel:
    moveq #3,%d0
    movel %d0,sg_q_state
sqh_out:
    movel %sp@(32),%d0
    movew %d0,%sr
    movem.l %sp@,%d0-%d2/%a0-%a4
    lea.l %sp@(36),%sp
    moveal 0x40a7887c,%a2        | instruction native déplacée, CCR inchangé
    jmp 0x400550e0
    .section .text.sg_q_service,"ax"
| UI : notifications après le commit ; la copie audio est déjà complète.
sg_q_service:
    movel sg_q_state,%d0
    cmpil #2,%d0
    beqw sqv_applied
    movel sg_q_state,%d0
    cmpil #3,%d0
    bnew sqv_done
    clrl sg_q_state
    moveq #1,%d0
    movel %d0,sg_error
    braw sqv_redraw
sqv_applied:
    clrl sg_q_state
    jsr 0x400cf866
    movel %d0,%sp@-
    jsr 0x4000f23e
    addql #4,%sp
    cmpl sg_q_track,%d0
    bnew sqv_stale
    moveal %d0,%a0
    movel %a0@(16),%d0
    cmpl sg_q_raw,%d0
    bnew sqv_stale
    movel 0x40a7887c,%d0
    cmpl sg_q_pattern,%d0
    bnew sqv_stale
    lea.l %sp@(-12),%sp
    movem.l %d2/%a2-%a3,%sp@
    moveal sg_q_track,%a3
    moveal sg_q_raw,%a2
    moveq #0,%d2
sqv_note:
    moveq #0,%d0
    lea.l %a2@(580),%a0
    moveb %a0@(0,%d2:l),%d0
    movel %d0,%sp@-
    movel %d2,%sp@-
    movel %a3,%sp@-
    jsr 0x40016642
    lea.l %sp@(12),%sp
    addql #1,%d2
    cmpl sg_config,%d2
    bltw sqv_note
    moveal sg_q_powner,%a0
    clrl %sp@-
    movel %a0,%sp@-
    moveal %a0@,%a1
    moveal %a1@(16),%a1
    jsr %a1@
    addql #8,%sp
    movem.l %sp@,%d2/%a2-%a3
    lea.l %sp@(12),%sp
sqv_redraw:
    movel sg_obj,%d0
    beqw sqv_done
    movel %d0,%sp@-
    jsr 0x40076082
    addql #4,%sp
sqv_done:
    rts
sqv_stale:
    clrl sg_undo_valid
    braw sqv_redraw
    .section .text.sg_q_stop,"ax"
| Stop local/MIDI : annuler une préparation, garder les notifications après commit.
sg_q_stop:
    movel %d0,%sp@-
    movel sg_q_state,%d0
    cmpil #1,%d0
    bnew sqstop_native
    moveq #3,%d0
    movel %d0,sg_q_state
sqstop_native:
    movel %sp@+,%d0
    movel %d2,%sp@-
    tstl %sp@(12)
    jmp 0x40055f1a
    .endif
