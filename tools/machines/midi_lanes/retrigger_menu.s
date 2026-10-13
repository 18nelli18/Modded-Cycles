| Menu retrigger B : rendu stock et données privées, sans observer audio.
    .text
    .globl mlp_retrigger_open,mlp_retrigger_enc,mlp_retrigger_value,mlp_retrigger_render
mlp_retrigger_open:
    jsr ml_repeat_prepare_ui
    tstl ml_repeat_edit_settings
    beq .Lrt_open_done
    moveq #4,%d0
    movel %d0,mlp_setup
    clrl mlp_row
    clrl mlp_edit
.Lrt_open_done:
    rts
| Basculer uniquement le lock d'activation du pas, jamais le défaut de voie.
    .globl mlp_retrigger_toggle_step
mlp_retrigger_toggle_step:
    lea.l %sp@(-8),%sp
    moveml %d2/%a2,%sp@
    pea 3
    jsr mlp_retrigger_value
    addql #4,%sp
    moveq #1,%d2
    eorl %d0,%d2
    jsr .Lrt_record
    tstl %a0
    beq .Lrt_toggle_done
    lea.l %a0@(8),%a2
    movel %d2,%sp@-
    clrl %sp@-
    movel mlp_step,%sp@-
    movel %a2,%sp@-
    jsr ml_repeat_lock
    lea.l %sp@(16),%sp
    tstl %d0
    beq .Lrt_toggle_done
    movel mlp_held,%d0
    orl mlp_changed,%d0
    movel %d0,mlp_changed
.Lrt_toggle_done:
    moveml %sp@,%d2/%a2
    addql #8,%sp
    rts
| a0 = défauts de la voie, ou NULL. Aucun objet audio natif.
.Lrt_record:
    moveal ml_repeat_edit_settings,%a0
    tstl %a0
    beq .Lrt_record_done
    movel mlp_track,%d0
    cmpil #5,%d0
    bhi .Lrt_record_bad
    muluw #520,%d0
    addal %d0,%a0
.Lrt_record_done:
    rts
.Lrt_record_bad:
    subal %a0,%a0
    rts
mlp_retrigger_value:
    lea.l %sp@(-20),%sp
    movem.l %d2/%a2,%sp@
    movel %sp@(24),%d2
    cmpil #5,%d2
    bhi .Lrt_read_bad
    jsr .Lrt_record
    tstl %a0
    beq .Lrt_read_bad
    moveal %a0,%a2
    tstl mlp_held
    beq .Lrt_read_default
    pea %sp@(8)
    movel mlp_step,%sp@-
    pea %a2@(8)
    movel %a2,%sp@-
    jsr ml_repeat_resolve
    lea.l %sp@(16),%sp
    tstl %d0
    beq .Lrt_read_bad
    lea.l %sp@(8),%a2
.Lrt_read_default:
    lea.l .Lrt_fields,%a0
    moveq #0,%d1
    moveb %a0@(0,%d2:l),%d1
    moveq #0,%d0
    moveb %a2@(0,%d1:l),%d0
    cmpil #3,%d1
    bne .Lrt_read_done
    extbl %d0
    bra .Lrt_read_done
.Lrt_read_bad:
    moveq #0,%d0
.Lrt_read_done:
    movem.l %sp@,%d2/%a2
    lea.l %sp@(20),%sp
    rts
mlp_retrigger_enc:
    lea.l %sp@(-16),%sp
    movem.l %d2-%d3/%a2,%sp@
    movel %sp@(20),%d3
    movel mlp_row,%d2
    tstl mlp_edit
    bne .Lrt_enc_edit
    addl %d3,%d2
    cmpil #5,%d2
    bhi .Lrt_enc_done
    movel %d2,mlp_row
    bra .Lrt_enc_done
.Lrt_enc_edit:
    cmpil #2,%d2
    beq .Lrt_enc_done
    cmpil #5,%d2
    bhi .Lrt_enc_done
    movel %d2,%sp@-
    jsr mlp_retrigger_value
    addql #4,%sp
    addl %d0,%d3
    jsr .Lrt_record
    tstl %a0
    beq .Lrt_enc_done
    moveal %a0,%a2
    lea.l .Lrt_fields,%a0
    moveq #0,%d0
    moveb %a0@(0,%d2:l),%d0
    moveq #0,%d1
    tstl mlp_held
    beq .Lrt_enc_store
    lea.l %a2@(8),%a2
    movel mlp_step,%d1
.Lrt_enc_store:
    movel %d3,%sp@-
    movel %d0,%sp@-
    movel %d1,%sp@-
    movel %a2,%sp@-
    jsr ml_repeat_lock
    lea.l %sp@(16),%sp
    tstl %d0
    beq .Lrt_enc_done
    movel mlp_held,%d0
    orl mlp_changed,%d0
    movel %d0,mlp_changed
