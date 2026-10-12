| Prototype verrous retrigger/arp B : table privée de 64 x 8 octets par voie.
| enabled/rate/length/curve/mode/octaves/masque/0 ; aucune donnée audio native.
| ml_repeat_lock(table,step,field,value) -> 1 si écrit, 0 si invalide.
| Publication d'un seul octet ; l'activation est écrite après les paramètres.
| Le raccordement au pattern, au menu et au stockage reste à effectuer.
    .text
    .globl ml_repeat_lock,ml_repeat_locks_init,ml_repeat_resolve
ml_repeat_lock:
    movel %sp@(8),%d0
    cmpil #63,%d0
    bhi .Llock_bad
    lsll #3,%d0
    moveal %sp@(4),%a0
    addal %d0,%a0
    movel %sp@(12),%d1
    cmpil #5,%d1
    bhi .Llock_bad
    movel %sp@(16),%d0
    cmpil #3,%d1
    beq .Llock_curve
    cmpil #5,%d1
    beq .Llock_octave
    lea.l .Llock_max,%a1
    moveb %a1@(0,%d1:l),%d1
    andil #255,%d1
    cmpl %d1,%d0
    bhi .Llock_bad
    bra .Llock_write
.Llock_curve:
    cmpil #-128,%d0
    blt .Llock_bad
    cmpil #127,%d0
    bgt .Llock_bad
    bra .Llock_write
.Llock_octave:
    subql #1,%d0
    cmpil #3,%d0
    bhi .Llock_bad
    addql #1,%d0
.Llock_write:
    movew %sr,%d1
    movel %d1,%sp@-
    movew #0x2700,%sr
    movel %sp@(16),%d1
    moveb %d0,%a0@(0,%d1:l)
    bset %d1,%a0@(6)
    moveq #1,%d0
    movel %sp@+,%d1
    movew %d1,%sr
    rts
| Résoudre les locks partiels avec les six réglages de voie, sans les altérer.
| ml_repeat_resolve(defaults8,table512,step,out8) -> bool.
| Validation intégrale avant publication ; lecture sous IPL7, aucun I/O.
ml_repeat_resolve:
    lea.l %sp@(-24),%sp
    movem.l %d2/%a2-%a3,%sp@
    movew %sr,%d0
    movel %d0,%sp@(12)
    movew #0x2700,%sr
    moveq #0,%d2
    movel %sp@(36),%d0
    cmpil #63,%d0
    bhi .Lresolve_done
    moveal %sp@(28),%a0
    moveal %sp@(32),%a1
    moveal %sp@(40),%a2
    lsll #3,%d0
    addal %d0,%a1
    lea.l %sp@(16),%a3
    movel %a0@,%a3@
    movel %a0@(4),%a3@(4)
    moveq #0,%d0
    moveb %a1@(6),%d0
    andil #0xc0,%d0
    bne .Lresolve_done
    moveq #0,%d1
.Lresolve_field:
    btst %d1,%a1@(6)
    beq .Lresolve_inherit
    moveb %a1@(0,%d1:l),%d0
    moveb %d0,%a3@(0,%d1:l)
.Lresolve_inherit:
    moveq #0,%d0
    moveb %a3@(0,%d1:l),%d0
    cmpil #3,%d1
    beq .Lresolve_valid
    cmpil #5,%d1
    beq .Lresolve_octave
    lea.l .Llock_max,%a0
    moveq #0,%d2
    moveb %a0@(0,%d1:l),%d2
    cmpl %d2,%d0
    bhi .Lresolve_bad
    bra .Lresolve_valid
.Lresolve_octave:
    subql #1,%d0
    cmpil #3,%d0
    bhi .Lresolve_bad
.Lresolve_valid:
    addql #1,%d1
    cmpil #6,%d1
    bne .Lresolve_field
    clrw %a3@(6)
    movel %a3@,%a2@
    movel %a3@(4),%a2@(4)
    moveq #1,%d2
    bra .Lresolve_done
.Lresolve_bad:
    moveq #0,%d2
.Lresolve_done:
    movel %d2,%d0
    movel %sp@(12),%d1
    movem.l %sp@,%d2/%a2-%a3
    lea.l %sp@(24),%sp
    movew %d1,%sr
    rts
.Llock_bad:
    moveq #0,%d0
    rts
ml_repeat_locks_init:
    moveal %sp@(4),%a0
    moveq #63,%d0
    moveq #1,%d1
.Llock_init:
    clrl %a0@
    clrl %a0@(4)
    moveb %d1,%a0@(5)
    addql #8,%a0
    subql #1,%d0
    bpl .Llock_init
    moveq #1,%d0
    rts
    .section .rodata
