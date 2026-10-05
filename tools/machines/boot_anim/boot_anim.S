/* Animation de démarrage « modded-cycles » (notes/39). Liée par boot_anim.ld à la place du corps de la tâche
 * d'animation d'origine (0x40053a6c, créée par 0x400539fc) ; les écritures sur l'OS sont dans
 * tools/gen_boot_anim.py, qui écrit aussi anim.inc (géométrie, horaire, colonnes du texte).
 *
 * Contrat (le même que la tâche d'origine) :
 *   - tâche de l'OS, lancée une fois au démarrage, priorité 7, pile de 16 Ko (0x40a745c0) ; ne rend jamais la main ;
 *   - une image par tick du minuteur 0x400539b8 (2 ticks de 10 ms = 20 ms : 50 images par seconde), qui
 *     incrémente le sémaphore 0x40a78618 ;
 *   - chaque image est dessinée dans le tampon de dessin de l'écran (0x4008e728 : *0x401492f0, 1 024 o, colonnes
 *     de 64 pixels, 8 o par colonne, bit 7 de l'octet = la ligne du haut), puis 0x4008e622 envoie à l'écran les
 *     blocs de 8x8 qui ont changé et échange les deux tampons ;
 *   - au début, l'écran entier est effacé (0x4008e6ba, ce que fait l'OS quand il démarre sans animation) : les
 *     carreaux d'origine finissaient par couvrir tout l'écran, ici une bonne partie de l'écran reste vide ;
 *   - à la fin, comme l'original (0x40053e34) : 10 ticks d'attente, signal 0x40a78620 (la tâche principale l'attend
 *     en 0x40053a54 avant d'afficher l'écran normal), retrait du minuteur, attente sans fin.
 * L'original allumait aussi des LED de trig ; ici aucune (la tâche principale les éteint toutes de toute façon,
 * 0x4008e8de). */
	.include "anim.inc"

	.equ	TIMER_ADD, 0x40002144		/* (rappel, période en ticks de 10 ms) */
	.equ	TIMER_DEL, 0x40002200		/* (rappel) */
	.equ	SEM_WAIT, 0x40001aca		/* (sémaphore) : décrémente ou attend */
	.equ	SEM_POST1, 0x40001c80		/* (sémaphore binaire) : signale */
	.equ	SEM_TAKE, 0x40001b3e		/* (sémaphore binaire) : attend */
	.equ	TICK_CB, 0x400539b8		/* rappel du minuteur : incrémente SEM_TICK */
	.equ	SEM_TICK, 0x40a78618
	.equ	SEM_DONE, 0x40a78620
	.equ	GET_BUF, 0x4008e728		/* rend *0x401492f0, le tampon de dessin */
	.equ	FLUSH, 0x4008e622		/* envoie les blocs changés, échange les tampons */
	.equ	BLANK, 0x4008e6ba		/* vide les deux tampons et tout l'écran (démarrage sans animation) */

	.globl	ba_task
	.section .text.boot_anim, "ax"

/* Entrée de la tâche (0x40053a6c). d7 = numéro de l'image, a3 = tampon de dessin. */
ba_task:
	jsr	BLANK				/* l'écran part de zéro : FLUSH n'envoie que ce qui change */
	pea	2.w
	pea	TICK_CB
	jsr	TIMER_ADD
	addq.l	#8, %sp
	moveq	#0, %d7
frame:
	jsr	GET_BUF
	movea.l	%d0, %a3
	movea.l	%d0, %a0
	move.l	#256, %d0
1:	clr.l	(%a0)+
	subq.l	#1, %d0
	bne.s	1b

/* Les quatre carrés : (centre x, centre y, image de départ). Chacun grandit selon GROW puis garde SIDE. */
	lea	sq_tab(%pc), %a2
	moveq	#4, %d6
2:	moveq	#0, %d1
	move.b	(%a2)+, %d1
	moveq	#0, %d2
	move.b	(%a2)+, %d2
	moveq	#0, %d0
	move.b	(%a2)+, %d0
	move.l	%d7, %d3
	sub.l	%d0, %d3			/* d = image - départ */
	blt.s	4f
	moveq	#NGROW, %d0
	cmp.l	%d0, %d3
	blt.s	3f
	moveq	#SIDE, %d3
	bra.s	31f
3:	lea	grow(%pc), %a0
	move.b	0(%a0, %d3.l), %d3
	extb.l	%d3
31:	moveq	#1, %d4
	bsr	centered
4:	subq.l	#1, %d6
	bne.s	2b

/* Le carré d'accent (l'orange du logo) se creuse : un anneau, puis un cœur plein. */
	move.l	%d7, %d6
	subi.l	#PUNCH, %d6
	blt.s	6f
	move.l	%d6, %d3
	add.l	%d3, %d3
	addq.l	#2, %d3				/* 2 + 2d, jusqu'à HOLE */
	moveq	#HOLE, %d0
	cmp.l	%d0, %d3
	ble.s	5f
	move.l	%d0, %d3
5:	moveq	#ACX, %d1
	moveq	#ACY, %d2
	moveq	#0, %d4
	bsr	centered
	moveq	#4, %d0
	cmp.l	%d0, %d6
	blt.s	6f
	moveq	#ACX, %d1
	moveq	#ACY, %d2
	moveq	#CORE, %d3
	moveq	#1, %d4
	bsr	centered

