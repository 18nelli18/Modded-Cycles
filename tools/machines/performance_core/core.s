| Noyau performance extrait : services communs sans sampler Model-TG.
| Source propre pour boot/dispatch ; slide/Scale Lock MIT TinyGregAudio
| sont sélectionnés par gen_performance_core.py depuis le commit épinglé.
    .text
    .globl boot_extra_hook,key_hook,led_hook,core_pre,core_audio_end
boot_extra_hook:
    lea %sp@(-16),%sp
    moveml %d4-%d7,%sp@
    lea 0x4019b590,%a0
    moveq #0,%d4
    moveq #0,%d5
    moveq #0,%d6
    moveq #0,%d7
core_clear:
    cmpal #blob_start,%a0
    bne core_clear_next
    moveal #reserved_end,%a0
core_clear_next:
    cmpal #0x423380b0,%a0
    bcc core_clear_done
    moveml %d4-%d7,%a0@
    lea %a0@(16),%a0
    bra core_clear
core_clear_done:
    moveml %sp@,%d4-%d7
    lea %sp@(16),%sp
    lea 0xfc044000,%a0
    jmp 0x4000053a

| Hook8o à400a7da8 : store voix puis test/branche natifs, d0 libre.
core_pre:
    movel %d1,%fp@(60)
    jsr sld_apply
    tstl %a3@
    beq core_pre_skip
    jmp 0x400a7db0
core_pre_skip:
    jmp 0x400a7de0

| Même appel sortie que l'OS, puis compteur bloc partagé sans I/O ajouté.
core_audio_end:
    movel %sp@(8),%sp@-
    movel %sp@(8),%sp@-
    jsr 0x400567ba
    addql #8,%sp
    addql #1,blk_clk
    rts
led_hook:
    lea %sp@(-48),%sp
    moveml %d0-%d7/%a0-%a3,%sp@
    movew %sr,%d0
    andil #0x700,%d0
    bne core_led_done
    jsr sld_tick
core_led_done:
    moveml %sp@,%d0-%d7/%a0-%a3
    lea %sp@(48),%sp
    rts
key_hook:
    moveal %sp@(4),%a0
    movel %a0@(12),%d0
    cmpil #13,%d0
    beq kh_mod
    movel %d0,%d1
    subil #16,%d1
    cmpil #15,%d1
    bls kh_slide
kh_out:
    rts
kh_eat:
    moveq #0,%d0
    rts
    .balign 4
    .globl blk_clk,set_held,mod_used,mm_obj,rtg_on,sle_on
blk_clk: .long 0
set_held: .long 0
mod_used: .long 0
mm_obj: .long 0
rtg_on: .long 0
sle_on: .long 0
popup_mult: .long 0
sld_keys: .long 0
sld_tp: .space 64
sld_rp: .space 64
sld_lph: .long 0
sld_init: .long 0
msg_slon: .asciz "Slide ON"
msg_sloff: .asciz "Slide OFF"
    .balign 4
SLD_BASE: .space 2048
    .text
    .globl note_on_hook,note_off_hook
note_on_hook:
    lea %sp@(-8),%sp
    moveml %d5-%d6,%sp@
    jsr snap_note
    moveml %sp@,%d5-%d6
    lea %sp@(8),%sp
    cmpl %d3,%d0
    bcc core_note_on_go
    jmp 0x4008190e
core_note_on_go:
    jmp 0x40081742
note_off_hook:
    lea %sp@(-8),%sp
    moveml %d5-%d6,%sp@
    jsr snap_note
    moveml %sp@,%d5-%d6
    lea %sp@(8),%sp
    cmpl %d3,%d0
    bcc core_note_off_go
    jmp 0x400815f0
core_note_off_go:
    jmp 0x4008147a
