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

/* Les modes du resonateur (struct mode : b, a2, a3, ic1, ic2), sur un bloc de 32 trames : ic1 et ic2 dans acc0 et
 * acc1, la sortie dans acc2 (modal_dsp.h, mode_fix et mode_lin : les memes calculs). x a 33 mots : le dernier
 * chargement lit x[32], inutilise. Les accumulateurs sont rendus vides. */

/* void modal_modes(struct mode *md, int n, const s32 *x, s32 *so, s32 *sa, const s32 *amp, int quiet)
 * n modes (pair), position fixe : s[k] += amp ic1[k] / 2 pour k = 0..32, modes pairs dans so, impairs dans sa ;
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
	lea	132(%a0), %a2		/* fin : x + 33 */
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
	add.l	%d3, (%a1)		/* s[32] */
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
	addi.l	#132, %d1
	move.l	%d1, 48(%sp)		/* fin : x + 33 */
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
	move.l	%acc0, %d0		/* ic1[32] */
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
 * Corde, passe 1 du chemin rapide de str_process, retard fixe : ReadHermite (hermite de modal_dsp.h), n echantillons.
 * ph : le x0 du 1er echantillon (&line[w + partie entiere du retard]), qui recule d'un mot a chaque echantillon ;
 * f : la partie fractionnaire (Q31). hb[k] = hermite(ph - k, f) + in[k].
 * Deux echantillons a la fois (notes/74 §5.5) : leurs trois produits en chaine se croisent sur les accumulateurs
 * (acc0 et acc1, puis acc2 et acc3, puis acc0 et acc1), si bien qu'aucune lecture d'accumulateur n'attend la fin
 * du pipeline de l'EMAC ; l'arrondi de chaque qmulr entre avant son produit (la meme somme). Les deux fenetres de
 * 4 mots se recouvrent : 5 mots lus. Le dernier echantillon d'un n impair, seul. */
	.globl	modal_str_read
modal_str_read:
	lea	-44(%sp), %sp
	movem.l	%d2-%d7/%a2-%a6, (%sp)
	movea.l	48(%sp), %a0		/* ph */
	move.l	52(%sp), %d6		/* f */
	movea.l	56(%sp), %a1		/* in */
	movea.l	60(%sp), %a2		/* hb */
	move.l	64(%sp), %d0		/* n */
	beq.w	9f
	lea	(%a2, %d0.l*4), %a4	/* fin de hb */
	movea.l	#0x8000, %a3		/* 2^15 x 2^15 : l'arrondi de qmulr */
	asr.l	#1, %d0
	lsl.l	#3, %d0
	pea	(%a2, %d0.l)		/* fin des paires, sur la pile */
	cmpa.l	(%sp), %a2
	beq.w	4f
1:	mac.l	%a3, %a3, %acc0
	mac.l	%a3, %a3, %acc1
	movem.l	-8(%a0), %d0-%d4	/* p[-2] .. p[2] : A = p (p[-1] .. p[2]), B = p - 1 (p[-2] .. p[1]) */
	move.l	%d3, %d5
	sub.l	%d1, %d5
	asr.l	#1, %d5			/* cA = (x1 - xm1) >> 1 */
	sub.l	%d2, %d4
	asr.l	#1, %d4			/* (x2 - x0) >> 1 de A */
	move.l	%d2, %d7
	sub.l	%d3, %d7		/* vA = x0 - x1 */
	move.l	%d5, %d3
	add.l	%d7, %d3		/* wA = cA + vA */
	add.l	%d3, %d4
	add.l	%d7, %d4		/* aA = wA + vA + ((x2 - x0) >> 1) */
	add.l	%d4, %d3		/* bnA = wA + aA */
	movea.l	%d2, %a5		/* x0A */
	move.l	%d2, %d7
	sub.l	%d0, %d7
	asr.l	#1, %d7			/* cB */
	move.l	%d1, %d0
	sub.l	%d2, %d0		/* vB */
	movea.l	%d1, %a6		/* x0B */
	move.l	%d0, %d1
	add.l	%d7, %d1		/* wB */
	move.l	%d1, %d2
	add.l	%d0, %d2
	add.l	%d5, %d2		/* aB = wB + vB + ((x2 - x0) >> 1) de B, qui est cA */
	add.l	%d2, %d1		/* bnB = wB + aB */
	mac.l	%d4, %d6, %acc0		/* qmulr(aA, f) */
	mac.l	%d2, %d6, %acc1		/* qmulr(aB, f) */
	mac.l	%a3, %a3, %acc2
	mac.l	%a3, %a3, %acc3
	movclr.l %acc0, %d4
	sub.l	%d3, %d4		/* - bnA */
	movclr.l %acc1, %d2
	sub.l	%d1, %d2		/* - bnB */
	mac.l	%d4, %d6, %acc2		/* qmulr(., f) */
	mac.l	%d2, %d6, %acc3
	mac.l	%a3, %a3, %acc0
	mac.l	%a3, %a3, %acc1
	movclr.l %acc2, %d4
	add.l	%d5, %d4		/* + cA */
	movclr.l %acc3, %d2
	add.l	%d7, %d2		/* + cB */
	mac.l	%d4, %d6, %acc0		/* qmulr(., f) */
	mac.l	%d2, %d6, %acc1
	move.l	(%a1)+, %d0		/* in[k] */
	subq.l	#8, %a0			/* deux echantillons plus bas */
	movclr.l %acc0, %d4
	add.l	%d0, %d4
	add.l	%a5, %d4		/* + x0A */
	move.l	%d4, (%a2)+
	movclr.l %acc1, %d2
	add.l	(%a1)+, %d2		/* in[k + 1] */
	add.l	%a6, %d2		/* + x0B */
	move.l	%d2, (%a2)+
	cmpa.l	(%sp), %a2
	bne.w	1b