/* Le texte, une lettre toutes les deux images à partir de TYPE : n = (image - TYPE) / 2 + 1, au plus NLET. */
6:	move.l	%d7, %d0
	subi.l	#TYPE, %d0
	blt.s	9f
	lsr.l	#1, %d0
	addq.l	#1, %d0
	moveq	#NLET, %d1
	cmp.l	%d1, %d0
	ble.s	7f
	move.l	%d1, %d0
7:	lea	txt_end(%pc), %a0
	moveq	#0, %d5
	move.b	-1(%a0, %d0.l), %d5		/* colonnes à dessiner */
	lea	txt_cols(%pc), %a1
	moveq	#TX0, %d1			/* x */
8:	mvz.w	(%a1)+, %d2			/* bit TROWS-1 = la ligne du haut */
	moveq	#TY0, %d0			/* y */
	moveq	#TROWS, %d3
81:	btst	#TROWS-1, %d2
	beq.s	82f
	bsr	pset
82:	add.l	%d2, %d2
	addq.l	#1, %d0
	subq.l	#1, %d3
	bne.s	81b
	addq.l	#1, %d1
	subq.l	#1, %d5
	bne.s	8b

/* Attendre le tick, envoyer l'image. */
9:	pea	SEM_TICK
	jsr	SEM_WAIT
	addq.l	#4, %sp
	jsr	FLUSH
	addq.l	#1, %d7
	moveq	#NF, %d0
	cmp.l	%d0, %d7
	blt	frame

/* Fin, comme l'original (0x40053e34). */
	moveq	#10, %d2
10:	pea	SEM_TICK
	jsr	SEM_WAIT
	addq.l	#4, %sp
	subq.l	#1, %d2
	bne.s	10b
	pea	SEM_DONE
	jsr	SEM_POST1
	pea	TICK_CB
	jsr	TIMER_DEL
	addq.l	#8, %sp
11:	pea	SEM_TICK
	jsr	SEM_TAKE
	addq.l	#4, %sp
	bra.s	11b

/* pset : allume le pixel (d1 = x, d0 = y) du tampon a3. Détruit a0, d4 ; garde les autres. */
pset:
	move.l	%d1, %d4
	lsl.l	#3, %d4
	lea	0(%a3, %d4.l), %a0		/* la colonne : 8 o */
	move.l	%d0, %d4
	lsr.l	#3, %d4
	adda.l	%d4, %a0
	move.l	%d0, %d4
	not.l	%d4				/* bit 7 - (y & 7) : bset le prend modulo 8 */
	bset	%d4, (%a0)
	rts

/* centered : carré arrondi plein de côté d3 (pair), centré sur (d1, d2) ; d4 = 1 allume, 0 éteint.
 * Coins : 2 puis 1 pixel retirés à partir de 12 de côté, 1 pixel à partir de 5, aucun en dessous.
 * Détruit d0-d5, a0-a1 ; garde d6, d7. */
centered:
	tst.l	%d3
	ble	29f
	lea	-8(%sp), %sp
	movem.l	%d6-%d7, (%sp)
	move.l	%d3, %d0
	lsr.l	#1, %d0
	sub.l	%d0, %d1			/* x0 */
	sub.l	%d0, %d2			/* y0 */
	moveq	#0, %d5				/* i, la colonne dans le carré */
21:	cmp.l	%d3, %d5
	bge.s	28f
	move.l	%d3, %d0
	subq.l	#1, %d0
	sub.l	%d5, %d0			/* s - 1 - i */
	cmp.l	%d5, %d0
	ble.s	22f
	move.l	%d5, %d0			/* e = distance au bord le plus proche */
22:	moveq	#0, %d6				/* retrait du coin */
	cmpi.l	#12, %d3
	blt.s	23f
	moveq	#2, %d6
	sub.l	%d0, %d6
	bgt.s	24f
	moveq	#0, %d6
	bra.s	24f
23:	cmpi.l	#5, %d3
	blt.s	24f
	tst.l	%d0
	bne.s	24f
	moveq	#1, %d6
24:	move.l	%d1, %d0
	add.l	%d5, %d0
	lsl.l	#3, %d0
	lea	0(%a3, %d0.l), %a0		/* la colonne */
	move.l	%d2, %d0
	add.l	%d6, %d0			/* y = y0 + retrait */
	neg.l	%d6
	add.l	%d2, %d6
	add.l	%d3, %d6			/* fin = y0 + s - retrait */
25:	cmp.l	%d6, %d0
	bge.s	27f
	move.l	%d0, %d7
	lsr.l	#3, %d7
	lea	0(%a0, %d7.l), %a1
	move.l	%d0, %d7
	not.l	%d7
	tst.l	%d4
	beq.s	26f
	bset	%d7, (%a1)
	bra.s	261f
26:	bclr	%d7, (%a1)
261:	addq.l	#1, %d0
	bra.s	25b
27:	addq.l	#1, %d5
	bra.s	21b
28:	movem.l	(%sp), %d6-%d7
	lea	8(%sp), %sp
29:	rts

	.section .rodata.boot_anim, "a"
	.include "anim_data.inc"		/* sq_tab, grow, txt_end, txt_cols */
