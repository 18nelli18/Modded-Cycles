| FUNC+PLAY A : compléter clear/Undo natifs avec les deux LFO sélectionnés.
| Deux JSR UI seulement ; le copier/coller natif et l'audio ne sont pas hookés.
| ABI identique aux cibles OS : (track,kind), D0/SR natifs et d2-d7/a2-a6 gardés.
| Le record Undo est retenu par son vrai control block, jamais par adresse seule.
| Aucune E/S ; état privé borné. Getters/notifications hors IPL7 exclusivement.
    .text
    .globl avcl_clear,avcl_undo,avcl_state,avcl_busy,avcl_end
avcl_clear:
    tstl avcl_busy
    bne .Lclear_native
    moveq #0,%d0
    bra .Lentry
.Lclear_native:
    jmp 0x40019582
avcl_undo:
    tstl avcl_busy
    bne .Lundo_native
    moveq #1,%d0
    bra .Lentry
.Lundo_native:
    jmp 0x40018c50
.Lentry:
    lea %sp@(-216),%sp
    moveml %d2-%d7/%a2-%a5,%sp@
    moveal %sp,%a5
    movel %d0,%a5@(48)
    clrl %a5@(52)
    moveq #1,%d0
    movel %d0,avcl_busy
    movel %a5@(224),%d0
    cmpil #1,%d0
    bne .Lnative
    movew %sr,%d0
    andil #0x700,%d0
    bne .Lnative
    moveal %a5@(220),%a2
    lea %a5@(56),%a3
    bsr .Lresolve
    tstl %d0
    beq .Lnative
    tstl %a5@(48)
    bne .Lundo_validate
    bsr .Lcapture
    moveq #1,%d0
    movel %d0,%a5@(52)
    bra .Lnative
.Lundo_validate:
    bsr .Lmatches
    movel %d0,%a5@(52)
.Lnative:
    movel %a5@(224),%sp@-
    movel %a5@(220),%sp@-
    tstl %a5@(48)
    bne .Lcall_undo
    jsr 0x40019582
    bra .Lreturned
.Lcall_undo:
    jsr 0x40018c50
.Lreturned:
    movew %sr,%d1
    movew %d1,%a5@(44)
    movel %d0,%a5@(40)
    addql #8,%sp
    tstb %d0
    beq .Lout
    tstl %a5@(48)
    bne .Lundo_finish
    | Clear réussi : abandonner l'ancien token, même si aucun LFO n'est résolu.
    bsr .Lrelease
    tstl %a5@(52)
    beq .Lout
    lea %a5@(56),%a3
    bsr .Lidentical
    tstl %d0
    beq .Lout
    | Retenir l'Undo natif avant les notifications de son pouvant l'invalider.
    jsr 0x400cfe46
    moveal %d0,%a4
    lea avcl_state,%a3
    moveal %a3,%a1
    lea %a5@(56),%a0
    moveq #38,%d0
.Lcommit:
    movel %a0@+,%a1@+
    subql #1,%d0
    bpl .Lcommit
    clrl %a3@
    clrl %a3@(36)
    clrl %a3@(40)
    movel %a4@(20),%d0
    cmpil #1,%d0
    bne .Lreset
    tstl %a4@(12)
    beq .Lreset
    tstl %a4@(16)
    beq .Lreset
    movel %a4@(12),%a3@(36)
    pea %a4@(16)
    pea %a3@(40)
    jsr 0x400cfae0
    addql #8,%sp
.Lreset:
    lea .Ldefaults,%a4
    bsr .Lapply
    | Nos notifications peuvent vider l'Undo ; ne jamais écraser un autre record.
    tstl %a3@(36)
    beq .Lout
    jsr 0x400cfe46
    moveal %d0,%a4
    tstl %a4@(12)
    bne .Lpublished
    pea 1
    pea %a3@(36)
    movel %a4,%sp@-
    jsr 0x4006e0e6
    addql #8,%sp
    movel %a4,%sp@-
    jsr 0x4006df18
    addql #8,%sp
.Lpublished:
    bsr .Lpair_matches
    tstl %d0
    beq .Linvalidate
    bsr .Lidentical
    tstl %d0
    beq .Linvalidate
    movel %d0,%a3@
    bra .Lout
.Lundo_finish:
    tstl %a5@(52)
    beq .Linvalidate
    lea avcl_state,%a3
    bsr .Lidentical
    tstl %d0
    beq .Linvalidate
    clrl %a3@
    lea %a3@(44),%a4
    bsr .Lapply
.Linvalidate:
    bsr .Lrelease
.Lout:
    clrl avcl_busy
    movel %a5@(40),%d0
    movew %a5@(44),%d1
    moveml %sp@,%d2-%d7/%a2-%a5
    lea %sp@(216),%sp
    movew %d1,%sr
    rts

