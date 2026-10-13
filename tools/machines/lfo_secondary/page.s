| Note 58 : page LFO 2 expérimentale, rendu natif du menu de paramètres.
| Construction adaptée de Model-TG (TinyGregAudio, MIT), commit 70b39dd ;
| licence dans tweaks/model-cycles_OS1.13/LICENSE-Model-TG.
| Contexte audio fourni et initialisé séparément ; fermeture sans le libérer.
    .section .text.lf2p_open,"ax"
    .globl lf2p_open,lf2p_dtor0,lf2p_dtor1
lf2p_open:
    lea.l   lf2p_opened,%a0
    clrl    %a0@
    lea.l   %sp@(-24),%sp
    moveml  %d2-%d4/%a2-%a4,%sp@
    moveq   #0,%d0                | uniquement dans la tâche UI, comme loop_toggle
    movew   %sr,%d0
    andil   #0x0700,%d0
    bnew    lf2p_o_done
    tstl lf2_context
    beqw lf2p_o_done
    lea.l   lf2p_obj,%a0
    tstl    %a0@
    bnew    lf2p_o_done             | page déjà ouverte
    tstl    0x40fe4178
    beqw    lf2p_o_done             | gestion des vues pas encore initialisée
    | groupe vtable privé, reconstruit depuis celui de l’OS
    lea.l   0x40117918,%a0
    lea.l   lf2p_vt,%a1
    moveq   #(0xb0/4)-1,%d0
lf2p_o_cp:
    movel   %a0@+,%a1@+
    subql   #1,%d0
    bplw    lf2p_o_cp
    lea.l   lf2p_vt,%a1
    movel   #lf2p_dtor0,%d0
    movel   %d0,%a1@(0x08)
    movel   #lf2p_dtor1,%d0
    movel   %d0,%a1@(0x0c)
    movel   #lf2p_menu_key,%d0
    movel   %d0,%a1@(0x10)
    movel   #lf2p_render,%d0
    movel   %d0,%a1@(0x18)
    movel   #lf2p_enc,%d0
    movel   %d0,%a1@(0x4c)
    movel   #lf2p_enc_th,%d0
    movel   %d0,%a1@(0x60)
    movel #lf2p_pad,%d0
    movel %d0,%a1@(0x9c)
    jmp lf2p_o_allocate
    .section .text.lf2p_open_allocate,"ax"
lf2p_o_allocate:
    | Même sélection de piste que le menu LFO natif, sans la modifier.
    jsr 0x400cf866
    tstl %d0
    beq lf2p_o_default_track
    movel %d0,%sp@-
    jsr 0x4000eb90
    movel %d0,%sp@-
    jsr 0x40012412
    addql #8,%sp
    cmpil #5,%d0
    bls lf2p_o_track_ready
lf2p_o_default_track:
    moveq #0,%d0
lf2p_o_track_ready:
    movel %d0,lf2p_track
    lea.l   0x400802e0,%a3        | operator new
    pea     0xb00
    jsr     %a3@
    addql   #4,%sp
    tstl    %d0
    beqw    lf2p_o_done
    movea.l %d0,%a4
    movel   %a4,%sp@-
    jsr     0x400a22b0            | constructeur OS de la page MACHINES
    addql   #4,%sp
    movel %a4,%sp@-
    jsr lf2l_init
    addql #4,%sp
    lea.l   lf2p_vt,%a1
    lea.l   %a1@(8),%a0
    movel   %a0,%a4@              | vptr principal
    lea.l   %a1@(0x58),%a0
    movel   %a0,%a4@(4)           | base +4 (événements encodeur)
    lea.l lf2p_vt+0x94,%a0
    movel %a0,%a4@(16)
    pea     0x10                  | détenteur de référence, comme l’ouverture OS
    jsr     %a3@                  | construite à 0x4001ca40
    addql   #4,%sp
    tstl %d0
    bnew lf2p_o_holder
    movel %a4,%sp@-
    jsr 0x400f4486
    addql #4,%sp
    braw lf2p_o_done
    .section .text.lf2p_open_holder,"ax"
lf2p_o_holder:
    movea.l %d0,%a0
    movel %a4,lf2p_obj
    moveq #5,%d0
    movel %d0,lf2p_row
    clrl lf2p_edit
    clrl lf2p_assigned
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
    lea.l   lf2p_opened,%a0
    moveq   #1,%d0
    movel   %d0,%a0@
lf2p_o_done:
    movel lf2p_opened,%d0
    moveml  %sp@,%d2-%d4/%a2-%a4
    lea.l   %sp@(24),%sp
    rts

    .section .text.lf2p_dtor,"ax"
