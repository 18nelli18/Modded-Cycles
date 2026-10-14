/* SPDX-License-Identifier: MIT
 * KeyboardView : TRACK + TRIG 1/16 change KBT de -/+12.
 * Contrat : (vue, KeyEvent), retour booléen ; préserver d2-d7/a2-a6 et la pile.
 * Appui consommé après le setter stock ; maintien consommé sans répétition.
 * Tout relâchement rejoint le callback stock, qui utilise la note mémorisée.
 * Code original ; aucun corps de routine Elektron copié (notes/73).
 */
.section .cave,"ax"
.globl octave_keyboard
.balign 4
octave_keyboard:
 lea -16(%sp),%sp
 movem.l %d2/%a2-%a4,(%sp)
 move.l 24(%sp),%a2
 move.l 12(%a2),%d2
 cmpi.l #16,%d2
 beq .Ledge
 cmpi.l #31,%d2
 bne .Lnative
.Ledge:
 move.l 16(%a2),%d0
 btst #0,%d0
 beq .Lnative
 pea 2
 jsr 0x4007faf4
 addq.l #4,%sp
 tst.l %d0
 beq .Lnative
 pea 1
 jsr 0x4007faf4
 addq.l #4,%sp
 tst.l %d0
 bne .Lnative
 pea 3
 jsr 0x4007faf4
 addq.l #4,%sp
 tst.l %d0
 bne .Lnative
 pea 4
 jsr 0x4007faf4
 addq.l #4,%sp
 tst.l %d0
 bne .Lnative
 jsr 0x400cf9a8
 move.l %d0,%a3
 move.l %a3,-(%sp)
 jsr 0x4006b978
 addq.l #4,%sp
 tst.b %d0
 bne .Lnative
 move.l %a3,-(%sp)
 jsr 0x4006bb18
 addq.l #4,%sp
 tst.b %d0
 bne .Lnative
 move.l 16(%a2),%d0
 btst #3,%d0
 bne .Lconsumed
 jsr 0x400cf866
 move.l %d0,-(%sp)
 jsr 0x4000f23e
 addq.l #4,%sp
 move.l %d0,%a4
 move.l %a4,-(%sp)
 jsr 0x40016da6
 addq.l #4,%sp
 cmpi.l #16,%d2
 bne .Lup
 subi.l #12,%d0
 bra .Lset
.Lup:
 addi.l #12,%d0
.Lset:
 move.l %d0,-(%sp)
 move.l %a4,-(%sp)
 jsr 0x40016dd6
 addq.l #8,%sp
.Lconsumed:
 moveq #1,%d0
 movem.l (%sp),%d2/%a2-%a4
 lea 16(%sp),%sp
 rts
.Lnative:
 movem.l (%sp),%d2/%a2-%a4
 lea 16(%sp),%sp
 jmp 0x4001a0d2
