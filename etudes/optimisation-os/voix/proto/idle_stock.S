/* Arrêt des voix muettes pour l'OS 1.13 d'origine (prototype, non versionné).
 *
 * Détour 1, 0x400a7dfe (cmp.l d4,d0 ; bcs.s 0x400a7e24 ; movea.l d6,a0 -> jmp gate) : avant update/render d'une
 * piste. Registres de la boucle des voix (0x400a7d4a) : d0 = 5 (borne des machines), d4 = machine de la voix,
 * d1 = modulation de note, d2 = piste, d3 = sortie de la piste (32 x int32, SRAM), d6 = table des update,
 * a2 = paramètres, fp = voix, a5 = voix + 0x34 (trig de ce bloc), a3 = voix + 0x38 (trig du bloc précédent).
 *   - machine hors borne : 0x400a7e24, comme l'OS ;
 *   - trig (+0x34 ou +0x38) : compteur de blocs faibles à 0, puis update/render tels quels (0x400a7e04 après
 *     l'instruction déplacée movea.l d6,a0) ;
 *   - compteur >= IDLE_N : voix pas calculée : sortie à zéro, +0x38 = +0x34 (0), et suite de la boucle en
 *     0x400a7e38 (la division par 2 de 32 zéros donne des zéros) ;
 *   - sinon : update/render tels quels.
 * Seuls d0, d1, a0, a1 sont modifiés, comme par le code d'origine (0x400a7e40 recharge d0, le haut de la boucle
 * recalcule d1, a0 et a1).
 *
 * Détour 2, 0x400a7e24 (move.l (a5),(a3) ; movea.l d3,a1 ; clr.l d0 -> jmp after) : après render. Rejoue la
 * copie +0x34 -> +0x38, divise la piste par 2 comme l'OS (asr.l #1, mêmes valeurs) et teste en même temps si
 * tous les échantillons divisés sont dans [-IDLE_T, IDLE_T[ : OU des (x + IDLE_T) < 2 IDLE_T en non signé
 * (IDLE_T puissance de 2). Faible : compteur + 1 (plafonné à IDLE_N) ; sinon compteur à 0. Suite en 0x400a7e38.
 * d2..d6 sont sauvés et rendus ; d0, d1, a0, a1 modifiés comme par la division d'origine.
 */
	.equ	VL_RUN,   0x400a7e04
	.equ	VL_AFTER, 0x400a7e24
	.equ	VL_NEXT,  0x400a7e38

	.text
	.globl	gate
gate:
	cmp.l	%d4, %d0
	bcs.s	9f			/* machine hors borne : comme l'OS */
	lea	QUIET(%pc), %a0
	move.l	(%a5), %d0
	or.l	(%a3), %d0
	bne.s	2f			/* trig : la voix repart */
	move.b	(%a0,%d2.l), %d0	/* d0 = 0 avant : compteur sur 8 bits */
	cmpi.l	#IDLE_N, %d0		/* d1 (modulation de note) doit rester intact pour update */
	bcc.s	3f			/* muette depuis IDLE_N blocs : pas calculée */
1:	movea.l	%d6, %a0		/* instruction déplacée */
	jmp	VL_RUN
2:	clr.b	(%a0,%d2.l)
	bra.s	1b
3:	move.l	(%a5), (%a3)		/* +0x38 = +0x34, comme 0x400a7e24 */
	movea.l	%d3, %a0
	moveq	#3, %d1
4:	clr.l	(%a0)+
	clr.l	(%a0)+
	clr.l	(%a0)+
	clr.l	(%a0)+
	clr.l	(%a0)+
	clr.l	(%a0)+
	clr.l	(%a0)+
	clr.l	(%a0)+
	subq.l	#1, %d1
	bpl.s	4b
	jmp	VL_NEXT
9:	jmp	VL_AFTER

	.globl	after
after:
	move.l	(%a5), (%a3)		/* instructions déplacées */
	movea.l	%d3, %a1
	lea	-20(%sp), %sp
	movem.l	%d2-%d6, (%sp)
	moveq	#0, %d0			/* OU des (x/2 + IDLE_T) */
	move.l	#IDLE_T, %d6
	moveq	#7, %d1
5:	movem.l	(%a1), %d2-%d5
	asr.l	#1, %d2
	asr.l	#1, %d3
	asr.l	#1, %d4
	asr.l	#1, %d5
	movem.l	%d2-%d5, (%a1)
	add.l	%d6, %d2
	or.l	%d2, %d0
	add.l	%d6, %d3
	or.l	%d3, %d0
	add.l	%d6, %d4
	or.l	%d4, %d0
	add.l	%d6, %d5
	or.l	%d5, %d0
	lea	16(%a1), %a1
	subq.l	#1, %d1
	bpl.s	5b
	move.l	(%sp), %d2		/* piste */
	lea	QUIET(%pc), %a0
	add.l	%d6, %d6		/* 2 IDLE_T */
	cmp.l	%d6, %d0
	bcs.s	6f
	clr.b	(%a0,%d2.l)		/* la voix sonne */
	bra.s	7f
6:	move.b	(%a0,%d2.l), %d1	/* d1 = 0xffffffff ici : on le refait */
	andi.l	#0xff, %d1
	moveq	#IDLE_N, %d0
	cmp.l	%d0, %d1
	bcc.s	7f
	addq.l	#1, %d1
	move.b	%d1, (%a0,%d2.l)
7:	movem.l	(%sp), %d2-%d6
	lea	20(%sp), %sp
	jmp	VL_NEXT

	.balign	4

QUIET:	.byte	0, 0, 0, 0, 0, 0, 0, 0	/* blocs faibles de chaque piste (à zéro au démarrage : image) */
