| Banque autonome actuelle : copie des supports propres, clear natif borne,
| puis reprise OS. Toutes les sources sont dans la charge deja decompressee.
| Tables PIC configurees par le compositeur ; aucun appel fichier ou MIDI ici.
    .text
    .globl midi_current_stage,midi_current_copies,midi_current_skips
    .globl midi_current_wizard,midi_current_context,midi_current_drain
    .globl midi_current_init
    .globl midi_current_safe_ui,midi_current_led0,midi_current_led1
    .globl midi_current_led2,midi_current_led3,midi_current_led4
midi_current_stage:
    lea %sp@(-60),%sp
    moveml %d0-%d7/%a0-%a6,%sp@
    lea midi_current_copies(%pc),%a2
.Lcopy:
    moveal %a2@+,%a0
    tstl %a0
    beq .Lcopies_done
    moveal %a2@+,%a1
    movel %a2@+,%d0
.Lcopy_long:
    movel %a0@+,%a1@+
    subql #1,%d0
    bne .Lcopy_long
    bra .Lcopy
.Lcopies_done:
    tstl midi_current_wizard(%pc)
    beq .Lnative_map
    movel #0x4c03e000,%d0
    movec %d0,%acr1
.Lnative_map:
    nop
    movel #0x000cc100,%d0
    movec %d0,%cacr
    nop
    moveal midi_current_init(%pc),%a0
    tstl %a0
    beq .Linitialized
    jsr %a0@
.Linitialized:
    lea midi_current_skips(%pc),%a2
    lea 0x4019b590,%a0
    moveq #0,%d4
    moveq #0,%d5
    moveq #0,%d6
    moveq #0,%d7
.Lclear:
    cmpal %a2@,%a0
    bne .Lnot_skip
    moveal %a2@(4),%a0
    lea %a2@(8),%a2
.Lnot_skip:
    cmpal #0x423380b0,%a0
    bcc .Ldone
    moveml %d4-%d7,%a0@
    lea %a0@(16),%a0
    bra .Lclear
.Ldone:
    moveml %sp@,%d0-%d7/%a0-%a6
    lea %sp@(60),%sp
    lea 0xfc044000,%a0
    jmp 0x4000053a

| Aucun prepare/heap/service avant la premiere ouverture explicite de B.
midi_current_safe_ui:
    moveal midi_current_context(%pc),%a0
    tstl %a0@
    beq .Lui_done
    tstl 0x40fe4178
    beq .Lui_done
    tstl 0x40fe4228
    beq .Lui_done
    moveal midi_current_drain(%pc),%a0
    jmp %a0@
.Lui_done:
    rts

    .macro SAFE_LED n
midi_current_led\n:
    tstl 0x40fe4178
    beq .Lled_done\n
    tstl 0x40fe4228
    beq .Lled_done\n
    jmp 0xf0010000+4*\n
.Lled_done\n:
    rts
    .endm
    SAFE_LED 0
    SAFE_LED 1
    SAFE_LED 2
    SAFE_LED 3
    SAFE_LED 4
    .balign 4
midi_current_wizard: .long 0
midi_current_context: .long 0
midi_current_drain: .long 0
midi_current_init: .long 0
midi_current_copies: .space 12*8
midi_current_skips: .space 8*8
