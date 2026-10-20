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
 */
	.text

/* void modal_mode_run(struct mode *m, const s32 *x, s32 *o, s32 amp)
 * Un mode du resonateur (filtre passe-bande d'etat variable), position fixe, sur un bloc de 32 trames : la boucle
 * interne de reso_process. struct mode : b, a2, a3, ic1, ic2.
 *   v3 = x - ic2 ; t1 = -b ic1 + a2 v3 ; t2 = a2 ic1 + a3 v3 ; v1 = ic1 + t1 ;
 *   ic1 = v1 + t1 ; ic2 += 2 t2 ; o += amp v1 */
	.globl	modal_mode_run
modal_mode_run:
	lea	-40(%sp), %sp
	movem.l	%d2-%d7/%a2-%a5, (%sp)
	movea.l	44(%sp), %a0		/* m */
	movea.l	48(%sp), %a1		/* x */
	movea.l	52(%sp), %a2		/* o */
	movea.l	56(%sp), %a3		/* amp */
	movem.l	(%a0), %d3-%d6/%a5	/* b, a2, a3, ic1 ; ic2 dans a5 (lea : ic2 += 2 t2 en une instruction) */
	neg.l	%d3			/* -b */
	lea	128(%a1), %a4		/* fin de x */
1:
	.rept	8
	mac.l	%d3, %d6, %acc0		/* -b ic1 */
	mac.l	%d4, %d6, %acc1		/* a2 ic1 */
	move.l	(%a1)+, %d0
	sub.l	%a5, %d0		/* v3 = x - ic2 */
	mac.l	%d4, %d0, %acc0		/* t1 = -b ic1 + a2 v3 */
	mac.l	%d5, %d0, %acc1		/* t2 = a2 ic1 + a3 v3 */
	movclr.l %acc0, %d1
	add.l	%d1, %d6		/* v1 = ic1 + t1 */
	mac.l	%a3, %d6, %acc2		/* amp v1 */
	add.l	%d1, %d6		/* ic1 = v1 + t1 */
	movclr.l %acc1, %d2
	lea	(%a5, %d2.l*2), %a5	/* ic2 += 2 t2 */
	movclr.l %acc2, %d1
	add.l	%d1, (%a2)+		/* o += amp v1 */
	.endr
	cmpa.l	%a4, %a1
	bne.w	1b
	move.l	%d6, 12(%a0)		/* ic1 */
	move.l	%a5, 16(%a0)		/* ic2 */
	movem.l	(%sp), %d2-%d7/%a2-%a5
	lea	40(%sp), %sp
	rts

/* void modal_str_read(const s32 *ph, s32 f, const s32 *in, s32 *hb, int n)
 * Corde, passe 1 du chemin rapide de str_process, retard fixe : ReadHermite (hermite de modal_dsp.h), n echantillons.
 * ph : le x0 du 1er echantillon (&line[w + partie entiere du retard]), qui recule d'un mot a chaque echantillon ;
 * f : la partie fractionnaire (Q31). hb[k] = hermite(ph - k, f) + in[k]. */
	.globl	modal_str_read
modal_str_read:
	lea	-36(%sp), %sp
	movem.l	%d2-%d7/%a2-%a4, (%sp)
	movea.l	40(%sp), %a0		/* ph */
	move.l	44(%sp), %d6		/* f */
	movea.l	48(%sp), %a1		/* in */
	movea.l	52(%sp), %a2		/* hb */
	move.l	56(%sp), %d0		/* n */
	beq.w	9f
	lea	(%a2, %d0.l*4), %a4	/* fin de hb */
	movea.l	#0x8000, %a3		/* 2^15 x 2^15 : l'arrondi de qmulr */
1:	movem.l	-4(%a0), %d0-%d3	/* xm1, x0, x1, x2 */
	subq.l	#4, %a0
	move.l	%d2, %d4
	sub.l	%d0, %d4
	asr.l	#1, %d4			/* c = (x1 - xm1) >> 1 */
	move.l	%d1, %d5
	sub.l	%d2, %d5		/* v = x0 - x1 */
	move.l	%d4, %d0
	add.l	%d5, %d0		/* w = c + v */
	sub.l	%d1, %d3
	asr.l	#1, %d3
	add.l	%d0, %d3
	add.l	%d5, %d3		/* a = w + v + ((x2 - x0) >> 1) */
	add.l	%d3, %d0		/* bn = w + a */
	mac.l	%d3, %d6, %acc0
	mac.l	%a3, %a3, %acc0
	movclr.l %acc0, %d3		/* qmulr(a, f) */
	sub.l	%d0, %d3		/* - bn */
	mac.l	%d3, %d6, %acc0
	mac.l	%a3, %a3, %acc0
	movclr.l %acc0, %d3		/* qmulr(., f) */
	add.l	%d4, %d3		/* + c */
	mac.l	%d3, %d6, %acc0
	mac.l	%a3, %a3, %acc0
	movclr.l %acc0, %d3		/* qmulr(., f) */
	add.l	%d1, %d3		/* + x0 */
	add.l	(%a1)+, %d3		/* + in[k] */
	move.l	%d3, (%a2)+
	cmpa.l	%a4, %a2
	bne.w	1b
9:	movem.l	(%sp), %d2-%d7/%a2-%a4
	lea	36(%sp), %sp
	rts