.Llock_max: .byte 1,16,127,0,5,4

| Suppression UI du pas sélectionné : retirer tous ses locks privés.
| Les défauts de voie restent intacts ; annuler le repeat réserve son Note Off.
    .text
    .globl ml_repeat_delete_selected
ml_repeat_delete_selected:
    lea.l %sp@(-12),%sp
    moveml %d2/%a2,%sp@
    movew %sr,%d0
    movel %d0,%sp@(8)
    andil #0x700,%d0
    bne .Ldelete_done
    movel mlp_track,%d2
    cmpil #5,%d2
    bhi .Ldelete_done
    movel mlp_step,%d0
    cmpil #63,%d0
    bhi .Ldelete_done
    moveal ml_repeat_edit_settings,%a2
    tstl %a2
    beq .Ldelete_done
    lsll #3,%d0
    addal %d0,%a2
    movel %d2,%d0
    muluw #520,%d0
    addal %d0,%a2
    movew #0x2700,%sr
    clrl %a2@(8)
    movel #0x00010000,%d0
    movel %d0,%a2@(12)
    movel %d2,%d0
    muluw #20,%d0
    lea ml_repeat_states,%a0
    addal %d0,%a0
    movel %d2,%sp@-
    movel %a0,%sp@-
    movel ml_runtime,%sp@-
    jsr ml_repeat_cancel
    lea.l %sp@(12),%sp
.Ldelete_done:
    movel %sp@(8),%d0
    movew %d0,%sr
    moveml %sp@,%d2/%a2
    lea.l %sp@(12),%sp
    rts

| Clipboard des réglages B : d0=copy/snapshot/undo/paste/clear (0..4).
| Appelé sous IPL7 ; copie 520 octets, clear conserve les 8 défauts.
    .data
    .balign 4
.Lrepeat_clip: .long 0
    .text
    .globl ml_repeat_clip
ml_repeat_clip:
    lea.l %sp@(-16),%sp
    moveml %d2-%d3/%a2-%a3,%sp@
    movel %d0,%d3
    moveal ml_repeat_edit_settings,%a2
    tstl %a2
    beq .Lrclip_done
    movel mlp_track,%d2
    cmpil #5,%d2
    bhi .Lrclip_done
    movel %d2,%d0
    muluw #520,%d0
    addal %d0,%a2
    cmpil #2,%d3
    blo .Lrclip_transfer
    movel %d2,%d0
    muluw #20,%d0
    lea ml_repeat_states,%a0
    addal %d0,%a0
    movel %d2,%sp@-
    movel %a0,%sp@-
    movel ml_runtime,%sp@-
    jsr ml_repeat_cancel
    lea.l %sp@(12),%sp
.Lrclip_transfer:
    cmpil #4,%d3
    beq .Lrclip_clear
    moveal .Lrepeat_clip,%a3
    tstl %a3
    beq .Lrclip_done
    tstl %d3
    beq .Lrclip_snapshot
    cmpil #1,%d3
    bne .Lrclip_restore
    moveal .Lrepeat_clip,%a3
    lea %a3@(520),%a3
.Lrclip_snapshot:
    moveal %a2,%a0
    moveal %a3,%a1
    bra .Lrclip_copy
.Lrclip_restore:
    cmpil #2,%d3
    bne .Lrclip_paste
    moveal .Lrepeat_clip,%a3
    lea %a3@(520),%a3
.Lrclip_paste:
    moveal %a3,%a0
    moveal %a2,%a1
.Lrclip_copy:
    movel #129,%d0
.Lrclip_loop:
    movel %a0@+,%a1@+
    subql #1,%d0
    bpl .Lrclip_loop
    bra .Lrclip_done
.Lrclip_clear:
    lea %a2@(8),%a0
    movel %a0,%sp@-
    jsr ml_repeat_locks_init
    addql #4,%sp
.Lrclip_done:
    moveml %sp@,%d2-%d3/%a2-%a3
    lea.l %sp@(16),%sp
    rts

| Allocation UI seulement, hors section critique ; aucun bloc TG supplémentaire.
    .globl ml_repeat_clip_prepare
ml_repeat_clip_prepare:
    movel .Lrepeat_clip,%d0
    bne .Lrclip_prepared
    movel #1040,%sp@-
    jsr 0x400802e0
    addql #4,%sp
    tstl %d0
    beq .Lrclip_prepared
    movel %d0,.Lrepeat_clip
.Lrclip_prepared:
    rts
