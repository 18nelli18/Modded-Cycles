/* Coexistence Scale Lock (notes/40), sans modifier le code de Model-TG.
 * Deux détours immédiatement AVANT ses comparaisons de plage :
 * ON  0x40081734 : d7=fp@(28), d6=fp@(32) ; d2=piste, d3=note.
 * OFF 0x4008146c : d3=fp@(12), d5=fp@(16) ; d2=piste.
 * d0=127 à l'entrée ; conserver les volatils autour du helper C.
 * Le chemin normal rejoint la comparaison stock, ou le hook TG s'il existe.
 * CHORD Keys rejoue exactement cette comparaison puis rejoint sa continuation
 * sans passer par le pliage de gamme TG. Aucun état global partagé temporaire.
 */
    .macro CK_SCALE_TEST release
    lea %sp@(-16),%sp
    movem.l %d0-%d1/%a0-%a1,%sp@
    .if \release
    move.l %fp,%sp@-
    .else
    pea 0
    .endif
    move.l %d3,%sp@-
    move.l %d2,%sp@-
    jsr ck_tg_scale_bypass
    lea %sp@(12),%sp
    tst.l %d0
    .endm

    .macro CK_SCALE_RESTORE
    movem.l %sp@,%d0-%d1/%a0-%a1
    lea %sp@(16),%sp
    .endm

    .section .text.ck_tg_note_on_hook,"ax"
    .balign 2
    .global ck_tg_note_on_hook
ck_tg_note_on_hook:
    move.l %fp@(28),%d7
    move.l %fp@(32),%d6
    CK_SCALE_TEST 0
    bne.s 1f
    CK_SCALE_RESTORE
    jmp 0x4008173c
1:  CK_SCALE_RESTORE
    cmp.l %d3,%d0
    bcc.s 2f
    jmp 0x4008190e
2:  jmp 0x40081742

    .section .text.ck_tg_note_off_hook,"ax"
    .balign 2
    .global ck_tg_note_off_hook
ck_tg_note_off_hook:
    move.l %fp@(12),%d3
    move.l %fp@(16),%d5
    CK_SCALE_TEST 1
    bne.s 1f
    CK_SCALE_RESTORE
    jmp 0x40081474
1:  CK_SCALE_RESTORE
    cmp.l %d3,%d0
    bcc.s 2f
    jmp 0x400815f0
2:  jmp 0x4008147a

/* Appelé uniquement par release_key. Les arguments restent ceux du helper
 * stock (vue, piste, note) et toutes ses sorties audio/MIDI restent natives.
 * Sa pile à l'appel note_off est décrite dans chord_tg_hooks.c ; le symbole
 * de retour exporté identifie cet appel, sans drapeau global temporaire.
 */
    .section .text.ck_tg_key_release,"ax"
    .balign 2
    .global ck_tg_key_release
    .global ck_tg_key_release_return
ck_tg_key_release:
    move.l %sp@(12),%sp@-
    move.l %sp@(12),%sp@-
    move.l %sp@(12),%sp@-
    jsr 0x40019c84
ck_tg_key_release_return:
    lea %sp@(12),%sp
    rts
