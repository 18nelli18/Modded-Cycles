/* Code chaud en SRAM (notes/76) : l'appel du calcul audio, le cache d'instructions, les talons des detours.
 * Points d'entree a adresse fixe (tools/gen_sram_hot.py, ENTRY) : hot_boot au debut du code, hot_probe 6 o plus
 * loin ; le tweak des moteurs les vise avant que le chargeur soit compile. */
	.text
	.globl	hot_boot
hot_boot:
	jmp	hot_init		/* hot.c, appele par le 2e etage du crochet de demarrage (stub.S, BOOT2) */

/* a la place de l'appel de la passerelle en 0x40059382 (jsr 0x467337fc) : le chargeur (hot_step), puis la
 * passerelle, ou sa copie en SRAM, puis hot_after. La passerelle et la fonction audio lisent leur argument comme
 * si 0x40059382 les appelait : l'adresse de retour de l'interruption est mise de cote (comme le fait la
 * passerelle). d0 (rendu par la fonction audio) est garde. */
	.globl	hot_probe
hot_probe:
	move.l	(%sp)+, hot_ret
	jsr	hot_step
	movea.l	%d0, %a0
	jsr	(%a0)
	move.l	%d0, -(%sp)
	jsr	hot_after
	move.l	(%sp)+, %d0
	move.l	hot_ret, -(%sp)
	rts

/* apres les detours ecrits au demarrage : le cache d'instructions, laisse actif par le bootstrap, peut tenir les
 * anciennes entrees. Meme valeur que le crochet de demarrage (stub.S, AFTER) : ICINVA + BCINVA. */
	.globl	hot_icinv
hot_icinv:
	nop
	move.l	#0x000cc100, %d0
	movec	%d0, %cacr
	nop
	rts

/* en marche, apres une recopie de code en SRAM : le CACR de l'OS (0x40000548) sans DCINVA, comme le firmware de
 * mesure (notes/75) et mod_settings (notes/72) : caches d'instructions et de branchements vides, celui de donnees
 * garde */
	.globl	hot_icinv_run
hot_icinv_run:
	nop
	move.l	#0xa40ce100, %d0
	movec	%d0, %cacr
	nop
	rts

/* hot_copy(d, s, n) : n mots longs de s vers d, 6 par movem (les tables des talons a chaque bloc, les copies) */
	.globl	hot_copy
hot_copy:
	lea	-24(%sp), %sp
	movem.l	%d2-%d7, (%sp)
	movea.l	28(%sp), %a1
	movea.l	32(%sp), %a0
	move.l	36(%sp), %d0
	moveq	#6, %d1
	bra.s	2f
1:	movem.l	(%a0), %d2-%d7
	movem.l	%d2-%d7, (%a1)
	lea	24(%a0), %a0
	lea	24(%a1), %a1
	sub.l	%d1, %d0
2:	cmp.l	%d1, %d0
	bge.s	1b
	bra.s	4f
3:	move.l	(%a0)+, (%a1)+
4:	subq.l	#1, %d0
	bpl.s	3b
	movem.l	(%sp), %d2-%d7
	lea	24(%sp), %sp
	rts

/* talon i : vers hot_tab[i] (la copie pendant le calcul audio, l'original sinon). Aucun registre ne change. */
	.globl	hot_stubs
	.align	2
hot_stubs:
	.set	i, 0
	.rept	HOT_NDET
	move.l	hot_tab + 4 * i, -(%sp)
	rts
	.set	i, i + 1
	.endr
	.globl	hot_end
hot_end:

	.bss
	.align	2
hot_ret:
	.space	4
