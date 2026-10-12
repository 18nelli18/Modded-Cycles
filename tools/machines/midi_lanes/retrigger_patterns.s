| Réglages retrigger/arp privés par banque B : 6 x (8 défauts + 64 x8 locks).
| Table de 96 couples banque/settings ; recherche audio uniquement au changement
| de propriétaire. Allocation UI seule, publication du couple sous IPL7.
| prepare(bank) -> settings3120 ou0 ; lookup(bank) -> settings ou0.
| Load natif retire les extensions ; sauvegarde encore absente.
    .data
    .balign 4
.Lpatterns: .space 768
    .globl ml_repeat_play_settings,ml_repeat_edit_settings,ml_repeat_reset_pending
ml_repeat_reset_pending: .long 0
ml_repeat_play_settings: .long 0
ml_repeat_edit_settings: .long 0
    .text
    .globl ml_repeat_pattern_prepare,ml_repeat_pattern_lookup,ml_repeat_prepare_ui
ml_repeat_prepare_ui:
    movel %a2,%sp@-
    movew %sr,%d0
    andil #0x700,%d0
    bne .Lprepare_ui_done
    jsr ml_repeat_project_reset
    tstl ml_repeat_arp_bank
    bne .Lprepare_ui_pattern
    pea 240
    jsr 0x400802e0
    addql #4,%sp
    tstl %d0
    beq .Lprepare_ui_done
    moveal %d0,%a2
    movel %a2,%sp@-
    jsr ml_arp_bank_init
    addql #4,%sp
    movel %a2,ml_repeat_arp_bank
.Lprepare_ui_pattern:
    movel ml_pattern,%sp@-
    jsr ml_repeat_pattern_prepare
    addql #4,%sp
    movel %d0,ml_repeat_edit_settings
    moveal ml_pattern,%a0
    cmpal ml_play_pattern,%a0
    bne .Lprepare_ui_done
    movel %d0,ml_repeat_play_settings
.Lprepare_ui_done:
    moveal %sp@+,%a2
    rts
ml_repeat_pattern_lookup:
    .ifdef ML_STORAGE2
    tstl ml_repeat_reset_pending
    bne .Llookup_bad
    movel %sp@(4),%d0
    beq .Llookup_bad
    addil #1584,%d0
    rts
    .endif
    tstl ml_repeat_reset_pending
    bne .Llookup_bad
    movel %sp@(4),%d1
    beq .Llookup_bad
    lea.l .Lpatterns,%a0
    moveq #95,%d0
.Llookup_loop:
    cmpl %a0@,%d1
    beq .Llookup_found
    addql #8,%a0
    subql #1,%d0
    bpl .Llookup_loop
.Llookup_bad:
    moveq #0,%d0
    rts
.Llookup_found:
    movel %a0@(4),%d0
    rts
ml_repeat_pattern_prepare:
    .ifdef ML_STORAGE2
    movew %sr,%d0
    andil #0x700,%d0
    bne .Llookup_bad
    bra ml_repeat_pattern_lookup
    .endif
    lea.l %sp@(-24),%sp
    movem.l %d2-%d3/%a2-%a4,%sp@
    movew %sr,%d0
    movel %d0,%sp@(20)
    andil #0x700,%d0
    bne .Lprepare_bad
    movel %sp@(28),%d2
    beq .Lprepare_bad
    movel %d2,%d0
    andil #3,%d0
    bne .Lprepare_bad
    movel %d2,%sp@-
    jsr ml_repeat_pattern_lookup
    addql #4,%sp
    tstl %d0
    bne .Lprepare_done
    lea.l .Lpatterns,%a2
    moveq #95,%d3
.Lprepare_slot:
    tstl %a2@
    beq .Lprepare_allocate
    addql #8,%a2
    subql #1,%d3
    bpl .Lprepare_slot
    bra .Lprepare_bad