4:	addq.l	#4, %sp
	cmpa.l	%a4, %a2
	beq.w	9f
	movem.l	-4(%a0), %d0-%d3	/* le dernier : xm1, x0, x1, x2 */
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
9:	movem.l	(%sp), %d2-%d7/%a2-%a6
	lea	44(%sp), %sp
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
 * out[k] += hb[k] ; out[k + 32] (aux) += l0 + qmul(l1 - l0, frac), comb = qmul(dv, pv += p_inc).
 * Deux echantillons a la fois (notes/74 §5.5) : les deux qmul du peigne sur acc0 et acc1, les deux interpolations
 * sur acc2 et acc3 ; les ecritures et les lectures dans l'ordre du C (A ecrit, A lit, B ecrit, B lit : le peigne
 * peut lire ce qui vient d'etre ecrit). */
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
	move.l	%d1, 8192(%a1)		/* line[wp], line[wp + DLINE] */
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
	move.l	%d5, 8188(%a1)		/* line[wp - 1], line[wp - 1 + DLINE] */
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
	add.l	%d2, 124(%a3)		/* aux[k] += */
	subq.l	#8, %a1			/* wp -= 2 */
	movclr.l %acc3, %d2
	add.l	%d4, %d2
	add.l	%d5, (%a3)+		/* out[k + 1] += sB */
	add.l	%d2, 124(%a3)		/* aux[k + 1] += */
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
	move.l	%d1, 8192(%a1)		/* line[wp], line[wp + DLINE] */
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
	add.l	%d4, 124(%a3)		/* aux[k] += ... */
9:	movem.l	(%sp), %d2-%d7/%a2-%a6
	lea	44(%sp), %sp
	rts

/* void modal_svf_lp(struct svf *f, s32 *x, s32 p2, s32 p3)
 * svf_lp_block sur 32 trames, en place (struct svf : b, a2, a3, ic1, ic2) ; p2, p3 ajoutes a t1, t2 a la 1re :
 *   v3 = x - ic2 ; t1 = -b ic1 + a2 v3 ; t2 = a2 ic1 + a3 v3 ; ic1 += 2 t1 ; ic2 += t2 ; x = ic2 ; ic2 += t2 */
	.globl	modal_svf_lp
modal_svf_lp:
	lea	-28(%sp), %sp
	movem.l	%d2-%d7/%a2, (%sp)
	movea.l	32(%sp), %a2		/* f */
	movea.l	36(%sp), %a0		/* x */
	movem.l	(%a2), %d1-%d5		/* b, a2, a3, ic1, ic2 */
	neg.l	%d1			/* -b */
	lea	128(%a0), %a1		/* fin */
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
 * period (Q11.20), gain, level ; struct dcblock : x, y, pole, f. nb = rin + 512 o.
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
	lea	512(%a1), %a5		/* nb */
	lea	640(%a1), %a2		/* fin de nb */
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
	pea	128(%a1)		/* fin de rin */
