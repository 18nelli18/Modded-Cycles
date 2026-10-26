/*
 * MACRO : les boucles les plus chaudes de quelques modeles de Braids, ecrites a la main pour le ColdFire (notes/81).
 *
 * Chaque noyau fait exactement les calculs entiers du C de Braids qu'il remplace (memes produits, memes decalages,
 * memes troncatures) : la sortie est la meme au bit pres, et Braids compile depuis ses sources d'origine reste la
 * reference (tools/emu/test_macro.py). Le gain : l'etat tenu en registres d'un bout a l'autre, l'index et la fraction
 * de la phase tires d'un seul decalage. Pas d'EMAC : des muls.l, comme le C.
 *
 * Interpolate824(table, p) (stmlib/utils/dsp.h), table de int16 :
 *   a = table[p >> 24], b = table[(p >> 24) + 1], a + ((b - a) * ((p >> 8) & 0xffff) >> 16)
 * Ici : q = p >> 8 ; swap(q) donne p >> 24 en bas (la fraction en haut) ; mvz.w q donne la fraction.
 */
	.text

/* Interpolate824(a0, d0) -> d5 ; detruit d3, d4 */
	.macro	INTERP
	move.l	%d0, %d3
	lsr.l	#8, %d3			/* q = p >> 8 */
	move.l	%d3, %d4
	swap	%d4
	mvz.w	%d4, %d4		/* p >> 24 */
	mvz.w	%d3, %d3		/* (p >> 8) & 0xffff */
	mvs.w	2(%a0,%d4.l*2), %d5	/* b */
	mvs.w	(%a0,%d4.l*2), %d4	/* a */
	sub.l	%d4, %d5
	muls.l	%d3, %d5
	swap	%d5
	ext.l	%d5			/* (b - a) * f >> 16 */
	add.l	%d4, %d5
	.endm

/* void macro_sine_acc(int32_t *acc, int n, uint32_t *phase, uint32_t inc, int32_t amp, int shift,
 *                     const int16_t *table)
 * pour k = 0..n-1 : *phase += inc ; acc[k] += Interpolate824(table, *phase) * amp >> shift
 * (STRUCK BELL : un partiel, amplitude fixe le temps d'un rendu). n pair.
 * Pile : 40 registres, 40 retour, 44 acc, 48 n, 52 phase, 56 inc, 60 amp, 64 shift, 68 table. */
	.globl	macro_sine_acc
macro_sine_acc:
	lea	-40(%sp), %sp
	movem.l	%d2-%d7/%a2-%a5, (%sp)
	move.l	48(%sp), %d0
	beq.w	9f
	movea.l	44(%sp), %a1
	lea	(%a1,%d0.l*4), %a3	/* fin */
	movea.l	52(%sp), %a2
	move.l	(%a2), %d0
	move.l	56(%sp), %d1
	move.l	60(%sp), %d2
	move.l	64(%sp), %d6
	movea.l	68(%sp), %a0
	moveq	#24, %d7
1:	.rept	2
	add.l	%d1, %d0
	move.l	%d0, %d4
	lsr.l	%d7, %d4		/* p >> 24 */
	move.l	%d0, %d3
	lsr.l	#8, %d3
	mvz.w	%d3, %d3		/* (p >> 8) & 0xffff */
	mvs.w	2(%a0,%d4.l*2), %d5	/* b */
	mvs.w	(%a0,%d4.l*2), %d4	/* a */
	sub.l	%d4, %d5
	muls.l	%d3, %d5
	swap	%d5
	ext.l	%d5			/* (b - a) * f >> 16 */
	add.l	%d4, %d5		/* Interpolate824 */
	muls.l	%d2, %d5
	asr.l	%d6, %d5
	add.l	%d5, (%a1)+
	.endr
	cmpa.l	%a3, %a1
	bne.s	1b
	move.l	%d0, (%a2)
9:	movem.l	(%sp), %d2-%d7/%a2-%a5
	lea	40(%sp), %sp
	rts

