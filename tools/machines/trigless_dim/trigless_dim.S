/* Trigless trigs (lock trigs) atténués sur les touches de pas (mod de djd_oz, notes/45). Lié par trigless_dim.ld dans
 * un masque de sprite libéré ; les écritures sur l'OS sont dans tools/gen_trigless_dim.py (HOOKS).
 *
 * L'OS montre un trigless trig comme un trig de note, allumé à fond (état de LED 4 : éteint 0,35 s toutes les 2 s).
 * Le mod lui donne son propre état, 260 (0x104, écrit par le mode grille en 0x40021f52 à la place de 4) : traité
 * comme 4 partout ailleurs, il est en plus éteint 16 ticks sur 25 de l'horloge des LED (120 Hz), soit 36 % de
 * lumière.
 *
 * Réécriture du code de djd_oz (son .syx « Trigless-Trigs-LED-36pct-v4-experimental », envoyé à Maxime le
 * 06/10/2026) : mêmes accroches, même motif d'allumage (+9 modulo 25, allumé au passage de 25). Lui recopiait son code
 * au démarrage au-dessus du BSS (0x42339000) ; ici il s'exécute en place, son état est écrit à zéro dans l'image.
 *
 * Une différence : lui recherchait les LED dans l'état 260 à chaque tick des LED. Or la tâche des minuteurs (priorité
 * 10) interrompt la tâche de l'interface (priorité 6) n'importe où dans son image, aussi entre la remise à zéro des
 * 54 états (0x4000602a) et leur écriture par le mode grille : ce tick-là ne trouve aucun 260 et rallume les touches à
 * fond. Ici les LED à atténuer sont relevées à la fin de chaque image (td_frame, accroche sur le « jmp 0x4008e77e » de
 * 0x40006044), quand les états sont complets ; le tick n'applique que ce relevé.
 *
 * Contextes : td_blink et td_frame dans la tâche de l'interface (2 Hz, 30 Hz), td_tick et les envois de la tâche des
 * minuteurs (120 Hz), td_cmp et td_send dans les deux (0x4008e77e est aussi appelée par la tâche de l'interface).
 * td_frame écrit td_lock, td_tick écrit td_cnt et td_mask, chacun en deux mots longs ; les autres ne lisent qu'un
 * octet du masque. Un mélange de l'ancien et du nouveau relevé ne peut durer qu'un tick. */

	.equ	LED_BIT, 0x4010abf8		/* LED logique -> bit des 7 octets de LED (-1 : pas de LED) */
	.equ	LOCK, 260			/* état d'un trigless trig */
	.equ	ON_STEP, 9			/* allumé ON_STEP ticks sur ON_TOTAL */
	.equ	ON_TOTAL, 25

	.globl	td_blink, td_send, td_cmp, td_frame, td_tick, td_cnt, td_mask, td_lock

	.section .text.td, "ax"

/* 0x40005f36 : jmp td_blink à la place de « cmp.l 40(a4),d1 ; beq.s 0x40005f6c » (d1 = 4), dans le clignotement des
 * LED (0x40005efc, 2 Hz). Les états 4 et 260 clignotent de la même façon. d1 est libre ensuite. */
td_blink:
	move.l	40(%a4), %d1
	cmpi.l	#LOCK, %d1
	beq.s	1f
	cmpi.l	#4, %d1
	beq.s	1f
	jmp	0x40005f3c
1:	jmp	0x40005f6c

/* 0x4008e754 : jmp td_send à la place de « eor.l d0,d3 ; mvz.b d3,d0 ; move.l d0,-(sp) » dans l'envoi de la rangée
 * d2 (0x4008e732) : l'octet envoyé (d3, aussi gardé comme dernier envoyé) perd les bits du masque. a1 est libre. */
td_send:
	eor.l	%d0, %d3
	lea	td_mask, %a1
	moveq	#0, %d0
	move.b	(%a1, %d2.l), %d0
	not.l	%d0
	and.l	%d0, %d3
	mvz.b	%d3, %d0
	move.l	%d0, -(%sp)
	jmp	0x4008e75a

