/* LFO 2, 3, 4 : trois LFO de plus par piste (idée de DavidCaruso, Model-TG-VA-DR-v1 ; réécrit ici, notes/56 §3).
 *
 * Sur la page LFO, chaque appui bref sur [LFO] passe de LFO 1 à LFO 2, 3, 4 au relâchement (un grand chiffre dans le
 * cadre de gauche), le 5e ferme la page ; [LFO] tenue avec un potard tourné (l'affectation de destination de l'OS)
 * ou une autre touche garde la page. Chaque LFO de plus a ses réglages SPD, MULT, WAVE, DEST, DEP ; FADE, SPH, MODE
 * (et le retrig) sont ceux de LFO 1. LFO 2 est rangé dans les mots k = 28..32 du son (libres dans l'OS et sous
 * Model-TG) : sauvé avec le son (4 octets libres de l'enregistrement, +88..+91) et p-lockable. LFO 3 et LFO 4 ont un
 * bloc par kit (les 96 patterns du projet) en mémoire (T34), sauvé dans 52 octets inutilisés de l'enregistrement du
 * kit, remis aux défauts avec le son de la piste, emporté par les copies de kit entier ; pas de p-lock.
 *
 * Moteur (interruption audio) : pour chaque LFO de plus utilisé, un faux « obj » (même forme que celui de la
 * fonction audio : 14 o + 6 pistes × 66 o) reçoit ses réglages et FADE/SPH/MODE de LFO 1 ; on met son état à la
 * place de celui de l'OS (0x40fde838, 6 × 32 o), on appelle la vraie fonction des LFO (0x40091ab2), on reprend
 * l'état, puis on ajoute la modulation calculée au vrai mot de la piste (borné 0..0x7f00 comme l'OS), sauf si la
 * destination est celle de LFO 1. Les LFO de plus passent avant LFO 1 : ils peuvent moduler ses réglages.
 *
 * Mémoire de travail (états, faux obj) : SCR ; blocs LFO 3/4 des 96 kits et tampons de kit retenus : SCR34 (sous SCR).
 * Les deux au-dessus du BSS de l'OS (0x423380b0) et sous ses tampons DMA
 * (0x42340000), où ni l'OS ni aucun autre mod n'écrit (notes/56 §3) ; pas remise à zéro au démarrage : les états
 * sont mis à zéro (et les blocs LFO 3/4 aux défauts, drapeau « kready ») au premier usage après chaque démarrage
 * (drapeau « ready » dans un masque, que le démarrage
 * recharge à 0 depuis la flash ; un mot magique en SDRAM pourrait survivre à une coupure brève). Le reste (code,
 * réglages de LFO 3/4, variables de la page) est dans des masques de sprites libérés (tools/gen_lfo_plus.py les
 * place) ; ces zones de l'image sont rechargées de la flash à chaque démarrage.
 *
 * Convention de l'OS : arguments sur la pile, résultat dans d0, d0-d1/a0-a1 libres, d2-d7/a2-a6 gardés. Les
 * accroches au milieu d'une fonction de l'OS gardent en plus ce que la suite de la fonction attend (dit à chacune).
 * Les écritures sur l'OS sont dans tools/gen_lfo_plus.py (HOOKS, PTRS). */

	.equ	LFO_FN, 0x40091ab2		/* (obj, tempo, masque des retrigs) : les 6 LFO de l'OS */
	.equ	LFO_ST, 0x40fde838		/* leur état, 6 × 32 o : +16 destination, +20 quantité */
	.equ	CUR_PROJ, 0x400cf866		/* projet courant */
	.equ	PROJ_SEQ, 0x4000eb90		/* projet + 48 */
	.equ	SEL_TRACK, 0x40012412		/* piste sélectionnée */
	.equ	NEEDS_REDRAW, 0x40076082	/* View::setNeedsRedraw(vue) */
	.equ	KEY_CODE, 0x4007240c		/* code de la touche d'un événement */
	.equ	FILL_RECT, 0x40070dea		/* (bitmap, x0, y0, x1, y1, couleur) ; couleur < 0 : inverse */
	.equ	TEXT, 0x40071a04		/* (bitmap, police, x, y, drapeaux, format, ...) ; 2 = centré */
	.equ	TITLE_FONT, 0x40ea14d4		/* police du nom de la page (cadre de gauche) */

	.equ	S_LFO1, SCR			/* état de LFO 1 pendant les LFO de plus */
	.equ	S_ST2, SCR + 192		/* états des LFO 2, 3, 4 (192 o chacun) */
	.equ	S_ST3, SCR + 384
	.equ	S_ST4, SCR + 576
	.equ	S_FOBJ, SCR + 768		/* faux obj : 14 + 6 × 66 = 410 o */
	.equ	S_END, SCR + 1180

	.equ	CUR_KIT, 0x40a78888		/* le kit joué (pointeur) */
	.equ	KITS, 0x409c9c80		/* les 96 kits du projet, KIT_SZ o chacun */
	.equ	KIT_SZ, 7094
	.equ	L34_MAGIC, 0x4c463334		/* « LF34 », en +648 de l'enregistrement d'un kit */
	.equ	T34, SCR34			/* 96 blocs de 120 o : LFO 3 puis LFO 4, 6 pistes × 5 mots */
	.equ	BUFK, SCR34 + 11520		/* 4 tampons de kit retenus (adresses ; -1 : aucun) */
	.equ	BUFN, SCR34 + 11536		/* prochaine case à reprendre */
	.equ	BUFD, SCR34 + 11540		/* leurs blocs (4 × 120 o) */
	.equ	S34_END, SCR34 + 12020

	.equ	K28, 56				/* octet du mot k = 28 dans une piste (2k) */

	.globl	lfo_audio, lfo_id2k, lfo_get, lfo_set, lfo_key, lfo_draw, lfo_ctor, lfo_dtor, lfo_gate, lfo_dest
	.globl	lfo_pack, lfo_unpack, lfo_init, lfo_plk_save, lfo_plk_load, lfo_tail
	.globl	page, pend, ready, kready, view, lfo34, slots, sel_track, slot_of_id, copy192, run_set, taken, audio_sets
	.globl	audio_done, cur34, blk34, snd34, pk5, upk5, dflt5, kit_save, kit_load, kit_copy, buf_find, buf_put
	.globl	lfo_learn, lfo_led

/* ================================================================== moteur, interruption audio ============ */

	.section .text.audio, "ax"

/* 0x400597c6, dans la fonction audio (0x4005979e) : jsr lfo_audio à la place de jsr 0x40091ab2(obj, tempo,
 * masque). a3 = l'argument de la fonction audio : (a3) = les cibles des paramètres (même forme que obj), d'où le
 * lissage 0x40058474 tire les mots de obj. Rend comme l'appel d'origine (d2-d7/a2-a6 gardés). */
lfo_audio:
	lea	-44(%sp), %sp
	movem.l	%d2-%d7/%a2-%a6, (%sp)		/* obj 48(sp), tempo 52(sp), masque 56(sp) */
	movea.l	48(%sp), %a4
	movea.l	(%a3), %a0
	/* k = 31 (destination de LFO 2) recopié brut des cibles, comme l'OS le fait pour k = 4 (0x400584d6) :
	 * sans lissage, la destination ne passe pas par les destinations intermédiaires. */
	lea	62+14(%a4), %a1
	lea	62+14(%a0), %a0
	moveq	#0, %d1
	moveq	#0, %d2				/* d2 : bit 0 LFO 2, bit 1 LFO 3, bit 2 LFO 4 utilisés */
	moveq	#6, %d0
1:	move.w	(%a0), %d1
	move.w	%d1, (%a1)
	or.l	%d1, %d2
	lea	66(%a0), %a0
	lea	66(%a1), %a1
	subq.l	#1, %d0
	bne.s	1b
	andi.l	#0xff00, %d2
	sne	%d2
	andi.l	#1, %d2
	jsr	cur34				/* bloc du kit joué : destinations de LFO 3 puis LFO 4, */
	addq.l	#6, %a0				/* 6 pistes chacun */
	moveq	#2, %d3
	moveq	#2, %d4				/* deux tables */
	moveq	#0, %d5
