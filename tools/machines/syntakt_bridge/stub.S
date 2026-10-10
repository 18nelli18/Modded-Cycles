/* Crochet de demarrage (notes/17) : au debut de 0x400004b2 (remise a zero du BSS de l'OS Cycles),
 * recopie la charge utile ajoutee a la fin de l'image (section 3 agrandie) vers 0x43000000, au-dessus
 * du BSS, puis refait les deux instructions deplacees et reprend a 0x400004ba.
 * PAYLOAD_SRC, PAYLOAD_DST et PAYLOAD_LONGS sont fournis par tools/gen_sdvintage_exact.py (-D) ; SRAM_RUN_AT et
 * SRAM_LONGS par tools/gen_syntakt_engines.py. PACK sans CHAIN_TO : machine MACRO seule (tools/gen_macro.py). */
	.text
	.globl	boot_stub
boot_stub:
#ifdef PACK
	/* avec Model-TG (notes/31), et pour la machine MACRO (notes/43) : la charge utile est rangee en morceaux
	 * (segs.inc : adresse, mots) ; tout a zero, puis chaque morceau a sa place. Seuls d0, d1, a0 et a1 servent.
	 * Avec Model-TG : appele par le jsr de 0x40000530, a la place de boot_extra_hook, ou l'on finit (CHAIN_TO). */
	lea	PAYLOAD_DST, %a1
	move.l	#PAYLOAD_LONGS, %d0
0:	clr.l	(%a1)+
	subq.l	#1, %d0
	bne.s	0b
	lea	PAYLOAD_SRC, %a0
	lea	segs, %a1
	move.l	%a1, %d1
4:	movea.l	%d1, %a1
	move.l	4(%a1), %d0
	beq.s	6f
	movea.l	(%a1), %a1
	addq.l	#8, %d1
5:	move.l	(%a0)+, (%a1)+
	subq.l	#1, %d0
	bne.s	5b
	bra.s	4b
6:
#else
	lea	PAYLOAD_SRC, %a0
	lea	PAYLOAD_DST, %a1
	move.l	#PAYLOAD_LONGS, %d0
1:	move.l	(%a0)+, (%a1)+
	subq.l	#1, %d0
	bne.s	1b
#endif
#ifdef SRAM_RUN_AT
	/* gen_syntakt_engines.py (notes/28) : le debut de la charge utile (code et tables du Syntakt) passe en SRAM
	 * interne, a la place des tables d'ondes de CHORD, apres l'initialisation de la SRAM par l'OS (0x4000045c) */
	lea	PAYLOAD_DST, %a0
	lea	SRAM_RUN_AT, %a1
	move.l	#SRAM_LONGS, %d0
2:	move.l	(%a0)+, (%a1)+
	subq.l	#1, %d0
	bne.s	2b
#endif
#ifdef SRAM2_RUN_AT
	/* puis, a la suite dans la charge utile, la 2e zone (etats des voix du Syntakt, notes/29) */
	lea	SRAM2_RUN_AT, %a1
	move.l	#SRAM2_LONGS, %d0
3:	move.l	(%a0)+, (%a1)+
	subq.l	#1, %d0
	bne.s	3b
#endif
#ifdef CHAIN_TO
	jmp	CHAIN_TO		/* boot_extra_hook de Model-TG (ACR1, remise a zero du BSS sauf son bloc) */
#else
	lea	-16(%sp), %sp		/* instructions deplacees de 0x400004b2 */
	movem.l	%d4-%d7, (%sp)
	jmp	0x400004ba
#endif
#ifdef PACK
	.align	2
segs:
#include "segs.inc"
	.long	0, 0
#endif
