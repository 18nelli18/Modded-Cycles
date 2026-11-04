/* P-lock HARMONY, OS 1.13, notes/42. Slot RAM27 / identifiant sérialisé33.
 * Sauvegarde complète : d4=slot*4, a5=table stock, a3=lane, d2=piste.
 * Rejoue lea/suba/adda de 0x4005b9be, avant le crochet LFO+ en 0x4005b9c6.
 * HARMONY écrit ID33 puis reprend en 0x4005b9ce ; les autres lanes passent
 * dans le writer installé (stock ou LFO+). Aucun registre supplémentaire modifié.
 * Sauvegarde partielle : d3=slot ; a4 reçoit l'identifiant, d0=-1 comme stock.
 * Décodage : prologue original pour tous les identifiants existants et FX.
 * Note : d3=objet piste, d4=piste, d2=pas. Sauvegarde les volatils, appelle
 * le snapshot puis rejoue l'appel singleton ; ABI et pile stock conservées.
 */
#include "chord_plocks.h"
    .section .text.ck_plock_save_hook,"ax"
    .balign 2
    .global ck_plock_save_hook
ck_plock_save_hook:
    lea %a2@(0,%d1:l:2),%a3
    suba.l %a2,%a2
    adda.l %a1,%a3
    cmpi.l #(CK_HARMONY_SLOT*4),%d4
    bne.s 1f
    move.b #CK_HARMONY_ID,%a3@
    move.b %d2,%a3@(1)
    jmp 0x4005b9ce
1:  jmp 0x4005b9c6

    .section .text.ck_plock_partial_hook,"ax"
    .balign 2
    .global ck_plock_partial_hook
ck_plock_partial_hook:
    cmpi.l #CK_HARMONY_SLOT,%d3
    bne.s 1f
    movea.l #CK_HARMONY_ID,%a4
    bra.s 2f
1:  movea.l %a1@(0,%d3:l:4),%a4
2:  moveq #-1,%d0
    jmp 0x4005bad8

    .section .text.ck_plock_decode_hook,"ax"
    .balign 2
    .global ck_plock_decode_hook
ck_plock_decode_hook:
    move.l %sp@(4),%d0
    cmpi.l #6,%d0
    bcc.s 1f
    move.l %sp@(8),%d0
    cmpi.l #CK_HARMONY_ID,%d0
    bne.s 1f
    moveq #CK_HARMONY_SLOT,%d0
    rts
1:  move.l %d2,%sp@-
    moveq #6,%d2
    move.l %sp@(8),%d1
    jmp 0x4005aa22

    .section .text.ck_plock_note_hook,"ax"
    .balign 2
    .global ck_plock_note_hook
ck_plock_note_hook:
    lea %sp@(-16),%sp
    movem.l %d0-%d1/%a0-%a1,%sp@
    move.l %d2,%sp@-
    move.l %d4,%sp@-
    move.l %d3,%sp@-
    jsr ck_plock_note
    lea %sp@(12),%sp
    movem.l %sp@,%d0-%d1/%a0-%a1
    lea %sp@(16),%sp
    jsr 0x400cfd0e
    jmp 0x4001227a

/* Événement accepté : a2=événement, d2=piste, +12=source (1 séquenceur).
 * L'arbitrage natif précède l'accroche, donc un trig rejeté ne change rien.
 * L'origine audio suit l'ordre réel de la file, sans effacer l'état UI.
 * Les fins conservent l'origine de la queue. Sauvegarde des volatils
 * avant l'appel C, puis rejeu exact du calcul d1=(flags & 0x81).
 */
    .section .text.ck_plock_sequence_hook,"ax"
    .balign 2
    .global ck_plock_sequence_hook
ck_plock_sequence_hook:
    lea %sp@(-16),%sp
    movem.l %d0-%d1/%a0-%a1,%sp@
    move.l %a2,%sp@-
    move.l %d2,%sp@-
    jsr ck_audio_event
    addq.l #8,%sp
    movem.l %sp@,%d0-%d1/%a0-%a1
    lea %sp@(16),%sp
    move.l %a2@(40),%d1
    andi.l #129,%d1
    jmp 0x40058ed0