2:	moveq	#6, %d0
	moveq	#0, %d1
3:	move.w	(%a0), %d5
	or.l	%d5, %d1
	lea	10(%a0), %a0
	subq.l	#1, %d0
	bne.s	3b
	andi.l	#0xff00, %d1
	beq.s	4f
	or.l	%d3, %d2
4:	add.l	%d3, %d3
	subq.l	#1, %d4
	bne.s	2b
	tst.l	%d2
	bne.s	1f
audio_done:
	movem.l	(%sp), %d2-%d7/%a2-%a6		/* LFO 1 : l'appel d'origine, mêmes arguments */
	lea	44(%sp), %sp
	jmp	LFO_FN
1:	jmp	audio_sets

	.section .text.audio2, "ax"

/* Suite de lfo_audio quand au moins un LFO de plus est utilisé (d2 : lesquels ; pile de lfo_audio). */
audio_sets:
	movea.l	%d2, %a6
	move.l	52(%sp), %d6			/* tempo */
	move.l	56(%sp), %d7			/* masque des retrigs */
	tst.b	ready
	bne.s	5f
	lea	S_ST2, %a0			/* premier usage depuis le démarrage : états à zéro */
	move.l	#(192 * 3) / 4, %d0
6:	clr.l	(%a0)+
	subq.l	#1, %d0
	bne.s	6b
	moveq	#1, %d0
	move.b	%d0, ready
5:	lea	LFO_ST, %a0
	lea	S_LFO1, %a1
	jsr	copy192
	move.l	%a6, %d0
	btst	#0, %d0
	beq.s	7f
	/* LFO 2 : SPD, MULT, DEST, DEP dans les mots k = 28, 29, 31, 32 de obj ; WAVE dans le mot k = 0 des CIBLES
	 * (notes/86 §3) : k 30 est à Lo-Fi Bits, et dans obj le mot k 0 reçoit la modulation de LFO 1 et de la
	 * vélocité quand leur destination est None (0x40091d1c, 0x40056e88). Table de 6 × 10 o sur la pile, au format
	 * de LFO 3/4 ; les cibles = (a3) de la fonction audio, a3 empilé par lfo_audio en 28(sp). */
	movea.l	28(%sp), %a2
	movea.l	(%a2), %a2
	lea	14(%a2), %a2			/* cibles, mot k = 0 de la piste 0 */
	lea	-60(%sp), %sp
	lea	14+K28(%a4), %a0
	movea.l	%sp, %a1
	moveq	#6, %d0
9:	move.w	(%a0), (%a1)			/* SPD */
	move.w	2(%a0), 2(%a1)			/* MULT */
	move.w	(%a2), 4(%a1)			/* WAVE */
	move.w	6(%a0), 6(%a1)			/* DEST */
	move.w	8(%a0), 8(%a1)			/* DEP */
	lea	66(%a0), %a0
	lea	66(%a2), %a2
	lea	10(%a1), %a1
	subq.l	#1, %d0
	bne.s	9b
	movea.l	%sp, %a0
	moveq	#10, %d0
	lea	S_ST2, %a5
	jsr	run_set
	lea	60(%sp), %sp
7:	move.l	%a6, %d0
	btst	#1, %d0
	beq.s	8f
	jsr	cur34				/* LFO 3, du kit joué */
	moveq	#10, %d0
	lea	S_ST3, %a5
	jsr	run_set
8:	move.l	%a6, %d0
	btst	#2, %d0
	beq.s	10f
	jsr	cur34				/* LFO 4 */
	lea	60(%a0), %a0
	moveq	#10, %d0
	lea	S_ST4, %a5
	jsr	run_set
10:	lea	S_LFO1, %a0
	lea	LFO_ST, %a1
	jsr	copy192
	jmp	audio_done

	.section .text.run_set, "ax"

/* Un jeu de 6 LFO de plus. a0 = réglages de la piste 0 ({SPD, MULT, WAVE, DEST, DEP}, mots), d0 = pas entre deux
 * pistes, a5 = état du jeu (192 o), a4 = obj, d6 = tempo, d7 = masque. Détruit d0-d5/a0-a3/a5. */
run_set:
	lea	S_FOBJ+14, %a1
	lea	14(%a4), %a2
	moveq	#6, %d5
1:	move.w	(%a0), 2(%a1)			/* k1 vitesse */
	move.w	2(%a0), 4(%a1)			/* k2 multiplicateur */
	move.w	6(%a2), 6(%a1)			/* k3 fondu : celui de LFO 1 */
	move.w	6(%a0), 8(%a1)			/* k4 destination */
	move.w	4(%a0), 10(%a1)			/* k5 forme */
	move.w	12(%a2), 12(%a1)		/* k6 phase de départ, k7 mode : ceux de LFO 1 */
	move.w	14(%a2), 14(%a1)
	move.w	8(%a0), 16(%a1)			/* k8 profondeur */
	adda.l	%d0, %a0
	lea	66(%a1), %a1
	lea	66(%a2), %a2
	subq.l	#1, %d5
	bne.s	1b
	movea.l	%a5, %a0
	lea	LFO_ST, %a1
	jsr	copy192
	move.l	%d7, -(%sp)
	move.l	%d6, -(%sp)
	pea	S_FOBJ
	jsr	LFO_FN
	lea	12(%sp), %sp
	lea	LFO_ST, %a0
	movea.l	%a5, %a1
	jsr	copy192
	/* la modulation, comme l'OS l'applique (0x40091cda..0x40091d1c), aux vrais mots de la piste */
	lea	14(%a4), %a2
	moveq	#6, %d5
2:	move.l	16(%a5), %d0			/* destination calculée */
	beq.s	3f
	moveq	#32, %d1
	cmp.l	%d0, %d1
	bcs.s	3f				/* > 32 (non signé) : aucune */
	add.l	%d0, %d0
	mvs.w	(%a2, %d0.l), %d1
	add.l	20(%a5), %d1
	bpl.s	4f
	moveq	#0, %d1
4:	cmpi.l	#0x7f00, %d1
	ble.s	5f
	move.l	#0x7f00, %d1
5:	move.w	%d1, (%a2, %d0.l)
3:	lea	32(%a5), %a5
	lea	66(%a2), %a2
	subq.l	#1, %d5
	bne.s	2b
	rts
	.space	8

	.section .text.copy192, "ax"

/* 192 o de a0 vers a1 (6 × 32). Détruit d0-d5/a2-a3. */
copy192:
	movem.l	(%a0), %d0-%d5/%a2-%a3
	movem.l	%d0-%d5/%a2-%a3, (%a1)
	movem.l	32(%a0), %d0-%d5/%a2-%a3
	movem.l	%d0-%d5/%a2-%a3, 32(%a1)
	movem.l	64(%a0), %d0-%d5/%a2-%a3
	movem.l	%d0-%d5/%a2-%a3, 64(%a1)
	movem.l	96(%a0), %d0-%d5/%a2-%a3
	movem.l	%d0-%d5/%a2-%a3, 96(%a1)
	movem.l	128(%a0), %d0-%d5/%a2-%a3
	movem.l	%d0-%d5/%a2-%a3, 128(%a1)
	movem.l	160(%a0), %d0-%d5/%a2-%a3
	movem.l	%d0-%d5/%a2-%a3, 160(%a1)
	rts

/* ================================================================== réglages : id -> k, get/set =========== */

	.section .text.param, "ax"

