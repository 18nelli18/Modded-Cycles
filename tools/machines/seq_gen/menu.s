| Page du générateur : construction adaptée de Model-TG (TinyGregAudio, MIT),
| commit 70b39dd ; licence dans tweaks/model-cycles_OS1.13/LICENSE-Model-TG.
| SG_SCROLL : variante à quatre lignes du flasher de test (notes/53 §10).
    .section .text.sg_open,"ax"
    .globl sg_open
sg_open:
    lea.l   sg_opened,%a0
    clrl    %a0@
    lea.l   %sp@(-24),%sp
    moveml  %d2-%d4/%a2-%a4,%sp@
    moveq   #0,%d0                | uniquement dans la tâche UI, comme loop_toggle
    movew   %sr,%d0
    andil   #0x0700,%d0
    bnew    sg_o_done
    lea.l   sg_obj,%a0
    tstl    %a0@
    bnew    sg_o_done             | page déjà ouverte
    tstl    0x40fe4178
    beqw    sg_o_done             | gestion des vues pas encore initialisée
    | groupe vtable privé, reconstruit depuis celui de l’OS
    lea.l   0x40117918,%a0
    lea.l   sg_vt,%a1
    moveq   #(0xb0/4)-1,%d0
sg_o_cp:
    movel   %a0@+,%a1@+
    subql   #1,%d0
    bplw    sg_o_cp
    lea.l   sg_vt,%a1
    movel   #sg_dtor0,%d0
    movel   %d0,%a1@(0x08)
    movel   #sg_dtor1,%d0
    movel   %d0,%a1@(0x0c)
    movel   #sg_menu_key,%d0
    movel   %d0,%a1@(0x10)
    movel   #sg_render,%d0
    movel   %d0,%a1@(0x18)
    movel   #sg_enc,%d0
    movel   %d0,%a1@(0x4c)
    movel   #sg_enc_th,%d0
    movel   %d0,%a1@(0x60)
    jmp sg_o_allocate
    .section .text.sg_open_allocate,"ax"
sg_o_allocate:
    lea.l   0x400802e0,%a3        | operator new
    pea     0x500
    jsr     %a3@
    addql   #4,%sp
    tstl    %d0
    beqw    sg_o_done
    movea.l %d0,%a4
    movel   %a4,%sp@-
    jsr     0x400a22b0            | constructeur OS de la page MACHINES
    addql   #4,%sp
    lea.l   sg_vt,%a1
    lea.l   %a1@(8),%a0
    movel   %a0,%a4@              | vptr principal
    lea.l   %a1@(0x58),%a0
    movel   %a0,%a4@(4)           | base +4 (événements encodeur)
    pea     0x10                  | détenteur de référence, comme l’ouverture OS
    jsr     %a3@                  | construite à 0x4001ca40
    addql   #4,%sp
    tstl %d0
    bnew sg_o_holder
    movel %a4,%sp@-
    jsr 0x400f4486
    addql #4,%sp
    braw sg_o_done
sg_o_holder:
    movea.l %d0,%a0
    movel %a4,sg_obj
    clrl sg_row
    clrl sg_edit
    clrl sg_undo_valid
    clrl sg_error
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
    lea.l   sg_opened,%a0
    moveq   #1,%d0
    movel   %d0,%a0@
sg_o_done:
    moveml  %sp@,%d2-%d4/%a2-%a4
    lea.l   %sp@(24),%sp
    rts

    .section .text.sg_dtor,"ax"
| ---- destructeurs : oublier la page, puis appeler ceux de l’OS ----
sg_dtor0:
    lea.l   sg_obj,%a0
    clrl    %a0@
    clrl    sg_undo_valid
    jmp     0x400f43ca
sg_dtor1:
    lea.l   sg_obj,%a0
    clrl    %a0@
    clrl    sg_undo_valid
    jmp     0x400f4486

    .section .text.sg_menu_key,"ax"
sg_menu_key:
    lea.l %sp@(-8),%sp
    movem.l %d2/%a2,%sp@
    moveal %sp@(12),%a2
    movel %sp@(16),%d2
    movel %d2,%sp@-
    jsr 0x4007240c
    addql #4,%sp
    cmpil #32,%d0
    beqw smk_data
    cmpil #12,%d0
    beqw smk_close
    cmpil #13,%d0
    beqw smk_close
    cmpil #15,%d0
    beqw smk_close
    cmpil #2,%d0
    beqw smk_close
    cmpil #3,%d0
    beqw smk_close
    | Page modale : pas de jeu/édition ni transport pendant une transaction.
    braw smk_used