.Lprepare_allocate:
    pea 3120
    jsr 0x400802e0
    addql #4,%sp
    tstl %d0
    beq .Lprepare_bad
    moveal %d0,%a3
    moveal %a3,%a4
    moveq #5,%d3
.Lprepare_lane:
    | enabled0/Rte8/Len0/curve0/ArpOFF/Oct1/0/0.
    movel #0x00080000,%d0
    movel %d0,%a4@
    movel #0x05010000,%d0
    movel %d0,%a4@(4)
    pea %a4@(8)
    jsr ml_repeat_locks_init
    addql #4,%sp
    lea.l %a4@(520),%a4
    subql #1,%d3
    bpl .Lprepare_lane
    movew #0x2700,%sr
    movel %a3,%a2@(4)
    movel %d2,%a2@
    movel %a3,%d0
    bra .Lprepare_done
.Lprepare_bad:
    moveq #0,%d0
.Lprepare_done:
    movel %sp@(20),%d1
    movem.l %sp@,%d2-%d3/%a2-%a4
    lea.l %sp@(24),%sp
    movew %d1,%sr
    rts

| Après chargement natif réussi : bloquer les réglages et annuler les notes.
| Rejoue exactement l'épilogue déplacé ; résultat D0 et SR conservés.
    .globl ml_repeat_project_hook,ml_repeat_project_reset,ml_repeat_project_notice
ml_repeat_project_hook:
    jsr ml_repeat_project_notice
    moveml %sp@,%d2-%d3/%a2
    lea.l %sp@(32),%sp
    rts
ml_repeat_project_notice:
    lea.l %sp@(-20),%sp
    moveml %d0-%d1/%a0-%a1,%sp@
    movew %sr,%d1
    movel %d1,%sp@(16)
    tstb %d0
    beq .Lproject_hook_done
    movew #0x2700,%sr
    moveq #1,%d0
    movel %d0,ml_repeat_reset_pending
    clrl ml_repeat_play_settings
    clrl ml_repeat_edit_settings
    clrl ml_repeat_owner
    tstl ml_runtime
    beq .Lproject_hook_done
    pea ml_repeat_states
    movel ml_runtime,%sp@-
    jsr ml_repeat_cancel_all
    addql #8,%sp
.Lproject_hook_done:
    movel %sp@(16),%d1
    movew %d1,%sr
    moveml %sp@,%d0-%d1/%a0-%a1
    lea.l %sp@(20),%sp
    rts
| UI : retirer chaque entrée avant free ; l'audio ne consulte plus la table.
ml_repeat_project_reset:
    tstl ml_repeat_reset_pending
    beq .Lproject_reset_done
    lea.l %sp@(-16),%sp
    moveml %d2/%a2-%a3,%sp@
    movew %sr,%d0
    movel %d0,%sp@(12)
    andil #0x700,%d0
    bne .Lproject_reset_out
    lea .Lpatterns,%a2
    moveq #95,%d2
.Lproject_reset_loop:
    movew #0x2700,%sr
    moveal %a2@(4),%a3
    clrl %a2@
    clrl %a2@(4)
    movel %sp@(12),%d0
    movew %d0,%sr
    tstl %a3
    beq .Lproject_reset_next
    movel %a3,%sp@-
    jsr 0x400802ec
    addql #4,%sp
.Lproject_reset_next:
    addql #8,%a2
    subql #1,%d2
    bpl .Lproject_reset_loop
    .ifdef ML_CLIPBOARD
    jsr mlp_clip_invalidate
    .endif
    movel ml_repeat_arp_bank,%d0
    beq .Lproject_reset_publish
    movel %d0,%sp@-
    jsr ml_arp_bank_init
    addql #4,%sp
.Lproject_reset_publish:
    clrl ml_repeat_reset_pending
.Lproject_reset_out:
    movel %sp@(12),%d0
    movew %d0,%sr
    moveml %sp@,%d2/%a2-%a3
    lea.l %sp@(16),%sp
.Lproject_reset_done:
    rts
