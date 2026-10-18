| OS optimisé (notes/70) : envois delay et reverb (0x40056716 : 6 entrées, 0x40056698 : 7 entrées) sautés quand leurs
| gains et leurs pentes sont tous nuls (envois à 0).
| Masque 48x22 libéré 0x40170c48 (tools/gen_os_optimise.py). Détours à l'entrée des deux routines (8 o chacun).
|
| La routine fait, pour chacune des 32 trames : acc0 -= somme(g_t * x_t) ; sortie[2i] = acc0 (movclr) ; g_t += pente_t.
| Gains et pentes nuls, acc0 nul : chaque sortie vaut 0, les gains ne bougent pas, acc0 reste nul.
| Pile à l'entrée : 4 sortie (un mot sur deux), 8 entrées, 12 gains, 16 pentes.

	.text
	.globl	s6_check
s6_check:
	move.l	%acc0,%d0
	movea.l	12(%sp),%a0
	or.l	(%a0)+,%d0
	or.l	(%a0)+,%d0
	or.l	(%a0)+,%d0
	or.l	(%a0)+,%d0
	or.l	(%a0)+,%d0
	or.l	(%a0)+,%d0
	movea.l	16(%sp),%a0
	or.l	(%a0)+,%d0
	or.l	(%a0)+,%d0
	or.l	(%a0)+,%d0
	or.l	(%a0)+,%d0
	or.l	(%a0)+,%d0
	or.l	(%a0)+,%d0
	beq.s	zero_out
	lea	-32(%sp),%sp		| instructions remplacées (0x40056716)
	movem.l	%d2-%d7/%a2-%a3,(%sp)
	jmp	0x4005671e

	.globl	s7_check
s7_check:
	move.l	%acc0,%d0
	movea.l	12(%sp),%a0
	or.l	(%a0)+,%d0
	or.l	(%a0)+,%d0
	or.l	(%a0)+,%d0
	or.l	(%a0)+,%d0
	or.l	(%a0)+,%d0
	or.l	(%a0)+,%d0
	or.l	(%a0)+,%d0
	movea.l	16(%sp),%a0
	or.l	(%a0)+,%d0
	or.l	(%a0)+,%d0
	or.l	(%a0)+,%d0
	or.l	(%a0)+,%d0
	or.l	(%a0)+,%d0
	or.l	(%a0)+,%d0
	or.l	(%a0)+,%d0
	beq.s	zero_out
	lea	-40(%sp),%sp		| instructions remplacées (0x40056698)
	movem.l	%d2-%d7/%a2-%a5,(%sp)
	jmp	0x400566a0

zero_out:				| %d0 = 0 : sortie[0], [2], ... [62] = 0
	movea.l	4(%sp),%a0
	moveq	#8,%d1
1:	move.l	%d0,(%a0)
	move.l	%d0,8(%a0)
	move.l	%d0,16(%a0)
	move.l	%d0,24(%a0)
	lea	32(%a0),%a0
	subq.l	#1,%d1
	bne.s	1b
	rts