/* 0x4005a4ea, dans id -> k (0x4005a4e8 : moveq #borne,d1 ; move.l 4(sp),d0 ; cmp.l d0,d1 ; ...) : jmp lfo_id2k à
 * la place de move.l 4(sp),d0 ; cmp.l d0,d1. La borne mise par 0x4005a4e8 (76 d'origine, plus avec les machines
 * ajoutées) reste dans d1. Page LFO 2 : SPD, MULT, WAVE, DEST, DEP -> k = 28..32 ; pages LFO 3/4 : -> -1 (aucun
 * mot du son ; get/set passent par lfo_get/lfo_set). Sinon les deux instructions, et la suite en 0x4005a4f0. */
lfo_id2k:
	tst.b	page
	beq.s	9f
	move.l	4(%sp), %d0
	bsr.s	slot_of_id
	bmi.s	9f
	moveq	#0, %d1
	move.b	page, %d1
	subq.l	#1, %d1
	bne.s	1f
	moveq	#2, %d1				/* WAVE : mot k = 0 (notes/86 §3), k 30 est à Lo-Fi Bits */
	cmp.l	%d1, %d0
	beq.s	2f
	moveq	#28, %d1
	add.l	%d1, %d0
	rts
2:	moveq	#0, %d0
	rts
1:	moveq	#-1, %d0
	rts
9:	move.l	4(%sp), %d0
	cmp.l	%d0, %d1
	jmp	0x4005a4f0

/* d0 = id -> d0 = rang du réglage (0 SPD, 1 MULT, 2 WAVE, 3 DEST, 4 DEP) ou -1 (N à 1). Détruit a1. */
slot_of_id:
	subi.l	#0x1d, %d0
	cmpi.l	#7, %d0
	bhi.s	1f
	lea	slots, %a1
	mvs.b	(%a1, %d0.l), %d0
	rts
1:	moveq	#-1, %d0
	rts

	.section .text.param2, "ax"

/* d0 = id -> a0 = adresse de son réglage de LFO 3 ou 4 pour la piste sélectionnée, dans le bloc du kit joué, ou 0
 * (autre page, autre id, piste >= 6). Détruit d0-d1/a1. */
slot34:
	moveq	#0, %d1
	move.b	page, %d1
	subq.l	#2, %d1
	bcs.s	9f
	jsr	slot_of_id
	bmi.s	9f
	add.l	%d0, %d0
	mulu.w	#60, %d1
	add.l	%d1, %d0
	move.l	%d0, -(%sp)
	bsr.s	sel_track
	move.l	(%sp)+, %d1
	cmpi.l	#6, %d0
	bcc.s	9f
	mulu.w	#10, %d0
	add.l	%d1, %d0
	move.l	%d0, -(%sp)
	jsr	cur34
	adda.l	(%sp)+, %a0
	rts
9:	suba.l	%a0, %a0
	rts

/* d0 = piste sélectionnée. Détruit d1/a0-a1. */
sel_track:
	jsr	CUR_PROJ
	move.l	%d0, -(%sp)
	jsr	PROJ_SEQ
	move.l	%d0, (%sp)
	jsr	SEL_TRACK
	addq.l	#4, %sp
	rts

/* Pointeur 0x400fd150 (vtable 0x400fd134 [28], 0x4000ae20) : get(this, id) des réglages de la piste active.
 * Pages LFO 3/4 : la valeur de notre table ; sinon l'original. */
lfo_get:
	move.l	8(%sp), %d0
	bsr.s	slot34
	move.l	%a0, %d0
	beq.s	1f
	mvs.w	(%a0), %d0
	rts
1:	jmp	0x4000ae20

/* Pointeur 0x400fd190 (vtable 0x400fd134 [92], 0x4000ba7a) : set(this, id, valeur, ...). Pages LFO 3/4 : le mot de
 * notre table, puis redessin de la page (pas de p-lock : pas de mot du son) ; sinon l'original. */
lfo_set:
	move.l	8(%sp), %d0
	bsr.s	slot34
	move.l	%a0, %d0
	beq.s	1f
	move.w	14(%sp), (%a0)
	move.l	view, %d0
	beq.s	2f
	move.l	%d0, -(%sp)
	jsr	NEEDS_REDRAW
	addq.l	#4, %sp
2:	rts
1:	jmp	0x4000ba7a

/* ================================================================== la page LFO ============================ */

	.section .text.view, "ax"

/* Pointeur 0x401016e4 (vtable de la vue LFO 0x401016dc [2], 0x40024e86) : touche(vue, événement). L'original
 * (0x40024e0c sur vue - 56) : l'appui de [LFO] est pris et remet à 0 le drapeau « tenue » de la vue (objet + 604,
 * vue + 548) ; un potard tourné [LFO] tenue le met (0x40024db6, c'est l'affectation de destination de l'OS) ; le
 * relâchement ferme la page si le drapeau est à 0, sinon le remet à 0. Ici, code 8 (la touche [LFO]) sans FUNC :
 * l'appui va à l'original et est noté (pend) ; à son relâchement, si le drapeau est resté à 0 (appui bref), page
 * suivante (LFO 2, 3, 4) et redessin au lieu de fermer ; s'il est mis (tenue, potard tourné), l'original : la page
 * reste. Une autre touche pendant que [LFO] est tenue (le Clear LFO de l'OS, 0x4001fb16, remet les identifiants
 * 0x1e..0x24 aux défauts par 0x4000b274, donc ceux de la page affichée) annule la note : le relâchement va à
 * l'original. Sur LFO 4 tout va à l'original (un appui bref ferme la page, comme d'origine). La répétition
 * automatique va à l'original (qui l'avale). Indicateurs de l'événement (+16, lus par 0x40072470/0x40072490/
 * 0x400724a0) : bit 0 enfoncée, bit 1 FUNC, bit 3 répétition. */
lfo_key:
	move.l	8(%sp), -(%sp)
	jsr	KEY_CODE
	addq.l	#4, %sp
	cmp.l	#5, %d0			/* MACHINES : modificateur du geste [LFO] tenue + potard, mais seulement dans ce
						   geste. Posée seule sur la page LFO, elle ouvre l'écran des machines (0x40075822)
						   comme d'origine. Un appui avalé avale aussi son relâchement (m5) : l'OS ne voit
						   jamais un relâchement sans appui. atk_watch/KEY_BITS lit l'état physique */
	bne.s	0f
	tst.b	m5
	bne.s	7f			/* déjà avalée : son relâchement l'est aussi */
	move.b	KEY_BITS, %d1
	btst	#3, %d1			/* [LFO] tenue : bit 3 de KEY_BITS (table 0x4010ae5c[8]) */
	beq.w	9f			/* [LFO] pas tenue : l'original, qui ouvre les machines */
7:	movea.l	8(%sp), %a0
	move.l	16(%a0), %d1		/* indicateurs : mot long (bit 0 enfoncée, bit 1 FUNC, bit 3 répétition) */
	btst	#0, %d1
	bne.s	8f
	clr.b	m5			/* relâchement (aussi après le lâcher de [LFO]) */
	bra.s	6f
8:	moveq	#1, %d1
	move.b	%d1, m5
6:	clr.b	pend			/* comme toute autre touche : plus d'appui bref */
	moveq	#1, %d0
	rts
0:	moveq	#8, %d1
	cmp.l	%d0, %d1
	beq.s	1f
	clr.b	pend				/* autre touche : pas un appui bref */
	bra.s	9f
1:	movea.l	8(%sp), %a0
	move.l	16(%a0), %d1
	btst	#1, %d1
	bne.s	9f
	btst	#0, %d1
	bne.s	2f
	tst.b	pend				/* relâchement d'un appui passé à l'original ? */
	beq.s	9f
	clr.b	pend
	movea.l	4(%sp), %a0
	tst.b	548(%a0)			/* potard tourné [LFO] tenue : l'original */
	bne.s	9f
	moveq	#0, %d0				/* appui bref : page suivante */
	move.b	page, %d0
	addq.l	#1, %d0
	move.b	%d0, page
	move.l	4(%sp), -(%sp)
	jsr	NEEDS_REDRAW
	addq.l	#4, %sp
	moveq	#1, %d0
	rts
