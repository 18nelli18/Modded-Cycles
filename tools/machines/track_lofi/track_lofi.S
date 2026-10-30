/* Lo-fi de piste sur toutes les machines (notes/86) : Lo-Fi Rate (k 27) et Lo-Fi Bits (k 30).
 * Lié par track_lofi.ld dans deux masques de sprite 48x22 libérés (tools/sprites.py, 192 o chacun), écrit avec
 * Model-TG (tools/track_lofi.py) : ses descripteurs (ids 1 et 2, build.py de Model-TG) nomment ces deux mots, et des
 * instructions de Model-TG remplacées à taille égale sautent ici.
 *
 * Rangement : la case 18 de l'enregistrement du son (+64/+65), que la sauvegarde de l'OS n'écrit jamais (sa table
 * k -> case saute 0x12) ; un octet chacun, l'octet fort du mot (0..127 << 8 = 0..32512). Les anciens enregistrements y
 * ont 0 : lo-fi éteint. Au chargement, l'OS y lit k 0 (puis lfo_tail de lfo-plus y remet WAVE de LFO 2) : on ne
 * touche qu'à k 27 et k 30, après lui.
 *
 * Valeurs : 0 = OFF ; Rate v = 1..127 -> pas (v + 1) / 2 = 1..64 de MACRO (46K..4K, lofi_khz de
 * gen_syntakt_engines.py) ; Bits v = 1..127 -> 12 - 10 (v - 1) / 126 = 12B..2B. */

	.include "tl_tables.inc"

	.globl	tl_save, tl_load, tl_dh, tl_atk
	.globl	tl_s_rate, tl_s_rte, tl_s_bits, tl_s_bts
	.globl	tl_fmt_r, tl_fmt_b, tl_draw_r, tl_draw_b, tl_post, tl_trk, tl_st, tl_inc

	.equ	UI_REC, 0x40a71754		/* objets d'interface des descripteurs, 100 o chacun (0x4004df40) */
	.equ	UI_RATE, UI_REC + 100 * 1
	.equ	UI_BITS, UI_REC + 100 * 2
	.equ	SPRINTF, 0x40000e6e
	.equ	S_OFF, 0x40124b67		/* "OFF" de l'OS */

	.section .text.track_lofi, "ax"

/* À la place de « movel %sp@,%d0 ; addql #8,%sp ; rts » à la fin de snd_save_post (Model-TG) : a0 = enregistrement,
 * a1 = son ; sp@(0) garde d0 (le résultat de la sauvegarde), sp@(4) le son. d1 libre. */
tl_save:
	move.b	74(%a1), 64(%a0)		/* k 27 (son + 20 + 54), octet fort -> case 18, premier octet */
	move.b	80(%a1), 65(%a0)		/* k 30 (son + 20 + 60) -> case 18, second octet */
	move.l	(%sp), %d0
	addq.l	#8, %sp
	rts

/* À la place de « movel %sp@,%d0 ; addql #8,%sp ; rts » à la fin de snd_load_post (Model-TG) : a0 = enregistrement,
 * a1 = son. Un octet au-dessus de 127 (jamais écrit par tl_save) vaut 0. Pose aussi nos fonctions d'interface (le
 * chargement d'un projet passe ici avant tout affichage de ses p-locks). */
tl_load:
	lea	64(%a0), %a0
	moveq	#74, %d0
	bsr.s	1f
	moveq	#80, %d0
	bsr.s	1f
	bsr.s	tl_ui
	move.l	(%sp), %d0
	addq.l	#8, %sp
	rts
1:	moveq	#0, %d1
	move.b	(%a0)+, %d1
	bpl.s	2f
	moveq	#0, %d1
2:	lsl.l	#8, %d1
	move.w	%d1, (%a1, %d0.l)
	rts

/* À la place de « movel #other_descr,%d0 » dans dh_pass (Model-TG : MACHINES tenue, machine d'origine ; a0 =
 * other_descr, la copie de son descripteur) : COLOR et SHAPE (positions 2 et 3) -> Lo-Fi Rate et Bits, comme
 * DECAY, SWEEP, CONTOUR -> Attack, Filtre, Résonance. d1 rendu par dh_pass. */
tl_dh:
	moveq	#1, %d1
	move.l	%d1, 16(%a0)
	moveq	#2, %d1
	move.l	%d1, 20(%a0)
	move.l	%a0, %d0
	bra.s	tl_ui

/* À la place de « moveq #0x0d,%d1 ; movel %d1,%a0@(12) » où sampler_pre fait sampler_descr_atk (a0), le descripteur
 * du Sampler sous MACHINES (rendu tel quel en modes 0..2, recopié par smf_descr en modes 3..6) : Attack en
 * position 1, et Rate / Bits en 2 et 3. */
