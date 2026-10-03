/* Plus de temps pour effacer un trig en mode grille (notes/33). Lié par trig_hold.ld dans un masque de sprite
 * libéré ; les écritures sur l'OS sont dans tools/gen_trig_hold.py (HOOKS).
 *
 * L'OS efface (ou change) un trig existant au relâchement de sa touche, sauf si un « maintien » est arrivé avant :
 * l'horloge des touches (0x4007f914, 120 Hz) l'envoie 24 ticks (200 ms) après l'appui, puis tous les 8 ticks tant que
 * personne ne l'arrête. On garde l'heure de l'appui de chaque touche de pas, prise sur l'événement (+8 : compteur du
 * minuteur DMA 0, 135,168 MHz), en unités de 65 536 coups (0,485 ms, 16 bits : 31,8 s avant de reboucler) :
 *   - un maintien n'est accepté qu'au bout de T_UNITS sur un pas qui a une action en attente (trig à effacer ou à
 *     changer) ; avant, l'événement est consommé sans rien faire et les suivants continuent d'arriver ;
 *   - au relâchement, un appui plus long que T_UNITS garde le trig, même sans maintien reçu (une autre touche
 *     appuyée entre-temps reçoit les maintiens à sa place).
 * Les tours de potard pendant l'appui, la copie ou l'effacement des p-locks marquent déjà le maintien dans UIStates
 * (+356) : le trig reste, comme avant. */
	.globl	th_press, th_hold, th_release, th_t

	.section .text.trig_hold, "ax"

/* a0 = l'événement ; rend a1 = &th_t[touche], d0 = l'heure de l'événement (16 bits). d1 détruit.
 * Touches de pas : codes 16 à 31, donc code & 15 = la touche. */
slot:
	moveq	#15, %d1
	and.l	12(%a0), %d1
	lea	th_t, %a1
	adda.l	%d1, %a1
	adda.l	%d1, %a1
	move.l	8(%a0), %d0
	clr.w	%d0
	swap	%d0
	rts

/* a0 = l'événement ; rend d0 = durée depuis l'appui de sa touche (unités de 65 536 coups). */
elapsed:
	bsr.s	slot
	mvz.w	(%a1), %d1
	sub.l	%d1, %d0
	andi.l	#0xffff, %d0
	rts

/* 0x4002249c : jsr th_press à la place de jsr 0x40072490 (FUNC tenu ?), sur l'appui d'une touche de pas.
 * Note l'heure de l'appui, puis rend comme l'original le bit 1 des indicateurs (FUNC tenu). */
th_press:
	movea.l	4(%sp), %a0
	bsr.s	slot
	move.w	%d0, (%a1)
	moveq	#2, %d0
	and.l	16(%a0), %d0
	lsr.l	#1, %d0
	rts

/* 0x40022d44 : jsr th_hold à la place de jsr 0x40072460 (maintien ?). a3 = le pas (0 à 63).
 * 0 : pas un maintien (relâchement : suite d'origine), ou maintien trop tôt sur un pas qui a une action en attente
 * (l'OS le consomme sans rien faire). 1 : le maintien d'origine. */
th_hold:
	movea.l	4(%sp), %a0
	moveq	#8, %d0
	and.l	16(%a0), %d0
	beq.s	9f
	bsr.s	elapsed
	cmpi.l	#T_UNITS, %d0
	bcc.s	1f
	jsr	0x400cf9a8			/* UIStates */
	movea.l	%d0, %a0
	move.l	%a3, %d0
	moveq	#63, %d1
	and.l	%d1, %d0
	tst.l	92(%a0, %d0.l*4)		/* action en attente sur ce pas (0x4006b8fe) */
	beq.s	1f
	moveq	#0, %d0
	rts
1:	moveq	#1, %d0
9:	rts

/* 0x40022da6 : jsr th_release à la place de jsr 0x4006b736 (UIStates : maintien en cours ?), au relâchement.
 * 4(sp) = UIStates ; l'événement est le 2e argument de PatternGridView::consumeKeyEvent, en 12(%fp).
 * Non nul : le trig reste. */
th_release:
	movea.l	4(%sp), %a0
	move.b	356(%a0), %d0
	bne.s	9f
	movea.l	12(%fp), %a0
	bsr.s	elapsed
	cmpi.l	#T_UNITS, %d0
	scc	%d0
9:	rts

	.section .data.trig_hold, "aw"
	.balign	2
th_t:	.space	32				/* heure du dernier appui de chaque touche de pas */
