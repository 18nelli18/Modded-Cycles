/* SD VINTAGE et CP VINTAGE en 7e et 8e machines « SDVtg » (6) et « CPVtg » (7), a cote des 6 machines
 * d'origine (notes/19). Meme principe que machine7.S (notes/18), etendu a deux machines :
 *   descripteurs 76..80 = SDVtg, 81..85 = CPVtg ; enregistrements par machine 7 = SDVtg, 8 = CPVtg.
 * Pour les machines 0..5 et les descripteurs 0..75, chaque detour fait exactement ce que faisait l'OS.
 * REC8, REC9, REC_BUILT et VEC8 sont fournis par tools/gen_syntakt_machines.py (-D).
 */
	.text

/* Etat par descripteur : 76 objets de 100 o a 0x40a71754. SDVtg (76..80) et CPVtg (81..85) partagent
 * ceux de SNARE (51..55). Au-dela de 85 -> 0, comme la borne d'origine. */
map_state:
	moveq	#76, %d1
	cmp.l	%d1, %d0
	bcs.s	3f			/* 0..75 : inchange */
	moveq	#86, %d1
	cmp.l	%d1, %d0
	bcs.s	1f
	moveq	#0, %d0
	rts
1:	moveq	#81, %d1
	cmp.l	%d1, %d0
	bcs.s	2f
	moveq	#5, %d1
	sub.l	%d1, %d0		/* 81..85 -> 76..80 */
2:	moveq	#25, %d1
	sub.l	%d1, %d0		/* 76..80 -> 51..55 */
3:	rts

	.globl	state_at
state_at:
	move.l	4(%sp), %d0
	bsr.s	map_state
	moveq	#100, %d1
	muls.l	%d1, %d0
	add.l	#0x40a71754, %d0
	rts

	.globl	state_connect
state_connect:
	move.l	4(%sp), %d0
	bsr.s	map_state
	moveq	#100, %d1
	muls.l	%d1, %d0
	add.l	#0x40a71768, %d0
	pea	0x40a71500
	move.l	12(%sp), -(%sp)
	move.l	%d0, -(%sp)
	jsr	0x400ddf60
	lea	12(%sp), %sp
	move.l	#0x40a71500, %d0
	rts

/* en 0x4005a8f0 (CC recu -> descripteur) : piste 0..5 comme avant, machine 0..7 */
	.globl	cc_bounds
cc_bounds:
	moveq	#5, %d2
	cmp.l	%d1, %d2
	bcs.s	1f
	moveq	#7, %d2
	cmp.l	%d0, %d2
	bcs.s	2f
	jmp	0x4005a8fa
1:	jmp	0x4005a928
2:	jmp	0x4005a91c

/* image affichee pour une machine : SDVtg -> SNARE (1), CPVtg -> PERC (3), sinon elle-meme */
shown:
	moveq	#6, %d1
	cmp.l	%d1, %d0
	bne.s	1f
	moveq	#1, %d0
	rts
1:	moveq	#7, %d1
	cmp.l	%d1, %d0
	bne.s	2f
	moveq	#3, %d0
2:	rts

/* en 0x400a2638 (ecran MACHINES) : les deux images de la machine */
	.globl	drum_icons
drum_icons:
	move.l	%d3, %d0
	bsr.s	shown
	move.l	%d0, %d4
	lsl.l	#2, %d0
	lsl.l	#5, %d4
	sub.l	%d0, %d4		/* d4 = 28 * machine affichee */
	pea	0x1
	pea	0x17
	pea	0x20
	lea	0x40071da4, %a2
	movea.l	0x40fe32cc, %a1
	adda.l	%d4, %a1
	move.l	%a1, -(%sp)
	move.l	%d2, -(%sp)
	jsr	(%a2)
	lea	48(%sp), %sp		/* comme l'original : 28 o du texte + 20 o de cette image */
	pea	0x1
	pea	0x22
	add.l	0x40fe384c, %d4
	pea	0x60
	move.l	%d4, -(%sp)
	move.l	%d2, -(%sp)
	jsr	(%a2)
	lea	20(%sp), %sp
	jmp	0x400a2680

/* en 0x400a4dc4 (petite icone de la machine) : 0..5 inchanges, SDVtg -> SNARE, CPVtg -> PERC, sinon CHORD */
	.globl	small_icon
small_icon:
	lea	10(%a0), %a0
	move.l	%a0, -(%sp)
	move.l	16(%fp), -(%sp)
	move.l	%d2, %d0
	bpl.s	1f
	moveq	#0, %d0
1:	moveq	#5, %d1
	cmp.l	%d0, %d1
	bge.s	3f
	bsr.s	shown
	moveq	#5, %d1
	cmp.l	%d0, %d1
	bge.s	3f
	moveq	#5, %d0			/* au-dela de 7 : CHORD, comme l'OS */
3:	jmp	0x400a4dde

/* Enregistrements par machine (7 x 76 o a 0x40a71540) : 0 = aucune, 1..6 = machines 0..5.
 * 7 = SDVtg (REC8), 8 = CPVtg (REC9), construits au premier usage depuis celui de SNARE (index 2) :
 * chaines par le constructeur de copie de l'OS (0x400f8f02), descripteurs 51..55 -> 76..80 ou 81..85. */
#define REC_BASE	0x40a71540
#define REC_SNARE	(REC_BASE + 2 * 76)

	.globl	record_at
