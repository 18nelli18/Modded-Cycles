| Prototype 2 : routines communes au sommeil du delay et de la reverb (fx_dly.S, fx_rev.S).
| Écrit pour l'étude optim/sortie (émulation seulement). Masque 48x22 libre 0x401592bc (REGISTRY.md §1).

	.text
| zscan : %a0 = début, %d1 = nombre de mots (> 0). Rend Z = 1 si tous sont nuls. Détruit %d0, %d1, %a0.
	.globl	zscan
zscan:
	moveq	#0,%d0
1:	subq.l	#8,%d1
	bmi.s	3f
	or.l	(%a0)+,%d0
	or.l	(%a0)+,%d0
	or.l	(%a0)+,%d0
	or.l	(%a0)+,%d0
	or.l	(%a0)+,%d0
	or.l	(%a0)+,%d0
	or.l	(%a0)+,%d0
	or.l	(%a0)+,%d0
	beq.s	1b
	rts				| Z = 0
3:	addq.l	#8,%d1
	beq.s	8f
4:	or.l	(%a0)+,%d0
	subq.l	#1,%d1
	bne.s	4b
8:	tst.l	%d0
	rts

| zfill : %a0 = début, %d1 = nombre de blocs de 32 o (> 0) mis à zéro. Détruit %d0-%d7, %a1 ; %a0 pointe après.
	.globl	zfill
zfill:
	moveq	#0,%d0
	moveq	#0,%d2
	moveq	#0,%d3
	moveq	#0,%d4
	moveq	#0,%d5
	moveq	#0,%d6
	moveq	#0,%d7
	movea.l	%d0,%a1
1:	movem.l	%d0/%d2-%d7/%a1,(%a0)
	lea	32(%a0),%a0
	subq.l	#1,%d1
	bne.s	1b
	rts
