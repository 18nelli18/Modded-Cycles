| Compteur de charge des deux fichiers d'essai (référence et optimisé) : le MÊME code, à la MÊME place, dans les
| deux, pour que l'écart mesuré soit celui des optimisations. Firmware d'essai, pas une carte du flasher.
| Deux masques libres (REGISTRY.md §1), chacun redirigé par sprites.redirect_write : section .m1 (entrée,
| sonde, variables) et .m2 (affichage, boucle d'attente). Assemblé par gen_essai.py (m68k-linux-gnu-as
| -mcpu=54418, sections liées aux adresses des masques).
|
| Chronomètre : minuteur DMA 0 (0xfc07000c, 135,168 MHz, compteur libre ; un bloc = 90 112 ticks, notes/23 §5).
|
| 1. m_entry, détour de l'ENTRÉE de l'interruption de rendu 0x40058c5e (linkw %fp,#-168 ; moveml %d0-%a5,%sp@,
|    8 o -> jmp m_entry ; nop) : note l'heure d'entrée (m_t0), puis refait les deux instructions et rejoint
|    0x40058c66. d0 est rendu tel quel avant la sauvegarde des registres ; seule la pile au-dessous de sp sert.
| 2. m_probe, à la place de l'appel de la fonction audio (0x40059382 : jsr 0x4005979e -> jsr m_probe) : met de
|    côté l'adresse de retour (la fonction voit la pile d'un jsr direct), appelle 0x4005979e, lit l'heure de fin.
|    Durée = fin - m_t0 (de l'entrée de l'interruption à la fin de la fonction audio) ; période = m_t0 - m_t0 du
|    bloc précédent. Toutes les 750 blocs (0,5 s), m_show écrit « pic/moyenne/libre » en % (99 au plus) dans
|    m_name :
|      pic     = max sur la fenêtre de durée x 100 / période ;
|      moyenne = somme des durées / (somme des périodes / 100) ;
|      libre   = temps compté par la boucle d'attente (idle_acc) sur la fenêtre / (somme des périodes / 100).
|    Contrat : d0, d1, a0, a1 détruits (comme par tout appel C ; l'interruption ne les relit pas après
|    0x40059388) ; d2-d5 sauvés et rendus ; d6, d7, a2-a6 non touchés.
| 3. m_idle_loop, à la place de la boucle d'attente de la tâche de priorité 0 (0x4000543a : lea 24(%sp),%sp ;
|    bra.s . -> jmp m_idle_loop) : le compteur de temps libre de l'étude « système » (optim/systeme/proto/idle.S,
|    prouvé en émulation) : cumule les écarts courts (< 128 ticks) du minuteur ; un écart long = la tâche a été
|    interrompue, non compté. d0-d2 sont sauvés par le changement de contexte (0x4000041e).
| Les 6 noms de machines de l'écran MACHINES (table 0x401177e4, lue seulement par 0x400a2612) pointent sur
| m_name (« --/--/-- » au départ). L'interruption de rendu n'est pas réentrante (même niveau) : m_ret seul suffit.

	.equ	DTIM0,    0xfc07000c
	.equ	AUDIO,    0x4005979e
	.equ	ISR_NEXT, 0x40058c66
	.equ	NBLK,     750
	.equ	MAXPER,   1802240		| 20 blocs : au-delà (ou premier bloc), la fenêtre repart de zéro
	.equ	SEUIL,    128
| variables (d16 depuis V, pointé par %a1 dans la sonde)
	.equ	T0,   0
	.equ	LAST, 4
	.equ	RET,  8
	.equ	N,    12
	.equ	PER,  16
	.equ	DUR,  20
	.equ	MAX,  24
	.equ	IDLE, 28
	.equ	ACC,  32
	.equ	NAME, 36

	.section .m1,"ax"
	.globl	m_entry
m_entry:
	move.l	%d0,-(%sp)
	move.l	DTIM0,%d0
	move.l	%d0,V+T0
	move.l	(%sp)+,%d0
	link.w	%fp,#-168		| instructions déplacées (0x40058c5e, 0x40058c62)
	movem.l	%d0-%d7/%a0-%a5,(%sp)
	jmp	ISR_NEXT

	.globl	m_probe
