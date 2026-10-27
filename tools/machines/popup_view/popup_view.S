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
 *   - 0x0d -> PV_DECAY (Amp Decay : courbe 50x22 qui suit la valeur, grand nombre, points), la courbe prise en
 *     sens inverse puis retournée de gauche à droite : x PV_X0..PV_X1, y 8..29 (l'écran compte y depuis le bas).
 * La fenêtre est redessinée en entier à chaque image (0x4001e40a). */
#define PV_INVOKE	(0x40a71754 + PV_DECAY * 100 + 0x60)	/* invocateur de la courbe d'Amp Decay */
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

/* Attack : la fenêtre d'Amp Decay sur une copie des six arguments, avec la VRAIE valeur (grand nombre, points).
 * Seule la courbe change : 0x4001d818 la dessine par vt[68] (0x4000a6b0), qui appelle le std::function de l'objet
 * d'interface, invocateur +0x60 (Amp Decay : 0x4004e40c) en (foncteur +0x54, écran, x, y, valeur), à part du
 * formateur du nombre. Le temps de l'appel, cet invocateur devient pv_curve, puis l'ancien est remis : le dessin
 * est d'une seule tâche et rien d'autre ne lit le champ entre les deux. Ensuite la courbe est retournée. */
pv_attack:
	lea	-12(%sp), %sp
	movem.l	%d2-%d4, (%sp)
	lea	PV_INVOKE, %a1
	move.l	(%a1), -(%sp)			/* l'invocateur d'Amp Decay, remis au retour */
	lea	pv_curve, %a0
	move.l	%a0, (%a1)
	moveq	#5, %d1
4:	move.l	40(%sp), -(%sp)			/* 6e argument d'abord : 40 = 4 + 12 (registres) + 4 (retour) + 20 */
	subq.l	#1, %d1
	bpl.s	4b
	moveq	#PV_DECAY, %d0
	move.l	%d0, 8(%sp)			/* id de la copie */
	jsr	0x4001d818
	lea	24(%sp), %sp
	move.l	(%sp)+, PV_INVOKE
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

/* La courbe d'Attack : 0x4004e40c prend la trame (valeur >> 8) * 13 / 127 du vecteur 0x40fe401c (15 trames, la
 * dernière jamais atteinte). L'attack et l'amplitude tournent en sens inverse : on lui passe 0x7f00 - valeur
 * (0 -> trame 13, 0x7f00 -> trame 0), écrite sur place. La valeur est une copie : vt[68] a réécrit ses propres
 * arguments avant de sauter ici, et 0x4001d818 garde la sienne dans d5. */
pv_curve:
	move.l	#0x7f00, %d0
	sub.l	20(%sp), %d0
	move.l	%d0, 20(%sp)			/* (retour, foncteur, écran, x, y, valeur) */
	jmp	0x4004e40c