/* void macro_halfband(int32_t *out, const int16_t *x)
 * Le filtre demi-bande de la passerelle (macro.cc) : pour m = 0..31,
 *   out[m] = x[2m + 11] << 14 + sum_j HB[j] (x[2m + 10 - 2j] + x[2m + 12 + 2j]), j = 0..5
 * sur l'EMAC en mode entier : 13 produits 16 x 16 exacts, sommes exactes (|out| < 2^31), lues par movclr. x aligne
 * sur 4 octets : un long charge x[2k] (moitie haute) et x[2k + 1] (moitie basse). Le MACSR de l'OS (0xa0 dans la
 * boucle des voix) est rendu tel quel, l'accumulateur 0 vide.
 * Pile : 40 registres, 40 retour, 44 out, 48 x. */
	.globl	macro_halfband
macro_halfband:
	lea	-40(%sp), %sp
	movem.l	%d2-%d7/%a2-%a5, (%sp)
	movea.l	44(%sp), %a1
	movea.l	48(%sp), %a0
	move.l	%macsr, %d0
	movea.l	%d0, %a2		/* MACSR de l'OS */
	move.l	#0, %macsr		/* entier, signe, sans saturation */
	move.l	#0x2857f3c5, %d4	/* HB0 : HB1 = 10327 : -3131 */
	move.l	#0x062bfccc, %d5	/* HB2 : HB3 = 1579 : -820 */
	move.l	#0x01b2ff3b, %d6	/* HB4 : HB5 = 434 : -197 */
	move.l	#0x40000000, %d7	/* centre : 16384 (<< 14) */
	lea	128(%a1), %a3		/* fin des sorties */
1:	move.l	(%a0)+, %d0				/* x0 x1 */
	mac.w	%d0u, %d6l, (%a0)+, %d1, %acc0		/* x0 HB5 ; x2 x3 */
	mac.w	%d1u, %d6u, (%a0)+, %d2, %acc0		/* x2 HB4 ; x4 x5 */
	mac.w	%d2u, %d5l, (%a0)+, %d3, %acc0		/* x4 HB3 ; x6 x7 */
	mac.w	%d3u, %d5u, (%a0)+, %d0, %acc0		/* x6 HB2 ; x8 x9 */
	mac.w	%d0u, %d4l, (%a0)+, %d1, %acc0		/* x8 HB1 ; x10 x11 */
	mac.w	%d1u, %d4u, %acc0			/* x10 HB0 */
	mac.w	%d1l, %d7u, (%a0)+, %d2, %acc0		/* x11 << 14 ; x12 x13 */
	mac.w	%d2u, %d4u, (%a0)+, %d3, %acc0		/* x12 HB0 ; x14 x15 */
	mac.w	%d3u, %d4l, (%a0)+, %d0, %acc0		/* x14 HB1 ; x16 x17 */
	mac.w	%d0u, %d5u, (%a0)+, %d1, %acc0		/* x16 HB2 ; x18 x19 */
	mac.w	%d1u, %d5l, (%a0)+, %d2, %acc0		/* x18 HB3 ; x20 x21 */
	mac.w	%d2u, %d6u, (%a0)+, %d3, %acc0		/* x20 HB4 ; x22 x23 */
	mac.w	%d3u, %d6l, %acc0			/* x22 HB5 */
	movclr.l %acc0, %d0
	move.l	%d0, (%a1)+
	lea	-44(%a0), %a0				/* sortie suivante : x + 2 */
	cmpa.l	%a3, %a1
	bne.s	1b
	move.l	%a2, %d0
	move.l	%d0, %macsr
	movem.l	(%sp), %d2-%d7/%a2-%a5
	lea	40(%sp), %sp
	rts

/* struct macro_cymbal_state (braids_fast_digital.inc, RenderCymbal) :
 *  0 inc[7] (les 6 carres, puis l'horloge du bruit), 28 f0, 32 damp0, 36 f1, 40 damp1, 44 xfade,
 *  48 phase (horloge du bruit), 52 rng, 56 p[6], 80 lp0, 84 bp0, 88 lp1, 92 bp1
 * void macro_cymbal(int16_t *buffer, int n, struct macro_cymbal_state *st) : la boucle de RenderCymbal, exacte :
 *   phase += inc6 ; retenue : rng = rng * 1664525 + 1013904223
 *   p[k] += inc[k] ; hat = (sum p[k] >> 31 - 3) * 5461 ; hat = BP(svf0, hat)        (bp borne : CLIP sans effet)
 *   noise = CLIP(HP(svf1, ((rng >> 16) - 32768) >> 1)) ; *buffer++ = hat + ((noise - hat) * xfade >> 15)
 * Svf::Process : notch = in - (bp * damp >> 15) ; lp += f * bp >> 15 ; CLIP(lp) ; hp = notch - lp ;
 *   bp += f * hp >> 15 ; CLIP(bp). CLIP : -32767..32767.
 * Registres : a1..a6 les 6 phases, d2 lp0, d3 bp0, d4 lp1, d5 bp1, d6 somme, d7 = 0 ; le reste sur la pile.
 * Pile : 44 registres (d2-d7/a2-a6), puis la copie locale : 44 inc[7], 72 f0, 76 damp0, 80 f1, 84 damp1, 88 xfade,
 * 92 phase, 96 rng, 100 fin ; 104 retour, 108 buffer, 112 n, 116 st. */
	.macro	CLIPD r
	cmpi.l	#32767, \r
	ble.s	91f
	move.l	#32767, \r
	bra.s	92f