tl_atk:
	moveq	#0x0d, %d1
	move.l	%d1, 12(%a0)
	moveq	#1, %d1
	move.l	%d1, 16(%a0)
	moveq	#2, %d1
	move.l	%d1, 20(%a0)
	/* suite : tl_ui */

/* Texte (+0x20) et dessin dans la fenêtre de valeur (+0x30) des objets d'interface de nos deux descripteurs, faits
 * au démarrage de l'interface. Détruit d1. */
tl_ui:
	move.l	#tl_fmt_r, %d1
	move.l	%d1, UI_RATE + 0x20
	move.l	#tl_fmt_b, %d1
	move.l	%d1, UI_BITS + 0x20
	move.l	#tl_draw_r, %d1
	move.l	%d1, UI_RATE + 0x30
	move.l	#tl_draw_b, %d1
	move.l	%d1, UI_BITS + 0x30
	rts

tl_s_rate:	.asciz	"Lo-Fi Rate"
tl_s_rte:	.asciz	"RATE"
tl_s_bits:	.asciz	"Lo-Fi Bits"
tl_s_bts:	.asciz	"BITS"

	.section .text.tl_fmt, "ax"

/* (fonction, valeur, tampon) : le texte de la valeur, comme lofi_fmt de MACRO. d0-d1/a0-a1 libres. */
tl_fmt_r:
	bsr.s	tl_v
	beq.s	tl_off
	addq.l	#1, %d0
	lsr.l	#1, %d0				/* 1..64 */
	lea	tl_khz, %a0
	mvz.b	-1(%a0, %d0.l), %d0
	lea	tl_s_k, %a0
	bra.s	tl_pr
tl_fmt_b:
	bsr.s	tl_v
	beq.s	tl_off
	subq.l	#1, %d0
	moveq	#10, %d1
	mulu.l	%d1, %d0
	moveq	#126, %d1
	divu.l	%d1, %d0
	moveq	#12, %d1
	sub.l	%d0, %d1
	move.l	%d1, %d0			/* 12..2 */
	lea	tl_s_b, %a0
tl_pr:
	move.l	%d0, -(%sp)
	move.l	%a0, -(%sp)
	move.l	20(%sp), -(%sp)
	jsr	SPRINTF
	lea	12(%sp), %sp
	rts
tl_off:
	pea	S_OFF
	move.l	16(%sp), -(%sp)
	jsr	SPRINTF
	addq.l	#8, %sp
	rts
/* d0 = la valeur arrondie au pas (0..127), Z si 0 ; la valeur est en 12(sp) (appelé par bsr) */
tl_v:
	move.l	12(%sp), %d0
	addi.l	#0x80, %d0
	asr.l	#8, %d0
	bpl.s	1f
	moveq	#0, %d0
1:	moveq	#127, %d1
	cmp.l	%d1, %d0
	ble.s	2f
	move.l	%d1, %d0
2:	tst.l	%d0
	rts

	.section .text.tl_draw, "ax"

/* (fonction, valeur, bitmap, x, y, drapeau) : le texte dans la fenêtre de valeur, comme lofi_draw de MACRO
 * (0x40071a04, grande police 0x401429ec, alignement 2, « %s »), à la place de la jauge. */
tl_draw_r:
	lea	tl_fmt_r, %a1
	bra.s	tl_draw
tl_draw_b:
	lea	tl_fmt_b, %a1
tl_draw:
	lea	-24(%sp), %sp
	move.l	%sp, %d0
	move.l	%d0, -(%sp)
	move.l	36(%sp), -(%sp)
	clr.l	-(%sp)
	jsr	(%a1)
	lea	12(%sp), %sp
	pea	0x401429ec
	pea	20(%sp)
	jsr	0x40072260
	addq.l	#8, %sp
	move.l	%sp, %d0
	move.l	%d0, -(%sp)
	pea	0x40124b58
	pea	2
	move.l	56(%sp), -(%sp)
	move.l	56(%sp), -(%sp)
	pea	36(%sp)
	move.l	60(%sp), -(%sp)
	jsr	0x40071a04
	lea	28(%sp), %sp
	pea	16(%sp)
	jsr	0x40072080
	lea	28(%sp), %sp
	rts

tl_s_k:	.asciz	"%dK"
tl_s_b:	.asciz	"%dB"
tl_khz:	TL_KHZ