2:	btst	#3, %d1
	bne.s	9f
	moveq	#0, %d0
	move.b	page, %d0
	moveq	#3, %d1
	cmp.l	%d1, %d0
	beq.s	9f
	moveq	#1, %d0
	move.b	%d0, pend
9:	jmp	0x40024e86

	.section .text.draw, "ax"

/* Pointeur 0x401016ec (même vtable [4], 0x400426fa) : dessin(vue, bitmap). L'original, puis sur LFO 2..4 le
 * chiffre au milieu du cadre inversé de gauche, avec la police du nom de la page : cadre désinversé, chiffre,
 * cadre réinversé. */
lfo_draw:
	move.l	8(%sp), -(%sp)
	move.l	8(%sp), -(%sp)
	jsr	0x400426fa
	addq.l	#8, %sp
	moveq	#0, %d0
	move.b	page, %d0
	beq.s	9f
	lea	digits-2, %a0
	adda.l	%d0, %a0
	adda.l	%d0, %a0
	move.l	%a0, -(%sp)
	bsr.s	box
	pea	2
	pea	34
	pea	32
	pea	TITLE_FONT
	move.l	28(%sp), -(%sp)
	jsr	TEXT
	lea	20(%sp), %sp
	bsr.s	box
	addq.l	#4, %sp
9:	rts

/* Inverse le cadre de gauche (0, 0)-(63, 63) du bitmap ; appelé de lfo_draw (bitmap en 12(sp) de lfo_draw). */
box:
	pea	-1
	pea	63
	pea	63
	clr.l	-(%sp)
	clr.l	-(%sp)
	move.l	36(%sp), -(%sp)
	jsr	FILL_RECT
	lea	24(%sp), %sp
	rts

	.section .text.view2, "ax"

/* 0x4001c3dc : jsr lfo_ctor à la place de jsr 0x40025798 (constructeur de la vue LFO, seul appel). Page LFO 1 ;
 * la vue (objet + 56, comme 0x4001c3ea) est notée pour le redessin (0 si l'allocation a échoué). */
lfo_ctor:
	move.l	4(%sp), %d0
	beq.s	1f
	addi.l	#56, %d0
1:	move.l	%d0, view
	clr.b	page
	clr.b	pend
	jmp	0x40025798

/* 0x400d97f8, fin du destructeur de la vue LFO (0x400d979a ; a2 = l'objet) : jmp lfo_dtor à la place de
 * move.l a2,8(sp) ; movea.l (sp)+,a2. Si c'est notre vue : page LFO 1, plus de vue. Puis les deux instructions et
 * la suite en 0x400d97fe (jmp 0x400d96c4). */
lfo_dtor:
	lea	56(%a2), %a0
	cmpa.l	view, %a0
	bne.s	1f
	clr.l	view
	clr.b	page
	clr.b	pend
1:	move.l	%a2, 8(%sp)
	movea.l	(%sp)+, %a2
	jmp	0x400d97fe

/* 0x40025e10 : jmp lfo_gate à la place de lea -16(sp),sp ; move.l a2,-(sp). Cette fonction (appelée par 4 rappels
 * de la vue LFO pour WAVE, MULT, DEST, DEP, pas tenu) poserait un p-lock sur LFO 1 : rien sur les pages LFO 3/4,
 * qui n'ont pas de p-lock. */
lfo_gate:
	moveq	#0, %d0
	move.b	page, %d0
	subq.l	#2, %d0
	bcc.s	1f
	lea	-16(%sp), %sp
	move.l	%a2, -(%sp)
	jmp	0x40025e16
1:	rts

/* ================================================================== molette DEST ========================== */

	.section .text.dest, "ax"

/* 0x4000c140 : jmp lfo_dest ; nop à la place de link.w fp,#-32 ; move.l 12(fp),d0. Pas dans la liste des
 * destinations (this, valeur, pas, masque), appelé par 0x4000c264 pour DEST (id 32) seulement ; rend k << 8, le k
 * venant de id -> k (0x4005a4e8) appliqué à l'identifiant choisi dans la liste. Page LFO ouverte : la page est mise
 * à LFO 1 le temps du calcul (précaution : la liste de l'OS ne propose aucun réglage de LFO, mais un tel identifiant
 * y deviendrait sinon k = 28..32 ou -1), et on saute les destinations déjà prises par un autre des 4 LFO de la piste
 * (None toujours permise) ; si toutes celles qui suivent sont prises (4 essais de plus), la valeur ne change pas.
 * Page fermée : l'original. */
lfo_dest:
	tst.l	view
	beq.s	dest_orig
	lea	-24(%sp), %sp
	movem.l	%d2-%d5/%a2-%a3, (%sp)		/* this 28(sp), valeur 32, pas 36, masque 40 */
	jsr	taken
	move.l	%d0, %d4			/* destinations prises, un octet chacune */
	moveq	#0, %d0
	move.b	page, %d0
	movea.l	%d0, %a3			/* page affichée, rendue à la fin */
	clr.b	page
	move.l	32(%sp), %d3			/* valeur de départ */
	moveq	#5, %d5
1:	move.l	40(%sp), -(%sp)		/* masque */
	move.l	40(%sp), -(%sp)		/* pas */
	move.l	%d3, -(%sp)
	move.l	40(%sp), -(%sp)		/* this */
	bsr.s	dest_orig
	lea	16(%sp), %sp
	cmp.l	%d0, %d3
	beq.s	8f				/* bout de la liste */
	move.l	%d0, %d3
	bsr.s	is_taken
	beq.s	7f				/* libre */
	subq.l	#1, %d5
	bne.s	1b
8:	move.l	32(%sp), %d3			/* rien de libre plus loin : inchangée */
7:	move.l	%a3, %d0
	move.b	%d0, page
	move.l	%d3, %d0
	movem.l	(%sp), %d2-%d5/%a2-%a3
	lea	24(%sp), %sp
	rts

/* Les deux instructions déplacées, puis la suite de 0x4000c140 (aussi appelée comme sous-programme). */
dest_orig:
	link.w	%fp, #-32
	move.l	12(%fp), %d0
	jmp	0x4000c148

/* d3 = valeur (k << 8), d4 = destinations prises -> Z = 1 si libre. Détruit d0-d2/a2. */
is_taken:
	move.l	%d3, %d1
	lsr.l	#8, %d1
	andi.l	#0xff, %d1
	beq.s	9f
	move.l	%d4, %d0
	moveq	#4, %d2
1:	movea.l	%d0, %a2
	andi.l	#0xff, %d0
	cmp.l	%d0, %d1
	beq.s	8f
	move.l	%a2, %d0
	lsr.l	#8, %d0
	subq.l	#1, %d2
	bne.s	1b
9:	moveq	#0, %d0
	rts
8:	moveq	#1, %d0
	rts

	.section .text.taken, "ax"

/* d0 = destinations (k) de LFO 1, 2, 3, 4 de la piste (un octet chacune, LFO 1 en poids fort), 0 pour celui de la
 * page affichée. this en 32(sp) (appelé de lfo_dest). Détruit d1-d2/a0-a1. */
taken:
	movea.l	32(%sp), %a0
	move.l	4(%a0), %d0			/* objet de la piste, puis son son (vtable [40]), comme 0x4000ae20 */
	beq.s	9f
	movea.l	%d0, %a0
	movea.l	(%a0), %a1
	movea.l	40(%a1), %a1
	move.l	%a0, -(%sp)
	jsr	(%a1)
	addq.l	#4, %sp
	tst.l	%d0
	beq.s	9f
	movea.l	%d0, %a0
	moveq	#0, %d2
	move.b	28(%a0), %d2			/* LFO 1 : octet fort du mot k = 4 (son + 20 + 8) */
	lsl.l	#8, %d2
	move.b	82(%a0), %d2			/* LFO 2 : k = 31 */
	lsl.l	#8, %d2
	lsl.l	#8, %d2
	jsr	sel_track
	cmpi.l	#6, %d0
	bcc.s	1f
	mulu.w	#10, %d0
	move.l	%d0, -(%sp)
	jsr	cur34				/* bloc du kit joué (garde d2) */
	adda.l	(%sp)+, %a0
	addq.l	#6, %a0
	moveq	#0, %d1
	move.b	(%a0), %d1			/* LFO 3 */
	lsl.l	#8, %d1
	move.b	60(%a0), %d1			/* LFO 4 */
	or.l	%d1, %d2