| Résoudre les identités sans toucher aux valeurs : a2=track,a3=cellule152.
.Lresolve:
    clrl %a3@
    movel %a2,%a3@(4)
    tstl %a2
    beq .Lno
    movel %a2@(56),%d4
    cmpil #5,%d4
    bhi .Lno
    movel %d4,%a3@(24)
    moveal %a2@,%a0
    moveal %a0@(40),%a0
    movel %a2,%sp@-
    jsr %a0@
    addql #4,%sp
    movel %d0,%a3@(20)
    beq .Lno
    jsr 0x400cf866
    movel %d0,%a3@(8)
    beq .Lno
    movel %d0,%sp@-
    jsr 0x4000eb9c
    addql #4,%sp
    tstl %d0
    beq .Lno
    movel %d4,%sp@-
    movel %d0,%sp@-
    jsr 0x400097f0
    addql #8,%sp
    tstl %d0
    beq .Lno
    moveal %d0,%a0
    moveal %a0@(4),%a4
    movel %a4,%a3@(12)
    beq .Lno
    moveal %a4@,%a0
    moveal %a0@(40),%a0
    movel %a4,%sp@-
    jsr %a0@
    addql #4,%sp
    movel %d0,%a3@(16)
    beq .Lno
    movel A_LF2_context,%d0
    movel %d0,%a3@(28)
    movel A_LF2_epoch,%d0
    movel %d0,%a3@(32)
    movel A_audio_owner,%d0
    movel %d0,%a3@(152)
    moveq #1,%d0
    movel %d0,%a3@
    rts
.Lno:
    moveq #0,%d0
    rts

| Comparer contre une résolution fraîche ; la cellule source reste inchangée.
.Lidentical:
    lea %sp@(-48),%sp
    movel %a3,%sp@
    | Seulement métadonnées0..32 + owner152 : cellule temporaire pleine sur pile.
    lea %sp@(-156),%sp
    moveal %sp,%a3
    bsr .Lresolve
    moveal %sp@(156),%a1
    tstl %d0
    beq .Lidentity_out
    lea %a3@(4),%a0
    lea %a1@(4),%a1
    moveq #7,%d0
.Lidentity_loop:
    movel %a0@+,%d1
    cmpl %a1@+,%d1
    bne .Lidentity_bad
    subql #1,%d0
    bpl .Lidentity_loop
    moveal %sp@(156),%a1
    movel %a3@(152),%d0
    cmpl %a1@(152),%d0
    bne .Lidentity_bad
    moveq #1,%d0
    bra .Lidentity_out
.Lidentity_bad:
    moveq #0,%d0
.Lidentity_out:
    moveal %sp@(156),%a3
    lea %sp@(204),%sp
    rts

.Lmatches:
    lea avcl_state,%a3
    tstl %a3@
    beq .Lno
    bsr .Lidentical
    tstl %d0
    beq .Lno
.Lpair_matches:
    jsr 0x400cfe46
    moveal %d0,%a0
    movel %a0@(20),%d0
    cmpil #1,%d0
    bne .Lno
    movel %a0@(12),%d0
    beq .Lno
    cmpl %a3@(36),%d0
    bne .Lno
    movel %a0@(16),%d0
    beq .Lno
    cmpl %a3@(40),%d0
    bne .Lno
    moveq #1,%d0
    rts

| Copie atomique des huit mots, cinq mots sauvés et phases ; aucun appel OS.
.Lcapture:
    movew %sr,%d7
    movew #0x2700,%sr
    moveal %a3@(16),%a0
    lea %a0@(22),%a0
    lea %a3@(44),%a1
    moveq #3,%d0
.Lcapture1:
    movel %a0@+,%a1@+
    subql #1,%d0
    bpl .Lcapture1
    lea %a0@(38),%a0
    movel %a0@+,%a1@+
    movel %a0@+,%a1@+
    movew %a0@,%a1@
    clrw %a1@(2)
    lea %a3@(72),%a1
    moveal %a3@(28),%a0
    tstl %a0
    beq .Lcapture_default
    movel %a3@(24),%d0
    lsll #4,%d0
    lea %a0@(192),%a0
    addal %d0,%a0
    bra .Lcapture_cfg
.Lcapture_default:
    moveal %a3@(152),%a0
    tstl %a0
    beq .Lcapture_canonical
    movel %a3@(24),%d0
    lsll #4,%d0
    lea %a0@(4896),%a0
    addal %d0,%a0
    bra .Lcapture_cfg
.Lcapture_canonical:
    lea .Ldefaults+28,%a0
