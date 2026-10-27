/*
 * MODAL : les boucles les plus chaudes du coeur (modal_dsp.h), ecrites a la main pour le ColdFire (notes/74 §5).
 *
 * Chaque noyau fait exactement les memes operations de l'EMAC que le C qu'il remplace (memes produits, memes sommes,
 * memes lectures par movclr) : la sortie est la meme a l'octet pres, et le C reste la reference (modal_host.c,
 * tools/emu/test_modal.py compare la machine a modal.c compile pour l'ordinateur). Le gain : moins d'instructions
 * (registres tenus d'un bout a l'autre, boucles deroulees) et des produits qui s'enchainent sur plusieurs
 * accumulateurs au lieu d'attendre chacun le precedent.
 *
 * L'EMAC est en mode fractionnaire signe sature (MACSR = 0xa0) pendant la boucle des voix. L'OS se sert des quatre
 * accumulateurs le temps d'une fonction et les rend vides (movclr) : ses fonctions de rendu comptent sur des
 * accumulateurs a zero en entree. Ces noyaux les rendent vides aussi.
 *
 * Tailles (modal_cfg.h, avec modal_dsp.h) : MB trames par bloc (16 : Rings a 24 kHz, notes/81), lignes des cordes de
 * DLINE mots (doublees), ligne de l'etirement de SLINE mots. Les boucles deroulees par 8 et par 4 demandent un MB
 * multiple de 8.
 */
#include "modal_cfg.h"
#if MB % 8
#error "modal_asm.S : MB multiple de 8"
#endif
	.text

/* Les modes du resonateur (struct mode : b, a2, a3, ic1, ic2), sur un bloc de MB trames : ic1 et ic2 dans acc0 et
 * acc1, la sortie dans acc2 (modal_dsp.h, mode_fix et mode_lin : les memes calculs). x a MB + 1 mots : le dernier
 * chargement lit x[MB], inutilise. Les accumulateurs sont rendus vides. */

/* void modal_modes(struct mode *md, int n, const s32 *x, s32 *so, s32 *sa, const s32 *amp, int quiet)
 * n modes (pair), position fixe : s[k] += amp ic1[k] / 2 pour k = 0..MB, modes pairs dans so, impairs dans sa ;
 * quiet : sans entree, un mode dont ic1 et ic2 sont sous MODE_EPS (64) n'est pas calcule.
 * Pile : 0 registres, 44 paires restantes, 48 retour, 52 md, 56 n, 60 x, 64 so, 68 sa, 72 amp, 76 quiet. */
	.globl	modal_modes
modal_modes:
	lea	-48(%sp), %sp
	movem.l	%d2-%d7/%a2-%a6, (%sp)
	movea.l	52(%sp), %a3		/* md */
	move.l	56(%sp), %d0		/* n */
	movea.l	64(%sp), %a5		/* so */
	movea.l	68(%sp), %a6		/* sa */
	movea.l	72(%sp), %a4		/* amp */
	asr.l	#1, %d0
	beq.w	9f
	move.l	%d0, 44(%sp)
1:	movea.l	%a5, %a1
	bsr.w	mode_fix
	movea.l	%a6, %a1
	bsr.w	mode_fix
	subq.l	#1, 44(%sp)
	bne.s	1b
9:	movem.l	(%sp), %d2-%d7/%a2-%a6
	lea	48(%sp), %sp
	rts

/* un mode (a3), sommes en a1, amplitude (a4) ; avance a3 et a4. Pile de modal_modes a 4 o de plus (bsr). */
mode_fix:
	movem.l	(%a3), %d4-%d6		/* b, a2, a3 */
	neg.l	%d4			/* -b */
	move.l	12(%a3), %d0		/* ic1 */
	move.l	16(%a3), %d1		/* ic2 */
	tst.l	80(%sp)			/* quiet */
	beq.s	2f
	moveq	#63, %d2
	move.l	%d0, %d3
	bpl.s	3f
	neg.l	%d3
3:	cmp.l	%d2, %d3
	bgt.s	2f
	move.l	%d1, %d3
	bpl.s	4f
	neg.l	%d3
4:	cmp.l	%d2, %d3
	ble.w	8f			/* |ic1| et |ic2| < 64 : pas calcule */
2:	move.l	%d0, %acc0
	move.l	%d1, %acc1
	move.l	(%a4), %d7		/* amp */
	movea.l	64(%sp), %a0		/* x */
	lea	4*(MB+1)(%a0), %a2	/* fin : x + MB + 1 */
	move.l	(%a0)+, %d2		/* x[0] */
5:
	.rept	8
	move.l	%acc0, %d0		/* r1 = ic1 */
	mac.l	%d7, %d0, >>, %acc2	/* s += amp ic1 / 2 */
	move.l	%acc1, %d1		/* r2 = ic2 */
	sub.l	%d1, %d2		/* v3 = x - ic2 */
	mac.l	%d4, %d0, <<, %acc0	/* ic1 += -2 b ic1 */
	mac.l	%d5, %d2, <<, %acc0	/* ic1 += 2 a2 v3 */
	mac.l	%d5, %d0, <<, %acc1	/* ic2 += 2 a2 ic1 */
	mac.l	%d6, %d2, <<, (%a0)+, %d2, %acc1	/* ic2 += 2 a3 v3 ; x suivant */
	movclr.l %acc2, %d3
	add.l	%d3, (%a1)+		/* s[k] */
	.endr
	cmpa.l	%a2, %a0
	bne.w	5b
	move.l	%acc0, %d0
	mac.l	%d7, %d0, >>, %acc2
	movclr.l %acc0, %d0
	movclr.l %acc1, %d1
	movclr.l %acc2, %d3
	add.l	%d3, (%a1)		/* s[MB] */
	move.l	%d0, 12(%a3)
	move.l	%d1, 16(%a3)
8:	lea	20(%a3), %a3
	addq.l	#4, %a4
	rts

/* void modal_modes_lin(struct mode *md, int n, const s32 *x, s32 *ob, s32 *ab, const s32 *amp)
 * Position qui bouge : amplitude a = amp[i] + (k + 1) da a l'echantillon k (da = amp[i + 32], MAXMODES),
 * o[k] += (a ic1[k] + a ic1[k + 1]) / 2 ; tous les modes calcules. La sortie de l'echantillon k - 1 se fait au
 * debut de l'echantillon k (la 1re iteration entre apres elle).
 * Pile : 0 registres, 44 paires restantes, 48 fin de x, 52 retour, 56 md, 60 n, 64 x, 68 ob, 72 ab, 76 amp. */
	.globl	modal_modes_lin
modal_modes_lin:
	lea	-52(%sp), %sp
	movem.l	%d2-%d7/%a2-%a6, (%sp)
	movea.l	56(%sp), %a3		/* md */
	move.l	60(%sp), %d0		/* n */
	movea.l	68(%sp), %a5		/* ob */
	movea.l	72(%sp), %a6		/* ab */
	movea.l	76(%sp), %a4		/* amp */
	move.l	64(%sp), %d1
	addi.l	#4*(MB+1), %d1
	move.l	%d1, 48(%sp)		/* fin : x + MB + 1 */
	asr.l	#1, %d0
	beq.w	9f
	move.l	%d0, 44(%sp)
1:	movea.l	%a5, %a1
	bsr.w	mode_lin
	movea.l	%a6, %a1
	bsr.w	mode_lin
	subq.l	#1, 44(%sp)
	bne.s	1b
9:	movem.l	(%sp), %d2-%d7/%a2-%a6
	lea	52(%sp), %sp
	rts

/* un mode (a3), sortie a1, amplitude (a4) et son pas (128(a4), MAXMODES = 32) ; avance a3 et a4. Fin de x en 52(%sp), x en
 * 68(%sp) (bsr : 4 o de plus). */
mode_lin:
	movem.l	(%a3), %d4-%d6		/* b, a2, a3 */
	neg.l	%d4
	move.l	12(%a3), %d0
	move.l	16(%a3), %d1
	move.l	%d0, %acc0
	move.l	%d1, %acc1
	move.l	(%a4), %d7		/* amp */
	movea.l	68(%sp), %a0		/* x */
	move.l	(%a0)+, %d2		/* x[0] */
	move.l	%acc0, %d0		/* r1 = ic1[0] */
	bra.w	6f
5:	move.l	%acc0, %d0		/* r1 = ic1[k] */
	mac.l	%d7, %a2, >>, %acc2	/* o[k - 1] += amp (ic1[k - 1] + ic1[k]) / 2 */
	mac.l	%d7, %d0, >>, %acc2
	movclr.l %acc2, %d3
	add.l	%d3, (%a1)+
6:
	movea.l	%d0, %a2		/* ic1[k - 1] */
	add.l	128(%a4), %d7		/* amp += da */
	move.l	%acc1, %d1		/* r2 = ic2 */
	sub.l	%d1, %d2		/* v3 = x - ic2 */
	mac.l	%d4, %d0, <<, %acc0
	mac.l	%d5, %d2, <<, %acc0
	mac.l	%d5, %d0, <<, %acc1
	mac.l	%d6, %d2, <<, (%a0)+, %d2, %acc1
	.rept	7
	move.l	%acc0, %d0
	mac.l	%d7, %a2, >>, %acc2	/* o[k - 1] += amp (ic1[k - 1] + ic1[k]) / 2 */
	mac.l	%d7, %d0, >>, %acc2
	movclr.l %acc2, %d3
	add.l	%d3, (%a1)+
	movea.l	%d0, %a2		/* ic1[k - 1] */
	add.l	128(%a4), %d7		/* amp += da */
	move.l	%acc1, %d1		/* r2 = ic2 */
	sub.l	%d1, %d2		/* v3 = x - ic2 */
	mac.l	%d4, %d0, <<, %acc0
	mac.l	%d5, %d2, <<, %acc0
	mac.l	%d5, %d0, <<, %acc1
	mac.l	%d6, %d2, <<, (%a0)+, %d2, %acc1
	.endr
	cmpa.l	52(%sp), %a0
	bne.w	5b
	move.l	%acc0, %d0		/* ic1[MB] */
	mac.l	%d7, %a2, >>, %acc2	/* o[k - 1] += amp (ic1[k - 1] + ic1[k]) / 2 */
	mac.l	%d7, %d0, >>, %acc2
	movclr.l %acc2, %d3
	add.l	%d3, (%a1)+
	movclr.l %acc0, %d0
	movclr.l %acc1, %d1
	move.l	%d0, 12(%a3)
	move.l	%d1, 16(%a3)
	lea	20(%a3), %a3
	addq.l	#4, %a4
	rts