smk_data:
    movel %d2,%sp@-
    jsr 0x40072434
    addql #4,%sp
    tstb %d0
    beqw smk_used
    movel sg_row,%d0
    cmpil #5,%d0
    beqw smk_generate
    cmpil #6,%d0
    beqw smk_undo
    moveq #1,%d0
    eorl %d0,sg_edit
    braw smk_redraw
smk_generate:
    jsr sg_action_generate
    braw smk_redraw
smk_undo:
    jsr sg_action_undo
smk_redraw:
    movel %a2,%sp@-
    jsr 0x40076082
    addql #4,%sp
    braw smk_used
smk_close:
    movel %d2,%sp@-
    jsr 0x400724a0
    addql #4,%sp
    tstb %d0
    beqw smk_used
    moveq #1,%d0
    movel %d0,TG_mod_used
    moveal %a2@,%a0
    movel %a2,%sp@-
    moveal %a0@(0x28),%a0
    jsr %a0@
    addql #4,%sp
smk_used:
    moveq #1,%d0
    movem.l %sp@,%d2/%a2
    lea.l %sp@(8),%sp
    rts

    .section .text.sg_enc,"ax"
sg_enc_th:
    subql #4,%sp@(4)
sg_enc:
    lea.l %sp@(-12),%sp
    movem.l %d2-%d3/%a2,%sp@
    moveal %sp@(16),%a2
    moveal %sp@(20),%a0
    movel %a0@(12),%d0
    cmpil #1,%d0
    bnew sme_out
    pea 1
    pea 1
    movel %a0,%sp@-
    jsr 0x4006f73a
    lea.l %sp@(12),%sp
    tstl %d0
    beqw sme_out
    moveq #1,%d3
    tstl %d0
    bplw sme_sign
    moveq #-1,%d3
sme_sign:
    movel sg_row,%d2
    tstl sg_edit
    bnew sme_value
    addl %d3,%d2
    bmiw sme_out
    cmpil #6,%d2
    bgtw sme_out
    movel %d2,sg_row
    braw sme_redraw
sme_value:
    tstl %d2
    bnew sme_root
    moveq #0,%d0
    moveb TG_scale_state,%d0
    addl %d3,%d0
    bmiw sme_out
    cmpil #4,%d0
    bgtw sme_out
    moveb %d0,TG_scale_state
    braw sme_redraw
sme_root:
    cmpil #1,%d2
    bnew sme_range
    moveq #0,%d0
    moveb TG_key_state,%d0
    addl %d3,%d0
    bmiw sme_out
    cmpil #11,%d0
    bgtw sme_out
    moveb %d0,TG_key_state
    braw sme_redraw
sme_range:
    jmp sme_range_body
    .section .text.sg_enc_range,"ax"
sme_range_body:
    lea.l sg_config,%a0
    cmpil #2,%d2
    bnew sme_high
    movel %a0@(8),%d0
    addl %d3,%d0
    bmiw sme_out
    cmpl %a0@(12),%d0
    bgtw sme_out
    movel %d0,%a0@(8)
    braw sme_redraw
sme_high:
    cmpil #3,%d2
    bnew sme_density
    movel %a0@(12),%d0
    addl %d3,%d0
    cmpil #127,%d0
    bgtw sme_out
    cmpl %a0@(8),%d0
    bltw sme_out
    movel %d0,%a0@(12)
    braw sme_redraw
sme_density:
    cmpil #4,%d2
    bnew sme_out
    movel %a0@(4),%d0
    addl %d3,%d0
    bmiw sme_out
    cmpil #100,%d0
    bgtw sme_out
    movel %d0,%a0@(4)
sme_redraw:
    movel %a2,%sp@-
    jsr 0x40076082
    addql #4,%sp
sme_out:
    moveq #1,%d0
    movem.l %sp@,%d2-%d3/%a2
    lea.l %sp@(12),%sp
    rts

    .section .text.sg_render,"ax"
sg_render:
    .ifdef SG_SCROLL
    jmp sg_render_start
    .section .text.sg_render_start,"ax"
