| Note 57 : prototypes de raccordement, pas encore placés au flasher.
| Start : déplacer 0x40054686 (move.l (a0),0x80001848), reprendre +6.
| a0 pointe l'échéance native ; d6 non nul indique Continue après pause.
| Le chemin natif est à IPL7 : publication atomique de l'armement audio.
| Tous registres/SR restaurés avant le move natif (CCR stock conservé).
    .text
    .globl ml_start_hook,ml_audio_hook,ml_native_tick
ml_start_hook:
    lea.l %sp@(-8),%sp
    movem.l %d0,%sp@
    movew %sr,%d0
    movel %d0,%sp@(4)
    movel %a0@,%d0
    movel %d0,ml_start_due
    movel %d6,ml_start_resume
    movel ml_context,%d0
    movel %d0,ml_start_context
    addql #1,ml_start_serial
    movel %sp@(4),%d0
    movew %d0,%sr
    movem.l %sp@,%d0
    lea.l %sp@(8),%sp
    movel %a0@,0x80001848
    jmp 0x4005468c

| Remplacer jsr 0x40053330 à 0x400594a8 par jsr ml_audio_hook.
| Exécuter d'abord l'appel stock, puis conserver ses résultats et son SR.
| Le hook intervient après l'avance du temps ; jamais de MIDI physique ici.
ml_audio_hook:
    jsr 0x40053330
    lea.l %sp@(-20),%sp
    movem.l %d0-%d1/%a0-%a1,%sp@
    movew %sr,%d0
    movel %d0,%sp@(16)
    jsr ml_native_tick
    movel %sp@(16),%d0
    movew %d0,%sr
    movem.l %sp@,%d0-%d1/%a0-%a1
    lea.l %sp@(20),%sp
    rts

| Prototype volontairement fermé : contexte créé pendant la lecture
| attend le prochain Play. Aucun démarrage libre non synchronisé.
| Le premier tick utilise l'échéance armée, les suivants l'heure audio.
ml_native_tick:
    lea.l %sp@(-12),%sp
    movem.l %d2-%d3/%a2,%sp@
    moveal ml_context,%a2
    tstl %a2
    beq .Lnt_done
    movel 0x8000184c,%d2
    movel 0x40a7883c,%d3
    cmpil #1,%d3
    bne .Lnt_call
    tstl ml_start_serial
    beq .Lnt_done
    cmpl ml_start_context,%a2
    bne .Lnt_done
    movel ml_start_serial,%d0
    cmpl ml_start_seen,%d0
    beq .Lnt_call
    movel %d2,%d0
    subl ml_start_due,%d0
    bmi .Lnt_done
    tstl ml_start_resume
    bne .Lnt_armed
    | Un nouveau Start remet les voies au pas 1 même sans tick Stop observé.
    clrl %sp@-
    movel %d2,%sp@-
    jsr ml_audio_tick
    addql #8,%sp
.Lnt_armed:
    movel ml_start_serial,%d0
    movel %d0,ml_start_seen
    movel ml_start_due,%d2
.Lnt_call:
    movel %d3,%sp@-
    movel %d2,%sp@-
    jsr ml_audio_tick
    addql #8,%sp
.Lnt_done:
    movem.l %sp@,%d2-%d3/%a2
    lea.l %sp@(12),%sp
    rts
    .data
    .balign 4
    .globl ml_start_due,ml_start_resume,ml_start_context,ml_start_serial,ml_start_seen
ml_start_due: .long 0
ml_start_resume: .long 0
ml_start_context: .long 0
ml_start_serial: .long 0
ml_start_seen: .long 0