/* void modal_str_read(const s32 *ph, s32 f, const s32 *in, s32 *hb, int n)
 * Corde, passe 1 du chemin rapide de str_process, retard fixe : la lecture lineaire (rd_lin de modal_dsp.h, notes/81),
 * n echantillons. ph : le x0 du 1er echantillon (&line[w + partie entiere du retard]), qui recule d'un mot a chaque
 * echantillon ; f : la partie fractionnaire (Q31). hb[k] = x0 + qmulr(x1 - x0, f) + in[k], x0 = ph[-k], x1 = ph[1 - k] :
 * le x1 d'un echantillon est le x0 du precedent. Deux echantillons a la fois (acc0, acc1). */
	.globl	modal_str_read
modal_str_read:
	lea	-28(%sp), %sp
	movem.l	%d2-%d6/%a2-%a3, (%sp)
	movea.l	32(%sp), %a0		/* ph */
	move.l	36(%sp), %d6		/* f */
	movea.l	40(%sp), %a1		/* in */
	movea.l	44(%sp), %a2		/* hb */
	move.l	48(%sp), %d0		/* n */
	beq.s	9f
	lea	(%a2, %d0.l*4), %a3	/* fin de hb */
	move.l	#0x8000, %d5		/* l'arrondi */
	move.l	4(%a0), %d1		/* x1 du 1er */
	btst	#0, %d0
	beq.s	1f
	move.l	(%a0), %d0		/* n impair : le 1er seul */
	subq.l	#4, %a0
	sub.l	%d0, %d1
	mac.l	%d1, %d6, %acc0
	mac.l	%d5, %d5, %acc0
	move.l	%d0, %d1
	add.l	(%a1)+, %d0
	movclr.l %acc0, %d2
	add.l	%d2, %d0
	move.l	%d0, (%a2)+
	cmpa.l	%a3, %a2
	beq.s	9f
1:	movem.l	-4(%a0), %d2-%d3	/* x0 de B, x0 de A */
	subq.l	#8, %a0
	sub.l	%d3, %d1		/* A : x1 - x0 */
	mac.l	%d1, %d6, %acc0
	mac.l	%d5, %d5, %acc0
	move.l	%d3, %d4
	sub.l	%d2, %d4		/* B : x1 - x0 */
	mac.l	%d4, %d6, %acc1
	mac.l	%d5, %d5, %acc1
	move.l	%d2, %d1		/* le x1 du A suivant */
	add.l	(%a1)+, %d3
	add.l	(%a1)+, %d2
	movclr.l %acc0, %d0
	add.l	%d0, %d3
	move.l	%d3, (%a2)+
	movclr.l %acc1, %d4
	add.l	%d4, %d2
	move.l	%d2, (%a2)+
	cmpa.l	%a3, %a2
	bne.s	1b
9:	movem.l	(%sp), %d2-%d6/%a2-%a3
	lea	28(%sp), %sp
	rts

/* void modal_str_damp(s32 *hb, s32 *dk, int n)
 * Corde, passe 2 du chemin rapide, reglages fixes : DampingFilter (fir_damp) puis le passe-bas d'amortissement
 * (svf), en place sur les n echantillons de hb (n % 4 un par un d'abord, puis 4 a la fois). dk : fx1, fx2, h0, h1
 * (fir_h0, fir_h1), ib (-b), a2, a3, ic1, ic2 ; fx1, fx2, ic1, ic2 rendus a la fin.
 *   y = h0 fx1 + h1 (x + fx2) ; fx2 = fx1 ; fx1 = x ; v3 = y - ic2 ; t1 = ib ic1 + a2 v3 ; t2 = a2 ic1 + a3 v3 ;
 *   x = ic2 + t2 ; ic1 += 2 t1 ; ic2 = x + t2   (produits arrondis : qmac2r) */
	.macro	DAMP1
	move.l	(%a0), %d0		/* x */
	move.l	%d0, %d1
	add.l	%d5, %d1		/* x + fx2 */
	mac.l	%d6, %d4, %acc0		/* h0 fx1 */
	mac.l	%d7, %d1, %acc0		/* h1 (x + fx2) */
	mac.l	%a1, %a1, %acc0
	move.l	%d4, %d5		/* fx2 = fx1 */
	move.l	%d0, %d4		/* fx1 = x */
	movclr.l %acc0, %d1		/* y */
	sub.l	%a6, %d1		/* v3 = y - ic2 */
	mac.l	%a2, %a5, %acc0		/* ib ic1 */
	mac.l	%a3, %d1, %acc0		/* a2 v3 */
	mac.l	%a1, %a1, %acc0
	mac.l	%a3, %a5, %acc1		/* a2 ic1 */
	mac.l	%a4, %d1, %acc1		/* a3 v3 */
	mac.l	%a1, %a1, %acc1
	movclr.l %acc0, %d2		/* t1 */
	movclr.l %acc1, %d3		/* t2 */
	adda.l	%d3, %a6		/* ic2 + t2 */
	move.l	%a6, (%a0)+		/* x = ic2 + t2 */
	adda.l	%d3, %a6		/* ic2 = x + t2 */
	lea	(%a5, %d2.l*2), %a5	/* ic1 += 2 t1 */
	.endm
	.globl	modal_str_damp
modal_str_damp:
	lea	-44(%sp), %sp
	movem.l	%d2-%d7/%a2-%a6, (%sp)
	movea.l	48(%sp), %a0		/* hb */
	movea.l	52(%sp), %a1		/* dk */
	move.l	56(%sp), %d0		/* n */
	lea	(%a0, %d0.l*4), %a2
	move.l	%a2, -(%sp)		/* fin de hb */
	andi.l	#3, %d0
	lea	(%a0, %d0.l*4), %a2
	move.l	%a2, -(%sp)		/* fin des echantillons un par un */
	movem.l	(%a1), %d4-%d7/%a2-%a6	/* fx1, fx2, h0, h1, ib, a2, a3, ic1, ic2 */
	movea.l	#0x8000, %a1		/* l'arrondi */
2:	cmpa.l	(%sp), %a0
	beq.s	1f
	DAMP1
	bra.s	2b
1:	cmpa.l	4(%sp), %a0
	beq.w	3f
	DAMP1
	DAMP1
	DAMP1
	DAMP1
	bra.w	1b
3:	addq.l	#8, %sp
	movea.l	52(%sp), %a1
	movem.l	%d4-%d5, (%a1)		/* fx1, fx2 */
	move.l	%a5, 28(%a1)		/* ic1 */
	move.l	%a6, 32(%a1)		/* ic2 */
	movem.l	(%sp), %d2-%d7/%a2-%a6
	lea	44(%sp), %sp
	rts

/* void modal_str_write(const s32 *hb, s32 *pw, s32 *out, const s32 *dpp, int n)
 * Corde, passe 3 du chemin rapide, retard fixe (la position peut bouger) : n echantillons ecrits dans la ligne
 * (doublee : line[wp] et line[wp + DLINE]), puis la lecture du peigne. pw = &line[wp], recule d'un mot ; la lecture
 * se fait apres le recul (l'appelant decoupe pour qu'il ne passe jamais sous line[0]). dpp : dv, pv, p_inc.
 * out[k] += hb[k] ; out[k + MB] (aux) += l0 + qmul(l1 - l0, frac), comb = qmul(dv, pv += p_inc).
 * Deux echantillons a la fois (notes/74 §5.5) : les deux qmul du peigne sur acc0 et acc1, les deux interpolations
 * sur acc2 et acc3 ; les ecritures et les lectures dans l'ordre du C (A ecrit, A lit, B ecrit, B lit : le peigne
 * peut lire ce qui vient d'etre ecrit). */
	.globl	modal_str_write
modal_str_write:
	lea	-44(%sp), %sp
	movem.l	%d2-%d7/%a2-%a6, (%sp)
	movea.l	48(%sp), %a0		/* hb */
	movea.l	52(%sp), %a1		/* pw */
	movea.l	56(%sp), %a3		/* out ; aux = out + MB mots */
	movea.l	60(%sp), %a2
	movea.l	(%a2), %a5		/* dv */
	move.l	4(%a2), %d7		/* pv */
	movea.l	8(%a2), %a6		/* p_inc */
	move.l	64(%sp), %d0		/* n */
	beq.w	9f
	lea	(%a0, %d0.l*4), %a4	/* fin de hb */
	asr.l	#1, %d0
	lsl.l	#3, %d0
	pea	(%a0, %d0.l)		/* fin des paires, sur la pile */
	cmpa.l	(%sp), %a0
	beq.w	4f
1:	add.l	%a6, %d7		/* pv += p_inc (A) */
	mac.l	%a5, %d7, %acc0		/* comb de A = qmul(dv, pv) */
	add.l	%a6, %d7		/* (B) */
	mac.l	%a5, %d7, %acc1		/* comb de B */
	move.l	(%a0)+, %d1		/* sA = hb[k] */
	move.l	%d1, (%a1)
	move.l	%d1, 4*DLINE(%a1)	/* line[wp], line[wp + DLINE] */
	movclr.l %acc0, %d0
	move.l	%d0, %d2
	asr.l	#8, %d2
	asr.l	#8, %d2
	asr.l	#4, %d2			/* iA = comb >> 20 */
	lsl.l	#8, %d0
	lsl.l	#3, %d0
	bclr	#31, %d0		/* fracA = (comb << 11) & 0x7fffffff */
	lea	-4(%a1, %d2.l*4), %a2
	movem.l	(%a2), %d3-%d4		/* l0A = line[wp - 1 + iA], l1A : lus apres l'ecriture de A, avant celle de B */
	sub.l	%d3, %d4
	mac.l	%d4, %d0, %acc2		/* qmul(l1 - l0, fracA) */
	move.l	(%a0)+, %d5		/* sB = hb[k + 1] */
	move.l	%d5, -4(%a1)
	move.l	%d5, 4*DLINE-4(%a1)	/* line[wp - 1], line[wp - 1 + DLINE] */
	movclr.l %acc1, %d0
	move.l	%d0, %d2
	asr.l	#8, %d2
	asr.l	#8, %d2
	asr.l	#4, %d2			/* iB */
	lsl.l	#8, %d0
	lsl.l	#3, %d0
	bclr	#31, %d0		/* fracB */
	lea	-8(%a1, %d2.l*4), %a2
	movem.l	(%a2), %d4/%d6		/* l0B = line[wp - 2 + iB], l1B */
	sub.l	%d4, %d6
	mac.l	%d6, %d0, %acc3
	movclr.l %acc2, %d2
	add.l	%d3, %d2		/* l0A + qmul(...) */
	add.l	%d1, (%a3)+		/* out[k] += sA */
	add.l	%d2, 4*MB-4(%a3)	/* aux[k] += */
	subq.l	#8, %a1			/* wp -= 2 */
	movclr.l %acc3, %d2
	add.l	%d4, %d2
	add.l	%d5, (%a3)+		/* out[k + 1] += sB */
	add.l	%d2, 4*MB-4(%a3)	/* aux[k + 1] += */
	cmpa.l	(%sp), %a0
	bne.w	1b
4:	addq.l	#4, %sp
	cmpa.l	%a4, %a0
	beq.w	9f
	add.l	%a6, %d7		/* le dernier d'un n impair, seul */
	mac.l	%a5, %d7, %acc0
	movclr.l %acc0, %d0		/* comb = qmul(dv, pv) */
	move.l	(%a0)+, %d1		/* s = hb[k] */
	move.l	%d1, (%a1)
	move.l	%d1, 4*DLINE(%a1)	/* line[wp], line[wp + DLINE] */
	subq.l	#4, %a1			/* wp-- */
	move.l	%d0, %d2
	asr.l	#8, %d2
	asr.l	#8, %d2
	asr.l	#4, %d2			/* i = comb >> 20 */
	lsl.l	#8, %d0
	lsl.l	#3, %d0
	bclr	#31, %d0		/* frac */
	lea	(%a1, %d2.l*4), %a2
	movem.l	(%a2), %d3-%d4		/* l0, l1 */
	sub.l	%d3, %d4
	mac.l	%d4, %d0, %acc0
	movclr.l %acc0, %d4
	add.l	%d3, %d4		/* l0 + qmul(l1 - l0, frac) */
	add.l	%d1, (%a3)+		/* out[k] += s */
	add.l	%d4, 4*MB-4(%a3)	/* aux[k] += ... */
9:	movem.l	(%sp), %d2-%d7/%a2-%a6
	lea	44(%sp), %sp
	rts

/* void modal_svf_lp(struct svf *f, s32 *x, s32 p2, s32 p3)
 * svf_lp_block sur MB trames, en place (struct svf : b, a2, a3, ic1, ic2) ; p2, p3 ajoutes a t1, t2 a la 1re :
 *   v3 = x - ic2 ; t1 = -b ic1 + a2 v3 ; t2 = a2 ic1 + a3 v3 ; ic1 += 2 t1 ; ic2 += t2 ; x = ic2 ; ic2 += t2 */
	.globl	modal_svf_lp
modal_svf_lp:
	lea	-28(%sp), %sp
	movem.l	%d2-%d7/%a2, (%sp)
	movea.l	32(%sp), %a2		/* f */
	movea.l	36(%sp), %a0		/* x */
	movem.l	(%a2), %d1-%d5		/* b, a2, a3, ic1, ic2 */
	neg.l	%d1			/* -b */
	lea	4*MB(%a0), %a1		/* fin */
	move.l	(%a0), %d0		/* trame 0 : avec p2, p3 */
	sub.l	%d5, %d0
	mac.l	%d1, %d4, %acc0
	mac.l	%d2, %d0, %acc0
	mac.l	%d2, %d4, %acc1
	mac.l	%d3, %d0, %acc1
	movclr.l %acc0, %d6
	add.l	40(%sp), %d6		/* t1 + p2 */
	add.l	%d6, %d4
	add.l	%d6, %d4
	movclr.l %acc1, %d7
	add.l	44(%sp), %d7		/* t2 + p3 */
	add.l	%d7, %d5
	move.l	%d5, (%a0)+
	add.l	%d7, %d5
1:	move.l	(%a0), %d0
	sub.l	%d5, %d0		/* v3 */
	mac.l	%d1, %d4, %acc0
	mac.l	%d2, %d0, %acc0		/* t1 */
	mac.l	%d2, %d4, %acc1
	mac.l	%d3, %d0, %acc1		/* t2 */
	movclr.l %acc0, %d6
	add.l	%d6, %d4
	add.l	%d6, %d4		/* ic1 += 2 t1 */
	movclr.l %acc1, %d7
	add.l	%d7, %d5
	move.l	%d5, (%a0)+		/* x = ic2 + t2 */
	add.l	%d7, %d5		/* ic2 += 2 t2 */
	cmpa.l	%a1, %a0
	bne.s	1b
	movem.l	%d4-%d5, 12(%a2)	/* ic1, ic2 */
	movem.l	(%sp), %d2-%d7/%a2
	lea	28(%sp), %sp
	rts

/* void modal_pluck(struct plucker *p, s32 *rin, struct dcblock *dc)
 * Le pincement hors de la bouffee de bruit (remaining nul) puis le filtre anti-continu (modal_dsp.h : pl_process,
 * rin += nb, dc_one ; les memes operations). struct plucker : svf (b, a2, a3, ic1, ic2), comb[256], wp, remaining,
 * period (Q11.20), gain, level ; struct dcblock : x, y, pole, f. nb = rin + 4 MB mots (struct modal_part).
 * 1 : nb[k] = qmul(gain, comb[i] + qmul(comb[i + 1] - comb[i], frac)), i = wp + (period >> 20) (masque 255) ;
 *     comb[wp] = nb[k] ; wp-- (masque 255)
 * 2 : nb passe-bas (svf_lp_block), x = rin[k] + nb[k], rin[k] = dc_one(x) : y = qmul(y, pole) + retenue de la
 *     partie fractionnaire + x - x1, la partie fractionnaire (les 31 bits bas de y pole) gardee dans f. */
	.globl	modal_pluck
modal_pluck:
	lea	-44(%sp), %sp
	movem.l	%d2-%d7/%a2-%a6, (%sp)
	movea.l	48(%sp), %a4		/* p */
	movea.l	52(%sp), %a1		/* rin */
	lea	20(%a4), %a0		/* comb */
	move.l	1044(%a4), %d0		/* wp */
	move.l	1052(%a4), %d1		/* period */
	move.l	%d1, %d2
	moveq	#11, %d4
	lsl.l	%d4, %d2
	bclr	#31, %d2		/* frac = (period << 11) & 0x7fffffff */
	moveq	#20, %d4
	asr.l	%d4, %d1		/* period >> 20 */
	move.l	1056(%a4), %d3		/* gain */
	lea	16*MB(%a1), %a5		/* nb */
	lea	20*MB(%a1), %a2		/* fin de nb */
1:	move.l	%d0, %d4
	add.l	%d1, %d4
	andi.l	#255, %d4
	movea.l	(%a0, %d4.l*4), %a3	/* comb[i] */
	addq.l	#1, %d4
	andi.l	#255, %d4
	move.l	(%a0, %d4.l*4), %d5
	sub.l	%a3, %d5		/* comb[i + 1] - comb[i] */
	mac.l	%d5, %d2, %acc0
	movclr.l %acc0, %d5
	add.l	%a3, %d5		/* rd_linear */
	mac.l	%d3, %d5, %acc0
	movclr.l %acc0, %d5		/* qmul(gain, .) */
	move.l	%d5, (%a0, %d0.l*4)	/* comb[wp] */
	move.l	%d5, (%a5)+		/* nb[k] */
	subq.l	#1, %d0
	andi.l	#255, %d0
	cmpa.l	%a2, %a5
	bne.s	1b
	move.l	%d0, 1044(%a4)
	/* 2 : passe-bas du pincement, puis anti-continu */
	movea.l	56(%sp), %a0		/* dc */
	movem.l	(%a4), %d5-%d7		/* b, a2, a3 */
	neg.l	%d5
	movea.l	%d5, %a2		/* -b */
	movea.l	%d6, %a3		/* a2 */
	movea.l	%d7, %a6		/* a3 */
	move.l	12(%a4), %d0		/* ic1 */
	move.l	16(%a4), %d1		/* ic2 */
	movem.l	(%a0), %d2-%d3		/* dc x1, y */
	movea.l	8(%a0), %a5		/* pole */
	move.l	12(%a0), %d4		/* f */
	pea	4*MB(%a1)		/* fin de rin */
2:	move.l	16*MB(%a1), %d5		/* nb[k] */
	sub.l	%d1, %d5		/* v3 */
	mac.l	%a2, %d0, %acc0
	mac.l	%a3, %d5, %acc0		/* t1 */
	mac.l	%a3, %d0, %acc1
	mac.l	%a6, %d5, %acc1		/* t2 */
	movclr.l %acc0, %d6
	add.l	%d6, %d0
	add.l	%d6, %d0		/* ic1 += 2 t1 */
	movclr.l %acc1, %d7
	add.l	%d7, %d1		/* passe-bas = ic2 + t2 */
	move.l	(%a1), %d5
	add.l	%d1, %d5		/* x = rin[k] + nb[k] */
	add.l	%d7, %d1		/* ic2 += 2 t2 */
	mac.l	%a5, %d3, %acc2		/* qmul(y, pole) */
	move.l	%d3, %d6
	muls.l	8(%a0), %d6		/* les 32 bits bas de y pole */
	andi.l	#0x7fffffff, %d6
	add.l	%d6, %d4		/* f += */
	move.l	%d5, %d7
	sub.l	%d2, %d7		/* x - x1 */
	move.l	%d5, %d2		/* x1 = x */
	movclr.l %acc2, %d3
	add.l	%d4, %d4		/* X = f >> 31 */
	addx.l	%d7, %d3		/* y = qmul(y, pole) + (f >> 31) + x - x1 */
	lsr.l	#1, %d4			/* f &= 0x7fffffff */
	move.l	%d3, (%a1)+
	cmpa.l	(%sp), %a1
	bne.s	2b
	addq.l	#4, %sp
	movem.l	%d0-%d1, 12(%a4)	/* ic1, ic2 */
	movem.l	%d2-%d3, (%a0)		/* x1, y */
	move.l	%d4, 12(%a0)		/* f */
	movem.l	(%sp), %d2-%d7/%a2-%a6
	lea	44(%sp), %sp
	rts