m_probe:
	move.l	(%sp)+,V+RET
	jsr	AUDIO
	move.l	DTIM0,%d1		| fin du bloc
	lea	-16(%sp),%sp
	movem.l	%d2-%d5,(%sp)
	lea	V,%a1
	move.l	T0(%a1),%d0
	sub.l	%d0,%d1			| d1 = durée
	move.l	LAST(%a1),%d2
	move.l	%d0,LAST(%a1)
	tst.l	%d2
	beq.s	m_reset			| premier bloc
	sub.l	%d2,%d0			| d0 = période
	beq.s	m_reset
	cmpi.l	#MAXPER,%d0
	bhi.s	m_reset			| pause
	cmpi.l	#MAXPER,%d1
	bls.s	1f
	move.l	#MAXPER,%d1		| borne (pas de débordement de x 100)
1:	add.l	%d0,PER(%a1)
	add.l	%d1,DUR(%a1)
	moveq	#100,%d2
	mulu.l	%d2,%d1
	divu.l	%d0,%d1			| % de la période
	cmp.l	MAX(%a1),%d1
	bls.s	2f
	move.l	%d1,MAX(%a1)
2:	addq.l	#1,N(%a1)
	move.l	N(%a1),%d2
	cmpi.l	#NBLK,%d2
	bcs.s	m_out
	jsr	m_show			| toutes les NBLK blocs
m_reset:
	moveq	#0,%d0
	move.l	%d0,N(%a1)
	move.l	%d0,PER(%a1)
	move.l	%d0,DUR(%a1)
	move.l	%d0,MAX(%a1)
	move.l	ACC(%a1),IDLE(%a1)
m_out:
	movem.l	(%sp),%d2-%d5
	lea	16(%sp),%sp
	move.l	V+RET,-(%sp)
	rts

	.balign	4
	.globl	V, idle_acc, m_name
V:	.long	0, 0, 0, 0, 0, 0, 0, 0	| T0, LAST, RET, N, PER, DUR, MAX, IDLE
idle_acc:
	.long	0			| ACC
m_name:	.asciz	"--/--/--"		| NAME
	.balign	4

	.section .m2,"ax"
| m_show : %a1 = V. Écrit « pic/moyenne/libre » dans m_name. Détruit d0-d5, a0 (d2-d5 sauvés par la sonde).
	.globl	m_show
m_show:
	move.l	PER(%a1),%d3
	moveq	#100,%d2
	divu.l	%d2,%d3			| centième de la fenêtre
	beq.s	9f
	move.l	DUR(%a1),%d4
	divu.l	%d3,%d4			| moyenne
	move.l	ACC(%a1),%d5
	sub.l	IDLE(%a1),%d5
	divu.l	%d3,%d5			| libre
	lea	NAME(%a1),%a0
	move.l	MAX(%a1),%d0
	bsr.s	put2
	moveq	#47,%d1			| '/'
	move.b	%d1,(%a0)+
	move.l	%d4,%d0
	bsr.s	put2
	moveq	#47,%d1
	move.b	%d1,(%a0)+
	move.l	%d5,%d0
	bsr.s	put2
	clr.b	(%a0)
9:	rts

| put2 : d0 -> 1 ou 2 chiffres en (a0)+ (borné à 99), comme put2 de bridge_engines.c ; détruit d0, d1
put2:
	moveq	#99,%d1
	cmp.l	%d1,%d0
	bls.s	1f
	move.l	%d1,%d0
1:	moveq	#0,%d1
2:	cmpi.l	#10,%d0
	bcs.s	3f
	subi.l	#10,%d0
	addq.l	#1,%d1
	bra.s	2b
3:	tst.l	%d1
	beq.s	4f
	addi.l	#48,%d1
	move.b	%d1,(%a0)+
4:	addi.l	#48,%d0
	move.b	%d0,(%a0)+
	rts

	.globl	m_idle_loop
m_idle_loop:
	lea	24(%sp),%sp		| ce que faisait l'original
	move.l	DTIM0,%d1
1:	move.l	DTIM0,%d0
	move.l	%d0,%d2
	sub.l	%d1,%d2
	move.l	%d0,%d1
	cmpi.l	#SEUIL,%d2
	bhi.s	2f
	add.l	%d2,idle_acc
2:	bra.s	1b
