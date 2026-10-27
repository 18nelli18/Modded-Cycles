/* Fenêtre de valeur d'Attack, du Filtre et de la Résonance de Model-TG (notes/82). Lié par popup_view.ld dans un
 * masque de sprite libéré ; écrit avec Model-TG par tools/popup_view.py (gen_model_tg.py).
 *
 * Model-TG met Attack (0x0d), Filtre (0x0c) et Résonance (0x0b) sous MACHINES + DECAY / SWEEP / CONTOUR. Ce sont
 * des identifiants « Error » de l'OS : leur objet d'interface (UI_REC 0x40a71754 + id*100) n'a pas de dessin (+0x5c
 * nul) et remplace le grand nombre par un petit potard (+0x2c, vt[64] 0x4000a66a rend 1). La fenêtre de valeur
 * (slot 144 de ParameterPageView, 0x4001d818) est appelée en (vue, écran, id, valeur, verrou, 1) par le rendu
 * 0x4001e40a, APRÈS le cadre du nom : Model-TG la détourne (wf_popup) et, hors Start/End du Sampler, saute ici par
 * wp_stock. Le nom affiché reste donc celui de l'identifiant d'origine ; seul le dessin prend un autre identifiant :
 *   - 0x0c -> 0x49 et 0x0b -> 0x4a : les Filtre et Résonance du Sampler (courbes 48x22, grand nombre, points) ;
 *   - 0x0d -> PV_DECAY (Amp Decay : courbe 50x22 qui suit la valeur, grand nombre, points), puis la courbe est
 *     retournée de gauche à droite : x PV_X0..PV_X1, y 8..29 (l'écran compte y depuis le bas).
 * La fenêtre est redessinée en entier à chaque image (0x4001e40a) : retourner après le dessin d'origine est sûr. */
	.globl	pv_popup

	.section .text.popup_view, "ax"
pv_popup:
	move.l	12(%sp), %d0			/* l'identifiant */
	moveq	#0x0c, %d1
	cmp.l	%d1, %d0
	bne.s	1f
	moveq	#0x49, %d1			/* Filtre -> celui du Sampler */
	bra.s	2f
1:	moveq	#0x0b, %d1
	cmp.l	%d1, %d0
	bne.s	3f
	moveq	#0x4a, %d1			/* Résonance -> celle du Sampler */
2:	move.l	%d1, 12(%sp)
	jmp	0x4001d818
3:	moveq	#0x0d, %d1
	cmp.l	%d1, %d0
	beq.s	pv_attack
	jmp	0x4001d818

/* Attack : la fenêtre d'Amp Decay sur une copie des six arguments, puis la courbe retournée. */
pv_attack:
	lea	-12(%sp), %sp
	movem.l	%d2-%d4, (%sp)
	moveq	#5, %d1
4:	move.l	36(%sp), -(%sp)			/* 6e argument d'abord : 36 = 12 (registres) + 4 (retour) + 20 */
	subq.l	#1, %d1
	bpl.s	4b
	moveq	#PV_DECAY, %d0
	move.l	%d0, 8(%sp)			/* id de la copie */
	jsr	0x4001d818
	lea	24(%sp), %sp
	movea.l	20(%sp), %a0			/* l'écran (Bitmap) */
	movea.l	16(%a0), %a1			/* ses pixels : colonnes de 12(a0) mots, bit 31 - y du mot 0 pour y < 32 */
	move.l	12(%a0), %d2
	lsl.l	#2, %d2				/* octets par colonne */
	moveq	#PV_X0, %d0
	mulu.l	%d2, %d0
	lea	0(%a1,%d0.l), %a0		/* colonne PV_X0 */
	moveq	#PV_X1, %d0
	mulu.l	%d2, %d0
	adda.l	%d0, %a1			/* colonne PV_X1 */
	move.l	#0x00fffffc, %d3		/* y 8..29 : bits 23..2 */
	moveq	#(PV_X1 - PV_X0 - 1) / 2, %d1
5:	move.l	(%a0), %d0
	move.l	(%a1), %d4
	eor.l	%d0, %d4
	and.l	%d3, %d4			/* les bits qui diffèrent entre les deux colonnes */
	eor.l	%d4, (%a0)
	eor.l	%d4, (%a1)
	adda.l	%d2, %a0
	suba.l	%d2, %a1
	subq.l	#1, %d1
	bpl.s	5b
	movem.l	(%sp), %d2-%d4
	lea	12(%sp), %sp
	rts
