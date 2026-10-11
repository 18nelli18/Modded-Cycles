| Mutes immédiats et cartouche d'entrée ; exclusivement tâche UI.
    .ifdef SG_ADVANCED
    .globl sg_func,sg_pads,sg_intro,sg_intro_time,sg_tick,sg_pad,sg_intro_render,sg_sound_key
    .section .data.sg_performance,"aw"
sg_func: .long 0
sg_pads: .long 0
sg_intro: .long 0
sg_intro_time: .long 0
sg_sound_taken: .long 0
sg_sound_event: .long 0
sg_sound_time: .long 0

    .section .text.sg_tick,"ax"
sg_tick:
    lea.l %sp@(-20),%sp
    movem.l %d0-%d2/%a0-%a1,%sp@
    moveq #0,%d0
    movew %sr,%d0
    andil #0x700,%d0
    bnew sgt_done
    tstl sg_obj
    beqw sgt_done
    tstl sg_intro
    beqw sgt_done
    movel TG_blk_clk,%d0
    subl sg_intro_time,%d0
    cmpil #1500,%d0
    bcsw sgt_done
    clrl sg_intro
    movel sg_obj,%sp@-
    jsr 0x40076082
    addql #4,%sp
sgt_done:
    movem.l %sp@,%d0-%d2/%a0-%a1
    lea.l %sp@(20),%sp
    jmp TG_led_hook

    .section .text.sg_pad,"ax"
| Callback PadHandler, objet +16. Index de pad OS 1..6 -> pistes 0..5.
sg_pad:
    lea.l %sp@(-12),%sp
    movem.l %d2/%a2-%a3,%sp@
    moveal %sp@(20),%a2
    movel %a2@(20),%d2
    subql #1,%d2
    cmpil #5,%d2
    bhiw sgp_pass
    lea.l sg_pads,%a3
    movel %a3@,%d1
    tstl %a2@(16)
    beqw sgp_release
    movel %a2@(16),%d0
    cmpil #1,%d0
    bnew sgp_used
    btst %d2,%d1
    bnew sgp_used
    tstl sg_func
    beqw sgp_pass
    bset %d2,%d1
    movel %d1,%a3@
    jsr 0x400cf866
    movel %d0,%sp@-
    jsr 0x4000eb90
    addql #4,%sp
    pea 1
    movel %d2,%sp@-
    movel %d0,%sp@-
    jsr 0x40013904             | toggle stock immédiat, CC et observateurs compris
    lea.l %sp@(12),%sp
    braw sgp_used
sgp_release:
    btst %d2,%d1
    beqw sgp_pass
    bclr %d2,%d1
    movel %d1,%a3@
sgp_used:
    moveq #1,%d0
    braw sgp_out
sgp_pass:
    moveq #0,%d0
sgp_out:
    movem.l %sp@,%d2/%a2-%a3
    lea.l %sp@(12),%sp
    rts

    .section .text.sg_intro_render,"ax"
sg_intro_render:
    lea.l %sp@(-12),%sp
    movem.l %d2-%d3/%a2,%sp@
    movel %sp@(20),%d2
    clrl %sp@-
    pea 63
    pea 127
    clrl %sp@-
    clrl %sp@-
    movel %d2,%sp@-
    jsr 0x40070dea
    lea.l %sp@(24),%sp
    lea.l sg_intro_seq,%a2
    moveq #37,%d3
    jsr sgi_text
    lea.l sg_intro_gen,%a2
    moveq #21,%d3
    jsr sgi_text
    | Inverser le cartouche après les lettres : fond noir, lettres blanches.
    pea -1
    pea 53
    pea 98
    pea 10
    pea 29
    movel %d2,%sp@-
    jsr 0x40070dea
    lea.l %sp@(24),%sp
    movem.l %sp@,%d2-%d3/%a2
    lea.l %sp@(12),%sp
    rts
sgi_text:
    movel %a2,%sp@-
    pea sg_intro_fmt
    pea 0x12                 | centrage horizontal
    movel %d3,%sp@-
    pea 64
    pea 0x40ea14cc
    movel %d2,%sp@-
    jsr 0x40071a04
    lea.l %sp@(28),%sp
    rts
    .section .rodata.sg_intro,"a"
sg_intro_seq: .asciz "SEQ."
sg_intro_gen: .asciz "GEN."
sg_intro_fmt: .asciz "%s"

    .ifndef SG_SEQUENCE_ONLY
    .section .text.sg_sound_key,"ax"
| SETTINGS + TRACK : accès distinct aux réglages du son, sans tirage automatique.
sg_sound_key:
    movel %a0@(16),%d1
    btst #0,%d1
    beqw ssk_release
    tstl sg_sound_taken
    beqw ssk_fresh
    cmpal sg_sound_event,%a0
    bnew ssk_fresh
    movel %a0@(8),%d0
    cmpl sg_sound_time,%d0
    beqw ssk_eat
ssk_fresh:
    tstl TG_set_held
    beqw ssk_pass
    andil #10,%d1
    bnew ssk_pass
    tstl TG_mm_obj
    bnew ssk_pass
    tstl TG_rtg_on
    bnew ssk_pass
    tstl TG_sle_on
    bnew ssk_pass
    tstl sg_obj
    bnew ssk_pass
    moveq #1,%d1
    movel %d1,sg_sound_taken
    movel %d1,TG_mod_used
    movel %a0,sg_sound_event
    movel %a0@(8),%d1
    movel %d1,sg_sound_time
    movel %a0,%sp@-
    jsr sg_open
    moveq #19,%d0
    movel %d0,sg_row
    clrl sg_intro
    moveal %sp@+,%a0
    braw ssk_eat
ssk_release:
    tstl sg_sound_taken
    beqw ssk_pass
    clrl sg_sound_taken
    movel %a0,sg_sound_event
    movel %a0@(8),%d1
    movel %d1,sg_sound_time
ssk_eat:
    movel %a0@(16),%d1
    oril #8,%d1
    movel %d1,%a0@(16)
    moveq #0,%d0
    rts
ssk_pass:
    cmpal sg_sound_event,%a0
    bnew ssk_chain
    movel %a0@(8),%d0
    cmpl sg_sound_time,%d0
    bnew ssk_chain
    btst #0,%a0@(19)
    beqw ssk_eat
ssk_chain:
    jmp TG_key_hook
    .endif
    .endif
