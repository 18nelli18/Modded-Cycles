/* Crochet de la sélection des intervalles CHORD (notes/42).
 * Remplace à 0x400ab0e4 : addal #0x4012142c,%a0 (six octets).
 * Entrée : a3 = copie locale de chord_audio_update ; a0 = SHAPE * 16.
 * Sortie : a0 = table stock ou quatre rapports locaux. Aucun autre registre
 * modifié. Le move.l suivant dans l'OS remplace CCR avant de l'utiliser.
 * Le détournement de l'entrée 0x400aae88 est obligatoire avec ce hook, même
 * lorsqu'un autre mod a recopié la table de dispatch des moteurs.
 */
#include "chord_audio.h"
    .text
    .align 2
    .global chord_audio_ratios
    .type chord_audio_ratios,@function
chord_audio_ratios:
    tst.l %a3@(CK_AUDIO_ACTIVE_OFFSET)
    beq.s 1f
    lea %a3@(CK_AUDIO_RATIOS_OFFSET),%a0
    rts
1:
    adda.l #0x4012142c,%a0
    rts
    .size chord_audio_ratios,.-chord_audio_ratios

/* Entrée stock détournée à 0x400aae88 par jmp chord_audio_update ; nop.
 * Rejoue les huit octets du prologue avant la suite originale à 0x400aae90.
 * ABI C identique : arguments et retour restent sur la pile du wrapper.
 */
    .align 2
    .global chord_audio_original
    .type chord_audio_original,@function
chord_audio_original:
    lea %sp@(-28),%sp
    movem.l %d2-%d5/%a2-%a4,%sp@
    jmp 0x400aae90
    .size chord_audio_original,.-chord_audio_original