2:	move.l	512(%a1), %d5		/* nb[k] */
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
 * Corde avec dispersion, retard fixe : la lecture (ReadHermite, comme modal_str_read, sans entree) puis le
 * passe-tout de l'etirement (str_process). ap : st (ligne de 1024 mots), swp, j (son retard), apg ; swp rendu.
 *   rd = st[(swp + j) & 1023] ; wr = sv + qmulr(apg, rd) ; st[swp] = wr ; swp-- ; hb[k] = rd - qmulr(wr, apg) */
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
1:	movem.l	-4(%a0), %d0-%d3	/* xm1, x0, x1, x2 */
	subq.l	#4, %a0
	move.l	%d2, %d4
	sub.l	%d0, %d4
	asr.l	#1, %d4			/* c */
	move.l	%d1, %d5
	sub.l	%d2, %d5		/* v */
	move.l	%d4, %d0
	add.l	%d5, %d0		/* w */
	sub.l	%d1, %d3
	asr.l	#1, %d3
	add.l	%d0, %d3
	add.l	%d5, %d3		/* a */
	add.l	%d3, %d0		/* bn */
	mac.l	%d3, %d6, %acc0
	mac.l	%a3, %a3, %acc0
	movclr.l %acc0, %d3
	sub.l	%d0, %d3
	mac.l	%d3, %d6, %acc0
	mac.l	%a3, %a3, %acc0
	movclr.l %acc0, %d3
	add.l	%d4, %d3
	mac.l	%d3, %d6, %acc0
	mac.l	%a3, %a3, %acc0
	movclr.l %acc0, %d3
	add.l	%d1, %d3		/* sv */
	move.l	%d7, %d4
	add.l	%a5, %d4
	andi.l	#1023, %d4
	move.l	(%a1, %d4.l*4), %d4	/* rd */
	mac.l	%a6, %d4, %acc0
	mac.l	%a3, %a3, %acc0
	movclr.l %acc0, %d5
	add.l	%d3, %d5		/* wr */
	move.l	%d5, (%a1, %d7.l*4)	/* st[swp] */
	subq.l	#1, %d7
	andi.l	#1023, %d7
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

/* void modal_dc_in(struct dcblock *d, s32 *hb, const s32 *in)
 * L'anti-continu de la corde avec dispersion, quand son melange (ac) est nul : son etat seul avance (dc_one sur
 * hb[k]) ; puis hb[k] += in[k]. 32 echantillons. */
	.globl	modal_dc_in
modal_dc_in:
	lea	-28(%sp), %sp
	movem.l	%d2-%d7/%a2, (%sp)
	movea.l	32(%sp), %a0		/* d */
	movea.l	36(%sp), %a1		/* hb */
	movea.l	40(%sp), %a2		/* in */
	movem.l	(%a0), %d2-%d3		/* x1, y */
	move.l	12(%a0), %d4		/* f */
	moveq	#32, %d1
1:	move.l	(%a1), %d5		/* x */
	move.l	8(%a0), %d0		/* pole */
	mac.l	%d0, %d3, %acc0		/* qmul(y, pole) */
	move.l	%d3, %d6
	muls.l	%d0, %d6		/* les 32 bits bas de y pole */
	andi.l	#0x7fffffff, %d6
	add.l	%d6, %d4
	move.l	%d5, %d7
	sub.l	%d2, %d7		/* x - x1 */
	move.l	%d5, %d2
	movclr.l %acc0, %d3
	add.l	%d4, %d4		/* X = f >> 31 */
	addx.l	%d7, %d3		/* y */
	lsr.l	#1, %d4
	add.l	(%a2)+, %d5
	move.l	%d5, (%a1)+		/* hb[k] + in[k] */
	subq.l	#1, %d1
	bne.s	1b
	movem.l	%d2-%d3, (%a0)
	move.l	%d4, 12(%a0)
	movem.l	(%sp), %d2-%d7/%a2
	lea	28(%sp), %sp
	rts

/* void modal_str_read_mv(const s32 *pw, s32 *st, const s32 *in, s32 *hb, int n)
 * Corde, passe 1 quand le retard bouge (modal_dsp.h : la boucle de str_process) : pour chaque echantillon,
 * dv += d_inc, dc += dc_inc, d = qmul(dv, dc) - 2^20, hb[k] = hermite(pw - k + (d >> 20), frac) + in[k].
 * st : dv, dc (rendus), d_inc, dc_inc. pw : &line[w] du 1er echantillon (w recule d'un mot par echantillon).
 * Deux echantillons a la fois, comme modal_str_read (notes/74 §5.5) : les deux qmul du retard sur acc2 et acc3, la
 * chaine de A lancee avant de preparer B, puis les deux chaines croisees ; hb[k] recoit x0 + in[k] d'abord, le
 * dernier produit s'y ajoute. dv et dc passent par st entre deux paires (les registres manquent). */
	.globl	modal_str_read_mv