1:	moveq	#0, %d0
	move.b	page, %d0
	lsl.l	#3, %d0
	move.l	#0xff000000, %d1
	lsr.l	%d0, %d1
	not.l	%d1
	and.l	%d2, %d1
	move.l	%d1, %d0
	rts
9:	moveq	#0, %d0
	rts

/* ================================================================== [LFO] + potard, diode DEST ============= */

	.equ	KEY_BITS, 0x40f95744		/* état des touches que lit 0x4007faf4 ; MACHINES (code 5) = bit 0 */
	.equ	PITCH_ID, 42			/* PITCH, sous le potard PITCH de toutes les machines */
	.equ	FTUN_ID, 43			/* FINE : l'accord fin, sous MACHINES + PITCH sur toutes les machines */

	.section .text.learn, "ax"

/* 0x4001eb50, dans l'affectation par potard (0x4001eaa2, [LFO] tenue + un potard ; d2 = l'identifiant sous le
 * potard, lu dans l'enregistrement de KICK que Model-TG change tant que MACHINES est tenue : Attack, Filtre, Résonance
 * en positions 1, 4, 5 ; d7 = piste, a3 = l'accesseur des réglages de la piste, 0x400097f0, et non l'objet de la
 * piste, 0x40009c1a : passé à 0x40014042, il plantait l'OS, EXCEPTION V03 en 0x40014070) : jmp lfo_learn à la place de
 * move.l d2,-(sp) ; jsr 0x4005a4e8 ; addq.l #4,sp ; movea.l (a3),a0 ; move.l d0,d2 ; lsl.l #8,d2.
 *  - MACHINES tenue (bit 0 de KEY_BITS) sur PITCH (position 0) : FINE (id 43), l'accord fin, comme MACHINES + PITCH
 *    le règle sur la page de toutes les machines (notes/86 §8 ; l'enregistrement sous MACHINES le porte déjà en
 *    position 0, ce test reste pour le cas où il ne le porterait pas) ; FUNC+PITCH (a5 != 0) reste le stock PITCH.
 *  - Filtre ou Résonance de piste (0x0c / 0x0b, SWEEP / CONTOUR sous MACHINES) sur une piste Sampler : l'identifiant
 *    est relu dans le descripteur du Sampler sous MACHINES (0x4004df5c(7), descr_hook de Model-TG puis smf_descr,
 *    positions 4 et 5) : en modes 0..2 son propre filtre (0x49 / 0x4a, k 13/14), en modes 3..6 celui de la piste
 *    (0x0c / 0x0b, k 24/25), ce que les potards règlent dans chaque mode. Avant, l'enregistrement de KICK donnait
 *    toujours k 24/25 : muet en modes 0..2, et hors de la liste DEST du Sampler (DST None).
 *  - affectation libre ou déjà prise : admise (la molette DEST saute les prises, mais l'affectation directe par
 *    potard autorise le cumul, notes/56 §3.13).
 * d0-d1/a0-a1 libres ; d3-d6, a2-a5 gardés (la suite s'en sert). */
lfo_learn:
	tstl	68(%sp)				/* potard 0 seulement (PITCH) */
	bne.s	1f
	moveq	#PITCH_ID, %d0
	cmp.l	%d2, %d0
	bne.s	1f
	tstl	%a5				/* FUNC tenue : reste stock */
	bne.s	1f
	move.b	KEY_BITS, %d0
	btst	#0, %d0				/* MACHINES tenue */
	beq.s	1f
	/* sur n'importe quelle machine, MACHINES + PITCH tenu donne FINE (id 43), l'accord fin */
	moveq	#FTUN_ID, %d2
1:	moveq	#0x0c, %d1			/* Filtre (0x0c) ou Résonance (0x0b) de piste ? */
	sub.l	%d2, %d1
	moveq	#1, %d0
	cmp.l	%d1, %d0
	bcs.s	2f
	jsr	0x400cf866			/* projet */
	move.l	%d0, -(%sp)
	jsr	0x4000eb9c			/* kit joué */
	move.l	%d7, (%sp)
	move.l	%d0, -(%sp)
	jsr	0x40009c1a			/* objet de la piste d7 (a3 n'est que l'accesseur, 0x400097f0) */
	move.l	%d0, (%sp)
	jsr	0x40014042			/* machine de la piste */
	addq.l	#8, %sp
	moveq	#6, %d1
	cmp.l	%d0, %d1
	bne.s	2f				/* pas le Sampler */
	pea	7.w
	jsr	0x4004df5c			/* descripteur du Sampler (sous MACHINES) */
	addq.l	#4, %sp
	movea.l	%d0, %a0
	moveq	#0x0c, %d1
	sub.l	%d2, %d1			/* 0 : Filtre, position 4 ; 1 : Résonance, position 5 */
	move.l	24(%a0, %d1.l*4), %d2
2:	move.l	%d2, -(%sp)
	jsr	0x4005a4e8			/* id -> k */
	addq.l	#4, %sp
	move.l	%d0, %d2
	lsl.l	#8, %d2
	movea.l	(%a3), %a0
	jmp	0x4001eb60

/* 0x400262ac, dans la diode de la page LFO (0x400261aa ; d2 = l'identifiant de la destination, a2 = les 17
 * identifiants de l'enregistrement de la machine, que l'OS vient de copier et où il va le chercher ; sa position
 * donne la diode) : jmp lfo_led à la place de lea 12(sp),sp ; move.l sp,d0. L'enregistrement est celui de la
 * machine, sans le changement de Model-TG (MACHINES n'est plus tenue) : Attack, Filtre, Résonance n'y sont pas, et
 * FINE de MACRO y est en entrée 16, sans potard ; sans diode, ou une diode hors des potards. On cherche donc
 * l'identifiant du potard qui les règle sous MACHINES : DECAY (1) pour Attack, SWEEP (4) pour Filtre, CONTOUR (5)
 * pour Résonance, COLOR (2) et SHAPE (3) pour Lo-Fi Rate et Bits (ids 1 et 2, notes/86), PITCH (0) pour FINE
 * (toutes les machines, notes/86 §8). d0-d1 libres ; d0 = sp à la sortie, comme l'OS. */
lfo_led:
	lea	12(%sp), %sp
	move.l	%d2, %d0
	subq.l	#1, %d0
	moveq	#12, %d1
	cmp.l	%d0, %d1
	bcs.s	1f
	mvs.b	led_pos(%pc, %d0.l), %d0
	bmi.s	1f
	move.l	(%a2, %d0.l*4), %d2
	bra.s	9f
1:	moveq	#FTUN_ID, %d0			/* FINE : sous MACHINES + PITCH sur toutes les machines (notes/86 §8) */
	cmp.l	%d2, %d0
	bne.s	9f
	move.l	(%a2), %d2
9:	move.l	%sp, %d0
	jmp	0x400262b2
/* position du potard pour les ids 1..13 : Rate (1), Bits (2), rien (3..10), Résonance (0x0b), Filtre, Attack */
led_pos:	.byte	2, 3, -1, -1, -1, -1, -1, -1, -1, -1, 5, 4, 1
	.align	2

/* ================================================================== son et pattern ======================== */

	.section .text.store, "ax"