record_at:
	move.l	4(%sp), %d0
	moveq	#7, %d1
	cmp.l	%d1, %d0
	beq.s	rec_sd
	moveq	#8, %d1
	cmp.l	%d1, %d0
	beq.s	rec_cp
	moveq	#6, %d1
	cmp.l	%d0, %d1
	bcc.s	1f
	moveq	#-1, %d0
1:	moveq	#76, %d1
	muls.l	%d1, %d0
	add.l	#REC_BASE, %d0
	rts

	.globl	record_of
record_of:
	move.l	4(%sp), %d0
	moveq	#6, %d1
	cmp.l	%d1, %d0
	beq.s	rec_sd
	moveq	#7, %d1
	cmp.l	%d1, %d0
	beq.s	rec_cp
	moveq	#5, %d1
	cmp.l	%d0, %d1
	bcs.s	2f
	lea	0x401091b4, %a0
	mvs.b	(%a0,%d0.l), %d0
	moveq	#6, %d1
	cmp.l	%d0, %d1
	bcc.s	3f
2:	moveq	#-1, %d0
3:	moveq	#76, %d1
	muls.l	%d1, %d0
	add.l	#REC_BASE, %d0
	rts

rec_sd:
	lea	REC8, %a0
	moveq	#25, %d0
	bra.s	rec_build
rec_cp:
	lea	REC9, %a0
	moveq	#30, %d0

/* a0 = enregistrement a construire (76 o, puis 1 octet « construit »), d0 = decalage des descripteurs */
rec_build:
	tst.b	76(%a0)
	bne.s	9f
	move.l	%d2, -(%sp)
	move.l	%a2, -(%sp)
	movea.l	%a0, %a2
	move.l	%d0, %d2
	pea	REC_SNARE
	move.l	%a2, -(%sp)
	jsr	0x400f8f02		/* chaine +0 */
	addq.l	#8, %sp
	pea	REC_SNARE + 4
	pea	4(%a2)
	jsr	0x400f8f02		/* chaine +4 */
	addq.l	#8, %sp
	lea	REC_SNARE + 8, %a0
	lea	8(%a2), %a1
	moveq	#16, %d1
	move.l	%d1, -(%sp)		/* compteur sur la pile : d1 sert aux comparaisons */
1:	move.l	(%a0)+, %d0
	moveq	#51, %d1
	cmp.l	%d1, %d0
	blt.s	2f
	moveq	#55, %d1
	cmp.l	%d0, %d1
	blt.s	2f
	add.l	%d2, %d0		/* 51..55 (SNARE) -> descripteurs de la machine */
2:	move.l	%d0, (%a1)+
	subq.l	#1, (%sp)
	bpl.s	1b
	addq.l	#4, %sp
	moveq	#1, %d0
	move.b	%d0, 76(%a2)
	movea.l	%a2, %a0
	move.l	(%sp)+, %a2
	move.l	(%sp)+, %d2
9:	move.l	%a0, %d0
	rts

/* en 0x4001e8da (ecran principal, potard -> descripteur) : appele par jsr a la place de
 * « move.l 32(sp),d0 ; movea.l 104(a2),a1 ». Machines 6 et 7 : table VEC8 = [1..8] ; sinon le vecteur
 * [1..6] de l'ecran, inchange. */
	.globl	knob_vec
knob_vec:
	move.l	36(%sp), %d0		/* 32(sp) de l'appelant (+4 : adresse de retour) */
	movea.l	104(%a2), %a1
	moveq	#6, %d1
	cmp.l	%d1, %d0
	blt.s	1f
	lea	VEC8, %a1
1:	rts

/* Le champ « machine » des descripteurs vaut 0..5 pour une machine, 7 pour « toutes les machines » : la
 * 8e machine (index 7) ne peut pas s'y ecrire 7. Ses descripteurs (81..84) portent 6 (« propre a une
 * machine », comme ceux de SDVtg) ; deux detours les rattachent a la machine 7. */

/* remplace 0x4005a50a (machine du descripteur n, pour le test d'applicabilite 0x4000aa9a) */
	.globl	desc_machine
desc_machine:
	move.l	4(%sp), %d0
	moveq	#81, %d1
	cmp.l	%d1, %d0
	bcs.s	1f
	moveq	#84, %d1
	cmp.l	%d0, %d1
	bcs.s	1f
	moveq	#7, %d0			/* CPVtg */
	rts
1:	moveq	#86, %d1
	cmp.l	%d0, %d1
	bhi.s	2f
	moveq	#0, %d0			/* hors bornes : descripteur 0, comme l'original */
2:	move.l	%d0, %d1
	lsl.l	#3, %d1
	lsl.l	#6, %d0
	sub.l	%d1, %d0		/* 56 x n */
	lea	DESC8, %a0
	move.l	(%a0,%d0.l), %d0
	rts

/* en 0x4005a340 (constructeur des tables, d5 = champ machine, d2 = numero du descripteur) : a la place de
 * « moveq #5,d0 ; cmp.l d5,d0 ; bcc.s 0x4005a384 ». Propre a une machine si champ <= 6 ; les descripteurs
 * 81..84 (CPVtg) vont dans la rangee 7. */
	.globl	builder_row
builder_row:
	moveq	#6, %d0
	cmp.l	%d5, %d0
	bcs.s	1f			/* champ > 6 : groupe commun, comme l'OS */
	moveq	#81, %d0
	cmp.l	%d0, %d2
	bcs.s	2f
	moveq	#84, %d0
	cmp.l	%d2, %d0
	bcs.s	2f
	moveq	#7, %d5			/* rangee de CPVtg */
2:	jmp	0x4005a384
1:	jmp	0x4005a346