91:	cmpi.l	#-32767, \r
	bge.s	92f
	move.l	#-32767, \r
92:
	.endm

	.globl	macro_cymbal
macro_cymbal:
	lea	-104(%sp), %sp
	movem.l	%d2-%d7/%a2-%a6, (%sp)
	movea.l	116(%sp), %a0		/* st */
	moveq	#6, %d0
	lea	44(%sp), %a1
1:	move.l	(%a0)+, (%a1)+		/* inc[7] */
	subq.l	#1, %d0
	bpl.s	1b
	move.l	(%a0)+, 72(%sp)		/* f0 */
	move.l	(%a0)+, 76(%sp)		/* damp0 */
	move.l	(%a0)+, 80(%sp)		/* f1 */
	move.l	(%a0)+, 84(%sp)		/* damp1 */
	move.l	(%a0)+, 88(%sp)		/* xfade */
	move.l	(%a0)+, 92(%sp)		/* phase */
	move.l	(%a0)+, 96(%sp)		/* rng */
	movem.l	24(%a0), %d2-%d5	/* lp0 bp0 lp1 bp1 */
	movea.l	108(%sp), %a1		/* buffer */
	move.l	112(%sp), %d0
	lea	(%a1,%d0.l*2), %a1
	move.l	%a1, 100(%sp)		/* fin */
	movem.l	(%a0), %a1-%a6		/* p[6] */
	movea.l	108(%sp), %a0		/* buffer */
	moveq	#0, %d7
	tst.l	%d0
	beq.w	9f
2:	move.l	68(%sp), %d0		/* inc6 */
	add.l	%d0, 92(%sp)		/* phase += inc6 */
	bcc.s	3f
	move.l	96(%sp), %d0		/* retenue : rng = rng * 1664525 + 1013904223 */
	move.l	#1664525, %d1
	muls.l	%d1, %d0
	addi.l	#1013904223, %d0
	move.l	%d0, 96(%sp)
3:	moveq	#0, %d6
	adda.l	44(%sp), %a1
	move.l	%a1, %d0
	add.l	%d0, %d0
	addx.l	%d7, %d6
	adda.l	48(%sp), %a2
	move.l	%a2, %d0
	add.l	%d0, %d0
	addx.l	%d7, %d6
	adda.l	52(%sp), %a3
	move.l	%a3, %d0
	add.l	%d0, %d0
	addx.l	%d7, %d6
	adda.l	56(%sp), %a4
	move.l	%a4, %d0
	add.l	%d0, %d0
	addx.l	%d7, %d6
	adda.l	60(%sp), %a5
	move.l	%a5, %d0
	add.l	%d0, %d0
	addx.l	%d7, %d6
	adda.l	64(%sp), %a6
	move.l	%a6, %d0
	add.l	%d0, %d0
	addx.l	%d7, %d6
	subq.l	#3, %d6
	muls.w	#5461, %d6		/* hat */
	move.l	%d3, %d0		/* svf0, passe-bande */
	muls.l	76(%sp), %d0
	asr.l	#8, %d0
	asr.l	#7, %d0
	sub.l	%d0, %d6		/* notch */
	move.l	%d3, %d0
	muls.l	72(%sp), %d0
	asr.l	#8, %d0
	asr.l	#7, %d0
	add.l	%d0, %d2
	CLIPD	%d2
	sub.l	%d2, %d6		/* hp */
	move.l	%d6, %d0
	muls.l	72(%sp), %d0
	asr.l	#8, %d0
	asr.l	#7, %d0
	add.l	%d0, %d3
	CLIPD	%d3			/* hat = bp0 */
	move.l	96(%sp), %d6		/* le bruit */
	clr.w	%d6
	swap	%d6
	subi.l	#32768, %d6
	asr.l	#1, %d6
	move.l	%d5, %d0		/* svf1, passe-haut */
	muls.l	84(%sp), %d0
	asr.l	#8, %d0
	asr.l	#7, %d0
	sub.l	%d0, %d6		/* notch */
	move.l	%d5, %d0
	muls.l	80(%sp), %d0
	asr.l	#8, %d0
	asr.l	#7, %d0
	add.l	%d0, %d4
	CLIPD	%d4
	sub.l	%d4, %d6		/* hp */
	move.l	%d6, %d0
	muls.l	80(%sp), %d0
	asr.l	#8, %d0
	asr.l	#7, %d0
	add.l	%d0, %d5
	CLIPD	%d5
	CLIPD	%d6			/* noise = CLIP(hp) */
	sub.l	%d3, %d6
	muls.l	88(%sp), %d6
	asr.l	#8, %d6
	asr.l	#7, %d6
	add.l	%d3, %d6
	move.w	%d6, (%a0)+
	cmpa.l	100(%sp), %a0
	bne.w	2b