/* 0x4005b028 (sauvegarde du son, format 2, 0x4005afa0) et 0x4005b0dc (format 1, 0x4005b054) : jsr lfo_pack à la
 * place de move.w 94(a3),92(a2). a2 = l'enregistrement (100 o), a3 = le son. LFO 2 (k = 28..32, son + 76..85) en
 * un long en +88 (les deux dernières cases libres, que la sauvegarde vient de mettre à zéro, comme sous Model-TG),
 * par pk5. Garde tout sauf d0 (d1, a1, a4 servent ensuite). */
lfo_pack:
	move.w	94(%a3), 92(%a2)
	move.l	%d1, -(%sp)
	move.l	%a1, -(%sp)
	lea	-12(%sp), %sp			/* LFO 2 : k 28, 29, puis WAVE du mot k 0, puis k 31, 32 */
	movea.l	%sp, %a1
	move.l	76(%a3), (%a1)
	move.w	20(%a3), 4(%a1)
	move.l	82(%a3), 6(%a1)
	bsr.s	pk5
	lea	12(%sp), %sp
	move.l	%d0, 88(%a2)
	movea.l	(%sp)+, %a1
	move.l	(%sp)+, %d1
	rts

/* a1 = les 5 mots d'un LFO {SPD, MULT, WAVE, DEST, DEP} -> d0 = un long : bits 31-30 = 10 (marque), 29-22 SPD >> 7,
 * 21-17 MULT, 16-14 WAVE, 13-8 DEST, 7-0 DEP >> 7 (même format que DavidCaruso : ses sons se relisent ici). Sert à
 * LFO 2 dans le son et à LFO 3/4 dans le kit. Détruit d1. */
pk5:
	moveq	#2, %d0				/* marque */
	moveq	#0, %d1
	move.w	(%a1), %d1			/* SPD */
	lsr.l	#7, %d1
	andi.l	#0xff, %d1
	lsl.l	#8, %d0
	or.l	%d1, %d0
	moveq	#0, %d1
	move.b	2(%a1), %d1			/* MULT */
	andi.l	#0x1f, %d1
	lsl.l	#5, %d0
	or.l	%d1, %d0
	move.b	4(%a1), %d1			/* WAVE */
	andi.l	#7, %d1
	lsl.l	#3, %d0
	or.l	%d1, %d0
	move.b	6(%a1), %d1			/* DEST */
	andi.l	#0x3f, %d1
	lsl.l	#6, %d0
	or.l	%d1, %d0
	move.w	8(%a1), %d1			/* DEP */
	lsr.l	#7, %d1
	andi.l	#0xff, %d1
	lsl.l	#8, %d0
	or.l	%d1, %d0
	rts

	.section .text.unpack, "ax"

/* 0x4005af1c, chargement du son (0x4005aecc ; a2 = le son, a3 = l'enregistrement, mots k = 0..32 du son déjà mis à
 * zéro par 0x4008f238) : jsr lfo_unpack à la place de lea 0x4010eea8,a0. LFO 2 relu de +88 par upk5 (sans la marque,
 * tout son plus ancien : ses défauts). d0-d1/a1 libres ; a0 rendu comme l'instruction remplacée. */
lfo_unpack:
	move.l	88(%a3), %d0
	lea	76(%a2), %a1
	bsr.s	upk5
	lea	0x4010eea8, %a0
	rts

/* 0x4005af3e, après la boucle des cases du chargement du son (0x4005aecc ; a1 = table 0x4010eea8, a2 = le son,
 * a3 = l'enregistrement) : jsr lfo_tail ; nop à la place de mvs.b 28(a2),d0 ; move.l (a1,d0.l*4),d0. La boucle a
 * mis la case 18 dans k 0 (inutilisé par l'OS) : WAVE de LFO 2, que upk5 a posé en k 30, y passe, et k 30 (Lo-Fi
 * Bits, notes/86) repart de zéro. a1 et d0 rendus comme les deux instructions. */
lfo_tail:
	mvs.b	28(%a2), %d0
	move.l	(%a1, %d0.l*4), %d0
	move.w	80(%a2), 20(%a2)
	clr.w	80(%a2)
	rts

/* d0 = un long au format de pk5 -> les 5 mots d'un LFO en a1 ; marque autre que 10 : les défauts (dflt5). Détruit
 * d0-d1/a0. */
upk5:
	move.l	%d0, %d1
	andi.l	#0xc0000000, %d1
	cmpi.l	#0x80000000, %d1
	beq.s	1f
	movea.l	%a1, %a0
	bra.s	dflt5
1:	move.l	%d0, %d1			/* DEP */
	andi.l	#0xff, %d1
	lsl.l	#7, %d1
	move.w	%d1, 8(%a1)
	lsr.l	#8, %d0
	move.l	%d0, %d1			/* DEST */
	andi.l	#0x3f, %d1
	lsl.l	#8, %d1
	move.w	%d1, 6(%a1)
	lsr.l	#6, %d0
	move.l	%d0, %d1			/* WAVE */
	andi.l	#7, %d1
	lsl.l	#8, %d1
	move.w	%d1, 4(%a1)
	lsr.l	#3, %d0
	move.l	%d0, %d1			/* MULT */
	andi.l	#0x1f, %d1
	lsl.l	#8, %d1
	move.w	%d1, 2(%a1)
	lsr.l	#5, %d0				/* SPD */
	andi.l	#0xff, %d0
	lsl.l	#7, %d0
	move.w	%d0, (%a1)
	rts

/* Défauts d'un LFO en a0, a0 avancé de 10 : ceux du LFO d'origine (descripteurs 0x1d..0x24) : SPD 0x7000, MULT 4,
 * WAVE 0, DEST None, DEP 0x4000 (profondeur nulle). Ne détruit rien d'autre. */
dflt5:
	move.l	#0x70000400, (%a0)+
	clr.l	(%a0)+
	move.w	#0x4000, (%a0)+
	rts

/* 0x400618e2, fin de l'initialisation d'un son aux défauts (0x40061866 ; a2 = le son) : jsr lfo_init à la place de
 * lsl.l #8,d3 ; move.w d3,38(a2). Les deux instructions, puis les défauts de LFO 2 (l'OS y a mis 0 : aucun
 * descripteur ne vise k = 28..32), puis ceux de LFO 3 et 4 si c'est le son d'une piste d'un des 96 kits (snd34).
 * d0-d1/a0-a1 libres ensuite. */
lfo_init:
	lsl.l	#8, %d3
	move.w	%d3, 38(%a2)
	lea	76(%a2), %a0
	bsr.w	dflt5
	jmp	snd34

	.section .text.plk, "ax"

/* 0x4005b9c6, enregistrement des p-locks dans le pattern (0x4005b95c ; d0 = k, d4 = 4k, d1 = rangées écrites,
 * d2 = piste, a3 = la rangée) : jsr lfo_plk_save ; nop à la place de move.b 3(a5,d4.l),(a3) ; move.b d2,1(a3).
 * L'OS prend l'identifiant de rangée dans 0x4010ee4c[k], qui n'a que 23 entrées : pour k = 23..32 il lisait la
 * table suivante (Model-TG : un p-lock d'Attack, Filtre, Résonance revenait en None, LFO Speed, Multiplier). Ici
 * k = 23..32 -> plk_id. Garde tout. */
lfo_plk_save:
	tst.l	%d0				/* k 0 : WAVE de LFO 2, rangée 29 comme avant (notes/86 §3) */
	bne.s	3f
	move.b	#29, (%a3)
	bra.s	2f
3:	cmpi.l	#22, %d0
	bhi.s	1f
	move.b	3(%a5, %d4.l), (%a3)
	bra.s	2f
1:	move.b	plk_id-23(%pc, %d0.l), (%a3)
2:	move.b	%d2, 1(%a3)
	rts
