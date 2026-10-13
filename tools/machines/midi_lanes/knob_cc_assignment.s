| Assignation en brouillon : lecture musicale conserve ses valeurs validées.
| SETTINGS choisit dans draft144 ; release publie l'ensemble sous IPL7.
    .data
    .balign 4
    .globl mlkc_draft,mlkc_draft_active
mlkc_draft: .space 144
mlkc_draft_active: .long 0
    .text
    .globl mlkc_edit_state,mlkc_assign_sync,mlkc_assign_cancel
| a1 = état à éditer/dessiner. UI seulement, aucun envoi MIDI.
mlkc_edit_state:
    lea mlkc_state,%a1
    tstl TG_set_held
    beq .Lstate_done
    tstl mlkc_draft_active
    bne .Ldraft_ready
    moveal %a1,%a0
    lea mlkc_draft,%a1
    moveq #35,%d0
.Ldraft_copy:
    movel %a0@+,%a1@+
    subql #1,%d0
    bpl .Ldraft_copy
    moveq #1,%d0
    movel %d0,mlkc_draft_active
.Ldraft_ready:
    lea mlkc_draft,%a1
.Lstate_done:
    rts
mlkc_assign_sync:
    tstl TG_set_held
    bne .Lsync_done
    tstl mlkc_draft_active
    beq .Lsync_done
    movew %sr,%d0
    movel %d0,%sp@-
    movew #0x2700,%sr
    lea mlkc_draft,%a0
    lea mlkc_state,%a1
    moveq #35,%d1
.Lcommit:
    movel %a0@+,%a1@+
    subql #1,%d1
    bpl .Lcommit
    clrl mlkc_draft_active
    movel %sp@+,%d0
    movew %d0,%sr
.Lsync_done:
    rts
mlkc_assign_cancel:
    clrl mlkc_draft_active
    rts