/* 0x4008e7a8 : jmp td_cmp à la place de « mvz.b (a2,d2.l),d1 ; mvz.b d0,d0 » dans la comparaison des 7 rangées
 * (0x4008e77e) : la valeur à afficher (d0) perd les bits du masque avant d'être comparée au dernier envoi. a0 est
 * libre. */
td_cmp:
	lea	td_mask, %a0
	moveq	#0, %d1
	move.b	(%a0, %d2.l), %d1
	not.l	%d1
	and.l	%d1, %d0
	mvz.b	(%a2, %d2.l), %d1
	mvz.b	%d0, %d0
	jmp	0x4008e7ae

/* 0x40006086 : jmp td_frame à la place du « jmp 0x4008e77e » qui termine l'image des LED (0x40006044, tâche de
 * l'interface, 30 Hz ; 4(sp) = l'objet des LED, +40 = état des 54 LED logiques). td_lock reçoit le bit de chaque LED
 * dans l'état 260, puis l'envoi d'origine. Garde d2-d7/a2-a6. */
td_frame:
	movea.l	4(%sp), %a0
	lea	-12(%sp), %sp
	movem.l	%d2-%d4, (%sp)
	clr.l	-(%sp)				/* le relevé en construction : 8 octets sur la pile */
	clr.l	-(%sp)
	lea	40(%a0), %a0
	lea	LED_BIT, %a1
	moveq	#54, %d4
1:	move.l	(%a0)+, %d0
	move.l	(%a1)+, %d2
	cmpi.l	#LOCK, %d0
	bne.s	2f
	tst.l	%d2
	bmi.s	2f
	move.l	%d2, %d3
	lsr.l	#3, %d3				/* octet */
	bset	%d2, (%sp, %d3.l)		/* bit (numéro modulo 8) */
2:	subq.l	#1, %d4
	bne.s	1b
	move.l	(%sp)+, td_lock
	move.l	(%sp)+, td_lock+4
	movem.l	(%sp), %d2-%d4
	lea	12(%sp), %sp
	jmp	0x4008e77e

/* 0x4008e7ca : jmp td_tick au début du tick des LED (120 Hz, tâche des minuteurs). Avance le motif ; sur un tick
 * éteint, le masque prend le dernier relevé, sinon il est vide. Garde tous les registres, puis refait les deux
 * instructions déplacées. Le « beq » qui sautait l'envoi des rangées quand aucun minuteur de LED n'expirait
 * (0x4008e82e) est retiré par une autre écriture : le masque change à chaque tick. */
td_tick:
	move.l	%d0, -(%sp)
	move.l	%d1, -(%sp)
	move.l	td_cnt, %d0
	addi.l	#ON_STEP, %d0
	moveq	#ON_TOTAL, %d1
	cmp.l	%d1, %d0
	bcs.s	1f
	sub.l	%d1, %d0			/* tick allumé : masque vide */
	move.l	%d0, td_cnt
	clr.l	td_mask
	clr.l	td_mask+4
	bra.s	8f
1:	move.l	%d0, td_cnt			/* tick éteint : le relevé */
	move.l	td_lock, %d0
	move.l	td_lock+4, %d1
	move.l	%d0, td_mask
	move.l	%d1, td_mask+4
8:	move.l	(%sp)+, %d1
	move.l	(%sp)+, %d0
	lea	-12(%sp), %sp
	movem.l	%d2-%d3/%a2, (%sp)
	jmp	0x4008e7d2

	.section .data.td, "aw"
	.balign	4
td_cnt:	.long	0				/* motif : 0 à 24 */
td_mask: .space	8				/* bits des LED à éteindre (octet = rangée, bit = colonne) */
td_lock: .space	8				/* bits des LED dans l'état 260 à la fin de la dernière image */
