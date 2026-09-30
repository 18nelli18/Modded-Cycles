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

/* Enregistrements par machine (7 x 76 o a 0x40a71540, construits au demarrage) : deux chaines C++ puis
 * les 17 descripteurs de la page de parametres. Index 0 = aucune, 1..6 = machines 0..5. Il n'y en a pas
 * pour SDVtg : l'OS lisait avant le tableau et copiait des pointeurs au hasard (gel au choix de SDVtg).
 * Le 8e (REC8, dans la charge utile) est construit au premier usage, depuis celui de SNARE (index 2),
 * avec les descripteurs de SDVtg (51..55 -> 76..80) ; les chaines passent par le constructeur de copie
 * de l'OS (0x400f8f02), qui compte les references. */
#define REC_BASE	0x40a71540
#define REC_SNARE	(REC_BASE + 2 * 76)

/* remplace 0x4004df5c : enregistrement n (0..6), 7 = SDVtg */
	.globl	record_at
record_at:
	move.l	4(%sp), %d0
	moveq	#7, %d1
	cmp.l	%d1, %d0
	beq.s	rec8
	moveq	#6, %d1
	cmp.l	%d0, %d1
	bcc.s	1f
	moveq	#-1, %d0
1:	moveq	#76, %d1
	muls.l	%d1, %d0
	add.l	#REC_BASE, %d0
	rts

/* remplace 0x4004df76 : enregistrement de la machine m (0..5 par la table 0x401091b4), 6 = SDVtg */
	.globl	record_of
record_of:
	move.l	4(%sp), %d0
	moveq	#6, %d1
	cmp.l	%d1, %d0
	beq.s	rec8
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

rec8:
	tst.b	REC8_BUILT
	bne.s	9f
	move.l	%d2, -(%sp)
	pea	REC_SNARE
	pea	REC8
	jsr	0x400f8f02		/* chaine +0 */
	addq.l	#8, %sp
	pea	REC_SNARE + 4
	pea	REC8 + 4
	jsr	0x400f8f02		/* chaine +4 */
	addq.l	#8, %sp
	lea	REC_SNARE + 8, %a0
	lea	REC8 + 8, %a1
	moveq	#16, %d2
1:	move.l	(%a0)+, %d0
	moveq	#51, %d1
	cmp.l	%d1, %d0
	blt.s	2f
	moveq	#55, %d1
	cmp.l	%d0, %d1
	blt.s	2f
	moveq	#25, %d1
	add.l	%d1, %d0		/* 51..55 (SNARE) -> 76..80 (SDVtg) */
2:	move.l	%d0, (%a1)+
	subq.l	#1, %d2
	bpl.s	1b
	moveq	#1, %d0
	move.b	%d0, REC8_BUILT
	move.l	(%sp)+, %d2
9:	move.l	#REC8, %d0
	rts
