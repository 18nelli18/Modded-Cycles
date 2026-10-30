/* Pas tenu + MACHINES : le navigateur s'ouvre au relâchement de MACHINES, et seulement si rien d'autre n'a été fait
 * pendant (notes/86 §7). MACHINES tenue est le modificateur de Model-TG et du lo-fi de piste (DECAY, COLOR, SHAPE,
 * SWEEP, CONTOUR -> Attack, Rate, Bits, Filtre, Résonance) ; pas tenu + MACHINES + potard pose leur p-lock. L'OS, lui,
 * ouvre à l'appui de MACHINES pas tenu le navigateur des machines du pas (DrumSelect, ou PresetManager quand le pas est
 * tenu depuis un moment). Lié par trig_machines.ld dans les masques de sprite libérés 0x4018d918 (41x41, 328 o) et
 * 0x4016ea78 (52x22, 208 o), écrit avec Model-TG (tools/trig_machines.py).
 *
 * MainScreenView::consumeKeyEvent (0x4001c0d2, relevé de l'agent DSH, docs/2026-10-30-trig-machines-dsh.md) :
 * cas 5 (MACHINES) en 0x4001c252 : appui frais (0x400724a0) sans FUNC -> 0x4006b736 (UIStates+0x164, « maintien »)
 * choisit PresetManager (1) ou DrumSelect (0), ouverts à l'appui ; au relâchement, rien.
 *  - mt_main (prologue de 0x4001c0d2) : appui frais de MACHINES sans FUNC, un pas tenu (0x4006b78e, le masque des
 *    pas tenus) -> avalé, on note le navigateur que l'appui aurait ouvert ; relâchement de MACHINES avec cette attente,
 *    le pas toujours tenu -> la fonction rejouée avec une copie de l'événement en appui frais (mt_trig rend le
 *    navigateur noté) ; le pas lâché d'abord : rien ; tout appui frais d'une autre touche annule l'attente ;
 *  - mt_knob (prologue de ParameterPageView::encoder 0x4001f4f0) : un potard tourné annule l'attente ;
 *  - mt_key (prologue de ParameterPageView::consumeKeyEvent 0x4001f97e) : un appui frais d'une autre touche
 *    ([LFO]...) l'annule aussi ;
 *  - mt_trig (à la place de jsr 0x4006b736 en 0x4001c27c) : pendant le rejeu, le navigateur noté.
 * Sans pas tenu, ou avec FUNC, tout reste celui de l'OS, à l'appui. MACHINES tenue reste vue tenue par Model-TG
 * (état physique, 0x4007faf4 / KEY_BITS) : avaler l'événement ne change pas le modificateur. */

	.equ	PRESS, 0x400724a0		/* (événement) : appui frais (enfoncée, pas une répétition) */
	.equ	FUNCQ, 0x40072490		/* (événement) : FUNC tenue */
	.equ	UIST, 0x400cf9a8		/* UIStates */
	.equ	HELD, 0x4006b78e		/* (UIStates) : un pas tenu (+0x15c / +0x160) */
	.equ	HOLD, 0x4006b736		/* (UIStates) : maintien (+0x164) */
	.equ	MAIN, 0x4001c0d2

	.globl	mt_main, mt_trig, mt_knob, mt_key, mt_pend, mt_replay, mt_t

	.section .text.trig_machines, "ax"

/* jsr mt_main ; nop à la place de link.w fp,#-88 ; movem.l d2-d6/a2-a5,(sp). Pile : 16(sp) après nos 16 o = le
 * retour du jsr, puis le retour de l'appelant, this, l'événement (code +12, drapeaux +16 : bit 0 enfoncée, bit 3
 * répétition). Rend d0 = 1 (pris) ou la fonction de l'OS. */
mt_main:
	lea	-16(%sp), %sp
	movem.l	%d2-%d3/%a2-%a3, (%sp)
	movea.l	28(%sp), %a2			/* l'événement */
	movea.l	24(%sp), %a3			/* this */
	tst.b	mt_replay
	bne.w	9f
	moveq	#5, %d0
	cmp.l	12(%a2), %d0
	beq.s	1f
	tst.b	mt_pend				/* une autre touche : son appui annule l'attente */
	beq.w	9f
	bsr.w	mt_press
	beq.w	9f
	clr.b	mt_pend
	bra.w	9f
