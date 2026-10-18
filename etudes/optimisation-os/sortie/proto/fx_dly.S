| Prototype 2, delay : sommeil exact du delay (0x40057488) quand tout ce qu'il lit est nul.
| Écrit pour l'étude optim/sortie (émulation seulement). Placé dans le masque 34x34 libre 0x40185f48 (REGISTRY.md §1).
| ZSCAN, ZFILL (définis à l'assemblage) : fx_lib.S.
|
| Détour en 0x40057516 (après le prologue : b7c8, b7cc, b7d0, b7d4, b7d8 posés ; acc0 vidé). Vivants : d3, d6, d7,
| a4, a5, fp. Libres : d0, d1, d2, d4, d5, a0..a3. Le calcul accumule sur acc1..acc3 : ils doivent être nuls.
| Sommeil si acc1..3, l'état du filtre (b8dc, 4 mots), l'entrée (64 mots) et les deux prises lues par l'eDMA
| (65 mots chacune, depuis *0x8000b570 et +272) sont nuls. Alors le calcul aurait rendu : sortie = 0, temporaire
| b7dc = 0, tampon d'écriture (= prise A) = 0, b8dc = 0, gains a100 avancés de 32 pas, MACSR = 0xa0, acc = 0.

	.equ	CSR30, 0xfc0453de

	.text
	.globl	dz_check
dz_check:
	move.l	%acc1,%d0
	move.l	%acc2,%d1
	or.l	%d1,%d0
	move.l	%acc3,%d1
	or.l	%d1,%d0
	lea	0x8000b8dc,%a0
	or.l	(%a0)+,%d0
	or.l	(%a0)+,%d0
	or.l	(%a0)+,%d0
	or.l	(%a0)+,%d0
	bne.s	dz_wake
	movea.l	56(%sp),%a0		| entrée
	moveq	#64,%d1
	jsr	ZSCAN
	bne.s	dz_wake
	movea.l	0x8000b570,%a0		| prise A
	moveq	#65,%d1
	jsr	ZSCAN
	bne.s	dz_wake
	movea.l	0x8000b570,%a0		| prise B
	lea	272(%a0),%a0
	moveq	#65,%d1
	jsr	ZSCAN
	beq.s	dz_sleep
dz_wake:
	move.l	%d3,-(%sp)		| instructions remplacées (0x40057516..0x4005751b)
	move.l	%a5,%d3
	asr.l	#5,%d3
	jmp	0x4005751c

dz_sleep:
	movea.l	52(%sp),%a0		| sortie (64 mots)
	moveq	#8,%d1
	jsr	ZFILL
	lea	0x8000b7dc,%a0		| temporaire (64 mots)
	moveq	#8,%d1
	jsr	ZFILL
| gains a100 : 32 fois x += (cible - x) >> 5, soit x += (cible - x) & ~31 (modulo 2^32)
	lea	0x8000a100,%a0
	movem.l	(%a0),%d0-%d3
	move.l	#0x7ffffffe,%d4
	sub.l	%d0,%d4
	andi.l	#-32,%d4
	add.l	%d4,%d0
	moveq	#0,%d4
	sub.l	%d1,%d4
	andi.l	#-32,%d4
	add.l	%d4,%d1
	moveq	#0,%d4
	sub.l	%d2,%d4
	andi.l	#-32,%d4
	add.l	%d4,%d2
	move.l	#0x7fffffff,%d4
	sub.l	%d3,%d4
	andi.l	#-32,%d4
	add.l	%d4,%d3
	movem.l	%d0-%d3,(%a0)
	move.l	#0xa0,%macsr
| la reverb lit des tampons que l'eDMA (canal 30) remplit encore : le calcul du delay sauté ne lui laisse plus ce
| temps, on attend la fin de la chaîne (DONE), au plus 4096 lectures.
	move.l	#4096,%d1
1:	move.w	CSR30,%d0
	andi.l	#0x80,%d0
	bne.s	2f
	subq.l	#1,%d1
	bne.s	1b
2:	jmp	0x40057704		| épilogue du delay