/* void modal_str_read_ap(const s32 *ph, s32 f, s32 *hb, int n, s32 *ap)
 * Corde avec dispersion, retard fixe : la lecture (lineaire, comme modal_str_read, sans entree) puis le
 * passe-tout de l'etirement (str_process). ap : st (ligne de SLINE mots), swp, j (son retard), apg ; swp rendu.
 *   rd = st[(swp + j) & (SLINE - 1)] ; wr = sv + qmulr(apg, rd) ; st[swp] = wr ; swp-- ; hb[k] = rd - qmulr(wr, apg) */
	.globl	modal_str_read_ap
modal_str_read_ap:
	lea	-44(%sp), %sp
	movem.l	%d2-%d7/%a2-%a6, (%sp)
	movea.l	48(%sp), %a0		/* ph */
	move.l	52(%sp), %d6		/* f */
	movea.l	56(%sp), %a2		/* hb */
	move.l	60(%sp), %d0		/* n */
	beq.w	9f
	lea	(%a2, %d0.l*4), %a4	/* fin de hb */
	movea.l	64(%sp), %a1
	move.l	4(%a1), %d7		/* swp */
	movea.l	8(%a1), %a5		/* j */
	movea.l	12(%a1), %a6		/* apg */
	movea.l	(%a1), %a1		/* st */
	movea.l	#0x8000, %a3		/* l'arrondi */
1:	movem.l	(%a0), %d1-%d2		/* x0, x1 */
	subq.l	#4, %a0
	sub.l	%d1, %d2
	mac.l	%d2, %d6, %acc0
	mac.l	%a3, %a3, %acc0
	movclr.l %acc0, %d3
	add.l	%d1, %d3		/* sv = x0 + qmulr(x1 - x0, f) */
	move.l	%d7, %d4
	add.l	%a5, %d4
	andi.l	#SLINE-1, %d4
	move.l	(%a1, %d4.l*4), %d4	/* rd */
	mac.l	%a6, %d4, %acc0
	mac.l	%a3, %a3, %acc0
	movclr.l %acc0, %d5
	add.l	%d3, %d5		/* wr */
	move.l	%d5, (%a1, %d7.l*4)	/* st[swp] */
	subq.l	#1, %d7
	andi.l	#SLINE-1, %d7
	mac.l	%d5, %a6, %acc0
	mac.l	%a3, %a3, %acc0
	movclr.l %acc0, %d5
	sub.l	%d5, %d4		/* rd - qmulr(wr, apg) */
	move.l	%d4, (%a2)+
	cmpa.l	%a4, %a2
	bne.w	1b
	movea.l	64(%sp), %a1
	move.l	%d7, 4(%a1)
9:	movem.l	(%sp), %d2-%d7/%a2-%a6
	lea	44(%sp), %sp
	rts

/* void modal_str_read_mv(const s32 *pw, s32 *st, const s32 *in, s32 *hb, int n)
 * Corde, passe 1 quand le retard bouge (modal_dsp.h : la boucle de str_process) : pour chaque echantillon,
 * dv += d_inc, dc += dc_inc, d = qmul(dv, dc) - 2^20, hb[k] = rd_lin(pw - k + (d >> 20), frac) + in[k].
 * st : dv, dc (rendus), d_inc, dc_inc. pw : &line[w] du 1er echantillon (w recule d'un mot par echantillon). Le
 * qmul du retard sur acc1 et la lecture sur acc0, la lecture d'un echantillon pendant le retard du suivant. */
	.globl	modal_str_read_mv
modal_str_read_mv:
	lea	-44(%sp), %sp
	movem.l	%d2-%d7/%a2-%a6, (%sp)
	movea.l	48(%sp), %a0		/* pw */
	movea.l	52(%sp), %a6		/* st */
	movea.l	56(%sp), %a1		/* in */
	movea.l	60(%sp), %a2		/* hb */
	move.l	64(%sp), %d0		/* n */
	beq.s	9f
	lea	(%a2, %d0.l*4), %a3	/* fin de hb */
	movem.l	(%a6), %d4-%d7		/* dv, dc, d_inc, dc_inc */
	movea.l	#0x8000, %a4		/* l'arrondi */
	moveq	#20, %d3
1:	add.l	%d6, %d4		/* dv += d_inc */
	add.l	%d7, %d5		/* dc += dc_inc */
	mac.l	%d4, %d5, %acc1		/* qmul(dv, dc) */
	mac.l	%a4, %a4, %acc0		/* l'arrondi de la lecture */
	movclr.l %acc1, %d0
	subi.l	#0x100000, %d0		/* d */
	move.l	%d0, %d1
	asr.l	%d3, %d1		/* d >> 20 */
	lsl.l	#8, %d0
	lsl.l	#3, %d0
	bclr	#31, %d0		/* frac = (d << 11) & 0x7fffffff */
	lea	(%a0, %d1.l*4), %a5
	movem.l	(%a5), %d1-%d2		/* x0, x1 */
	subq.l	#4, %a0
	sub.l	%d1, %d2
	mac.l	%d2, %d0, %acc0
	add.l	(%a1)+, %d1		/* x0 + in[k] */
	movclr.l %acc0, %d2
	add.l	%d2, %d1
	move.l	%d1, (%a2)+
	cmpa.l	%a3, %a2
	bne.s	1b
	movem.l	%d4-%d5, (%a6)		/* dv, dc */
9:	movem.l	(%sp), %d2-%d7/%a2-%a6
	lea	44(%sp), %sp
	rts

/* void modal_str_damp_mv(s32 *hb, s32 *dk)
 * Corde, passe 2 quand le filtre bouge : comme modal_str_damp, h0 et h1 refaits a chaque echantillon depuis fbr et
 * fdmp (fir_h0, fir_h1), qui avancent de br_inc et dmp_inc apres. dk : fx1, fx2, fbr, fdmp, br_inc, dmp_inc, ib,
 * a2, a3, ic1, ic2 ; fx1, fx2, fbr, fdmp, ic1, ic2 rendus. Pile : 0 registres, 44 br_inc, 48 dmp_inc, 52 fin,
 * 56 retour, 60 hb, 64 dk. */
	.globl	modal_str_damp_mv
modal_str_damp_mv:
	lea	-56(%sp), %sp
	movem.l	%d2-%d7/%a2-%a6, (%sp)
	movea.l	60(%sp), %a0		/* hb */
	movea.l	64(%sp), %a1		/* dk */
	move.l	16(%a1), 44(%sp)	/* br_inc */
	move.l	20(%a1), 48(%sp)	/* dmp_inc */
	lea	4*MB(%a0), %a2
	move.l	%a2, 52(%sp)		/* fin de hb */
	movem.l	(%a1), %d4-%d7		/* fx1, fx2, fbr, fdmp */
	movem.l	24(%a1), %a2-%a6	/* ib, a2, a3, ic1, ic2 */
	movea.l	#0x8000, %a1		/* l'arrondi */
1:	move.l	%d6, %d0
	asr.l	#1, %d0
	addi.l	#0x40000000, %d0
	mac.l	%d7, %d0, %acc0
	mac.l	%a1, %a1, %acc0
	move.l	#0x20000000, %d1
	move.l	%d6, %d2
	asr.l	#2, %d2
	sub.l	%d2, %d1
	mac.l	%d7, %d1, %acc1
	mac.l	%a1, %a1, %acc1
	movclr.l %acc0, %d0		/* h0 = qmulr(fdmp, 0x40000000 + (fbr >> 1)) */
	movclr.l %acc1, %d1		/* h1 = qmulr(fdmp, 0x20000000 - (fbr >> 2)) */
	move.l	(%a0), %d2		/* x */
	move.l	%d2, %d3
	add.l	%d5, %d3		/* x + fx2 */
	mac.l	%d0, %d4, %acc0		/* h0 fx1 */
	mac.l	%d1, %d3, %acc0		/* h1 (x + fx2) */
	mac.l	%a1, %a1, %acc0
	move.l	%d4, %d5		/* fx2 = fx1 */
	move.l	%d2, %d4		/* fx1 = x */
	add.l	44(%sp), %d6		/* fbr += br_inc */
	add.l	48(%sp), %d7		/* fdmp += dmp_inc */
	movclr.l %acc0, %d1		/* y */
	sub.l	%a6, %d1		/* v3 = y - ic2 */
	mac.l	%a2, %a5, %acc0		/* ib ic1 */
	mac.l	%a3, %d1, %acc0		/* a2 v3 */
	mac.l	%a1, %a1, %acc0
	mac.l	%a3, %a5, %acc1		/* a2 ic1 */
	mac.l	%a4, %d1, %acc1		/* a3 v3 */
	mac.l	%a1, %a1, %acc1
	movclr.l %acc0, %d2		/* t1 */
	movclr.l %acc1, %d3		/* t2 */
	adda.l	%d3, %a6
	move.l	%a6, (%a0)+		/* x = ic2 + t2 */
	adda.l	%d3, %a6		/* ic2 = x + t2 */
	lea	(%a5, %d2.l*2), %a5	/* ic1 += 2 t1 */
	cmpa.l	52(%sp), %a0
	bne.w	1b
	movea.l	64(%sp), %a1
	movem.l	%d4-%d7, (%a1)		/* fx1, fx2, fbr, fdmp */
	move.l	%a5, 36(%a1)		/* ic1 */
	move.l	%a6, 40(%a1)		/* ic2 */
	movem.l	(%sp), %d2-%d7/%a2-%a6
	lea	56(%sp), %sp
	rts