sg_render_start:
    lea.l %sp@(-20),%sp
    movem.l %d2-%d5/%a2,%sp@
    movel %sp@(28),%d2
    .else
    lea.l %sp@(-16),%sp
    movem.l %d2-%d4/%a2,%sp@
    movel %sp@(24),%d2
    .endif
    clrl %sp@-
    pea 63
    pea 127
    clrl %sp@-
    clrl %sp@-
    movel %d2,%sp@-
    jsr 0x40070dea
    lea.l %sp@(24),%sp
    .ifdef SG_SCROLL
    jmp sg_view_start
    .section .text.sg_view_start,"ax"
sg_view_start:
    | Quatre lignes de 15 pixels ; sélection centrée, marges aux extrémités.
    movel sg_row,%d5
    subql #2,%d5
    bplw smr_view_nonnegative
    moveq #0,%d5
smr_view_nonnegative:
    cmpil #3,%d5
    blew smr_view_ready
    moveq #3,%d5
smr_view_ready:
    movel %d5,%d3
    jmp smr_loop
    .section .text.sg_render,"ax"
    .else
    moveq #0,%d3
    .endif
smr_loop:
    lea.l sg_labels,%a0
    moveal %a0@(0,%d3:l:4),%a2
    cmpil #5,%d3
    bnew smr_label
    tstl sg_error
    beqw smr_label
    lea.l sg_error_text,%a2
smr_label:
    movel %d3,%d4
    .ifdef SG_SCROLL
    subl %d5,%d4
    muluw #15,%d4
    moveq #49,%d0
    .else
    muluw #9,%d4
    moveq #55,%d0
    .endif
    subl %d4,%d0
    movel %a2,%sp@-
    pea sg_fmt_s
    pea 0x10
    movel %d0,%sp@-
    pea 2
    pea 0x40ea14cc
    movel %d2,%sp@-
    jsr 0x40071a04
    lea.l %sp@(28),%sp
    cmpil #5,%d3
    bgew smr_action
    moveq #0,%d0
    tstl %d3
    bnew smr_root
    moveb TG_scale_state,%d0
    lea.l sg_scales,%a0
    moveal %a0@(0,%d0:l:4),%a2
    braw smr_string
smr_root:
    cmpil #1,%d3
    bnew smr_number
    moveb TG_key_state,%d0
    lea.l sg_keys,%a0
    moveal %a0@(0,%d0:l:4),%a2
smr_string:
    movel %a2,%sp@-
    pea sg_fmt_s
    braw smr_value
smr_number:
    lea.l sg_config,%a0
    movel %a0@(4),%d0
    cmpil #4,%d3
    beqw smr_num
    movel %a0@(0,%d3:l:4),%d0
smr_num:
    movel %d0,%sp@-
    pea sg_fmt_d
smr_value:
    pea 0x14
    .ifdef SG_SCROLL
    moveq #49,%d0
    .else
    moveq #55,%d0
    .endif
    subl %d4,%d0
    movel %d0,%sp@-
    pea 125
    pea 0x40ea14cc
    movel %d2,%sp@-
    jsr 0x40071a04
    lea.l %sp@(28),%sp
    braw smr_next
smr_action:
    jmp smr_action_body
    .section .text.sg_render_tail,"ax"
smr_action_body:
    cmpil #6,%d3
    bnew smr_next
    lea.l sg_no_undo,%a2
    tstl sg_undo_valid
    beqw smr_string
    lea.l sg_ready,%a2
    braw smr_string
smr_next:
    addql #1,%d3
    .ifdef SG_SCROLL
    movel %d3,%d0
    subl %d5,%d0
    cmpil #4,%d0
    .else
    cmpil #7,%d3
    .endif
    bltw smr_loop
    pea -1
    movel sg_row,%d0
    .ifdef SG_SCROLL
    subl %d5,%d0
    muluw #15,%d0
    moveq #62,%d1
    .else
    muluw #9,%d0
    moveq #63,%d1
    .endif
    subl %d0,%d1
    movel %d1,%sp@-
    pea 127
    .ifdef SG_SCROLL
    subil #13,%d1
    .else
    subql #8,%d1
    .endif
    movel %d1,%sp@-
    moveq #0,%d0
    tstl sg_edit
    beqw smr_cursor
    moveq #64,%d0
smr_cursor:
    movel %d0,%sp@-
    movel %d2,%sp@-
    jsr 0x40070dea
    lea.l %sp@(24),%sp
    .ifdef SG_SCROLL
    movem.l %sp@,%d2-%d5/%a2
    lea.l %sp@(20),%sp
    .else
    movem.l %sp@,%d2-%d4/%a2
    lea.l %sp@(16),%sp
    .endif
    rts

    .section .text.sg_action,"ax"
