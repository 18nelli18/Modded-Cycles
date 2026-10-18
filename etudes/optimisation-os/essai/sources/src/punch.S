/* PUNCH (0x400a967a) : quand PUNCH est éteint, l'enveloppe est constante (pas d5 = 0) et le gain « x4 saturé »
 * vaut 4 x 0x20000000 = 1 exactement (d6 = 0x20000000) : chaque échantillon devient y = c * x avec c = a2 * d7.
 * Détour en 0x400a9714 (move.l 676(a0),d7 ; move.l (a3),d1 -> jmp pstub). Le 1er échantillon est calculé par les
 * instructions d'origine (accumulateurs tels qu'en entrée), les 31 autres par MAC avec chargement (5 instructions
 * au lieu de 13). Sinon : boucle d'origine (0x400a971c). Sortie en 0x400a9744 (d4, a1 intacts). */
	.equ	P_LOOP, 0x400a971c
	.equ	P_END,  0x400a9744
	.text
pstub:
	move.l	676(%a0), %d7		/* instructions déplacées */
	move.l	(%a3), %d1
	moveq	#32, %d0		/* 0x400a971a */
	tst.l	%d5
	bne.s	9f
	cmpi.l	#0x20000000, %d6
	bne.s	9f
	mac.l	%a2, %d7, %acc1		/* 1er échantillon : le corps d'origine */
	mac.l	%d6, %d1, %acc0
	mac.l	%d6, %d1, %acc0
	mac.l	%d6, %d1, %acc0
	mac.l	%d6, %d1, 4(%a3), %d1, %acc0
	movclr.l %acc1, %d2
	movclr.l %acc0, %d3
	mac.l	%d2, %d3, %acc0
	movclr.l %acc0, %d2
	move.l	%d2, (%a3)+
	mac.l	%a2, %d7, %acc1		/* c, accumulateur vide (comme aux 31 tours suivants d'origine) */
	movclr.l %acc1, %d2
	moveq	#30, %d0
1:	mac.l	%d2, %d1, 4(%a3), %d1, %acc0
	movclr.l %acc0, %d3
	move.l	%d3, (%a3)+
	subq.l	#1, %d0
	bpl.s	1b
	jmp	P_END
9:	jmp	P_LOOP