9:	movea.l	116(%sp), %a0		/* l'etat rendu */
	move.l	92(%sp), 48(%a0)
	move.l	96(%sp), 52(%a0)
	movem.l	%a1-%a6, 56(%a0)
	movem.l	%d2-%d5, 80(%a0)
	movem.l	(%sp), %d2-%d7/%a2-%a6
	lea	104(%sp), %sp
	rts

/* void macro_harm_out(int16_t *buffer, int n, const int32_t *lo, const int32_t *hi, HarmonicsState *h)
 * HARMONICS, la sortie (braids_semantic.inc, harm_out), exacte : pour t = 0..n-1 :
 *   out = CLIP(lo[t]) ; pos = pos + 1 (0 apres 21) ; hist[pos + 21] = hist[pos - 1] = out (pos = 0 : hist[21]) ;
 *   x = hist + pos ; y0 = CLIP((16384 + sum_j c[j] (x[21 - j] + x[j])) >> 15) ; y1 = x[11] ;
 *   pour k = 0, 1 : d = delay[dpos] ; delay[dpos] = hi[2t + k] ; dpos = dpos + 1 (0 apres 19) ;
 *                   v = CLIP(yk + d) ; *buffer++ = v ; *buffer++ = v
 * HarmonicsState : 144 hist[44], 232 pos, 236 delay[20], 316 dpos.
 * Pile : 44 registres, 44 retour, 48 buffer, 52 n, 56 lo, 60 hi, 64 h. */
	.macro	HB_TAP j c			/* c x[21 - j] + c x[j], a5 = &x[21] */
	mvs.w	-2*\j(%a5), %d2
	muls.w	#\c, %d2
	add.l	%d2, %d1
	mvs.w	2*\j-42(%a5), %d2
	muls.w	#\c, %d2
	add.l	%d2, %d1
	.endm
	.macro	HARM_DELAY y		/* v = CLIP(y + delay[dpos]) ; delay[dpos] = *hi++ ; deux fois v */
	move.l	(%a6,%d5.l*4), %d0
	move.l	(%a2)+, (%a6,%d5.l*4)
	addq.l	#1, %d5
	cmpi.l	#20, %d5
	bne.s	93f
	moveq	#0, %d5
93:	add.l	\y, %d0
	CLIPD	%d0
	move.w	%d0, (%a0)+
	move.w	%d0, (%a0)+
	.endm

	.globl	macro_harm_out
macro_harm_out:
	lea	-44(%sp), %sp
	movem.l	%d2-%d7/%a2-%a6, (%sp)
	move.l	52(%sp), %d7		/* n */
	ble.w	9f
	movea.l	48(%sp), %a0		/* buffer */
	movea.l	56(%sp), %a1		/* lo */
	movea.l	60(%sp), %a2		/* hi */
	movea.l	64(%sp), %a3		/* h */
	lea	144(%a3), %a4		/* hist */
	lea	236(%a3), %a6		/* delay */
	move.l	232(%a3), %d6		/* pos */
	move.l	316(%a3), %d5		/* dpos */
1:	move.l	(%a1)+, %d0
	CLIPD	%d0
	addq.l	#1, %d6
	cmpi.l	#22, %d6
	bne.s	2f
	moveq	#0, %d6
2:	lea	42(%a4,%d6.l*2), %a5	/* &hist[pos + 21] = &x[21] */
	move.w	%d0, (%a5)
	tst.l	%d6
	beq.s	3f
	move.w	%d0, -44(%a5)		/* hist[pos - 1] */
3:	move.l	#16384, %d1
	HB_TAP	0, 12
	HB_TAP	1, -50
	HB_TAP	2, 126
	HB_TAP	3, -262
	HB_TAP	4, 482
	HB_TAP	5, -824
	HB_TAP	6, 1344
	HB_TAP	7, -2156
	HB_TAP	8, 3545
	HB_TAP	9, -6560
	HB_TAP	10, 20727
	asr.l	#8, %d1
	asr.l	#7, %d1
	CLIPD	%d1			/* y0 */
	mvs.w	-20(%a5), %d3		/* y1 = x[11] */
	HARM_DELAY %d1
	HARM_DELAY %d3
	subq.l	#1, %d7
	bne.w	1b
	move.l	%d6, 232(%a3)
	move.l	%d5, 316(%a3)
9:	movem.l	(%sp), %d2-%d7/%a2-%a6
	lea	44(%sp), %sp
	rts


/* Interpolate824(a0, p) -> d5, p dans un registre ; d7 = 24 ; detruit d3, d4 */
	.macro	INTERP_R p
	move.l	\p, %d4
	lsr.l	%d7, %d4		/* p >> 24 */
	move.l	\p, %d3
	lsr.l	#8, %d3
	mvz.w	%d3, %d3
	mvs.w	2(%a0,%d4.l*2), %d5
	mvs.w	(%a0,%d4.l*2), %d4
	sub.l	%d4, %d5
	muls.l	%d3, %d5
	swap	%d5
	ext.l	%d5
	add.l	%d4, %d5
	.endm

/* void macro_harm_rot(int32_t *out, int n, uint32_t phase, uint32_t inc, const int32_t *amp, int k,
 *                     const int16_t *table)
 * HARMONICS (braids_semantic.inc, harm_rot), exact : pour chaque echantillon, phase += inc ;
 *   S = I(phase) << 16, C = I(phase + 2^30) << 16, s = I(phase) << 15, c = I(phase + 2^30) << 15 ;
 *   pour j = 0..k-1 : o += amp[j] s ; s' = rd(s C + c S) ; c' = rd(c C + (-s) S) ;
 *   out = rd(o) >> 15
 * sur l'EMAC, MACSR de l'OS (0xa0 : fractionnaire signe sature, troncature) : acc0 s', acc1 c', acc2 o, rendus
 * vides. amp[k] est lu (charge parallele), inutilise.
 * Pile : 44 registres, 44 retour, 48 out, 52 n, 56 phase, 60 inc, 64 amp, 68 k, 72 table. */
	.globl	macro_harm_rot
macro_harm_rot:
	lea	-44(%sp), %sp
	movem.l	%d2-%d7/%a2-%a6, (%sp)
	move.l	52(%sp), %d0
	ble.w	9f
	movea.l	48(%sp), %a1		/* out */
	lea	(%a1,%d0.l*4), %a3
	move.l	%a3, 52(%sp)		/* fin, a la place de n */
	movea.l	56(%sp), %a4		/* phase */
	movea.l	60(%sp), %a5		/* inc */
	movea.l	72(%sp), %a0		/* table */
	moveq	#24, %d7
1:	adda.l	%a5, %a4		/* phase += inc */
	move.l	%a4, %d0
	INTERP_R %d0			/* d5 = I(phase) */
	move.l	%d5, %d2
	swap	%d2
	clr.w	%d2			/* S (Q31) */
	move.l	%d5, %d6
	asl.l	#8, %d6
	asl.l	#7, %d6			/* s (Q30), dans d6 le temps du 2e calcul */
	move.l	%a4, %d1
	addi.l	#0x40000000, %d1
	INTERP_R %d1			/* d5 = I(phase + 2^30) */
	move.l	%d5, %d3
	swap	%d3
	clr.w	%d3			/* C (Q31) */
	move.l	%d5, %d1
	asl.l	#8, %d1
	asl.l	#7, %d1			/* c (Q30) */
	move.l	%d6, %d0		/* s */
	movea.l	64(%sp), %a2
	move.l	(%a2)+, %d6		/* amp[0] */
	move.l	68(%sp), %d4		/* k */
2:	mac.l	%d6, %d0, (%a2)+, %d6, %acc2	/* o += amp s ; amp suivante */
	mac.l	%d0, %d3, %acc0			/* s C */
	mac.l	%d1, %d2, %acc0			/* + c S */
	mac.l	%d1, %d3, %acc1			/* c C */
	move.l	%d0, %d5
	neg.l	%d5
	mac.l	%d5, %d2, %acc1			/* + (-s) S */
	movclr.l %acc0, %d0			/* s' */
	movclr.l %acc1, %d1			/* c' */
	subq.l	#1, %d4
	bne.s	2b
	movclr.l %acc2, %d5
	asr.l	#8, %d5
	asr.l	#7, %d5
	move.l	%d5, (%a1)+
	cmpa.l	52(%sp), %a1
	bne.w	1b
9:	movem.l	(%sp), %d2-%d7/%a2-%a6
	lea	44(%sp), %sp
	rts

/* struct macro_drum_args { AdditiveState *a; int32_t fade_increment, f, nmg, hg; uint32_t rng; int dual; }
 * void macro_drum_render(int16_t *buffer, int n, struct macro_drum_args *g)
 * STRUCK DRUM apres ses reglages (braids_fast_digital.inc), tout le rendu en un appel, exact :
 *   1. le bruit : pour k : rng = rng * 1664525 + 1013904223 ; x = (int16)(rng >> 16) borne a +-16384 ;
 *      lp0 += (x - lp0) f >> 15 ; lp1 += (lp0 - lp1) f >> 15 ; lp2 += (lp1 - lp2) f >> 15 ; L[k] = lp2 ;
 *   2. les 6 partiels : phase += pas ; s = Interpolate824(wav_sine, phase) ;
 *      amplitude = from + (delta fade[k] >> 15), delta fade[k] = (k + 1) (delta fade_increment) ;
 *      y = s amplitude >> 16 ; H[k] += y ; P0, P1, P3 : y des partiels 0, 1, 3 (dual : les partiels 0 et 1 de meme
 *      phase et meme pas, un sinus pour les deux) ;
 *   3. le melange : s = P0 + ((P1 L >> 8) (12288 - nmg) >> 14) + ((P3 L >> 9) nmg >> 14) + (H hg >> 14) ;
 *      CLIP ; *buffer++ = (s + previous) >> 1 ; *buffer++ = s ; previous = s.
 * AdditiveState : 0 phase[11], 44 pas[11], 88 amplitude[11], 132 cible[11], 176 previous (int16), 182 lp[3]
 * (l'ABI du m68k aligne les int sur 2 octets).
 * Pile : 44 registres, 44 fade_increment, 48 from du partiel 1 (dual), 52 fin de H, 56 L[12], 104 H[12],
 * 152 P0[12], 200 P1[12], 248 P3[12], 296 rebut[12], 344 retour, 348 buffer, 352 n, 356 g. */
	.globl	macro_drum_render
macro_drum_render:
	lea	-344(%sp), %sp
	movem.l	%d2-%d7/%a2-%a6, (%sp)
	move.l	352(%sp), %d7		/* n */
	ble.w	99f
	movea.l	356(%sp), %a5		/* g */
	movea.l	(%a5), %a6		/* AdditiveState */
	move.l	4(%a5), 44(%sp)		/* fade_increment */
	lea	104(%sp,%d7.l*4), %a0
	move.l	%a0, 52(%sp)		/* fin de H */
	/* --- 1. le bruit --- */
	movem.l	182(%a6), %d2-%d4	/* lp0 lp1 lp2 */
	move.l	20(%a5), %d5		/* rng */
	move.l	8(%a5), %d6		/* f */
	lea	56(%sp), %a1		/* L */
	move.l	%d7, %d1
1:	move.l	#1664525, %d0
	muls.l	%d0, %d5
	addi.l	#1013904223, %d5
	move.l	%d5, %d0
	swap	%d0
	ext.l	%d0
	cmpi.l	#16384, %d0
	ble.s	2f
	move.l	#16384, %d0