.Lcapture_cfg:
    moveq #3,%d0
.Lcapture_cfgloop:
    movel %a0@+,%a1@+
    subql #1,%d0
    bpl .Lcapture_cfgloop
    | Les cinq champs du son priment sur le cache UI après un Load récent.
    movew %a3@(60),%a3@(72)
    movew %a3@(62),%a3@(74)
    movew %a3@(64),%a3@(80)
    movew %a3@(66),%d0
    bne .Lcapture_dest
    movel #0x7f00,%d0
.Lcapture_dest:
    movew %d0,%a3@(78)
    movew %a3@(68),%a3@(86)
    movel %a3@(24),%d0
    lsll #5,%d0
    lea 0x40fde838,%a0
    addal %d0,%a0
    lea %a3@(88),%a1
    moveq #7,%d1
.Lcapture_phase1:
    movel %a0@+,%a1@+
    subql #1,%d1
    bpl .Lcapture_phase1
    moveal %a3@(28),%a0
    tstl %a0
    beq .Lcapture_phase_default
    addal %d0,%a0
    bra .Lcapture_phase2
.Lcapture_phase_default:
    lea .Ldefaults+76,%a0
.Lcapture_phase2:
    moveq #7,%d1
.Lcapture_phase2loop:
    movel %a0@+,%a1@+
    subql #1,%d1
    bpl .Lcapture_phase2loop
    movew %d7,%sr
    rts

| a3=identités/Undo,a4=108 octets LFO+phases ; appels notifiés à IPL0.
.Lapply:
    movew %sr,%d7
    movew #0x2700,%sr
    moveal %a3@(16),%a1
    lea %a1@(22),%a1
    moveal %a4,%a0
    moveq #3,%d0
.Lapply1:
    movel %a0@+,%a1@+
    subql #1,%d0
    bpl .Lapply1
    lea %a1@(38),%a1
    movel %a0@+,%a1@+
    movel %a0@+,%a1@+
    movew %a0@,%a1@
    moveal %a3@(28),%a1
    tstl %a1
    beq .Lapply_owner
    movel %a3@(24),%d0
    lsll #4,%d0
    lea %a1@(192),%a1
    addal %d0,%a1
    lea %a4@(28),%a0
    moveq #3,%d0
.Lapply_cfg:
    movel %a0@+,%a1@+
    subql #1,%d0
    bpl .Lapply_cfg
.Lapply_owner:
    moveal %a3@(152),%a1
    tstl %a1
    beq .Lapply_phases
    movel %a3@(24),%d0
    lsll #4,%d0
    lea %a1@(4896),%a1
    addal %d0,%a1
    lea %a4@(28),%a0
    moveq #3,%d0
.Lapply_snapshot:
    movel %a0@+,%a1@+
    subql #1,%d0
    bpl .Lapply_snapshot
.Lapply_phases:
    movel %a3@(24),%d0
    lsll #5,%d0
    lea 0x40fde838,%a1
    addal %d0,%a1
    lea %a4@(44),%a0
    moveq #7,%d1
.Lapply_phase1:
    movel %a0@+,%a1@+
    subql #1,%d1
    bpl .Lapply_phase1
    moveal %a3@(28),%a1
    tstl %a1
    beq .Lapply_notify
    addal %d0,%a1
    moveq #7,%d1
.Lapply_phase2:
    movel %a0@+,%a1@+
    subql #1,%d1
    bpl .Lapply_phase2
.Lapply_notify:
    movew %d7,%sr
    lea %sp@(-8),%sp
    movel #0x400fd0ac,%sp@
    moveq #1,%d4
.Lnotify_loop:
    movel %d4,%sp@(4)
    moveal %a3@(12),%a0
    moveal %a0@,%a1
    moveal %a1@(16),%a1
    pea %sp@
    movel %a0,%sp@-
    jsr %a1@
    addql #8,%sp
    addql #1,%d4
    cmpil #9,%d4
    bne .Lnotify_next
    moveq #28,%d4
.Lnotify_next:
    cmpil #33,%d4
    bne .Lnotify_loop
    addql #8,%sp
    rts

.Lrelease:
    lea avcl_state,%a0
    clrl %a0@
    clrl %a0@(36)
    pea %a0@(40)
    jsr 0x400cf23c
    addql #4,%sp
    clrl avcl_state+40
    rts

    .balign 4
.Ldefaults:
    .word 0x7000,0x0400,0x4000,0,0,0,0,0x4000
    .word 0x7000,0x0400,0,0,0x4000,0
    .word 0x7000,0x0400,0x4000,0x7f00,0,0,0,0x4000
    .space 64
    .balign 4
avcl_state: .space 156
avcl_busy: .long 0
avcl_end:
