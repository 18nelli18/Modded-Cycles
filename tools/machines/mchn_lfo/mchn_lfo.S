/* SPDX-License-Identifier: MIT
 * notes/58 : rendre Algorithm éligible sans modifier les tables copiées par les machines ajoutées.
 * Entrées après moveq #borne,d1 : la borne reste celle de la combinaison installée.
 * Seuls d0 et les CCR sont modifiés, comme dans les fonctions d'origine ; aucun état en RAM.
 */
.text
.globl mchn_flags, mchn_short
mchn_flags:
 move.l 4(%sp),%d0
 cmpi.l #41,%d0
 beq.s .Lmachine_flags
 cmp.l %d0,%d1
 jmp 0x4005a866
.Lmachine_flags:
 move.l #0x600,%d0
 rts
mchn_short:
 move.l 8(%sp),%d0
 cmpi.l #41,%d0
 beq.s .Lmachine_short
 cmp.l %d0,%d1
 jmp 0x4000b210
.Lmachine_short:
 move.l #0x40129965,%d0
 rts
