/* Filtre et Résonance de piste pour le Sampler en modes Granular/Stretch/Pluck/Wave (notes/83).
 * Lié par sampler_mode_filter.ld dans le masque de sprite libéré 0x4016bcd8 (tools/sprites.py, 192 o).
 *
 * Sous MACHINES, pour les modes Granular(3), Stretch(4), Pluck(5), Wave(6), les positions SWEEP (+24)
 * et CONTOUR (+28) renvoient le filtre de piste (0x0c / 0x0b, trackData +48 / +50, gflt_coef / gflt_run),
 * exactement comme sur les machines stock.
 * En modes One shot(0), Loop(1), Slice(2), le filtre propre du Sampler (0x49 / 0x4a) est conservé
 * sans double filtrage. */

	.globl	smf_descr
	.globl	smf_gflt

	.section .text.sampler_mode_filter, "ax"

/* À la place de « movel #sampler_descr_atk,%d0 ; rts » dans descr_hook (Model-TG), qui remplace la fonction feuille
 * 0x4004df5c : elle ne touche que d0 et d1, et l'appelant compte sur a0/a1 (Model-TG l'a payé d'un plantage, voir
 * descr_hook). d1, d2, a0 et a1 sont donc rendus intacts ; seul d0 (le descripteur) change. */
smf_descr:
	lea	-16(%sp), %sp
	movem.l	%d1-%d2/%a0-%a1, (%sp)
	jsr	CUR_PROJ
	move.l	%d0, -(%sp)
	jsr	CUR_KIT
	move.l	%d0, -(%sp)
	jsr	SEL_TRACK
	addq.l	#8, %sp
	move.l	%d0, %d2
	cmpi.l	#6, %d2
	bhs.s	.Luse_atk

	lea	LOOP_MODE, %a0
	move.l	(%a0,%d2.l*4), %d0
	cmpi.l	#3, %d0
	blt.s	.Luse_atk

	/* Modes 3..6 : copie dans other_descr et affectation SWEEP -> 0x0c, CONTOUR -> 0x0b */
	lea	OTHER_DESCR, %a0
	lea	SAMPLER_DESCR_ATK, %a1
	moveq	#18, %d1
1:	move.l	(%a1)+, (%a0)+
	subq.l	#1, %d1
	bpl.s	1b

	moveq	#0x0c, %d1
	move.l	%d1, -52(%a0)		/* other_descr + 24 (SWEEP = Filter) */
	moveq	#0x0b, %d1
	move.l	%d1, -48(%a0)		/* other_descr + 28 (CONTOUR = Res) */
	lea	-76(%a0), %a0
	move.l	%a0, %d0
	bra.s	.Ldescr_out

.Luse_atk:
	lea	SAMPLER_DESCR_ATK, %a0
	move.l	%a0, %d0

.Ldescr_out:
	movem.l	(%sp), %d1-%d2/%a0-%a1
	lea	16(%sp), %sp
	rts

smf_gflt:
	cmpi.l	#6, %d1
	bne.s	.Lgflt_on
	lea	LOOP_MODE, %a0
	move.l	(%a0,%d2.l*4), %d0
	cmpi.l	#3, %d0
	blt.s	.Lgflt_off
.Lgflt_on:
	moveq	#0, %d0
	jmp	GC_CONT
.Lgflt_off:
	moveq	#0, %d0
	jmp	GC_STORE
