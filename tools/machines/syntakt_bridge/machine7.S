/* SD VINTAGE en 7e machine « SDVtg », a cote de SNARE (notes/18).
 *
 * Petits detours appeles par des « jmp » poses dans l'OS Cycles 1.13, a la place d'instructions qui ne
 * peuvent pas etre changees sur place. Charges dans la charge utile en SDRAM (0x43033000), recopiee au
 * demarrage avec le reste (tools/gen_sdvintage_7th.py). Pour les machines 0..5 et les descripteurs 0..75,
 * chaque detour fait exactement ce que faisait le code d'origine.
 */
	.text

/* Etat par descripteur : 76 objets de 100 o a 0x40a71754, construits au demarrage par l'OS.
 * Les descripteurs de SDVtg (76..80) partagent ceux de SNARE (51..55) : une piste n'a qu'une machine.
 * Index 76..80 -> 51..55 ; au-dela de 80 -> 0, comme la borne d'origine. */
map_state:
	moveq	#76, %d1
	cmp.l	%d1, %d0
	bcs.s	2f			/* 0..75 : inchange */
	moveq	#81, %d1
	cmp.l	%d1, %d0
	bcs.s	1f
	moveq	#0, %d0			/* hors bornes : 0, comme l'original */
	rts
1:	moveq	#25, %d1
	sub.l	%d1, %d0		/* 76..80 -> 51..55 */
2:	rts

/* remplace 0x4004df40 : adresse de l'etat du descripteur n */
	.globl	state_at
state_at:
	move.l	4(%sp), %d0
	bsr.s	map_state
	moveq	#100, %d1
	muls.l	%d1, %d0
	add.l	#0x40a71754, %d0
	rts

/* remplace 0x4004dfa2 : meme calcul (champ +0x14), puis l'appel d'origine */
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

/* en 0x4005a8f0 (CC recu -> descripteur) : piste 0..5 comme avant, machine 0..6 au lieu de 0..5 */
	.globl	cc_bounds
cc_bounds:
	moveq	#5, %d2
	cmp.l	%d1, %d2
	bcs.s	1f
	moveq	#6, %d2
	cmp.l	%d0, %d2
	bcs.s	2f
	jmp	0x4005a8fa		/* rangee de la machine */
1:	jmp	0x4005a928		/* piste hors bornes : 0 */
2:	jmp	0x4005a91c		/* table commune */

/* en 0x400a2638 (ecran MACHINES) : les deux images de la machine, SNARE (1) pour SDVtg (6) */
	.globl	drum_icons
drum_icons:
	move.l	%d3, %d4
	moveq	#6, %d0
	cmp.l	%d4, %d0
	bne.s	1f
	moveq	#1, %d4
1:	move.l	%d4, %d0
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

/* en 0x400a4dc4 (petite icone de la machine) : bornee a 0..5, SNARE au-dela (au lieu de CHORD) */
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
	bge.s	2f
	moveq	#1, %d0
2:	jmp	0x400a4dde