2:	cmpi.l	#-16384, %d0
	bge.s	3f
	move.l	#-16384, %d0
3:	sub.l	%d2, %d0
	muls.l	%d6, %d0
	asr.l	#8, %d0
	asr.l	#7, %d0
	add.l	%d0, %d2
	move.l	%d2, %d0
	sub.l	%d3, %d0
	muls.l	%d6, %d0
	asr.l	#8, %d0
	asr.l	#7, %d0
	add.l	%d0, %d3
	move.l	%d3, %d0
	sub.l	%d4, %d0
	muls.l	%d6, %d0
	asr.l	#8, %d0
	asr.l	#7, %d0
	add.l	%d0, %d4
	move.l	%d4, (%a1)+
	subq.l	#1, %d1
	bne.s	1b
	movem.l	%d2-%d4, 182(%a6)
	move.l	%d5, 20(%a5)
	/* --- 2. les partiels --- */
	lea	_ZN6braids8wav_sineE, %a0	/* braids::wav_sine */
	tst.l	24(%a5)			/* dual */
	beq.s	10f
	lea	104(%sp), %a1		/* H = y0 + y1 */
	lea	152(%sp), %a3		/* P0 */
	lea	200(%sp), %a2		/* P1 */
	bsr.w	drum_two
	move.l	(%a6), 4(%a6)		/* phase[1] = phase[0] */
	bra.s	11f
10:	moveq	#0, %d0
	lea	104(%sp), %a1
	lea	152(%sp), %a3		/* P0 */
	suba.l	%a2, %a2		/* H = y */
	bsr.w	drum_one
	moveq	#1, %d0
	lea	104(%sp), %a1
	lea	200(%sp), %a3		/* P1 */
	movea.l	%a1, %a2		/* H += y */
	bsr.w	drum_one
11:	moveq	#2, %d0
	lea	104(%sp), %a1
	lea	296(%sp), %a3
	movea.l	%a1, %a2
	bsr.w	drum_one
	moveq	#3, %d0
	lea	104(%sp), %a1
	lea	248(%sp), %a3		/* P3 */
	movea.l	%a1, %a2
	bsr.w	drum_one
	moveq	#4, %d0
	lea	104(%sp), %a1
	lea	296(%sp), %a3
	movea.l	%a1, %a2
	bsr.w	drum_one
	moveq	#5, %d0
	lea	104(%sp), %a1
	lea	296(%sp), %a3
	movea.l	%a1, %a2
	bsr.w	drum_one
	/* --- 3. le melange --- */
	movea.l	348(%sp), %a0		/* buffer */
	lea	152(%sp), %a1		/* P0 */
	lea	200(%sp), %a2		/* P1 */
	lea	248(%sp), %a3		/* P3 */
	lea	56(%sp), %a4		/* L */
	lea	104(%sp), %a5		/* H */
	movea.l	356(%sp), %a6
	move.l	12(%a6), %d5		/* nmg */
	move.l	#12288, %d6
	sub.l	%d5, %d6
	move.l	16(%a6), %d3		/* hg */
	movea.l	(%a6), %a6
	mvs.w	176(%a6), %d4		/* previous */
	move.l	%d7, %d1
20:	move.l	(%a4)+, %d7		/* L */
	move.l	(%a2)+, %d0
	muls.l	%d7, %d0
	asr.l	#8, %d0
	muls.l	%d6, %d0
	asr.l	#8, %d0
	asr.l	#6, %d0
	move.l	(%a1)+, %d2
	add.l	%d0, %d2
	move.l	(%a3)+, %d0
	muls.l	%d7, %d0
	asr.l	#8, %d0
	asr.l	#1, %d0
	muls.l	%d5, %d0
	asr.l	#8, %d0
	asr.l	#6, %d0
	add.l	%d0, %d2
	move.l	(%a5)+, %d0
	muls.l	%d3, %d0
	asr.l	#8, %d0
	asr.l	#6, %d0
	add.l	%d0, %d2
	CLIPD	%d2
	move.l	%d2, %d0
	add.l	%d4, %d0
	asr.l	#1, %d0
	move.w	%d0, (%a0)+
	move.w	%d2, (%a0)+
	move.l	%d2, %d4
	subq.l	#1, %d1
	bne.w	20b
	move.w	%d4, 176(%a6)