/* void modal_str_write_mv(const s32 *hb, s32 *pw, s32 *out, s32 *dpp, int n)
 * Corde, passe 3 quand le retard bouge : comme modal_str_write, dv += d_inc a chaque echantillon. dpp : dv, pv
 * (rendus), p_inc, d_inc. Deux echantillons a la fois, comme modal_str_write ; d_inc sur la pile. */
	.globl	modal_str_write_mv
modal_str_write_mv:
	lea	-44(%sp), %sp
	movem.l	%d2-%d7/%a2-%a6, (%sp)
	movea.l	48(%sp), %a0		/* hb */
	movea.l	52(%sp), %a1		/* pw */
	movea.l	56(%sp), %a3		/* out ; aux = out + MB mots */
	movea.l	60(%sp), %a2
	movea.l	(%a2), %a5		/* dv */
	move.l	4(%a2), %d7		/* pv */
	movea.l	8(%a2), %a6		/* p_inc */
	move.l	64(%sp), %d0		/* n */
	beq.w	9f
	lea	(%a0, %d0.l*4), %a4	/* fin de hb */
	asr.l	#1, %d0
	lsl.l	#3, %d0
	pea	(%a0, %d0.l)		/* fin des paires */
	move.l	12(%a2), -(%sp)		/* d_inc, sur la pile ; dpp en 68(%sp) */
	cmpa.l	4(%sp), %a0
	beq.w	4f
1:	adda.l	(%sp), %a5		/* dv += d_inc */
	add.l	%a6, %d7		/* pv += p_inc (A) */
	mac.l	%a5, %d7, %acc0		/* comb de A = qmul(dv, pv) */
	adda.l	(%sp), %a5
	add.l	%a6, %d7		/* (B) */
	mac.l	%a5, %d7, %acc1		/* comb de B */
	move.l	(%a0)+, %d1		/* sA = hb[k] */
	move.l	%d1, (%a1)
	move.l	%d1, 4*DLINE(%a1)	/* line[wp], line[wp + DLINE] */
	movclr.l %acc0, %d0
	move.l	%d0, %d2
	asr.l	#8, %d2
	asr.l	#8, %d2
	asr.l	#4, %d2			/* iA = comb >> 20 */
	lsl.l	#8, %d0
	lsl.l	#3, %d0
	bclr	#31, %d0		/* fracA = (comb << 11) & 0x7fffffff */
	lea	-4(%a1, %d2.l*4), %a2
	movem.l	(%a2), %d3-%d4		/* l0A = line[wp - 1 + iA], l1A : lus apres l'ecriture de A, avant celle de B */
	sub.l	%d3, %d4
	mac.l	%d4, %d0, %acc2		/* qmul(l1 - l0, fracA) */
	move.l	(%a0)+, %d5		/* sB = hb[k + 1] */
	move.l	%d5, -4(%a1)
	move.l	%d5, 4*DLINE-4(%a1)	/* line[wp - 1], line[wp - 1 + DLINE] */
	movclr.l %acc1, %d0
	move.l	%d0, %d2
	asr.l	#8, %d2
	asr.l	#8, %d2
	asr.l	#4, %d2			/* iB */
	lsl.l	#8, %d0
	lsl.l	#3, %d0
	bclr	#31, %d0		/* fracB */
	lea	-8(%a1, %d2.l*4), %a2
	movem.l	(%a2), %d4/%d6		/* l0B = line[wp - 2 + iB], l1B */
	sub.l	%d4, %d6
	mac.l	%d6, %d0, %acc3
	movclr.l %acc2, %d2
	add.l	%d3, %d2		/* l0A + qmul(...) */
	add.l	%d1, (%a3)+		/* out[k] += sA */
	add.l	%d2, 4*MB-4(%a3)	/* aux[k] += */
	subq.l	#8, %a1			/* wp -= 2 */
	movclr.l %acc3, %d2
	add.l	%d4, %d2
	add.l	%d5, (%a3)+		/* out[k + 1] += sB */
	add.l	%d2, 4*MB-4(%a3)	/* aux[k + 1] += */
	cmpa.l	4(%sp), %a0
	bne.w	1b
4:	cmpa.l	%a4, %a0
	beq.w	5f
	adda.l	(%sp), %a5		/* dv += d_inc */
	add.l	%a6, %d7		/* le dernier d'un n impair, seul */
	mac.l	%a5, %d7, %acc0
	movclr.l %acc0, %d0		/* comb = qmul(dv, pv) */
	move.l	(%a0)+, %d1		/* s = hb[k] */
	move.l	%d1, (%a1)
	move.l	%d1, 4*DLINE(%a1)	/* line[wp], line[wp + DLINE] */
	subq.l	#4, %a1			/* wp-- */
	move.l	%d0, %d2
	asr.l	#8, %d2
	asr.l	#8, %d2
	asr.l	#4, %d2			/* i = comb >> 20 */
	lsl.l	#8, %d0
	lsl.l	#3, %d0
	bclr	#31, %d0		/* frac */
	lea	(%a1, %d2.l*4), %a2
	movem.l	(%a2), %d3-%d4		/* l0, l1 */
	sub.l	%d3, %d4
	mac.l	%d4, %d0, %acc0
	movclr.l %acc0, %d4
	add.l	%d3, %d4		/* l0 + qmul(l1 - l0, frac) */
	add.l	%d1, (%a3)+		/* out[k] += s */
	add.l	%d4, 4*MB-4(%a3)	/* aux[k] += ... */
5:	addq.l	#8, %sp
	movea.l	60(%sp), %a2		/* dpp */
	move.l	%a5, (%a2)		/* dv */
	move.l	%d7, 4(%a2)		/* pv */
9:	movem.l	(%sp), %d2-%d7/%a2-%a6
	lea	44(%sp), %sp
	rts

/* void modal_up(const s32 *w, s32 *out, const s32 *c)
 * La passerelle (modal.c, notes/81) : la sortie a 24 kHz remontee a 48 kHz par le filtre demi-bande (HBN paires,
 * c = M_HBI). w : 2 HBN - 1 + MB mots ; pour m = 0..MB-1 :
 *   out[2m] = clamp(sum_j c[j] (w[m + j] + w[m + 2 HBN - 1 - j])) << 6   (une lecture de l'EMAC)
 *   out[2m + 1] = clamp(w[m + HBN]) << 6                               (clamp : +-2,0, soit +-2^25)
 * Le dernier mac charge c[HBN], lu et inutilise. Pile : 44 registres, 44 retour, 48 w, 52 out, 56 c. */
	.macro	CLAMP2 r
	cmpi.l	#0x1ffffff, \r
	ble.s	95f
	move.l	#0x1ffffff, \r
	bra.s	96f
95:	cmpi.l	#-0x2000000, \r
	bge.s	96f
	move.l	#-0x2000000, \r
96:
	.endm
	.globl	modal_up
modal_up:
	lea	-44(%sp), %sp
	movem.l	%d2-%d7/%a2-%a6, (%sp)
	movea.l	48(%sp), %a0		/* w */
	movea.l	52(%sp), %a1		/* out */
	movea.l	56(%sp), %a3		/* c */
	lea	4*MB(%a0), %a2		/* fin */
1:	movea.l	%a0, %a4		/* w[m + j] */
	lea	4*2*HBN(%a0), %a5	/* w[m + 2 HBN - 1 - j], par -(a5) */
	movea.l	%a3, %a6
	move.l	(%a6)+, %d5		/* c[0] */
	.rept	HBN
	move.l	(%a4)+, %d0
	add.l	-(%a5), %d0		/* la paire */
	mac.l	%d0, %d5, (%a6)+, %d5, %acc0	/* + c[j] (paire) ; c[j + 1] */
	.endr
	movclr.l %acc0, %d0
	CLAMP2	%d0
	lsl.l	#6, %d0
	move.l	%d0, (%a1)+
	move.l	4*HBN(%a0), %d0		/* w[m + HBN] */
	CLAMP2	%d0
	lsl.l	#6, %d0
	move.l	%d0, (%a1)+
	addq.l	#4, %a0
	cmpa.l	%a2, %a0
	bne.w	1b
	movem.l	(%sp), %d2-%d7/%a2-%a6
	lea	44(%sp), %sp
	rts

/* void modal_lim(const s32 *oa, s32 *w, s32 *peak, const s32 *k)
 * La fin de modal_process (le limiteur de Rings, modal_dsp.h) et la difference de la passerelle (modal.c), en une
 * passe : oa = out[MB] puis aux[MB] ; peak : peak, lz, ln (modal_limiter) ; k = m_soft, ATK, DEC, pg. Par trame :
 *   l = shl(qmul(out, pg), 1) ; r = shl(qmul(aux, pg), 1) ; pk = max(|l|, |r|, |r - l|) ; err = pk - peak ;
 *   peak += qmul(err > 0 ? ATK : DEC, err) ; g = peak <= UNIT ? 0,8 : lim_gain(peak, ..., err <= 0) ;
 *   w[k] = softlimit(qmul(l, g)) - softlimit(qmul(r, g))
 * softlimit au-dela de 4,0 : modal_softbig (C). Les memes operations que le C. */
	.macro	SOFTL x, t1, t2, t3
	move.l	\x, \t1
	bpl.s	.Lsl1_\@
	neg.l	\t1			/* a = |x| */
.Lsl1_\@:
	cmpi.l	#0x4000000, \t1
	blt.s	.Lsl2_\@
	lea	-20(%sp), %sp
	movem.l	%d0-%d1/%a0-%a1, 4(%sp)
	move.l	\t1, (%sp)
	jsr	modal_softbig
	move.l	%d0, \t2
	movem.l	4(%sp), %d0-%d1/%a0-%a1
	lea	20(%sp), %sp
	bra.s	.Lsl3_\@