.Lrt_enc_done:
    movem.l %sp@,%d2-%d3/%a2
    lea.l %sp@(16),%sp
    rts
    .section .rodata
.Lrt_fields: .byte 1,2,3,0,4,5
    .text
| Rendu MenuView natif avec modèle et lignes privés : géométrie, polices,
| surbrillance et titre stock ; aucun constructeur/observer de piste audio.
mlp_retrigger_render:
    lea.l %sp@(-584),%sp
    moveml %d2/%a2-%a3,%sp@
    lea.l %sp@(16),%a2
    moveal %a2,%a0
    movel #140,%d0
.Lrt_zero:
    clrl %a0@+
    subql #1,%d0
    bpl .Lrt_zero
    lea.l .Lrt_vtable,%a0
    movel %a0,%a2@
    lea.l .Lrt_title_data,%a0
    movel %a0,%a2@(148)
    movel 0x40ea14d0,%d0
    movel %d0,%a2@(156)
    movel %d0,%a2@(160)
    lea.l .Lrt_subtitle_data,%a0
    tstl mlp_held
    beq .Lrt_subtitle_ready
    pea 3
    jsr mlp_retrigger_value
    addql #4,%sp
    tstl %d0
    lea.l .Lrt_step_off,%a0
    beq .Lrt_subtitle_ready
    lea.l .Lrt_step_on,%a0
.Lrt_subtitle_ready:
    movel %a0,%a2@(556)
    movel %sp@(592),%sp@-
    movel %a2,%sp@-
    jsr 0x400423e4
    addql #8,%sp
    moveml %sp@,%d2/%a2-%a3
    lea.l %sp@(584),%sp
    rts
.Lrt_count:
    moveq #6,%d0
    rts
.Lrt_zero_value:
    moveq #0,%d0
    rts
.Lrt_row_value:
    movel mlp_row,%d0
    cmpil #3,%d0
    bcs .Lrt_row_ready
    subql #3,%d0
.Lrt_row_ready:
    rts
.Lrt_top:
    movel mlp_row,%d0
    cmpil #3,%d0
    bcs .Lrt_zero_value
    moveq #3,%d0
    rts
.Lrt_visible:
    moveq #3,%d0
    rts
.Lrt_item:
    movel %sp@(8),%d0
    muluw #84,%d0
    lea.l .Lrt_rows,%a1
    addal %d0,%a1
    movel %a1,%a0@
    clrl %a0@(4)
    rts
.Lrt_label:
    lea.l %sp@(-8),%sp
    movel %a0,%sp@
    moveal %sp@(12),%a1
    movel %a1@,%sp@-
    pea .Lallocator
    | std::string(this,texte,allocator), même routine que le label stock.
    movel %sp@+,%d0
    movel %sp@+,%d1
    movel %d0,%sp@-
    movel %d1,%sp@-
    movel %a0,%sp@-
    jsr 0x400f980c
    lea.l %sp@(12),%sp
    movel %sp@,%d0
    addql #8,%sp
    rts
 .Lrt_value:
    lea.l %sp@(-16),%sp
    moveml %d2/%a2-%a3,%sp@
    moveal %sp@(24),%a3
    moveal %sp@(28),%a2
    movel %a3@(80),%d2
    movel %d2,%sp@-
    jsr mlp_retrigger_value
    addql #4,%sp
    cmpil #2,%d2
    bne .Lrt_value_active
    lea.l .Lrt_pending,%a1
    bra .Lrt_string
.Lrt_value_active:
    tstl %d2
    beq .Lrt_rate
    cmpil #3,%d2
    beq .Lrt_boolean
    cmpil #4,%d2
    beq .Lrt_mode
    cmpil #1,%d2
    bne .Lrt_number
    | Même table de texte que la ligne Len du menu natif, sans copie.
    cmpil #127,%d0
    bhi .Lrt_number
    lea.l 0x40149328,%a0
    moveal %a0@(0,%d0:l:4),%a1
    bra .Lrt_string
.Lrt_rate:
    lea.l .Lrt_rates,%a0
    cmpil #16,%d0
    bhi .Lrt_number
    moveal %a0@(0,%d0:l:4),%a1
    bra .Lrt_string
.Lrt_boolean:
    lea.l .Lrt_off,%a1
    tstl %d0
    beq .Lrt_string
    lea.l .Lrt_on,%a1
    bra .Lrt_string
.Lrt_mode:
    lea.l .Lrt_modes,%a0
    cmpil #5,%d0
    bhi .Lrt_number
    moveal %a0@(0,%d0:l:4),%a1
.Lrt_string:
    movel %a1,%sp@-
    pea .Lfmt_s
    bra .Lrt_draw_value