modal_str_read_mv:
	lea	-44(%sp), %sp
	movem.l	%d2-%d7/%a2-%a6, (%sp)
	movea.l	48(%sp), %a0		/* pw */
	movea.l	52(%sp), %a6		/* st */
	movea.l	56(%sp), %a5		/* in */
	movea.l	60(%sp), %a2		/* hb */
	move.l	64(%sp), %d0		/* n */
	beq.w	9f
	lea	(%a2, %d0.l*4), %a4	/* fin de hb */
	movem.l	(%a6), %d6-%d7		/* dv, dc */
	movea.l	#0x8000, %a3		/* l'arrondi */
	asr.l	#1, %d0
	lsl.l	#3, %d0
	pea	(%a2, %d0.l)		/* fin des paires, sur la pile ; st en 56(%sp) */
	cmpa.l	(%sp), %a2
	beq.w	4f
1:	mac.l	%a3, %a3, %acc0		/* arrondis des 1ers produits de A et de B */
	mac.l	%a3, %a3, %acc1
	add.l	8(%a6), %d6		/* dv += d_inc (A) */
	add.l	12(%a6), %d7		/* dc += dc_inc */
	mac.l	%d6, %d7, %acc2		/* qmul(dv, dc) de A */
	add.l	8(%a6), %d6		/* (B) */
	add.l	12(%a6), %d7
	mac.l	%d6, %d7, %acc3		/* de B */
	movem.l	%d6-%d7, (%a6)		/* dv, dc */
	movclr.l %acc2, %d0
	subi.l	#0x100000, %d0		/* dA = qmul(dv, dc) - 2^20 */
	movclr.l %acc3, %d1
	subi.l	#0x100000, %d1		/* dB */
	move.l	%d0, %d2
	asr.l	#8, %d2
	asr.l	#8, %d2
	asr.l	#4, %d2			/* dA >> 20 */
	lea	(%a0, %d2.l*4), %a1
	lsl.l	#8, %d0
	lsl.l	#3, %d0
	bclr	#31, %d0		/* fA = (dA << 11) & 0x7fffffff */
	movem.l	-4(%a1), %d2-%d5	/* xm1, x0, x1, x2 de A */
	move.l	%d4, %d6
	sub.l	%d2, %d6
	asr.l	#1, %d6			/* cA = (x1 - xm1) >> 1 */
	move.l	%d3, %d2
	sub.l	%d4, %d2		/* vA = x0 - x1 */
	sub.l	%d3, %d5
	asr.l	#1, %d5			/* (x2 - x0) >> 1 */
	add.l	(%a5)+, %d3
	move.l	%d3, (%a2)		/* hb[k] = x0 + in[k] */
	move.l	%d6, %d4
	add.l	%d2, %d4		/* wA = cA + vA */
	add.l	%d4, %d5
	add.l	%d2, %d5		/* aA = wA + vA + ((x2 - x0) >> 1) */
	add.l	%d5, %d4		/* bnA = wA + aA */
	mac.l	%d5, %d0, %acc0		/* qmulr(aA, fA) */
	move.l	%d1, %d2		/* B, pendant ce produit */
	asr.l	#8, %d2
	asr.l	#8, %d2
	asr.l	#4, %d2			/* dB >> 20 */
	lea	-4(%a0, %d2.l*4), %a1	/* un echantillon plus bas */
	lsl.l	#8, %d1
	lsl.l	#3, %d1
	bclr	#31, %d1		/* fB */
	movem.l	-4(%a1), %d2-%d3/%d5/%d7	/* xm1, x0, x1, x2 de B */
	movea.l	%d3, %a1		/* x0B */
	sub.l	%d5, %d3		/* vB = x0 - x1 */
	sub.l	%d2, %d5
	asr.l	#1, %d5			/* cB = (x1 - xm1) >> 1 */
	move.l	%a1, %d2
	sub.l	%d2, %d7
	asr.l	#1, %d7			/* (x2 - x0) >> 1 */
	add.l	(%a5)+, %d2
	move.l	%d2, 4(%a2)		/* hb[k + 1] = x0 + in[k + 1] */
	move.l	%d5, %d2
	add.l	%d3, %d2		/* wB = cB + vB */
	add.l	%d2, %d7
	add.l	%d3, %d7		/* aB = wB + vB + ((x2 - x0) >> 1) */
	add.l	%d7, %d2		/* bnB = wB + aB */
	movclr.l %acc0, %d3
	sub.l	%d4, %d3		/* A : - bnA */
	mac.l	%a3, %a3, %acc2
	mac.l	%d3, %d0, %acc2		/* A : qmulr(., fA) */
	mac.l	%d7, %d1, %acc1		/* B : qmulr(aB, fB) */
	mac.l	%a3, %a3, %acc0
	mac.l	%a3, %a3, %acc3
	movclr.l %acc2, %d3
	add.l	%d6, %d3		/* A : + cA */
	movclr.l %acc1, %d4
	sub.l	%d2, %d4		/* B : - bnB */
	mac.l	%d3, %d0, %acc0		/* A : qmulr(., fA) */
	mac.l	%d4, %d1, %acc3		/* B : qmulr(., fB) */
	mac.l	%a3, %a3, %acc1
	movea.l	56(%sp), %a6		/* st */
	movclr.l %acc0, %d3
	add.l	%d3, (%a2)+		/* hb[k] += */
	movclr.l %acc3, %d4
	add.l	%d5, %d4		/* B : + cB */
	mac.l	%d4, %d1, %acc1		/* B : qmulr(., fB) */
	movem.l	(%a6), %d6-%d7		/* dv, dc de la paire suivante */
	subq.l	#8, %a0			/* w -= 2 */
	movclr.l %acc1, %d4
	add.l	%d4, (%a2)+		/* hb[k + 1] += */
	cmpa.l	(%sp), %a2
	bne.w	1b