99:	movem.l	(%sp), %d2-%d7/%a2-%a6
	lea	344(%sp), %sp
	rts

/* un partiel d0 (0..5) de l'AdditiveState a6 : y dans a3 ; H (a1) = y si a2 = 0, sinon H += y. d7 = n, a0 = table,
 * gardes ; a2 detruit. Pile de macro_drum_render a 4 octets de plus (le retour) : fade_increment a 48. */
drum_one:
	lea	(%a6,%d0.l*4), %a5	/* &phase[i] */
	move.l	(%a5), %d0		/* phase */
	move.l	44(%a5), %d1		/* pas */
	move.l	88(%a5), %d6		/* from */
	move.l	132(%a5), %d3
	sub.l	%d6, %d3		/* delta */
	muls.l	48(%sp), %d3		/* delta * fade_increment */
	movea.l	%d3, %a4
	moveq	#0, %d2			/* delta * fade[k] */
	move.l	%a2, %d3		/* (INTERP detruit d3 et d4 : la fin par pointeur) */
	lea	(%a3,%d7.l*4), %a2	/* fin de a3 */
	tst.l	%d3
	bne.s	2f
1:	add.l	%d1, %d0
	INTERP
	add.l	%a4, %d2
	move.l	%d2, %d3
	asr.l	#8, %d3
	asr.l	#7, %d3
	add.l	%d6, %d3		/* amplitude */
	muls.l	%d3, %d5
	swap	%d5
	ext.l	%d5			/* y */
	move.l	%d5, (%a1)+
	move.l	%d5, (%a3)+
	cmpa.l	%a2, %a3
	bne.s	1b
	bra.s	3f
2:	add.l	%d1, %d0
	INTERP
	add.l	%a4, %d2
	move.l	%d2, %d3
	asr.l	#8, %d3
	asr.l	#7, %d3
	add.l	%d6, %d3
	muls.l	%d3, %d5
	swap	%d5
	ext.l	%d5
	add.l	%d5, (%a1)+
	move.l	%d5, (%a3)+
	cmpa.l	%a2, %a3
	bne.s	2b
3:	move.l	%d0, (%a5)		/* phase */
	rts

/* les partiels 0 et 1 de meme phase et meme pas : un sinus, deux amplitudes ; H (a1) = y0 + y1, P0 (a3), P1 (a2).
 * Pile : fade_increment a 48, from du partiel 1 a 52, fin de H a 56 (macro_drum_render + le retour). */
drum_two:
	move.l	(%a6), %d0		/* phase */
	move.l	44(%a6), %d1		/* pas */
	move.l	88(%a6), %d6		/* from0 */
	move.l	132(%a6), %d3
	sub.l	%d6, %d3
	muls.l	48(%sp), %d3
	movea.l	%d3, %a4		/* pas de l'amplitude 0 */
	move.l	92(%a6), %d3		/* from1 */
	move.l	%d3, 52(%sp)
	move.l	136(%a6), %d4
	sub.l	%d3, %d4
	muls.l	48(%sp), %d4
	movea.l	%d4, %a5		/* pas de l'amplitude 1 */
	moveq	#0, %d2			/* delta0 fade */
	moveq	#0, %d7			/* delta1 fade (n est relu a la fin) */
1:	add.l	%d1, %d0
	INTERP				/* s dans d5 */
	move.l	%d5, %d4
	add.l	%a4, %d2
	move.l	%d2, %d3
	asr.l	#8, %d3
	asr.l	#7, %d3
	add.l	%d6, %d3
	muls.l	%d3, %d5
	swap	%d5
	ext.l	%d5			/* y0 */
	move.l	%d5, (%a3)+
	add.l	%a5, %d7
	move.l	%d7, %d3
	asr.l	#8, %d3
	asr.l	#7, %d3
	add.l	52(%sp), %d3
	muls.l	%d3, %d4
	swap	%d4
	ext.l	%d4			/* y1 */
	move.l	%d4, (%a2)+
	add.l	%d4, %d5
	move.l	%d5, (%a1)+		/* H = y0 + y1 */
	cmpa.l	56(%sp), %a1
	bne.s	1b
	move.l	%d0, (%a6)		/* phase[0] */
	move.l	352+4(%sp), %d7		/* n */
	rts