sg_action_generate:
    lea.l %sp@(-12),%sp
    movem.l %d2/%a2-%a3,%sp@
    clrl sg_error
    tstl 0x40a78874
    bnew sag_error
    tstl 0x40a7883c
    bnew sag_error
    jsr 0x400cf866
    movel %d0,%sp@-
    jsr 0x4000f23e
    addql #4,%sp
    tstl %d0
    beqw sag_error
    moveal %d0,%a3
    movel %a3,%sp@-
    jsr 0x40016402
    addql #4,%sp
    lea.l sg_config,%a0
    movel %d0,%a0@
    moveq #0,%d0
    moveb TG_scale_state,%d0
    movel %d0,%a0@(16)
    moveb TG_key_state,%d0
    andil #255,%d0
    movel %d0,%a0@(20)
    moveal sg_obj,%a2
    lea.l %a2@(930),%a1
    jsr sg_generate
    tstl %d0
    bmiw sag_error
    moveal sg_obj,%a2
    lea.l %a2@(930),%a1
    lea.l %a2@(208),%a2
    moveal %a3,%a0
    movel sg_config,%d0
    jsr sg_track_write
    tstl %d0
    beqw sag_error
    moveq #1,%d0
    movel %d0,sg_undo_valid
    movel %a3,sg_undo_track
    braw sag_out
sag_error:
    moveq #1,%d0
    movel %d0,sg_error
sag_out:
    movem.l %sp@,%d2/%a2-%a3
    lea.l %sp@(12),%sp
    rts
    .section .text.sg_undo,"ax"
sg_action_undo:
    tstl sg_undo_valid
    beqw sau_out
    lea.l %sp@(-8),%sp
    movem.l %a2-%a3,%sp@
    jsr 0x400cf866
    movel %d0,%sp@-
    jsr 0x4000f23e
    addql #4,%sp
    cmpl sg_undo_track,%d0
    bnew sau_done
    moveal %d0,%a3
    moveal sg_obj,%a2
    lea.l %a2@(208),%a2
    moveal %a3,%a0
    jsr sg_track_restore
    tstl %d0
    beqw sau_done
    clrl sg_undo_valid
sau_done:
    movem.l %sp@,%a2-%a3
    lea.l %sp@(8),%sp
sau_out:
    rts

    .section .data.sg_menu,"aw"
sg_obj: .long 0
sg_opened: .long 0
sg_undo_valid: .long 0
sg_undo_track: .long 0
sg_row: .long 0
sg_edit: .long 0
sg_error: .long 0
sg_config: .long 16,50,48,72,0,0,0x6d2b79f5
sg_vt: .space 0xb0
    .section .rodata.sg_menu,"a"
sg_labels: .long sg_scale,sg_root,sg_low,sg_high,sg_density,sg_go,sg_undo
sg_scales: .long sg_chrom,sg_major,sg_minor,sg_dorian,sg_penta
sg_keys: .long sg_c,sg_cs,sg_d,sg_ds,sg_e,sg_f,sg_fs,sg_g,sg_gs,sg_a,sg_as,sg_b
sg_scale: .asciz "Scale"
sg_root: .asciz "Root"
sg_low: .asciz "Low note"
sg_high: .asciz "High note"
sg_density: .asciz "Density %"
sg_go: .asciz "Generate"
sg_undo: .asciz "Undo"
sg_chrom: .asciz "CHROM"
sg_major: .asciz "MAJ"
sg_minor: .asciz "MIN"
sg_dorian: .asciz "DOR"
sg_penta: .asciz "PENTA"
sg_c: .asciz "C"
sg_cs: .asciz "C#"
sg_d: .asciz "D"
sg_ds: .asciz "D#"
sg_e: .asciz "E"
sg_f: .asciz "F"
sg_fs: .asciz "F#"
sg_g: .asciz "G"
sg_gs: .asciz "G#"
sg_a: .asciz "A"
sg_as: .asciz "A#"
sg_b: .asciz "B"
sg_fmt_s: .asciz "%s"
sg_fmt_d: .asciz "%d"
sg_ready: .asciz "Ready"
sg_no_undo: .asciz "--"
sg_error_text: .asciz "Check range/stop"