.Lrt_number:
    movel %d0,%sp@-
    pea .Lfmt_d
.Lrt_draw_value:
    pea 4
    movel %sp@(48),%sp@-
    movel %sp@(48),%d0
    addil #24,%d0
    movel %d0,%sp@-
    pea 0x40ea14cc
    movel %a2,%sp@-
    jsr 0x40071a04
    lea.l %sp@(28),%sp
    moveml %sp@,%d2/%a2-%a3
    lea.l %sp@(16),%sp
    rts
    .section .rodata
    .balign 4
.Lrt_vtable:
    .long 0,0,0,.Lrt_count,.Lrt_item,0,0,0,0,0,0,0,0,0
    .long .Lrt_top,.Lrt_row_value,.Lrt_visible,0,.Lrt_zero_value
.Lrt_title_header: .long 6,6,0
.Lrt_title_data: .asciz "Retrig"
    .balign 4
.Lrt_subtitle_header: .long 5,5,0
.Lrt_subtitle_data: .asciz "Setup"
    .balign 4
.Lrt_step_on_header: .long 2,2,0
.Lrt_step_on: .asciz "ON"
    .balign 4
.Lrt_step_off_header: .long 3,3,0
.Lrt_step_off: .asciz "OFF"
.Lrt_pending: .asciz "---"
.Lfmt_s: .asciz "%s"
.Lfmt_d: .asciz "%d"
.Lkbt: .asciz "KbT"
.Lpad: .asciz "Pad"
.Lallocator: .byte 0
    .balign 4
.Lrt_rows:
    .long 0,0,0,.Lrt_label0,0,1,.Lrt_label,0,0,0,0,0,0,1,.Lrt_value,0,0,0,0,0,0
    .long 0,0,0,.Lrt_label1,0,1,.Lrt_label,0,0,0,0,0,0,1,.Lrt_value,0,0,0,0,0,1
    .long 0,0,0,.Lrt_label2,0,1,.Lrt_label,0,0,0,0,0,0,1,.Lrt_value,0,0,0,0,0,2
    .long 0,0,0,.Lrt_label3,0,1,.Lrt_label,0,0,0,0,0,0,1,.Lrt_value,0,0,0,0,0,3
    .long 0,0,0,.Lrt_label4,0,1,.Lrt_label,0,0,0,0,0,0,1,.Lrt_value,0,0,0,0,0,4
    .long 0,0,0,.Lrt_label5,0,1,.Lrt_label,0,0,0,0,0,0,1,.Lrt_value,0,0,0,0,0,5

.Lrt_label0: .asciz "Rte"
.Lrt_label1: .asciz "Len"
.Lrt_label2: .asciz "V.Crv"
.Lrt_label3: .asciz "A.On"
.Lrt_label4: .asciz "Arp"
.Lrt_label5: .asciz "Oct"
    .balign 4
.Lrt_rates: .long .Lrt_rates0,.Lrt_rates1,.Lrt_rates2,.Lrt_rates3,.Lrt_rates4,.Lrt_rates5,.Lrt_rates6,.Lrt_rates7,.Lrt_rates8,.Lrt_rates9,.Lrt_rates10,.Lrt_rates11,.Lrt_rates12,.Lrt_rates13,.Lrt_rates14,.Lrt_rates15,.Lrt_rates16
.Lrt_rates0: .asciz "1/1"
.Lrt_rates1: .asciz "1/2"
.Lrt_rates2: .asciz "1/3"
.Lrt_rates3: .asciz "1/4"
.Lrt_rates4: .asciz "1/5"
.Lrt_rates5: .asciz "1/6"
.Lrt_rates6: .asciz "1/8"
.Lrt_rates7: .asciz "1/10"
.Lrt_rates8: .asciz "1/12"
.Lrt_rates9: .asciz "1/16"
.Lrt_rates10: .asciz "1/20"
.Lrt_rates11: .asciz "1/24"
.Lrt_rates12: .asciz "1/32"
.Lrt_rates13: .asciz "1/40"
.Lrt_rates14: .asciz "1/48"
.Lrt_rates15: .asciz "1/64"
.Lrt_rates16: .asciz "1/80"
    .balign 4
.Lrt_modes: .long .Lrt_modes0,.Lrt_modes1,.Lrt_modes2,.Lrt_modes3,.Lrt_modes4,.Lrt_modes5
.Lrt_modes0: .asciz "UP"
.Lrt_modes1: .asciz "DOWN"
.Lrt_modes2: .asciz "UPDN"
.Lrt_modes3: .asciz "RAND"
.Lrt_modes4: .asciz "PLAY"
.Lrt_modes5: .asciz "OFF"
.Lrt_inf: .asciz "INF"
.Lrt_on: .asciz "ON"
.Lrt_off: .asciz "OFF"
