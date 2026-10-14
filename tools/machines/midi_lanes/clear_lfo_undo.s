| Effacement B : snapshot deux cfg16 + deux phases32, puis Undo lié au clear.
| Adaptateurs seuls ; aucune allocation, E/S ou modification de piste audio.
| mclf_op remplace les appels clipboard sous IPL7 ; préparation frame seulement
| via mclf_refresh à IPL0. Pendant la transition seule la voie visée est muette
| côté LFO CC ; le moteur et les cinq autres voies continuent normalement.
    .text
    .globl mclf_op,mclf_refresh,mclf_redraw,mclf_prepare,mclf_emit,mclf_invalidate
mclf_op:
    lea %sp@(-32),%sp
    moveml %d2-%d5/%a2-%a4,%sp@
    movel %d0,%d5
    jsr B_ml_repeat_clip
    movel %d0,%sp@(28)
    cmpil #1,%d5
    beq .Lop_snapshot
    cmpil #2,%d5
    beq .Lop_undo
    cmpil #4,%d5
    beq .Lop_clear
    bra .Lop_out
.Lop_address:
    moveal B_ml_pattern,%a2
    movel B_mlp_track,%d4
    moveq #0,%d0
    tstl %a2
    beq .Laddress_out
    cmpil #5,%d4
    bhi .Laddress_out
    movel %d4,%d1
    lsll #5,%d1
    lea %a2@(4704),%a3
    addal %d1,%a3
    moveq #1,%d0
.Laddress_out:
    rts
.Lop_snapshot:
    clrl mclf_valid
    | d2 appartient au caller clipboard :1 clear,2 paste. Paste ne touche LFO.
    cmpil #1,%d2
    bne .Lop_out
    bsr .Lop_address
    tstl %d0
    beq .Lop_out
    movel %a2,mclf_pattern
    movel %d4,mclf_lane
    moveal %a3,%a0
    lea mclf_cfg,%a1
    moveq #7,%d0
.Lsnapshot_cfg:
    movel %a0@+,%a1@+
    subql #1,%d0
    bpl .Lsnapshot_cfg
    clrl mclf_phase_valid
    moveal B_mlcc_context,%a4
    movel %a4,mclf_context
    tstl %a4
    beq .Lsnapshot_ready
    cmpal B_mlcc_cfg_owner,%a2
    bne .Lsnapshot_ready
    bsr .Lphase_address
    lea mclf_phase,%a1
    moveq #7,%d0
.Lsnapshot_phase0:
    movel %a0@+,%a1@+
    subql #1,%d0
    bpl .Lsnapshot_phase0
    lea %a0@(160),%a0
    moveq #7,%d0
.Lsnapshot_phase1:
    movel %a0@+,%a1@+
    subql #1,%d0
    bpl .Lsnapshot_phase1
    moveq #1,%d0
    movel %d0,mclf_phase_valid
.Lsnapshot_ready:
    moveq #1,%d0
    movel %d0,mclf_valid
    bra .Lop_out
.Lop_undo:
    cmpil #1,%d2
    bne .Lop_out
    tstl mclf_valid
    beq .Lop_out
    bsr .Lop_address
    tstl %d0
    beq .Lop_out
    cmpal mclf_pattern,%a2
    bne .Lundo_invalid
    cmpl mclf_lane,%d4
    bne .Lundo_invalid
    lea mclf_cfg,%a0
    moveal %a3,%a1
    moveq #7,%d0
.Lundo_cfg:
    movel %a0@+,%a1@+
    subql #1,%d0
    bpl .Lundo_cfg
    moveq #2,%d0
    movel %d0,mclf_pending
    clrl mclf_valid
    bra .Lop_cancel
.Lundo_invalid:
    clrl mclf_valid
    bra .Lop_out
.Lop_clear:
    cmpil #1,%d2
    bne .Lop_out
    bsr .Lop_address
    tstl %d0
    beq .Lop_out
    | Le snapshot est déjà fait par op1, avant que le clipboard publie l'Undo.
    cmpal mclf_pattern,%a2
    bne .Lop_out
    cmpl mclf_lane,%d4
    bne .Lop_out
    moveal %a3,%a0
    moveq #1,%d1
.Lclear_cfg:
    movel #0x40000009,%a0@+
    movel #0x40000080,%a0@+
    clrl %a0@+
    movel #0x00004000,%a0@+
    subql #1,%d1
    bpl .Lclear_cfg
    moveq #1,%d0
    movel %d0,mclf_pending
.Lop_cancel:
    | Le flag est publié avant purge ; aucun ancien CC ne peut revenir en IRQ.
    movel B_mlccp_track,%d0
    cmpl %d4,%d0
    bne .Lcancel_queue
    lea %a2@(4704),%a0
    cmpal B_mlcc_settings,%a0
    bne .Lcancel_queue
    jsr B_mlccp_confirm_cancel
.Lcancel_queue:
    moveal B_mlcc_context,%a4
    tstl %a4
    beq .Lop_out
    cmpal B_mlcc_cfg_owner,%a2
    bne .Lop_out
    movel mclf_pending,%d0
    cmpil #1,%d0
    bne .Lcancel_only
    bsr .Lphase_zero
.Lcancel_only:
    bsr .Lqueue_cancel
.Lop_out:
    movel %sp@(28),%d0
    moveml %sp@,%d2-%d5/%a2-%a4
    lea %sp@(32),%sp
    rts

| Helpers appelés uniquement sous IPL7, a4=contexte,d4=voie.
.Lphase_address:
    movel %d4,%d0
    lsll #5,%d0
    lea %a4@(2480),%a0
    addal %d0,%a0
    rts
.Lphase_zero:
    bsr .Lphase_address
    moveq #7,%d0