.Lsl2_\@:
	move.l	\t1, \t2
	moveq	#17, \t3
	lsr.l	\t3, \t2		/* i = a >> 17 */
	lsl.l	#8, \t1
	lsl.l	#6, \t1
	bclr	#31, \t1		/* shl(a, 14) & Q31ONE */
	move.l	(%a4, \t2\().l*4), \t3	/* m_soft[i] */
	move.l	4(%a4, \t2\().l*4), \t2	/* m_soft[i + 1] */
	sub.l	\t3, \t2
	mac.l	\t2, \t1, %acc2
	movclr.l %acc2, \t2
	add.l	\t3, \t2		/* y */
.Lsl3_\@:
	tst.l	\x
	bpl.s	.Lsl4_\@
	neg.l	\t2
.Lsl4_\@:
	move.l	\t2, \x
	.endm
	.globl	modal_lim
modal_lim:
	lea	-52(%sp), %sp
	movem.l	%d2-%d7/%a2-%a6, 8(%sp)
	movea.l	56(%sp), %a0		/* out */
	lea	4*MB(%a0), %a1		/* aux */
	movea.l	60(%sp), %a2		/* w */
	movea.l	64(%sp), %a3
	move.l	(%a3), %d7		/* peak */
	move.l	4(%a3), (%sp)		/* lz */
	move.l	8(%a3), 4(%sp)		/* ln */
	movea.l	68(%sp), %a3
	movea.l	(%a3), %a4		/* m_soft */
	movea.l	4(%a3), %a5		/* ATK */
	movea.l	8(%a3), %a6		/* DEC */
	move.l	12(%a3), %d6		/* pg */
	lea	4*MB(%a0), %a3		/* fin de out */
1:	move.l	(%a0)+, %d0
	mac.l	%d0, %d6, %acc0
	move.l	(%a1)+, %d1
	mac.l	%d1, %d6, %acc1
	movclr.l %acc0, %d0
	add.l	%d0, %d0		/* l */
	movclr.l %acc1, %d1
	add.l	%d1, %d1		/* r */
	move.l	%d0, %d2
	bpl.s	2f
	neg.l	%d2			/* pk = |l| */
2:	move.l	%d1, %d3
	bpl.s	3f
	neg.l	%d3
3:	cmp.l	%d2, %d3
	ble.s	4f
	move.l	%d3, %d2
4:	move.l	%d1, %d3
	sub.l	%d0, %d3
	bpl.s	5f
	neg.l	%d3
5:	cmp.l	%d2, %d3
	ble.s	6f
	move.l	%d3, %d2
6:	sub.l	%d7, %d2		/* err (le C teste le signe du resultat, qui peut deborder) */
	tst.l	%d2
	ble.s	7f
	mac.l	%a5, %d2, %acc0
	bra.s	8f
7:	mac.l	%a6, %d2, %acc0
8:	movclr.l %acc0, %d3
	add.l	%d3, %d7		/* peak */
	move.l	#0x66666666, %d4	/* Q31(0,8) */
	cmpi.l	#0x1000000, %d7
	bgt.s	12f
	moveq	#-1, %d3
	move.l	%d3, 4(%sp)		/* ln = -1 : 1 / m a refaire */
	bra.w	9f
	/* lim_gain(peak) : n = clz(peak) - 1, m = peak << n ; z = (0xffffffff / (m >> 15)) << 13, ou au relachement
	 * (err <= 0) avec le meme n, le 1 / m d'avant ; t = 0x80000000 - shl(qmul(m, z), 1), z = shl(qmul(z, t), 1)
	 * (gardes : lz, ln) ; qmul(z, 0,8) << (n - 5) ou >> (5 - n) */
12:	move.l	%d2, %d5		/* err */
	move.l	%d7, %d2
	ff1.l	%d2
	subq.l	#1, %d2			/* n */
	move.l	%d7, %d3
	lsl.l	%d2, %d3		/* m */
	tst.l	%d5
	bgt.s	13f			/* attaque : la division */
	cmp.l	4(%sp), %d2
	bne.s	13f			/* n change : la division */
	move.l	(%sp), %d4		/* le 1 / m d'avant */
	bra.s	14f
13:	move.l	%d3, %d5
	moveq	#15, %d4
	asr.l	%d4, %d5		/* m >> 15 */
	moveq	#-1, %d4
	divu.l	%d5, %d4		/* 0xffffffff / (m >> 15) */
	moveq	#13, %d5
	lsl.l	%d5, %d4		/* z */
14:	mac.l	%d3, %d4, %acc0
	movclr.l %acc0, %d3
	add.l	%d3, %d3
	move.l	#0x80000000, %d5
	sub.l	%d3, %d5		/* t */
	mac.l	%d4, %d5, %acc0
	movclr.l %acc0, %d4
	add.l	%d4, %d4		/* 1 / m */
	move.l	%d4, (%sp)		/* lz */
	move.l	%d2, 4(%sp)		/* ln */
	move.l	#0x66666666, %d5
	mac.l	%d4, %d5, %acc0
	movclr.l %acc0, %d4		/* 0,8 / m */
	subq.l	#5, %d2
	bmi.s	10f
	lsl.l	%d2, %d4
	bra.s	9f
10:	neg.l	%d2
	asr.l	%d2, %d4
9:	mac.l	%d0, %d4, %acc0
	mac.l	%d1, %d4, %acc1
	movclr.l %acc0, %d0
	movclr.l %acc1, %d1
	SOFTL	%d0, %d2, %d3, %d5
	SOFTL	%d1, %d2, %d3, %d5
	sub.l	%d1, %d0
	move.l	%d0, (%a2)+
	cmpa.l	%a3, %a0
	bne.w	1b
	movea.l	64(%sp), %a3
	move.l	%d7, (%a3)		/* peak */
	move.l	(%sp), 4(%a3)		/* lz */
	move.l	4(%sp), 8(%a3)		/* ln */
	movem.l	8(%sp), %d2-%d7/%a2-%a6
	lea	52(%sp), %sp
	rts

/* La lecture lineaire d'une corde avec dispersion a un retard v (Q11.20) qui change a chaque echantillon : comme
 * la boucle de str_process, idx = wpk + (v >> 20), moins DLINE au-dela de 2 DLINE - 3 ; f = (v << 11) & 0x7fffffff ;
 * t3 = x0 + qmulr(x1 - x0, f). wpk en 32(%a3), la ligne en %a0, l'arrondi en %a6 ; v, t1, t2 detruits. */
	.macro	RDLIN v, t1, t2, t3
	move.l	\v, \t1
	moveq	#20, \t2
	asr.l	\t2, \t1		/* v >> 20 */
	add.l	32(%a3), \t1		/* idx */
	cmpi.l	#2*DLINE-3, \t1
	ble.s	.Lrd\@
	subi.l	#DLINE, \t1
.Lrd\@:
	lsl.l	#8, \v
	lsl.l	#3, \v
	bclr	#31, \v			/* f */
	move.l	(%a0, \t1\().l*4), \t2	/* x0 */
	move.l	4(%a0, \t1\().l*4), \t3	/* x1 */
	sub.l	\t2, \t3
	mac.l	\t3, \v, %acc1
	mac.l	%a6, %a6, %acc1
	movclr.l %acc1, \t3
	add.l	\t2, \t3
	.endm

/* void modal_str_read_nz(s32 *line, s32 *hb, const s32 *in, int n, s32 *k)
 * Corde avec dispersion au-dela de 0,75 (STRUCTURE haute : le bruit de dispersion module le retard), reglages
 * fixes : passe 1 de str_process, n echantillons, les memes calculs que sa boucle (modal_dsp.h, notes/81) :
 *   rs = rs 1664525 + 1013904223 ; dn += qmul(nfilt, qmul((rs ^ 2^31) >> 4, nk) - dn) ;
 *   d = shl(qmul(d0, 2^30 + shl(qmul(dn, na), 6)), 1) ; apd = qmul(d, sp) ; md = d - apd ;
 *   apd et md >= 4 : sv = la lecture a md, puis le passe-tout de l'etirement (j = apd >> 20) ; sinon a d ;
 *   hb[k] = sv + in[k] ; wpk--.
 * En trois boucles, pour que l'EMAC n'attende pas : le bruit (deux echantillons a la fois), le filtre du bruit (dn,
 * dans hb), puis la lecture, le retard de l'echantillon suivant calcule pendant celle de l'echantillon courant.
 * k : 0 d0, 4 sp, 8 apg, 12 na, 16 nfilt, 20 nk, 24 dn, 28 rs, 32 wpk, 36 swp, 40 1664525, 44 la ligne de
 * l'etirement, 48 (la fin de hb) ; dn, rs, wpk, swp rendus. Le retard lu ne descend pas sous le nombre d'echantillons
 * du bloc (str_process le verifie) : rien de ce qu'on lit n'est ecrit par ce bloc. hb[n] est lu (inutilise). */
	.globl	modal_str_read_nz
modal_str_read_nz:
	lea	-44(%sp), %sp
	movem.l	%d2-%d7/%a2-%a6, (%sp)
	move.l	60(%sp), %d0		/* n */
	beq.w	9f
	movea.l	48(%sp), %a0		/* line */
	movea.l	52(%sp), %a1		/* hb */
	movea.l	56(%sp), %a2		/* in */
	movea.l	64(%sp), %a3		/* k */
	lea	(%a1, %d0.l*4), %a5	/* la fin de hb */
	move.l	%a5, 48(%a3)
	movea.l	%a1, %a4
	move.l	28(%a3), %d7		/* rs */
	move.l	40(%a3), %d6		/* 1664525 */
	move.l	20(%a3), %d5		/* nk */
	btst	#0, %d0
	beq.s	2f
	muls.l	%d6, %d7		/* n impair : le 1er seul */
	addi.l	#1013904223, %d7
	move.l	%d7, %d0
	bchg	#31, %d0
	asr.l	#4, %d0
	mac.l	%d0, %d5, %acc0
	movclr.l %acc0, %d0
	move.l	%d0, (%a4)+
	cmpa.l	%a5, %a4
	beq.s	3f