/* void modal_str_damp(s32 *hb, s32 *dk)
 * Corde, passe 2 du chemin rapide, reglages fixes : DampingFilter (fir_damp) puis le passe-bas d'amortissement
 * (svf), en place sur les 32 echantillons de hb. dk : fx1, fx2, h0, h1 (fir_h0, fir_h1), ib (-b), a2, a3, ic1, ic2 ;
 * fx1, fx2, ic1, ic2 rendus a la fin.
 *   y = h0 fx1 + h1 (x + fx2) ; fx2 = fx1 ; fx1 = x ; v3 = y - ic2 ; t1 = ib ic1 + a2 v3 ; t2 = a2 ic1 + a3 v3 ;
 *   x = ic2 + t2 ; ic1 += 2 t1 ; ic2 = x + t2   (produits arrondis : qmac2r) */
	.globl	modal_str_damp
modal_str_damp:
	lea	-44(%sp), %sp
	movem.l	%d2-%d7/%a2-%a6, (%sp)
	movea.l	48(%sp), %a0		/* hb */
	movea.l	52(%sp), %a1		/* dk */
	movem.l	(%a1), %d4-%d7/%a2-%a6	/* fx1, fx2, h0, h1, ib, a2, a3, ic1, ic2 */
	movea.l	#0x8000, %a1		/* l'arrondi */
	pea	128(%a0)		/* fin de hb, sur la pile */
1:
	.rept	4
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
	.endr
	cmpa.l	(%sp), %a0
	bne.w	1b
	addq.l	#4, %sp
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
 * out[k] += hb[k] ; out[k + 32] (aux) += l0 + qmul(l1 - l0, frac), comb = qmul(dv, pv += p_inc). */
	.globl	modal_str_write
modal_str_write:
	lea	-44(%sp), %sp
	movem.l	%d2-%d7/%a2-%a6, (%sp)
	movea.l	48(%sp), %a0		/* hb */
	movea.l	52(%sp), %a1		/* pw */
	movea.l	56(%sp), %a3		/* out ; aux = out + 128 o */
	movea.l	60(%sp), %a2
	movea.l	(%a2), %a5		/* dv */
	move.l	4(%a2), %d7		/* pv */
	movea.l	8(%a2), %a6		/* p_inc */
	move.l	64(%sp), %d0		/* n */
	beq.w	9f
	lea	(%a0, %d0.l*4), %a4	/* fin de hb */
	moveq	#20, %d5
	moveq	#11, %d6
1:	add.l	%a6, %d7		/* pv += p_inc */
	mac.l	%a5, %d7, %acc0
	movclr.l %acc0, %d0		/* comb = qmul(dv, pv) */
	move.l	(%a0)+, %d1		/* s = hb[k] */
	move.l	%d1, (%a1)
	move.l	%d1, 8192(%a1)		/* line[wp], line[wp + DLINE] */
	subq.l	#4, %a1			/* wp-- */
	move.l	%d0, %d2
	asr.l	%d5, %d2		/* i = comb >> 20 */
	lsl.l	%d6, %d0
	bclr	#31, %d0		/* frac = (comb << 11) & 0x7fffffff */
	lea	(%a1, %d2.l*4), %a2
	movem.l	(%a2), %d3-%d4		/* l0 = line[wp + i], l1 = line[wp + i + 1] */
	sub.l	%d3, %d4
	mac.l	%d4, %d0, %acc0
	movclr.l %acc0, %d4
	add.l	%d3, %d4		/* l0 + qmul(l1 - l0, frac) */
	add.l	%d1, (%a3)+		/* out[k] += s */
	add.l	%d4, 124(%a3)		/* aux[k] += ... */
	cmpa.l	%a4, %a0
	bne.w	1b
9:	movem.l	(%sp), %d2-%d7/%a2-%a6
	lea	44(%sp), %sp
	rts

/* void modal_mode_run_lin(struct mode *m, const s32 *x, s32 *o, s32 amp, s32 damp)
 * Un mode du resonateur quand la position bouge : comme modal_mode_run, l'amplitude augmentee de damp avant
 * chaque echantillon (amp + (k + 1) damp a l'echantillon k : l'interpolation lineaire de reso_process). */
	.globl	modal_mode_run_lin
modal_mode_run_lin:
	lea	-44(%sp), %sp
	movem.l	%d2-%d7/%a2-%a6, (%sp)
	movea.l	48(%sp), %a0		/* m */
	movea.l	52(%sp), %a1		/* x */
	movea.l	56(%sp), %a2		/* o */
	movea.l	60(%sp), %a3		/* amp */
	movea.l	64(%sp), %a6		/* damp */
	movem.l	(%a0), %d3-%d6/%a5	/* b, a2, a3, ic1 ; ic2 dans a5 */
	neg.l	%d3			/* -b */
	lea	128(%a1), %a4		/* fin de x */
1:
	.rept	8
	mac.l	%d3, %d6, %acc0		/* -b ic1 */
	mac.l	%d4, %d6, %acc1		/* a2 ic1 */
	move.l	(%a1)+, %d0
	sub.l	%a5, %d0		/* v3 = x - ic2 */
	mac.l	%d4, %d0, %acc0		/* t1 */
	mac.l	%d5, %d0, %acc1		/* t2 */
	adda.l	%a6, %a3		/* amp += damp */
	movclr.l %acc0, %d1
	add.l	%d1, %d6		/* v1 = ic1 + t1 */
	mac.l	%a3, %d6, %acc2		/* amp v1 */
	add.l	%d1, %d6		/* ic1 = v1 + t1 */
	movclr.l %acc1, %d2
	lea	(%a5, %d2.l*2), %a5	/* ic2 += 2 t2 */
	movclr.l %acc2, %d1
	add.l	%d1, (%a2)+		/* o += amp v1 */
	.endr
	cmpa.l	%a4, %a1
	bne.w	1b
	move.l	%d6, 12(%a0)		/* ic1 */
	move.l	%a5, 16(%a0)		/* ic2 */
	movem.l	(%sp), %d2-%d7/%a2-%a6
	lea	44(%sp), %sp
	rts