1:	bsr.w	mt_press
	beq.s	2f
	move.l	%a2, -(%sp)
	jsr	FUNCQ
	addq.l	#4, %sp
	tst.b	%d0
	bne.w	9f				/* FUNC : l'OS */
	bsr.w	mt_held
	beq.w	9f				/* aucun pas tenu : l'OS */
	jsr	UIST
	move.l	%d0, -(%sp)
	jsr	HOLD
	addq.l	#4, %sp
	move.b	%d0, mt_t			/* le navigateur que l'appui aurait ouvert */
	moveq	#1, %d0
	move.b	%d0, mt_pend
	moveq	#1, %d0
	bra.s	8f
2:	btst	#0, 19(%a2)
	bne.w	9f				/* répétition : l'OS */
	tst.b	mt_pend
	beq.w	9f
	clr.b	mt_pend
	bsr.w	mt_held
	beq.w	9f				/* pas lâché avant MACHINES : rien */
	moveq	#1, %d0
	move.b	%d0, mt_replay
	lea	mt_ev, %a0
	moveq	#5, %d1
3:	move.l	(%a2)+, (%a0)+
	subq.l	#1, %d1
	bpl.s	3b
	move.l	mt_ev + 16, %d0
	ori.l	#1, %d0
	andi.l	#0xfffffff7, %d0
	move.l	%d0, mt_ev + 16			/* un appui frais */
	pea	mt_ev
	move.l	%a3, -(%sp)
	jsr	MAIN
	addq.l	#8, %sp
	clr.b	mt_replay
	moveq	#1, %d0
8:	movem.l	(%sp), %d2-%d3/%a2-%a3
	lea	20(%sp), %sp			/* et le retour du jsr : on rend à l'appelant */
	rts
9:	movem.l	(%sp), %d2-%d3/%a2-%a3
	lea	20(%sp), %sp
	link.w	%fp, #-88			/* les instructions remplacées, puis la suite */
	movem.l	%d2-%d6/%a2-%a5, (%sp)
	jmp	MAIN + 8

/* d0 (Z) : appui frais de l'événement a2 */
mt_press:
	move.l	%a2, -(%sp)
	jsr	PRESS
	addq.l	#4, %sp
	tst.b	%d0
	rts

/* d0 (Z) : un pas tenu */
mt_held:
	jsr	UIST
	move.l	%d0, -(%sp)
	jsr	HELD
	addq.l	#4, %sp
	tst.b	%d0
	rts

	.section .text.mt_side, "ax"

/* jsr mt_trig à la place de jsr 0x4006b736 (cas 5, appui frais) : pendant le rejeu, le navigateur noté à l'appui */
mt_trig:
	tst.b	mt_replay
	beq.s	1f
	moveq	#0, %d0
	move.b	mt_t, %d0
	rts
1:	jmp	HOLD

/* jsr mt_knob ; nop à la place de link.w fp,#-84 ; movem.l d2-d7/a2-a5,(sp) (ParameterPageView::encoder ;
 * l'événement en 12(sp) : +16 = pas, 0 pour un clic) */
mt_knob:
	tst.b	mt_pend
	beq.s	1f
	movea.l	12(%sp), %a0
	tst.l	16(%a0)
	beq.s	1f
	clr.b	mt_pend
1:	addq.l	#4, %sp
	link.w	%fp, #-84
	movem.l	%d2-%d7/%a2-%a5, (%sp)
	jmp	0x4001f4f8

/* jsr mt_key ; nop à la place de link.w fp,#-40 ; movem.l d2-d3/a2-a5,(sp) (ParameterPageView::consumeKeyEvent) :
 * l'appui frais d'une autre touche que MACHINES annule l'attente */
mt_key:
	tst.b	mt_pend
	beq.s	1f
	movea.l	12(%sp), %a0
	moveq	#5, %d0
	cmp.l	12(%a0), %d0
	beq.s	1f
	move.l	16(%a0), %d0
	btst	#0, %d0
	beq.s	1f
	btst	#3, %d0
	bne.s	1f
	clr.b	mt_pend
1:	addq.l	#4, %sp
	link.w	%fp, #-40
	movem.l	%d2-%d3/%a2-%a5, (%sp)
	jmp	0x4001f986

/* dans le masque, donc rechargé depuis la flash à chaque démarrage : rien en attente */
mt_pend:	.byte	0			/* un appui de MACHINES avalé, pas tenu */
mt_replay:	.byte	0			/* rejeu en cours */
mt_t:		.byte	0			/* navigateur noté : 0 DrumSelect, 1 PresetManager */
	.balign	4
mt_ev:		.space	24			/* copie de l'événement rejoué */