2:	muls.l	%d6, %d7		/* 1 : le bruit, deux echantillons a la fois */
	addi.l	#1013904223, %d7
	move.l	%d7, %d0
	bchg	#31, %d0
	asr.l	#4, %d0
	mac.l	%d0, %d5, %acc0
	muls.l	%d6, %d7
	addi.l	#1013904223, %d7
	move.l	%d7, %d1
	bchg	#31, %d1
	asr.l	#4, %d1
	mac.l	%d1, %d5, %acc1
	movclr.l %acc0, %d0
	move.l	%d0, (%a4)+
	movclr.l %acc1, %d1
	move.l	%d1, (%a4)+
	cmpa.l	%a5, %a4
	bne.s	2b
3:	move.l	%d7, 28(%a3)		/* rs */
	move.l	24(%a3), %d6		/* 2 : dn += qmul(nfilt, noise - dn) */
	move.l	16(%a3), %d5		/* nfilt */
	movea.l	%a1, %a4
4:	move.l	(%a4), %d0
	sub.l	%d6, %d0
	mac.l	%d5, %d0, %acc0
	movclr.l %acc0, %d0
	add.l	%d0, %d6
	move.l	%d6, (%a4)+
	cmpa.l	%a5, %a4
	bne.s	4b
	move.l	%d6, 24(%a3)		/* dn */
	movea.l	44(%a3), %a4		/* 3 : la ligne de l'etirement */
	movea.l	#0x8000, %a6		/* l'arrondi */
	move.l	12(%a3), %d5		/* na */
	move.l	(%a3), %d6		/* d0 */
	move.l	4(%a3), %d7		/* sp */
	move.l	(%a1), %d0		/* le retard du 1er : d, apd */
	mac.l	%d0, %d5, %acc2
	movclr.l %acc2, %d0
	lsl.l	#6, %d0
	addi.l	#0x40000000, %d0
	mac.l	%d6, %d0, %acc2
	movclr.l %acc2, %d0
	add.l	%d0, %d0		/* d */
	mac.l	%d0, %d7, %acc3
	movclr.l %acc3, %d1		/* apd */
5:	move.l	4(%a1), %d4		/* le dn de l'echantillon suivant : son retard pendant cette lecture */
	mac.l	%d4, %d5, %acc2
	move.l	%d0, %d2
	sub.l	%d1, %d2		/* md */
	cmpi.l	#0x400000, %d1
	blt.w	6f
	cmpi.l	#0x400000, %d2
	blt.w	6f
	moveq	#20, %d0
	asr.l	%d0, %d1		/* j = apd >> 20 */
	move.l	36(%a3), %d0		/* swp */
	add.l	%d0, %d1
	andi.l	#SLINE-1, %d1
	move.l	(%a4, %d1.l*4), %d1	/* rd */
	movea.l	8(%a3), %a5		/* apg */
	mac.l	%a5, %d1, %acc0
	mac.l	%a6, %a6, %acc0
	movclr.l %acc2, %d4		/* (suivant) */
	lsl.l	#6, %d4
	addi.l	#0x40000000, %d4
	mac.l	%d6, %d4, %acc2		/* (suivant) d */
	move.l	%d0, -(%sp)		/* swp */
	RDLIN	%d2, %d0, %d3, %d4	/* la lecture a md : d4 */
	move.l	(%sp)+, %d0
	movclr.l %acc0, %d3
	add.l	%d4, %d3		/* wr = sv + qmulr(apg, rd) */
	move.l	%d3, (%a4, %d0.l*4)	/* st[swp] */
	mac.l	%d3, %a5, %acc0
	mac.l	%a6, %a6, %acc0
	subq.l	#1, %d0
	andi.l	#SLINE-1, %d0
	move.l	%d0, 36(%a3)		/* swp */
	movclr.l %acc2, %d0
	add.l	%d0, %d0		/* (suivant) d */
	mac.l	%d0, %d7, %acc3		/* (suivant) apd */
	movclr.l %acc0, %d3
	sub.l	%d3, %d1		/* sv = rd - qmulr(wr, apg) */
	bra.s	7f
6:	movclr.l %acc2, %d4		/* (suivant) */
	lsl.l	#6, %d4
	addi.l	#0x40000000, %d4
	mac.l	%d6, %d4, %acc2		/* (suivant) d */
	RDLIN	%d0, %d2, %d3, %d1	/* la lecture a d */
	movclr.l %acc2, %d0
	add.l	%d0, %d0		/* (suivant) d */
	mac.l	%d0, %d7, %acc3		/* (suivant) apd */
7:	add.l	(%a2)+, %d1
	move.l	%d1, (%a1)+		/* hb[k] = sv + in[k] */
	subq.l	#1, 32(%a3)		/* wpk-- */
	movclr.l %acc3, %d1		/* (suivant) apd */
	cmpa.l	48(%a3), %a1
	bne.w	5b
9:	movem.l	(%sp), %d2-%d7/%a2-%a6
	lea	44(%sp), %sp
	rts

/* void modal_str_read_cb(s32 *line, s32 *hb, const s32 *in, int n, s32 *k)
 * Corde avec dispersion negative (STRUCTURE basse : le chevalet courbe module le retard, l'anti-continu est melange),
 * reglages fixes : passe 1 de str_process, n echantillons, les memes calculs que sa boucle (modal_dsp.h, notes/81) :
 *   d = shl(qmul(d0, max(2^30 - shl(qmul(cb, bc), 6), 2^29)), 1) ; sv = la lecture a d ;
 *   sac = dc_one(sv) ; sv += qmul(ac, sac - sv) ; value = |sv| - 0,025 ;
 *   cb = value > 0 ? (sv > 0 ? 2 value : -3 value) : 0 ; hb[k] = sv + in[k] ; wpk--.
 * k : 0 d0, 4 bc, 8 ac, 12 cb, 16 x, 20 y, 24 pole, 28 f (dc_one), 32 wpk, 36 0,025 (UNIT) ; cb, x, y, f, wpk rendus.
 * Le retard lu ne descend pas sous la moitie de d0 (le plancher du facteur) : str_process ne prend ce chemin que si
 * cette moitie depasse le bloc. */
	.globl	modal_str_read_cb
modal_str_read_cb:
	lea	-44(%sp), %sp
	movem.l	%d2-%d7/%a2-%a6, (%sp)
	movea.l	48(%sp), %a0		/* line */
	movea.l	52(%sp), %a1		/* hb */
	movea.l	56(%sp), %a2		/* in */
	move.l	60(%sp), %d0		/* n */
	beq.w	9f
	movea.l	64(%sp), %a3		/* k */
	lea	(%a1, %d0.l*4), %a5	/* fin de hb */
	movea.l	24(%a3), %a4		/* pole */
	movea.l	#0x8000, %a6		/* l'arrondi */
	movem.l	12(%a3), %d5-%d7	/* cb, x, y */
	move.l	28(%a3), %d4		/* f */
1:	move.l	4(%a3), %d1		/* bc */
	mac.l	%d5, %d1, %acc0
	movclr.l %acc0, %d0
	lsl.l	#6, %d0
	move.l	#0x40000000, %d1
	sub.l	%d0, %d1		/* le facteur du retard */
	cmpi.l	#0x20000000, %d1
	bge.s	2f
	move.l	#0x20000000, %d1	/* au moins 1/2 */
2:	move.l	(%a3), %d0		/* d0 */
	mac.l	%d0, %d1, %acc0
	movclr.l %acc0, %d0
	add.l	%d0, %d0		/* d */
	RDLIN	%d0, %d1, %d2, %d3	/* sv : d3 */
	mac.l	%a4, %d7, %acc2		/* dc_one : qmul(y, pole) */
	move.l	%d7, %d0
	move.l	%a4, %d1
	muls.l	%d1, %d0		/* les 32 bits bas de y pole */
	andi.l	#0x7fffffff, %d0
	add.l	%d0, %d4		/* f += */
	move.l	%d3, %d1
	sub.l	%d6, %d1		/* sv - x */
	move.l	%d3, %d6		/* x = sv */
	movclr.l %acc2, %d7
	add.l	%d4, %d4		/* X = f >> 31 */
	addx.l	%d1, %d7		/* y = sac */
	lsr.l	#1, %d4			/* f &= 0x7fffffff */
	move.l	%d7, %d0
	sub.l	%d3, %d0
	move.l	8(%a3), %d1		/* ac */
	mac.l	%d1, %d0, %acc0
	movclr.l %acc0, %d0
	add.l	%d0, %d3		/* sv += qmul(ac, sac - sv) */
	move.l	%d3, %d0
	bpl.s	3f
	neg.l	%d0
3:	sub.l	36(%a3), %d0		/* value = |sv| - 0,025 */
	tst.l	%d0
	ble.s	4f
	move.l	%d0, %d5
	add.l	%d5, %d5		/* 2 value */
	tst.l	%d3
	bgt.s	5f
	add.l	%d0, %d5
	neg.l	%d5			/* -3 value */
	bra.s	5f
4:	moveq	#0, %d5
5:	add.l	(%a2)+, %d3
	move.l	%d3, (%a1)+		/* hb[k] = sv + in[k] */
	subq.l	#1, 32(%a3)		/* wpk-- */
	cmpa.l	%a5, %a1
	bne.w	1b
	movem.l	%d5-%d7, 12(%a3)	/* cb, x, y */
	move.l	%d4, 28(%a3)		/* f */
9:	movem.l	(%sp), %d2-%d7/%a2-%a6
	lea	44(%sp), %sp
	rts

/* void modal_str_run(s32 *pw, const s32 *pr, const s32 *in, s32 *out, int n, s32 *k)
 * Une corde au repos (str_fast, notes/81), n echantillons, ses trois passes en une boucle : la lecture lineaire,
 * l'amortissement (FIR puis passe-bas), l'ecriture dans la ligne doublee et out. pw = &line[w], pr = &line[w + D]
 * (D : la partie entiere du retard), qui reculent d'un mot par echantillon ; le retard depasse n, ou chaque lecture
 * precede l'ecriture du meme echantillon : l'ordre de la boucle de str_process.
 *   x = x0 + qmulr(x1 - x0, f) + in[k] ; y = h0 fx1 + h1 (x + fx2) (arrondi) ; fx2 = fx1 ; fx1 = x ;
 *   v3 = y - ic2 ; t1 = ib ic1 + a2 v3 ; t2 = a2 ic1 + a3 v3 (arrondis) ; s = ic2 + t2 ; ic1 += 2 t1 ;
 *   ic2 = s + t2 ; line[w] = line[w + DLINE] = s ; out[k] += s
 * k : 0 f, 4 h0, 8 h1, 12 ib (-b), 16 a2, 20 a3, 24 fx1, 28 fx2, 32 ic1, 36 ic2, 40 (la fin de out) ; fx1, fx2, ic1,
 * ic2 rendus. */
	.globl	modal_str_run