/* identifiant de rangée pour k = 23..32 (0xff : rangée ignorée à la relecture ; k = 26 : état du Sampler de Model-TG,
 * jamais p-locké). Lo-Fi Rate (k 27) et Bits (k 30, notes/86 §4) : rangées 32 et 18, que l'OS n'écrit jamais (sa table
 * k -> rangée saute 0x12 ; son chargeur refuse au-delà de 32) */
plk_id:	.byte	24, 25, 26, 0xff, 32, 27, 28, 18, 30, 31

/* 0x4005aa22, identifiant de rangée -> k (0x4005aa1a(piste, id) ; d2 empilé puis = 6, d1 = piste) : jmp
 * lfo_plk_load à la place de move.l 12(sp),d0 ; cmp.l d1,d2. Pistes 0..5, identifiants 24..32 et 18 (que l'OS
 * n'écrit jamais) -> plk_k, k 30 ; sinon les deux instructions et la suite en 0x4005aa28. */
lfo_plk_load:
	move.l	12(%sp), %d0
	moveq	#5, %d2
	cmp.l	%d1, %d2
	bcs.s	1f
	moveq	#18, %d2			/* rangée 18 : Lo-Fi Bits, k 30 */
	cmp.l	%d0, %d2
	bne.s	2f
	moveq	#30, %d0
	bra.s	3f
2:	moveq	#-24, %d2
	add.l	%d0, %d2
	moveq	#8, %d0
	cmp.l	%d2, %d0
	bcs.s	4f
	mvz.b	plk_k(%pc, %d2.l), %d0
3:	move.l	(%sp)+, %d2
	rts
4:	move.l	12(%sp), %d0
1:	moveq	#6, %d2
	cmp.l	%d1, %d2
	jmp	0x4005aa28
plk_k:	.byte	23, 24, 25, 28, 29, 0, 31, 32, 27	/* rangées 24..32 ; 32 : Lo-Fi Rate, k 27 */

/* ================================================================== LFO 3/4 par pattern ===================== */

	.section .text.k34, "ax"

/* a0 = le bloc LFO 3/4 du kit joué (*CUR_KIT). Tant que T34 n'est pas aux défauts (kready = 0 : aucun kit chargé,
 * sauvé, copié ni remis aux défauts depuis le démarrage), le bloc de secours lfo34 : le moteur (interruption audio)
 * et la page n'écrivent jamais T34 eux-mêmes. Détruit d0-d1. */
cur34:
	tst.b	kready
	bne.s	1f
	lea	lfo34, %a0
	rts
1:	move.l	CUR_KIT, %d0
	move.l	%d2, -(%sp)
	bra.s	2f
/* d0 = un kit -> a0 = son bloc LFO 3/4 dans T34 et d0 = son rang (0..95) s'il est l'un des 96 kits du projet ; sinon
 * a0 = lfo34 (bloc de secours dans un masque) et d0 = -1. Premier usage depuis le démarrage : init34. Détruit d1. */
blk34:
	move.l	%d2, -(%sp)
	tst.b	kready
	bne.s	2f
	move.l	%d0, -(%sp)
	bsr.s	init34
	move.l	(%sp)+, %d0
2:	move.l	%d0, %d2
	subi.l	#KITS, %d0
	bcs.s	8f
	move.l	#KIT_SZ, %d1
	divu.l	%d1, %d0
	cmpi.l	#96, %d0
	bcc.s	8f
	mulu.l	%d0, %d1			/* juste au début d'un kit ? */
	addi.l	#KITS, %d1
	cmp.l	%d2, %d1
	bne.s	8f
	move.l	%d0, %d1
	mulu.w	#120, %d1
	lea	T34, %a0
	adda.l	%d1, %a0
	bra.s	9f
8:	lea	lfo34, %a0
	moveq	#-1, %d0
9:	move.l	(%sp)+, %d2
	rts

/* T34 aux défauts (96 × 12 LFO), aucun tampon de kit retenu, kready = 1. SCR34 n'est pas remise à zéro au
 * démarrage ; kready, dans un masque, l'est (rechargé de la flash). Le chargement du projet au démarrage passe par
 * kit_load, qui appelle blk34 : les blocs sont aux défauts avant d'être relus. Détruit d0-d1/a0. */
init34:
	lea	T34, %a0
	move.l	#96 * 12, %d1
1:	jsr	dflt5
	subq.l	#1, %d1
	bne.s	1b
	moveq	#-1, %d0			/* BUFK suit T34 */
	move.l	%d0, (%a0)+
	move.l	%d0, (%a0)+
	move.l	%d0, (%a0)+
	move.l	%d0, (%a0)+
	clr.l	(%a0)				/* BUFN */
	moveq	#1, %d0
	move.b	%d0, kready
	rts

	.section .text.snd34, "ax"

/* Fin de lfo_init (a2 = le son remis aux défauts) : si c'est le son de la piste t (0..5) d'un des 96 kits (kit + 28 +
 * 100 t : effacement du son d'une piste, des sons d'un pattern, nouveau kit, nouveau projet), LFO 3 et LFO 4 de
 * cette piste aux défauts, comme LFO 1 et 2. Garde d2-d7/a2-a6. */
snd34:
	move.l	%d2, -(%sp)
	move.l	%a2, %d0
	subi.l	#KITS, %d0
	bcs.s	9f
	move.l	%d0, %d2
	move.l	#KIT_SZ, %d1
	divu.l	%d1, %d0			/* le kit */
	cmpi.l	#96, %d0
	bcc.s	9f
	mulu.l	%d0, %d1
	sub.l	%d1, %d2			/* décalage dans le kit */
	subi.l	#28, %d2
	bcs.s	9f
	movea.l	%d2, %a1
	moveq	#100, %d1
	divu.l	%d1, %d2			/* la piste */
	cmpi.l	#6, %d2
	bcc.s	9f
	mulu.l	%d2, %d1			/* juste au début de son son ? */
	cmp.l	%a1, %d1
	bne.s	9f
	move.l	%a2, %d0
	sub.l	%a1, %d0
	subi.l	#28, %d0			/* le kit */
	jsr	blk34
	mulu.w	#10, %d2
	adda.l	%d2, %a0
	jsr	dflt5				/* LFO 3 */
	lea	50(%a0), %a0
	jsr	dflt5				/* LFO 4 */
9:	move.l	(%sp)+, %d2
	rts

	.section .text.kit, "ax"

/* 0x4005b2ae, entrée de la sauvegarde d'un kit dans son enregistrement (enregistrement, kit, ?) : jmp kit_save ; nop
 * à la place de lea -28(sp),sp ; movem.l d2-d3/a2-a6,(sp). Les trois arguments recopiés au-dessus d'un retour vers
 * kit_saved, les deux instructions, puis la suite en 0x4005b2b6. L'enregistrement (format 4) : nom, niveaux, les 6
 * sons en +32, le bloc FX en +632 (0x4005b266 en écrit +632..+645 et +700..+707), la réserve de sons en +708 ; rien
 * n'écrit ni ne lit +646..+699 (le chargement du bloc FX, 0x4005b21a, lit +632..+645). */
kit_save:
	move.l	12(%sp), -(%sp)
	move.l	12(%sp), -(%sp)
	move.l	12(%sp), -(%sp)
	pea	kit_saved
	lea	-28(%sp), %sp
	movem.l	%d2-%d3/%a2-%a6, (%sp)
	jmp	0x4005b2b6

/* Retour de la sauvegarde (d0.b = 1 si faite ; enregistrement 0(sp), kit 4(sp), puis le 3e argument) : LFO 3/4 du
 * kit en +648..+699 de l'enregistrement : L34_MAGIC, puis les 12 LFO par pk5 (LFO 3 pistes 0..5, puis LFO 4). Kit
 * hors des 96 : les défauts. d0 rendu. */