| ---- destructeurs : oublier la page, puis appeler ceux de l’OS ----
lf2p_dtor0:
    lea.l   lf2p_obj,%a0
    clrl    %a0@
    jmp     0x400f43ca
lf2p_dtor1:
    lea.l   lf2p_obj,%a0
    clrl    %a0@
    jmp     0x400f4486

    .section .text.lf2p_key,"ax"
    .globl lf2p_menu_key,lf2p_enc,lf2p_enc_th,lf2p_render,lf2p_pad
lf2p_menu_key:
    lea.l %sp@(-8),%sp
    movem.l %d2/%a2,%sp@
    moveal %sp@(12),%a2
    moveal %sp@(16),%a0
    movel %a0@(12),%d0
    movel %a0@(16),%d2
    cmpil #10,%d0
    beq .Lpk_transport
    cmpil #11,%d0
    beq .Lpk_transport
    cmpil #8,%d0
    beq .Lpk_lfo
    cmpil #12,%d0
    beq .Lpk_close_down
    cmpil #13,%d0
    beq .Lpk_close_down
    cmpil #32,%d0
    bne .Lpk_used
    btst #4,%d2
    beq .Lpk_used
    moveq #1,%d0
    eorl %d0,lf2p_edit
    bra .Lpk_redraw
.Lpk_lfo:
    andil #3,%d2
    bne .Lpk_used
    tstl lf2p_assigned
    beq .Lpk_close
    clrl lf2p_assigned
    bra .Lpk_used
.Lpk_close_down:
    andil #9,%d2
    cmpil #1,%d2
    bne .Lpk_used
.Lpk_close:
    moveal %a2@,%a0
    moveal %a0@(0x28),%a0
    movel %a2,%sp@-
    jsr %a0@
    addql #4,%sp
    bra .Lpk_used
.Lpk_transport:
    btst #1,%d2
    bne .Lpk_used
    moveq #0,%d0
    bra .Lpk_return
.Lpk_redraw:
    movel %a2,%sp@-
    jsr 0x40076082
    addql #4,%sp
.Lpk_used:
    moveq #1,%d0
.Lpk_return:
    movem.l %sp@,%d2/%a2
    lea.l %sp@(8),%sp
    rts

| Sélection explicite des six LFO secondaires par pads, sans voix sonore.
    .section .text.lf2p_pad,"ax"
lf2p_pad:
    moveal %sp@(8),%a0
    movel %a0@(20),%d0
    subql #1,%d0
    cmpil #5,%d0
    bhi .Lpp_done
    movel %a0@(16),%d1
    cmpil #1,%d1
    bne .Lpp_done
    movel %d0,lf2p_track
    moveal %sp@(4),%a0
    lea.l %a0@(-16),%a0
    movel %a0,%sp@-
    jsr 0x40076082
    addql #4,%sp
.Lpp_done:
    moveq #1,%d0
    rts

    .section .text.lf2p_enc_navigation,"ax"
lf2p_enc_th:
    subql #4,%sp@(4)
lf2p_enc:
    lea.l %sp@(-16),%sp
    movem.l %d2-%d4/%a2,%sp@
    moveal %sp@(20),%a2
    moveal %sp@(24),%a0
    movel %a0@(12),%d0
    cmpil #1,%d0
    bne .Lpe_quick
    pea 1
    pea 1
    movel %a0,%sp@-
    jsr 0x4006f73a
    lea.l %sp@(12),%sp
    tstl %d0
    beq .Lpe_out
    moveq #1,%d3
    tstl %d0
    bpl .Lpe_sign
    moveq #-1,%d3
.Lpe_sign:
    movel lf2p_row,%d2
    tstl lf2p_edit
    bne .Lpe_value
    lea.l lf2l_inverse,%a0
    movel %a0@(0,%d2:l:4),%d2
    addl %d3,%d2
    bmi .Lpe_out
    cmpil #8,%d2
    bhi .Lpe_out
    lea.l lf2l_order,%a0
    movel %a0@(0,%d2:l:4),%d2
    movel %d2,lf2p_row
    bra .Lpe_redraw
.Lpe_value:
    tstl %d2
    bne .Lpe_field
    movel lf2p_track,%d0
    addl %d3,%d0
    cmpil #5,%d0
    bhi .Lpe_out
    movel %d0,lf2p_track
    bra .Lpe_redraw
    .section .text.lf2p_enc_quick,"ax"