modal_str_run:
	lea	-44(%sp), %sp
	movem.l	%d2-%d7/%a2-%a6, (%sp)
	move.l	64(%sp), %d0		/* n */
	beq.w	9f
	movea.l	48(%sp), %a0		/* pw */
	movea.l	52(%sp), %a1		/* pr */
	movea.l	56(%sp), %a2		/* in */
	movea.l	60(%sp), %a3		/* out */
	movea.l	68(%sp), %a4		/* k */
	lea	(%a3, %d0.l*4), %a5
	move.l	%a5, 40(%a4)		/* la fin de out */
	movem.l	12(%a4), %d4-%d5	/* ib, a2 */
	movem.l	24(%a4), %d0-%d3	/* fx1, fx2, ic1, ic2 */
	movea.l	#0x8000, %a6		/* l'arrondi */
1:	move.l	(%a1), %d7		/* x0 */
	move.l	4(%a1), %d6		/* x1 */
	sub.l	%d7, %d6
	movea.l	(%a4), %a5		/* f */
	mac.l	%d6, %a5, %acc0
	mac.l	%a6, %a6, %acc0
	add.l	(%a2)+, %d7		/* x0 + in[k] */
	subq.l	#4, %a1
	movclr.l %acc0, %d6
	add.l	%d6, %d7		/* x */
	move.l	%d7, %d6
	add.l	%d1, %d6		/* x + fx2 */
	movea.l	4(%a4), %a5		/* h0 */
	mac.l	%a5, %d0, %acc0		/* h0 fx1 */
	movea.l	8(%a4), %a5		/* h1 */
	mac.l	%a5, %d6, %acc0		/* h1 (x + fx2) */
	mac.l	%a6, %a6, %acc0
	move.l	%d0, %d1		/* fx2 = fx1 */
	move.l	%d7, %d0		/* fx1 = x */
	movclr.l %acc0, %d7		/* y */
	sub.l	%d3, %d7		/* v3 = y - ic2 */
	mac.l	%d4, %d2, %acc0		/* ib ic1 */
	mac.l	%d5, %d7, %acc0		/* a2 v3 */
	mac.l	%a6, %a6, %acc0
	mac.l	%d5, %d2, %acc1		/* a2 ic1 */
	movea.l	20(%a4), %a5		/* a3 */
	mac.l	%a5, %d7, %acc1		/* a3 v3 */
	mac.l	%a6, %a6, %acc1
	movclr.l %acc0, %d6		/* t1 */
	movclr.l %acc1, %d7		/* t2 */
	add.l	%d7, %d3		/* s = ic2 + t2 */
	move.l	%d3, (%a0)
	move.l	%d3, 4*DLINE(%a0)	/* line[w], line[w + DLINE] */
	subq.l	#4, %a0
	add.l	%d3, (%a3)+		/* out[k] += s */
	add.l	%d7, %d3		/* ic2 = s + t2 */
	add.l	%d6, %d2
	add.l	%d6, %d2		/* ic1 += 2 t1 */
	cmpa.l	40(%a4), %a3
	bne.w	1b
	movem.l	%d0-%d3, 24(%a4)	/* fx1, fx2, ic1, ic2 */
9:	movem.l	(%sp), %d2-%d7/%a2-%a6
	lea	44(%sp), %sp
	rts

/* void modal_str_comb(const s32 *pb, s32 *aux, int n, s32 *cp)
 * Le peigne d'une corde au repos, apres modal_str_run (ou modal_str_dw) : aux[k] += l0 + qmul(l1 - l0, frac),
 * pv += p_inc, comb = qmul(dv, pv), l0 = pb[-k + (comb >> 20)], l1 juste apres, frac = (comb << 11) & 0x7fffffff.
 * pb : la place ecrite par l'echantillon suivant (str_process lit apres le recul de wp). Quand comb >> 20 est nul,
 * l0 est cette place, que la boucle de str_process lirait avant que l'echantillon suivant ne l'ecrive : son ancien
 * contenu, old[k] (cp[3], garde par str_fast avant d'ecrire ; pas lu si comb >> 20 n'est jamais nul sur le bloc).
 * Le retard peut bouger (la glissade des cordes sympathiques) : dv += d_inc avant chaque echantillon, comme pv.
 * cp : 0 dv (rendu), 4 pv (rendu), 8 p_inc, 12 old (avance de n), 16 d_inc. */
	.globl	modal_str_comb
modal_str_comb:
	lea	-36(%sp), %sp
	movem.l	%d2-%d7/%a2-%a4, (%sp)
	move.l	48(%sp), %d0		/* n */
	beq.s	9f
	movea.l	40(%sp), %a0		/* pb */
	movea.l	44(%sp), %a1		/* aux */
	movea.l	52(%sp), %a3
	lea	(%a1, %d0.l*4), %a2	/* la fin de aux */
	movem.l	(%a3), %d4-%d6/%a4	/* dv, pv, p_inc, old */
	move.l	16(%a3), %d7		/* d_inc */
	moveq	#20, %d3
1:	add.l	%d7, %d4		/* dv += d_inc */
	add.l	%d6, %d5		/* pv += p_inc */
	mac.l	%d4, %d5, %acc0
	movclr.l %acc0, %d0		/* comb */
	move.l	%d0, %d1
	asr.l	%d3, %d1		/* comb >> 20 */
	lsl.l	#8, %d0
	lsl.l	#3, %d0
	bclr	#31, %d0		/* frac */
	tst.l	%d1
	bne.s	3f
	move.l	(%a4), %d2		/* l0 : l'ancien contenu */
	bra.s	2f
3:	move.l	(%a0, %d1.l*4), %d2	/* l0 */
2:	move.l	4(%a0, %d1.l*4), %d1	/* l1 */
	sub.l	%d2, %d1
	mac.l	%d1, %d0, %acc1
	subq.l	#4, %a0
	addq.l	#4, %a4
	movclr.l %acc1, %d1
	add.l	%d2, %d1
	add.l	%d1, (%a1)+
	cmpa.l	%a2, %a1
	bne.s	1b
	movem.l	%d4-%d5, (%a3)		/* dv, pv */
	move.l	%a4, 12(%a3)		/* old */
9:	movem.l	(%sp), %d2-%d7/%a2-%a4
	lea	36(%sp), %sp
	rts

/* void modal_str_dw(const s32 *hb, s32 *pw, s32 *out, int n, s32 *k)
 * modal_str_run sans la lecture : x = hb[k] (la lecture faite a part, entree comprise : modal_str_read_ap, _nz,
 * _cb), puis l'amortissement, l'ecriture dans la ligne doublee et out. pw = &line[w], recule d'un mot par echantillon.
 * k : comme modal_str_run (0 inutilise). */
	.globl	modal_str_dw
modal_str_dw:
	lea	-44(%sp), %sp
	movem.l	%d2-%d7/%a2-%a6, (%sp)
	move.l	60(%sp), %d0		/* n */
	beq.w	9f
	movea.l	48(%sp), %a2		/* hb */
	movea.l	52(%sp), %a0		/* pw */
	movea.l	56(%sp), %a3		/* out */
	movea.l	64(%sp), %a4		/* k */
	lea	(%a3, %d0.l*4), %a5
	move.l	%a5, 40(%a4)		/* la fin de out */
	movem.l	12(%a4), %d4-%d5	/* ib, a2 */
	movem.l	24(%a4), %d0-%d3	/* fx1, fx2, ic1, ic2 */
	movea.l	#0x8000, %a6		/* l'arrondi */
1:	move.l	(%a2)+, %d7		/* x */
	move.l	%d7, %d6
	add.l	%d1, %d6		/* x + fx2 */
	movea.l	4(%a4), %a5		/* h0 */
	mac.l	%a5, %d0, %acc0		/* h0 fx1 */
	movea.l	8(%a4), %a5		/* h1 */
	mac.l	%a5, %d6, %acc0		/* h1 (x + fx2) */
	mac.l	%a6, %a6, %acc0
	move.l	%d0, %d1		/* fx2 = fx1 */
	move.l	%d7, %d0		/* fx1 = x */
	movclr.l %acc0, %d7		/* y */
	sub.l	%d3, %d7		/* v3 = y - ic2 */
	mac.l	%d4, %d2, %acc0		/* ib ic1 */
	mac.l	%d5, %d7, %acc0		/* a2 v3 */
	mac.l	%a6, %a6, %acc0
	mac.l	%d5, %d2, %acc1		/* a2 ic1 */
	movea.l	20(%a4), %a5		/* a3 */
	mac.l	%a5, %d7, %acc1		/* a3 v3 */
	mac.l	%a6, %a6, %acc1
	movclr.l %acc0, %d6		/* t1 */
	movclr.l %acc1, %d7		/* t2 */
	add.l	%d7, %d3		/* s = ic2 + t2 */
	move.l	%d3, (%a0)
	move.l	%d3, 4*DLINE(%a0)	/* line[w], line[w + DLINE] */
	subq.l	#4, %a0
	add.l	%d3, (%a3)+		/* out[k] += s */
	add.l	%d7, %d3		/* ic2 = s + t2 */
	add.l	%d6, %d2
	add.l	%d6, %d2		/* ic1 += 2 t1 */
	cmpa.l	40(%a4), %a3
	bne.w	1b
	movem.l	%d0-%d3, 24(%a4)	/* fx1, fx2, ic1, ic2 */
9:	movem.l	(%sp), %d2-%d7/%a2-%a6
	lea	44(%sp), %sp
	rts