.Lzero0:
    clrl %a0@+
    subql #1,%d0
    bpl .Lzero0
    lea %a0@(160),%a0
    moveq #7,%d0
.Lzero1:
    clrl %a0@+
    subql #1,%d0
    bpl .Lzero1
    rts
.Lphase_restore:
    tstl mclf_phase_valid
    beq .Lphase_zero
    cmpal mclf_context,%a4
    bne .Lphase_zero
    bsr .Lphase_address
    lea mclf_phase,%a1
    moveq #7,%d0
.Lrestore0:
    movel %a1@+,%a0@+
    subql #1,%d0
    bpl .Lrestore0
    lea %a0@(160),%a0
    moveq #7,%d0
.Lrestore1:
    movel %a1@+,%a0@+
    subql #1,%d0
    bpl .Lrestore1
    rts
.Lqueue_cancel:
    movel %d4,%sp@-
    pea %a4@(2864)
    jsr B_mlcc_lane_cancel
    addql #8,%sp
    movel B_mlcc_triggers,%d0
    bclr %d4,%d0
    movel %d0,B_mlcc_triggers
    rts

| Publication UI : l'inactif est construit par la routine existante à IPL0.
| La purge finale/phase/levée du gate ne prennent qu'une courte section IPL7.
mclf_refresh:
    lea %sp@(-24),%sp
    moveml %d2-%d4/%a2-%a4,%sp@
    movew %sr,%d0
    andil #0x700,%d0
    bne .Lrefresh_out
    jsr B_mlcc_refresh
    moveal B_ml_pattern,%a2
    cmpal mclf_pattern,%a2
    beq .Lrefresh_owner
    clrl mclf_valid
    | Si le nouveau propriétaire ne peut préparer sa frame, l'ancien moteur
    | peut encore tourner. Garder alors son gate jusqu'à une vraie publication.
    tstl mclf_pending
    beq .Lrefresh_out
    moveal B_mlcc_context,%a4
    tstl %a4
    beq .Lrefresh_drop
    movel B_mlcc_cfg_owner,%d0
    cmpl mclf_pattern,%d0
    beq .Lrefresh_out
.Lrefresh_drop:
    clrl mclf_pending
    bra .Lrefresh_out
.Lrefresh_owner:
    tstl mclf_pending
    beq .Lrefresh_out
    movel mclf_lane,%d4
    cmpil #5,%d4
    bhi .Lrefresh_out
    moveal B_mlcc_context,%a4
    tstl %a4
    bne .Lrefresh_context
    | Aucun moteur actif : cfg fait foi ; il sera préparé lors de sa création.
    clrl mclf_pending
    bra .Lrefresh_out
.Lrefresh_context:
    cmpal B_mlcc_cfg_owner,%a2
    bne .Lrefresh_out
    moveal %a4@(3016),%a3
    tstl %a3
    beq .Lrefresh_out
    movel %d4,%d0
    lsll #5,%d0
    lea %a2@(4704),%a0
    addal %d0,%a0
    lea %a3@(0,%d0:l),%a1
    moveq #7,%d1
.Lrefresh_verify:
    movel %a0@+,%d0
    cmpl %a1@+,%d0
    bne .Lrefresh_out
    subql #1,%d1
    bpl .Lrefresh_verify
    movew %sr,%d2
    movew #0x2700,%sr
    movel mclf_pending,%d0
    cmpil #2,%d0
    bne .Lrefresh_zero
    bsr .Lphase_restore
    bra .Lrefresh_purge
.Lrefresh_zero:
    bsr .Lphase_zero
.Lrefresh_purge:
    bsr .Lqueue_cancel
    clrl mclf_pending
    movew %d2,%sr
.Lrefresh_out:
    moveml %sp@,%d2-%d4/%a2-%a4
    lea %sp@(24),%sp
    rts

mclf_redraw:
    jsr mclf_refresh
    jmp B_mlp_redraw

| Éviter d'écraser un clear encore en attente si une frame invalide empêche
| publication. L'UI peut réessayer ; clavier, autres voies et transport restent.
mclf_prepare:
    tstl mclf_pending
    beq .Lprepare_original
    jsr mclf_refresh
    tstl mclf_pending
    beq .Lprepare_original
    moveq #0,%d0
    rts
.Lprepare_original:
    jmp B_ml_repeat_clip_prepare

| Même ABI six arguments que mlcc_lane_put ; gate avant toute mise en file.
mclf_emit:
    tstl mclf_pending
    beq .Lemit_original
    movel %sp@(8),%d0
    cmpl mclf_pattern,%d0
    bne .Lemit_original
    movel %sp@(12),%d0
    cmpl mclf_lane,%d0
    bne .Lemit_original
    moveq #0,%d0
    rts
.Lemit_original:
    jmp B_mlcc_lane_put

mclf_invalidate:
    clrl B_mlp_clip_undo_op
    clrl B_mlp_clip_undo_lane
    clrl mclf_valid
    | Invalider Undo sans réautoriser une vieille frame encore active. Une
    | publication interrompue se termine en reset, jamais en phases restaurées.
    tstl mclf_pending
    beq .Linvalidate_done
    movel %d0,%sp@-
    moveq #1,%d0
    movel %d0,mclf_pending
    movel %sp@+,%d0
.Linvalidate_done:
    rts

    .data
    .balign 4
    .globl mclf_valid,mclf_pattern,mclf_lane,mclf_context,mclf_phase_valid,mclf_pending,mclf_cfg,mclf_phase
mclf_valid: .long 0
mclf_pattern: .long 0
mclf_lane: .long 0
mclf_context: .long 0
mclf_phase_valid: .long 0
mclf_pending: .long 0
mclf_cfg: .space 32
mclf_phase: .space 64