.Lpe_quick:
    subql #2,%d0
    cmpil #11,%d0
    bhi .Lpe_out
    movel %d0,%d4
    pea 8
    jsr 0x4007faf4
    addql #4,%sp
    tstl %d0
    beq .Lpe_out
    pea 8
    pea 1
    movel %sp@(32),%sp@-
    jsr 0x4006f73a
    lea.l %sp@(12),%sp
    tstl %d0
    beq .Lpe_out
    movel %d0,%sp@-
    movel %d4,%sp@-
    jsr lf2p_quick_assign
    addql #8,%sp
    bra .Lpe_redraw
    .section .text.lf2p_enc_value,"ax"
.Lpe_field:
    jsr lf2p_raw_value
    tstl lf2_context
    beq .Lpe_out
    subql #1,%d2
    lea.l lf2p_max,%a0
    moveq #0,%d4
    movew %a0@(0,%d2:l:2),%d4
    cmpil #33,%d4
    bne .Lpe_not_dest
    cmpil #127,%d0
    bne .Lpe_not_dest
    moveq #33,%d0
.Lpe_not_dest:
    cmpil #32767,%d4
    bne .Lpe_add
    lsll #8,%d3
.Lpe_add:
    addl %d3,%d0
    bpl .Lpe_low_ok
    moveq #0,%d0
.Lpe_low_ok:
    cmpl %d4,%d0
    bls .Lpe_high_ok
    movel %d4,%d0
.Lpe_high_ok:
    cmpil #33,%d4
    bne .Lpe_set
    movel %d0,%d4
.Lpe_dest_scan:
    cmpil #33,%d4
    beq .Lpe_dest_off
    movel %d4,%sp@-
    jsr lf2p_destination_name
    addql #4,%sp
    moveal %d0,%a0
    movel %a0@,%d0
    cmpil #0x45525200,%d0
    bne .Lpe_dest_valid
    addl %d3,%d4
    bmi .Lpe_out
    bra .Lpe_dest_scan
.Lpe_dest_valid:
    movel %d4,%d0
    bra .Lpe_set
.Lpe_dest_off:
    moveq #127,%d0
.Lpe_set:
    movel %d0,%sp@-
    movel %d2,%sp@-
    movel lf2p_track,%sp@-
    movel lf2_context,%sp@-
    jsr lf2_edit
    lea.l %sp@(16),%sp
    jmp .Lpe_redraw
    .section .text.lf2p_enc_tail,"ax"
.Lpe_redraw:
    movel %a2,%sp@-
    jsr 0x40076082
    addql #4,%sp
.Lpe_out:
    moveq #1,%d0
    movem.l %sp@,%d2-%d4/%a2
    lea.l %sp@(16),%sp
    rts

| d2 = ligne 1..8, résultat brut d0, ne touche pas d2 ni d3..d7.
    .section .text.lf2p_raw_value,"ax"
lf2p_raw_value:
    moveq #0,%d0
    moveal lf2_context,%a0
    tstl %a0
    beq .Lpv_done
    movel lf2p_track,%d1
    lsll #4,%d1
    lea.l %a0@(190),%a0
    addal %d1,%a0
    movew %a0@(0,%d2:l:2),%d0
    cmpil #2,%d2
    beq .Lpv_enum
    cmpil #4,%d2
    beq .Lpv_enum
    cmpil #5,%d2
    beq .Lpv_enum
    cmpil #7,%d2
    bne .Lpv_done
.Lpv_enum:
    lsrl #8,%d0
.Lpv_done:
    rts

    .section .text.lf2p_value,"ax"
    .globl lf2l_value_start
lf2l_value_start:
    tstl %d2
    bne .Lpr_field
    movel lf2p_track,%d0
    addql #1,%d0
    bra .Lpr_number
.Lpr_field:
    jsr lf2p_raw_value
    cmpil #5,%d2
    beq .Lpr_wave_name
    cmpil #7,%d2
    bne .Lpr_dest
    cmpil #4,%d0
    bhi .Lpr_number
    lea.l 0x40108f40,%a0
    bra .Lpr_enum_name
.Lpr_wave_name:
    cmpil #6,%d0
    bhi .Lpr_number
    lea.l 0x40108f24,%a0
.Lpr_enum_name:
    movel %a0@(0,%d0:l:4),%sp@-
    pea lf2p_fmt_s
    bra .Lpr_value
.Lpr_dest:
    cmpil #4,%d2
    bne .Lpr_not_dest
    cmpil #127,%d0
    bne lf2p_dest_name
    pea lf2p_off
    pea lf2p_fmt_s
    bra .Lpr_value
    .section .text.lf2p_render_tail,"ax"
.Lpr_not_dest:
    cmpil #2,%d2
    beq lf2p_multiplier
    cmpil #1,%d2
    beq .Lpr_signed
    cmpil #3,%d2
    beq .Lpr_signed
    cmpil #8,%d2
    beq .Lpr_signed
    cmpil #6,%d2
    bne .Lpr_number
    lsrl #8,%d0
    bra .Lpr_number
