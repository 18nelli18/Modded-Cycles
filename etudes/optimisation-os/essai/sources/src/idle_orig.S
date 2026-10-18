/* Compteur de temps libre (prototype, émulation seulement) : remplace la boucle d'attente de la tâche de
   priorité 0 (0x4000543a : lea 24(sp),sp ; bra.s .) par une boucle qui lit le minuteur DMA 0 (135,168 MHz,
   compteur libre) et cumule les écarts courts (< SEUIL cycles de bus) : le temps où le processeur n'avait rien
   d'autre à faire. Un écart long = la tâche a été interrompue (interruption ou tâche plus prioritaire) : non compté.
   Registres d0-d2 : sauvés par le changement de contexte (0x4000041e : moveml d0-sp). */
	.equ	DTIM0, 0xfc07000c
	.equ	SEUIL, 128
	.text
	.globl	idle
idle:
	lea	24(%sp),%sp		/* ce que faisait l'original */
	move.l	DTIM0,%d1
1:	move.l	DTIM0,%d0
	move.l	%d0,%d2
	sub.l	%d1,%d2
	move.l	%d0,%d1
	cmp.l	#SEUIL,%d2
	bhi.s	2f
	add.l	%d2,idle_acc
2:	bra.s	1b
	.balign	4
	.globl	idle_acc
idle_acc:
	.long	0
