| Décompression aPLib dérivée de syntakt_bridge/stub.S, MIT.
| drumkilla/mtlib et Marcel Bierling ; mêmes règles Elektron.
| a0=flux, a1=destination ; d0/d2-d4/d6/a2 volatils.
    .section .text.ml_depack,"ax"
    .globl ml_depack
ml_depack:
    moveq #1,%d4
    moveq #0,%d6
10:	bsr.s	50f
	beq.s	11f
	move.b	(%a0)+, (%a1)+		/* litteral */
	bra.s	10b
11:	bsr.s	60f			/* correspondance : gamma -> d3 */
	moveq	#2, %d0
	cmp.l	%d0, %d3
	beq.s	12f			/* meme decalage que la precedente */
	lsl.l	#8, %d3
	moveq	#0, %d0
	move.b	(%a0)+, %d0
	add.l	%d0, %d3
	subi.l	#767, %d3		/* OFFSET_BIAS ; 0 : fin du flux */
	beq.s	19f
	move.l	%d3, %d4
12:	bsr.s	50f			/* longueur : 2 bits, ou gamma + 2 s'ils sont nuls */
	move.l	%d0, %d2
	add.l	%d2, %d2
	bsr.s	50f
	add.l	%d0, %d2
	bne.s	13f
	bsr.s	60f
	move.l	%d3, %d2
	addq.l	#2, %d2
13:	cmpi.l	#3328, %d4		/* FAR_THRESHOLD : une de plus au-dela */
	bls.s	14f
	addq.l	#1, %d2
14:	addq.l	#1, %d2
	movea.l	%a1, %a2
	suba.l	%d4, %a2
15:	move.b	(%a2)+, (%a1)+		/* octet par octet : la source peut chevaucher la destination */
	subq.l	#1, %d2
	bne.s	15b
	bra.s	10b
50:	add.l	%d6, %d6		/* un bit -> d0 (0 ou 1), Z s'il est nul */
	move.l	%d6, %d0
	andi.l	#0xff, %d0
	bne.s	51f
	moveq	#0, %d6
	move.b	(%a0)+, %d6
	add.l	%d6, %d6
	addq.l	#1, %d6
51:	move.l	%d6, %d0
	lsr.l	#8, %d0
	andi.l	#1, %d0
	rts
60:	moveq	#1, %d3			/* gamma d'Elias entrelace -> d3 */
61:	bsr.s	50b
	add.l	%d3, %d3
	add.l	%d0, %d3
	bsr.s	50b
	beq.s	61b
	rts
19:	rts