.Lpr_signed:
    subil #16384,%d0
    asrl #8,%d0
.Lpr_number:
    movel %d0,%sp@-
    pea lf2p_fmt_d
.Lpr_value:
    pea 0x14
    movel %d4,%sp@-
    pea 120
    pea 0x40ea14cc
    movel %d6,%sp@-
    jsr 0x40071a04
    lea.l %sp@(28),%sp
    bra .Lpr_restore
.Lpr_restore:
    movem.l %sp@,%d2/%d4/%d6/%a2
    lea.l %sp@(16),%sp
    rts

    .section .text.lf2p_dest_name,"ax"
lf2p_dest_name:
    movel %d0,%sp@-
    jsr lf2p_destination_name
    addql #4,%sp
    moveal %d0,%a0
    movel %a0@,%d1
    cmpil #0x45525200,%d1
    bne .Ldest_named
    movel #lf2p_off,%d0
.Ldest_named:
    movel %d0,%sp@-
    pea lf2p_fmt_s
    jmp .Lpr_value

    .section .text.lf2p_multiplier,"ax"
lf2p_multiplier:
    | Même représentation que 0x400459f4 : *1..*2k puis 1..2k.
    moveq #42,%d1
    cmpil #12,%d0
    bcs .Lmul_index
    subil #12,%d0
    moveq #32,%d1
.Lmul_index:
    moveq #1,%d2
    lsll %d0,%d2
    cmpil #10,%d0
    bcs .Lmul_small
    lsrl #8,%d2
    lsrl #2,%d2
    movel %d2,%sp@-
    movel %d1,%sp@-
    pea 0x40128627
    jmp lf2p_multiplier_draw
.Lmul_small:
    movel %d2,%sp@-
    movel %d1,%sp@-
    pea 0x4012fe63
    jmp lf2p_multiplier_draw

    .section .text.lf2p_multiplier_draw,"ax"
lf2p_multiplier_draw:
    pea 0x14
    movel %d4,%sp@-
    pea 120
    pea 0x40ea14cc
    movel %d6,%sp@-
    jsr 0x40071a04
    lea.l %sp@(32),%sp
    jmp .Lpr_restore

    .section .text.lf2p_destination_name,"ax"
    .globl lf2p_destination_name
lf2p_destination_name:
    | Même route de nom court que LFO 1 (0x400264fc..0x4002650e).
    lea.l %sp@(-8),%sp
    movem.l %d2/%a2,%sp@
    movel %sp@(12),%d2
    jsr 0x400cf866
    movel %d0,%sp@-
    jsr 0x4000eb9c
    addql #4,%sp
    movel lf2p_track,%sp@-
    movel %d0,%sp@-
    jsr 0x400097f0
    addql #8,%sp
    moveal %d0,%a2
    moveal %a2@,%a0
    moveal %a0@(52),%a0
    movel %d2,%sp@-
    movel %a2,%sp@-
    jsr %a0@
    addql #8,%sp
    movel %d0,%sp@-
    movel %a2,%sp@-
    jsr 0x4000b208
    addql #8,%sp
    movem.l %sp@,%d2/%a2
    lea.l %sp@(8),%sp
    rts

    .section .data.lf2p_state,"aw"
    .balign 4
    .globl lf2p_obj,lf2p_opened,lf2p_row,lf2p_edit,lf2p_track,lf2p_vt
lf2p_obj: .long 0
lf2p_opened: .long 0
lf2p_row: .long 0
lf2p_edit: .long 0
lf2p_track: .long 0
    .globl lf2p_assigned
lf2p_assigned: .long 0
    .section .data.lf2p_vtable,"aw"
    .balign 4
lf2p_vt: .space 0xb0
    .section .rodata.lf2p_labels,"a"
    .balign 4
lf2p_labels: .long lf2p_track_label,lf2p_speed,lf2p_mult,lf2p_fade,lf2p_dest,lf2p_wave,lf2p_start,lf2p_mode,lf2p_depth
lf2p_max: .word 32767,23,32767,33,6,32767,4,32767
lf2p_title: .asciz "LFO 2"
lf2p_track_label: .asciz "Track"
lf2p_speed: .asciz "Speed"
lf2p_mult: .asciz "Multiplier"
lf2p_fade: .asciz "Fade"
lf2p_dest: .asciz "Destination"
lf2p_wave: .asciz "Waveform"
lf2p_start: .asciz "Start phase"
lf2p_mode: .asciz "Mode"
lf2p_depth: .asciz "Depth"
lf2p_off: .asciz "OFF"
lf2p_fmt_s: .asciz "%s"
lf2p_fmt_d: .asciz "%d"