4:	addq.l	#4, %sp
	cmpa.l	%a4, %a2
	beq.w	9f
	add.l	8(%a6), %d6		/* le dernier d'un n impair, seul */
	add.l	12(%a6), %d7
	mac.l	%d6, %d7, %acc0
	movclr.l %acc0, %d5
	subi.l	#0x100000, %d5		/* d = qmul(dv, dc) - 2^20 */
	move.l	%d5, %d4
	asr.l	#8, %d4
	asr.l	#8, %d4
	asr.l	#4, %d4			/* d >> 20 */
	lea	(%a0, %d4.l*4), %a1
	lsl.l	#8, %d5
	lsl.l	#3, %d5
	bclr	#31, %d5		/* frac = (d << 11) & 0x7fffffff */
	movem.l	-4(%a1), %d0-%d3	/* xm1, x0, x1, x2 */
	move.l	%d2, %d4
	sub.l	%d0, %d4
	asr.l	#1, %d4			/* c = (x1 - xm1) >> 1 */
	move.l	%d1, %d0
	sub.l	%d2, %d0		/* v = x0 - x1 */
	move.l	%d4, %d2
	add.l	%d0, %d2		/* w = c + v */
	sub.l	%d1, %d3
	asr.l	#1, %d3
	add.l	%d2, %d3
	add.l	%d0, %d3		/* a = w + v + ((x2 - x0) >> 1) */
	add.l	%d3, %d2		/* bn = w + a */
	mac.l	%d3, %d5, %acc0
	mac.l	%a3, %a3, %acc0
	movclr.l %acc0, %d3		/* qmulr(a, f) */
	sub.l	%d2, %d3
	mac.l	%d3, %d5, %acc0
	mac.l	%a3, %a3, %acc0
	movclr.l %acc0, %d3
	add.l	%d4, %d3
	mac.l	%d3, %d5, %acc0
	mac.l	%a3, %a3, %acc0
	movclr.l %acc0, %d3
	add.l	%d1, %d3		/* + x0 */
	add.l	(%a5)+, %d3		/* + in[k] */
	move.l	%d3, (%a2)+
	movem.l	%d6-%d7, (%a6)
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
	lea	128(%a0), %a2
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
	movea.l	56(%sp), %a3		/* out ; aux = out + 128 o */
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
	move.l	%d1, 8192(%a1)		/* line[wp], line[wp + DLINE] */
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
	move.l	%d5, 8188(%a1)		/* line[wp - 1], line[wp - 1 + DLINE] */
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
	add.l	%d2, 124(%a3)		/* aux[k] += */
	subq.l	#8, %a1			/* wp -= 2 */
	movclr.l %acc3, %d2
	add.l	%d4, %d2
	add.l	%d5, (%a3)+		/* out[k + 1] += sB */
	add.l	%d2, 124(%a3)		/* aux[k + 1] += */
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
	move.l	%d1, 8192(%a1)		/* line[wp], line[wp + DLINE] */
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
	add.l	%d4, 124(%a3)		/* aux[k] += ... */
5:	addq.l	#8, %sp
	movea.l	60(%sp), %a2		/* dpp */
	move.l	%a5, (%a2)		/* dv */
	move.l	%d7, 4(%a2)		/* pv */
9:	movem.l	(%sp), %d2-%d7/%a2-%a6
	lea	44(%sp), %sp
	rts