kit_saved:
	tst.b	%d0
	beq.s	9f
	lea	-16(%sp), %sp
	movem.l	%d0/%d2-%d3/%a2, (%sp)
	move.l	20(%sp), %d0
	jsr	blk34
	movea.l	%a0, %a1
	moveq	#10, %d2			/* pas d'un LFO au suivant */
	tst.l	%d0
	bpl.s	1f
	lea	dflt, %a1			/* hors des 96 : les défauts, 12 fois */
	moveq	#0, %d2
1:	movea.l	16(%sp), %a2
	move.l	#L34_MAGIC, %d0
	move.l	%d0, 648(%a2)
	lea	652(%a2), %a2
	moveq	#12, %d3
2:	jsr	pk5
	move.l	%d0, (%a2)+
	adda.l	%d2, %a1
	subq.l	#1, %d3
	bne.s	2b
	movem.l	(%sp), %d0/%d2-%d3/%a2
	lea	16(%sp), %sp
9:	lea	12(%sp), %sp
	rts

	.section .text.kit2, "ax"

/* 0x4005d080, entrée du chargement d'un kit (kit, enregistrement) : jmp kit_load ; nop à la place de
 * lea -36(sp),sp ; movem.l d2-d5/a2-a6,(sp). Comme kit_save ; retour vers kit_loaded. */
kit_load:
	move.l	8(%sp), -(%sp)
	move.l	8(%sp), -(%sp)
	pea	kit_loaded
	lea	-36(%sp), %sp
	movem.l	%d2-%d5/%a2-%a6, (%sp)
	jmp	0x4005d088

/* Retour du chargement (d0.b = 1 si fait ; kit 0(sp), enregistrement 4(sp)) : un des 96 kits reçoit les 12 LFO de
 * +652..+699 si +648 porte L34_MAGIC ; sinon (tout enregistrement plus ancien, quoi que le trou contienne) les
 * défauts. Kit hors des 96 : rien. d0 rendu. */
kit_loaded:
	tst.b	%d0
	beq.s	9f
	lea	-16(%sp), %sp
	movem.l	%d0/%d2-%d3/%a2, (%sp)
	move.l	16(%sp), %d0
	jsr	blk34
	tst.l	%d0
	bmi.s	8f
	movea.l	%a0, %a1
	movea.l	20(%sp), %a2
	lea	652(%a2), %a2
	moveq	#4, %d2
	move.l	-4(%a2), %d0
	cmpi.l	#L34_MAGIC, %d0
	beq.s	1f
	lea	zero, %a2			/* sans la marque : un long nul (sans marque) -> défauts */
	moveq	#0, %d2
1:	moveq	#12, %d3
2:	move.l	(%a2), %d0
	adda.l	%d2, %a2
	jsr	upk5
	lea	10(%a1), %a1
	subq.l	#1, %d3
	bne.s	2b
8:	movem.l	(%sp), %d0/%d2-%d3/%a2
	lea	16(%sp), %sp
9:	addq.l	#8, %sp
	rts

	.section .text.copy, "ax"

/* 0x4008f1f0, entrée de memcpy (destination, source, n) : jmp kit_copy ; nop à la place de movea.l 4(sp),a1 ;
 * movea.l 8(sp),a0. n autre que KIT_SZ : les deux instructions et la suite en 0x4008f1f8. n = KIT_SZ (un kit
 * entier : le nouveau projet copie le kit 0 dans les kits 1..95, la copie / le collage de pattern et leurs
 * annulations passent par des tampons à eux) : la copie, puis le bloc LFO 3/4 de la source (un des 96 kits, ou un
 * tampon retenu) va à la destination (un des 96 kits, sinon un tampon retenu : les 4 derniers remplis) ; source
 * inconnue : rien. Rend la destination dans d0, comme memcpy ; garde d2-d7/a2-a6. */
kit_copy:
	move.l	12(%sp), %d0
	cmpi.l	#KIT_SZ, %d0
	beq.s	1f
mc_orig:
	movea.l	4(%sp), %a1
	movea.l	8(%sp), %a0
	jmp	0x4008f1f8
1:	move.l	12(%sp), -(%sp)
	move.l	12(%sp), -(%sp)
	move.l	12(%sp), -(%sp)
	bsr.s	mc_orig				/* la copie */
	lea	12(%sp), %sp
	move.l	%a2, -(%sp)
	move.l	12(%sp), %d0			/* la source */
	jsr	blk34
	tst.l	%d0
	bpl.s	2f
	move.l	12(%sp), %d0
	jsr	buf_find
	move.l	%a0, %d0
	beq.s	9f				/* inconnue */
2:	movea.l	%a0, %a2
	move.l	8(%sp), %d0			/* la destination */
	jsr	blk34
	tst.l	%d0
	bpl.s	3f
	move.l	8(%sp), %d0
	jsr	buf_put
3:	moveq	#29, %d1
4:	move.l	(%a2)+, (%a0)+
	subq.l	#1, %d1
	bpl.s	4b
9:	movea.l	(%sp)+, %a2
	move.l	4(%sp), %d0
	rts

	.section .text.buf, "ax"

/* d0 = un tampon -> a0 = le bloc de sa case dans BUFD, ou 0 s'il n'est pas retenu. Détruit d0-d1. */
buf_find:
	move.l	%d2, -(%sp)
	lea	BUFK, %a0
	moveq	#0, %d1
1:	cmp.l	(%a0)+, %d0
	beq.s	2f
	addq.l	#1, %d1
	moveq	#4, %d2
	cmp.l	%d1, %d2
	bne.s	1b
	suba.l	%a0, %a0
	bra.s	9f
2:	mulu.w	#120, %d1
	lea	BUFD, %a0
	adda.l	%d1, %a0
9:	move.l	(%sp)+, %d2
	rts

/* d0 = un tampon -> a0 = le bloc de sa case : la sienne, sinon la plus ancienne, qui devient la sienne. Détruit
 * d0-d1. */
buf_put:
	move.l	%d0, -(%sp)
	bsr.s	buf_find
	move.l	%a0, %d0
	bne.s	9f
	move.l	BUFN, %d1			/* la plus ancienne */
	lea	BUFK, %a0
	move.l	(%sp), %d0
	move.l	%d0, (%a0, %d1.l*4)
	move.l	%d1, %d0
	addq.l	#1, %d0
	andi.l	#3, %d0
	move.l	%d0, BUFN
	mulu.w	#120, %d1
	lea	BUFD, %a0
	adda.l	%d1, %a0
9:	addq.l	#4, %sp
	rts

/* ================================================================== données (masques, image) ============== */

	.section .data.lfo, "aw"
	.balign	4
view:	.long	0				/* la vue LFO ouverte (objet + 56), 0 sinon */
page:	.byte	0				/* 0..3 : LFO 1..4 affiché */
pend:	.byte	0				/* appui de [LFO] passé à l'original : bref ou tenu ? */
m5:	.byte	0				/* appui de MACHINES avalé (geste [LFO] tenue + potard) : son relâchement aussi */
ready:	.byte	0				/* états de SCR mis à zéro depuis le démarrage */
kready:	.byte	0				/* blocs de T34 aux défauts depuis le démarrage */
/* id 0x1d..0x24 -> rang du réglage : SPD, MULT, (FADE), DEST, WAVE, (SPH), (MODE), DEP */
slots:	.byte	0, 1, -1, 3, 2, -1, -1, 4
digits:	.asciz	"2"
	.asciz	"3"
	.asciz	"4"
	.balign	2
/* Bloc LFO 3/4 de secours (blk34 pour un kit hors des 96) : LFO 3 puis LFO 4, 6 pistes × {SPD, MULT << 8,
 * WAVE << 8, DEST << 8, DEP}, défauts du LFO d'origine */
lfo34:	.rept	12
	.short	0x7000, 0x0400, 0, 0, 0x4000
	.endr
dflt:	.short	0x7000, 0x0400, 0, 0, 0x4000	/* un LFO aux défauts (kit_saved) */
	.balign	4
zero:	.long	0				/* un LFO sans marque (kit_loaded) */
