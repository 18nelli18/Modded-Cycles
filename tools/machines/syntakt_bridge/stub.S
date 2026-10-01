/* Crochet de demarrage (notes/17) : au debut de 0x400004b2 (remise a zero du BSS de l'OS Cycles),
 * recopie la charge utile ajoutee a la fin de l'image (section 3 agrandie) vers 0x43000000, au-dessus
 * du BSS, puis refait les deux instructions deplacees et reprend a 0x400004ba.
 * PAYLOAD_SRC, PAYLOAD_DST et PAYLOAD_LONGS sont fournis par tools/gen_sdvintage_exact.py (-D) ; SRAM_RUN_AT et
 * SRAM_LONGS par tools/gen_syntakt_engines.py. */
	.text
	.globl	boot_stub
boot_stub:
	lea	PAYLOAD_SRC, %a0
	lea	PAYLOAD_DST, %a1
	move.l	#PAYLOAD_LONGS, %d0
1:	move.l	(%a0)+, (%a1)+
	subq.l	#1, %d0
	bne.s	1b
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
	lea	-16(%sp), %sp		/* instructions deplacees de 0x400004b2 */
	movem.l	%d4-%d7, (%sp)
	jmp	0x400004ba
