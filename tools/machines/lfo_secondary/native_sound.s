| Adaptation MIT de 18nelli18, tools/machines/lfo_plus/lfo_plus.S.
| Format DavidCaruso ; cinq réglages seulement, trois autres aux défauts.
    .ifdef LF2_NATIVE_SOUND
    .globl lf2n_pack,lf2n_unpack,lf2n_init
	.section .text.lf2n_store, "ax"

/* 0x4005b028 (sauvegarde du son, format 2, 0x4005afa0) et 0x4005b0dc (format 1, 0x4005b054) : jsr lf2n_pack à la
 * place de move.w 94(a3),92(a2). a2 = l'enregistrement (100 o), a3 = le son. LFO 2 (k = 28..32, son + 76..85) en
 * un long en +88 (les deux dernières cases libres, que la sauvegarde vient de mettre à zéro, comme sous Model-TG) :
 * bits 31-30 = 10 (marque), 29-22 SPD >> 7, 21-17 MULT, 16-14 WAVE, 13-8 DEST, 7-0 DEP >> 7 (même format que
 * DavidCaruso : ses sons se relisent ici). Garde tout sauf d0 (d1, a1, a4 servent ensuite). */
lf2n_pack:
	move.w	94(%a3), 92(%a2)
	move.l	%d1, -(%sp)
	moveq	#2, %d0				/* marque */
	moveq	#0, %d1
	move.w	76(%a3), %d1			/* SPD */
	lsr.l	#7, %d1
	andi.l	#0xff, %d1
	lsl.l	#8, %d0
	or.l	%d1, %d0
	moveq	#0, %d1
	move.b	78(%a3), %d1			/* MULT */
	andi.l	#0x1f, %d1
	lsl.l	#5, %d0
	or.l	%d1, %d0
	move.b	80(%a3), %d1			/* WAVE */
	andi.l	#7, %d1
	lsl.l	#3, %d0
	or.l	%d1, %d0
	move.b	82(%a3), %d1			/* DEST */
	andi.l	#0x3f, %d1
	lsl.l	#6, %d0
	or.l	%d1, %d0
	move.w	84(%a3), %d1			/* DEP */
	lsr.l	#7, %d1
	andi.l	#0xff, %d1
	lsl.l	#8, %d0
	or.l	%d1, %d0
	move.l	%d0, 88(%a2)
	move.l	(%sp)+, %d1
	rts

	.section .text.lf2n_unpack, "ax"

/* 0x4005af1c, chargement du son (0x4005aecc ; a2 = le son, a3 = l'enregistrement, mots k = 0..32 du son déjà mis à
 * zéro par 0x4008f238) : jsr lf2n_unpack à la place de lea 0x4010eea8,a0. LFO 2 relu de +88 s'il porte la marque,
 * sinon (tout son plus ancien) ses défauts. d0-d1/a1 libres ; a0 rendu comme l'instruction remplacée. */
lf2n_unpack:
	addq.l #1, lf2n_epoch
	move.l	88(%a3), %d0
	move.l	%d0, %d1
	andi.l	#0xc0000000, %d1
	cmpi.l	#0x80000000, %d1
	bne.s	1f
	move.l	%d0, %d1			/* DEP */
	andi.l	#0xff, %d1
	lsl.l	#7, %d1
	move.w	%d1, 84(%a2)
	lsr.l	#8, %d0
	move.l	%d0, %d1			/* DEST */
	andi.l	#0x3f, %d1
	lsl.l	#8, %d1
	move.w	%d1, 82(%a2)
	lsr.l	#6, %d0
	move.l	%d0, %d1			/* WAVE */
	andi.l	#7, %d1
	lsl.l	#8, %d1
	move.w	%d1, 80(%a2)
	lsr.l	#3, %d0
	move.l	%d0, %d1			/* MULT */
	andi.l	#0x1f, %d1
	lsl.l	#8, %d1
	move.w	%d1, 78(%a2)
	lsr.l	#5, %d0				/* SPD */
	andi.l	#0xff, %d0
	lsl.l	#7, %d0
	move.w	%d0, 76(%a2)
	bra.s	2f
1:	bsr.s	lf2n_defaults
2:	lea	0x4010eea8, %a0
	rts

/* 0x400618e2, fin de l'initialisation d'un son aux défauts (0x40061866 ; a2 = le son) : jsr lf2n_init à la place de
 * lsl.l #8,d3 ; move.w d3,38(a2). Les deux instructions, puis les défauts de LFO 2 (l'OS y a mis 0 : aucun
 * descripteur ne vise k = 28..32). d0-d1/a0-a1 libres ensuite. */
lf2n_init:
	lsl.l	#8, %d3
	move.w	%d3, 38(%a2)
/* Défauts de LFO 2 dans le son a2 : ceux du LFO d'origine (descripteurs 0x1d..0x24) : SPD 0x7000, MULT 4, WAVE 0,
 * DEST None, DEP 0x4000 (profondeur nulle). */
lf2n_defaults:
	move.l	#0x70000400, %d0
	move.l	%d0, 76(%a2)
	clr.l	80(%a2)
	move.w	#0x4000, 84(%a2)
	rts


    .data
    .balign 4
    .globl lf2n_epoch,lf2n_seen
lf2n_epoch: .long 0
lf2n_seen: .long -1
    .endif
