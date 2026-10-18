| OS optimisé (notes/70), reverb : sommeil exact de la reverb (0x400579c4) quand tout ce qu'elle lit est nul.
| Masque 41x41 libéré 0x4018d918 (tools/gen_os_optimise.py).
|
| Détour R1 en 0x40057ac8 (fin du prologue : coefficients, b510, a4fc déjà posés ; acc0..acc3 nuls, aucun registre
| vivant) : si l'entrée, les états (a2d0, a47c, a4c8) et les 17 tampons lus par l'eDMA sont nuls, le calcul du son
| rendrait des zéros partout ; on écrit ces zéros (sortie, temporaires) et on saute au calcul de la modulation
| 0x40057d72, gardé tel quel. Détour R2 en 0x40057dc6 (après la modulation) : en sommeil, on va à l'épilogue.
| Repère du sommeil : le mot de pile sp@(48), mort après 0x40057a82. ZSCAN, ZFILL : fx_lib.S.

	.equ	MAGIC, 0x534c5050

	.text
	.globl	rz_check
rz_check:
	lea	tab,%a2
	move.l	#0x80000000,%d3
	moveq	#(tab_end-tab)/4,%d2
1:	move.w	(%a2)+,%d3		| d3 = 0x8000xxxx
	movea.l	%d3,%a0
	moveq	#0,%d1
	move.w	(%a2)+,%d1
	jsr	ZSCAN
	bne.w	rz_wake
	subq.l	#1,%d2
	bne.s	1b
	movea.l	60(%sp),%a0		| entrée (0x8000b990)
	moveq	#64,%d1
	jsr	ZSCAN
	bne.w	rz_wake
| --- sommeil : ce que le calcul aurait écrit (zéros) ---
	movea.l	56(%sp),%a0		| sortie (64 mots)
	moveq	#8,%d1
	jsr	ZFILL
	lea	0x8000a1d0,%a0		| temporaires a1d0..a3d0 (128 mots ; a2d0..a350 est un état, déjà nul)
	moveq	#16,%d1
	jsr	ZFILL
	lea	0x8000a3f8,%a0		| a3f8 (écrit à 0 par l'OS) et temporaire a3fc..a47c (32 mots)
	clr.l	(%a0)+
	moveq	#4,%d1
	jsr	ZFILL
	lea	0x8000afdc,%a0		| mots écrits à 0 juste avant chaque tampon des lignes courtes
	moveq	#8,%d1
5:	clr.l	(%a0)
	lea	160(%a0),%a0
	subq.l	#1,%d1
	bne.s	5b
	move.l	#MAGIC,%d0
	move.l	%d0,48(%sp)
	jmp	0x40057d72		| modulation (code de l'OS), puis R2

rz_wake:
	clr.l	48(%sp)
	movea.l	#0x8000a9b0,%a5		| instruction remplacée (0x40057ac8)
	jmp	0x40057ace

	.globl	rz_mod
rz_mod:
	move.l	48(%sp),%d0
	cmpi.l	#MAGIC,%d0
	beq.s	1f
	movea.l	#0x8000ad20,%a0		| instruction remplacée (0x40057dc6)
	jmp	0x40057dcc
1:
	.globl	rz_slept
rz_slept:
	clr.l	48(%sp)
	jmp	0x40057f9e		| épilogue de la reverb

| Ce que la reverb lit (outre l'entrée) : (adresse & 0xffff, mots). Fenêtres toujours remplies par l'eDMA.
	.align	2
tab:
	.word	0xa2d0, 32		| états
	.word	0xa47c, 16
	.word	0xa4c8, 2
	.word	0xa9b0+176*0, 33	| lignes longues (0x4a340000 + k*64 Ko)
	.word	0xa9b0+176*1, 33
	.word	0xa9b0+176*2, 33
	.word	0xa9b0+176*3, 33
	.word	0xa9b0+176*4, 37	| modulée (a50c)
	.word	0xa9b0+176*5, 33
	.word	0xa9b0+176*6, 33
	.word	0xa9b0+176*7, 33
	.word	0xa9b0+176*8, 37	| modulée (a51c)
	.word	0xafe0+160*0, 33	| lignes courtes (0x4a3d0000 + k*4 Ko)
	.word	0xafe0+160*1, 33
	.word	0xafe0+160*2, 33
	.word	0xafe0+160*3, 33
	.word	0xafe0+160*4, 33
	.word	0xafe0+160*5, 33
	.word	0xafe0+160*6, 33
	.word	0xafe0+160*7, 33
tab_end:
