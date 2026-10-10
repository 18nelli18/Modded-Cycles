/* MIDI Keys, OS 1.13 (notes/40).
 * Jeu direct : l'appel audio/recorder vient de finir. d2=piste, d3=note,
 * d4=vélocité ; les paramètres poussés sont supprimés avant l'épilogue natif.
 * La partie MIDI native est remplacée, le traitement audio reste strictement
 * celui de l'OS. Aucun registre sauvé ni retour n'est stocké globalement.
 */
    .section .text.ck_midi_key_on_hook,"ax"
    .balign 2
    .global ck_midi_key_on_hook
ck_midi_key_on_hook:
    move.l %d4,%sp@-
    move.l %d3,%sp@-
    move.l %d2,%sp@-
    jsr ck_midi_live_on
    lea %sp@(40),%sp
    jmp 0x40019f3a

    .section .text.ck_midi_key_off_hook,"ax"
    .balign 2
    .global ck_midi_key_off_hook
ck_midi_key_off_hook:
    move.l %d3,%sp@-
    move.l %d2,%sp@-
    jsr ck_midi_live_off
    addq.l #8,%sp
    tst.l %d0
    beq.s 1f
    lea %sp@(16),%sp
    jmp 0x40019cf6
1:  move.l %d4,%sp@-
    jsr 0x40016e90
    jmp 0x40019cc2

    .section .text.ck_midi_pad_on_hook,"ax"
    .balign 2
    .global ck_midi_pad_on_hook
ck_midi_pad_on_hook:
    move.l %d4,%sp@-
    move.l %d3,%sp@-
    move.l %d2,%sp@-
    jsr ck_midi_live_on
    lea %sp@(40),%sp
    jmp 0x4001d0f2

    .section .text.ck_midi_pad_off_hook,"ax"
    .balign 2
    .global ck_midi_pad_off_hook
ck_midi_pad_off_hook:
    move.l %d3,%sp@-
    move.l %d2,%sp@-
    jsr ck_midi_live_off
    addq.l #8,%sp
    tst.l %d0
    beq.s 1f
    lea %sp@(12),%sp
    jmp 0x4001d176
1:  lea 0x400cf866,%a2
    jmp 0x4001d126

/* L'événement accepté a reçu son son et ses P-locks. d2=piste, a2=événement,
 * a3=fiche d'horloge dont +4 est l'instant prévu. Sauve tous les volatils,
 * conserve les autres registres par ABI C, puis rejoue clr.l à la reprise.
 */
    .section .text.ck_midi_sequence_hook,"ax"
    .balign 2
    .global ck_midi_sequence_hook
ck_midi_sequence_hook:
    lea %sp@(-16),%sp
    movem.l %d0-%d1/%a0-%a1,%sp@
    move.l %a3@(4),%sp@-
    move.l %a2,%sp@-
    move.l %d2,%sp@-
    jsr ck_midi_sequence
    lea %sp@(12),%sp
    movem.l %sp@,%d0-%d1/%a0-%a1
    lea %sp@(16),%sp
    clr.l 0x40a78e18
    jmp 0x400591a4