/* ================================================================== le son =================================
 * Après Volume + Dist, sur les 6 pistes (Q31, 32 trames par bloc, 0x80001858 + 128 t), comme le filtre par piste
 * (notes/47 §2) : échantillonnage-blocage puis masque de bits, l'algorithme de lofi_apply de Model-TG et les pas du
 * lo-fi de MACRO. Rate : la phase (Q16) avance de 2^(-86 r / 1536) par trame (r = 1..64), chaque passage de 1 prend
 * une nouvelle valeur ; Bits : la valeur prise garde ses b bits forts (b = 12..2, 32 - b bits de poids faible à 0).
 * Une piste dont les deux sont à 0 n'est pas touchée (bit pour bit) et sa phase est remise pour prendre la première
 * trame dès qu'elle repart. Les mots lus sont les mots lissés (+14 + 66 t + 2 k : p-locks, LFO, vélocité compris),
 * arrondis au pas et bornés à 0..127. Une piste Sampler en stéréo (sx_on de Model-TG) a son côté dans sx_side, avec
 * la même phase : la même valeur tenue des deux côtés. */

	.equ	TRK, 0x80001858
	.equ	VOLDIST, 0x40056f58

	.section .text.tl_post, "ax"

/* 0x40059852 : jsr tl_post à la place de jsr 0x40056f58 ; 4(sp) = 0x80001858, 8(sp) = a2 (mots lissés, 0x8000100c),
 * comme pour l'appel remplacé. Garde d2-d7/a2-a6. */
tl_post:
	move.l	8(%sp), -(%sp)
	move.l	8(%sp), -(%sp)
	jsr	VOLDIST
	addq.l	#8, %sp
	lea	-36(%sp), %sp
	movem.l	%d2-%d7/%a2-%a4, (%sp)
	movea.l	44(%sp), %a2
	lea	14 + 54(%a2), %a2		/* k 27 de la piste 0 ; k 30 en +6 */
	lea	TRK, %a0
	lea	SX_SIDE, %a4
	lea	tl_st, %a3
	moveq	#5, %d7
1:	jsr	tl_trk
	lea	66(%a2), %a2
	lea	128(%a0), %a0
	lea	128(%a4), %a4
	lea	12(%a3), %a3
	subq.l	#1, %d7
	bpl.s	1b
	movem.l	(%sp), %d2-%d7/%a2-%a4
	lea	36(%sp), %sp
	rts

/* par piste : phase (Q16), valeur tenue, valeur tenue du côté ; dans le masque, donc rechargé depuis la flash à chaque
 * démarrage : 0xffff, la première trame jouée est prise */
tl_st:	.fill	6 * 3, 4, 0x0000ffff

	.section .text.tl_trk, "ax"

/* une piste : a2 = son mot k 27 lissé, a0 = son bloc, a4 = son côté, a3 = son état (phase, tenue, tenue du côté).
 * Détruit d0-d6, a1. */
tl_trk:
	mvs.w	(%a2), %d0			/* Rate */
	bsr.w	tl_q
	move.l	#65536, %d3			/* éteint : chaque trame prise */
	tst.l	%d0
	beq.s	1f
	addq.l	#1, %d0
	lsr.l	#1, %d0				/* r = 1..64 */
	lea	tl_inc, %a1
	mvz.w	-2(%a1, %d0.l*2), %d3
1:	mvs.w	6(%a2), %d0			/* Bits */
	bsr.w	tl_q
	moveq	#-1, %d4
	tst.l	%d0
	beq.s	2f
	subq.l	#1, %d0
	moveq	#10, %d1
	mulu.l	%d1, %d0
	moveq	#126, %d1
	divu.l	%d1, %d0
	moveq	#20, %d1
	add.l	%d1, %d0			/* 32 - b, b = 12..2 */
	lsl.l	%d0, %d4
	bra.s	3f
2:	cmpi.l	#65536, %d3
	bne.s	3f
	move.l	#0xffff, (%a3)			/* les deux à 0 : rien ; la prochaine trame sera prise */
	rts
3:	move.l	(%a3), %d5
	move.l	4(%a3), %d6
	move.l	8(%a3), %d1
	movea.l	%a0, %a1
	moveq	#31, %d2
	move.l	%a4, -(%sp)
4:	add.l	%d3, %d5
	cmpi.l	#65536, %d5
	bcs.s	5f
	subi.l	#65536, %d5
	move.l	(%a1), %d6
	and.l	%d4, %d6
	move.l	(%a4), %d1
	and.l	%d4, %d1
5:	move.l	%d6, (%a1)+
	move.l	%d1, (%a4)+
	subq.l	#1, %d2
	bpl.s	4b
	movea.l	(%sp)+, %a4
	move.l	%d5, (%a3)
	move.l	%d6, 4(%a3)
	move.l	%d1, 8(%a3)
	rts

/* d0 = mot -> pas 0..127 (arrondi, borné) */
tl_q:
	addi.l	#0x80, %d0
	asr.l	#8, %d0
	bpl.s	1f
	moveq	#0, %d0
1:	moveq	#127, %d1
	cmp.l	%d1, %d0
	ble.s	2f
	move.l	%d1, %d0
2:	rts

	.section .text.tl_data, "ax"
tl_inc:	TL_INC					/* 64 mots : 65536 x 2^(-86 r / 1536), r = 1..64 */
