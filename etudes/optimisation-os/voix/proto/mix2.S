/* mix2 (0x400a9884) : la 1re boucle (0x400a98c4..0x400a9902) calcule le mélange dans la sortie, puis la 2e boucle
 * (0x400a991c..) le recalcule et l'écrase ; de la 1re ne reste que l'effet sur les gains (32 fois += pas).
 * Remplacée, à sa place (64 o, 0x400a98c4..0x400a9904), par ce seul effet : g0 += pas0 << 5, g1 += pas1 << 5
 * (mêmes valeurs modulo 2^32), et acc0 remis à zéro comme après la 1re boucle.
 * Registres : d3 = pas0, d4 = pas1, a1 = (i0, i1), a0 = voix ; d0, d1 écrasés ensuite par 0x400a9904.. */
start:
	move.l	(%a1), %d1
	move.l	%d3, %d0
	lsl.l	#5, %d0
	add.l	%d0, (24,%a0,%d1.l*4)
	move.l	4(%a1), %d1
	move.l	%d4, %d0
	lsl.l	#5, %d0
	add.l	%d0, (24,%a0,%d1.l*4)
	movclr.l %acc0, %d0
	bra.w	fin
	.org	0x40, 0x4e
fin:
