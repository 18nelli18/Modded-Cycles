/* Écoute des samples au casque (cue), avec le Sampler de Model-TG et l'écoute des samples (notes/48). Lié par
 * sample_cue.ld dans des masques de sprites 48x22 libérés (tools/sprites.py) ; les écritures sur l'OS sont dans
 * tools/gen_sample_cue.py (HOOKS).
 *
 * L'écoute des samples (notes/46) joue le sample sous le curseur sur la voix de la piste : il passe dans le mix,
 * donc sur MAIN OUT, l'USB et le rééchantillonnage. Ici, l'appui du pad qui l'écouterait ne va pas au moteur audio :
 * un petit lecteur à part lit le sample (déjà en mémoire, chargé par pv_note) depuis l'interruption audio, après
 * l'étage de sortie, et l'ajoute à une seule sortie (CUE_MODE) :
 *   1 « split » : le casque et MAIN OUT ne reçoivent que deux canaux, les mêmes (notes/48 §1) ; MAIN OUT R est coupé
 *     dans la puce audio (registre 0x1F, écriture dans gen_sample_cue.py), G porte la perf en mono, D la perf en
 *     mono plus l'écoute : au casque, la perf à gauche, la perf et l'écoute à droite ;
 *   2 « jacks » : l'écoute s'ajoute aux jacks (MAIN OUT et casque), pas à l'USB ;
 *   3 « usb » : l'écoute s'ajoute au mix envoyé à l'USB seulement.
 * Quatre accroches côté interface (tâche de l'interface, niveau 0) et une dans l'interruption audio :
 *   - cue_dec (0x4008180e, dans 0x4008171e, note jouée) : sur le pad de la piste active, avec un son désigné qui est
 *     le sample sous le curseur (le son que pv_parse construit, pv_src), la note ne part pas : l'écoute démarre ;
 *   - cue_off (0x4008145e, relâchement) : le relâchement d'un appui d'écoute ne part pas non plus ; celui de l'appui
 *     qui joue arrête l'écoute (fondu sur un bloc) ;
 *   - cue_arm (0x40081bd6, seul écrivain du son désigné) : un autre son désigné (curseur, fermeture) l'arrête ;
 *   - cue_load (0x400a6bec, chargement d'un fichier du navigateur) : l'arrête aussi ;
 *   - cue_out (0x40059878, fin du calcul d'un bloc, après rs_out de Model-TG) : le lecteur.
 *
 * Partage avec l'interruption : l'interface écrit les paramètres, interruptions masquées, puis GO ; l'arrêt est
 * une seule écriture (STOP). L'interruption vérifie à chaque bloc que la case de Model-TG contient toujours ce
 * sample (empreinte et adresse) avant d'en lire un octet, et ne lit jamais plus loin que son nombre d'échantillons.
 *
 * Adresses de Model-TG et de l'écoute des samples (symboles de 30-model-tg*.json et 33-sample-preview*.json),
 * passées par -D :
 *   TG_TOK_OF(a0 = son) -> d0 = l'empreinte nommée par « SMP… » si machine 6, sinon 0 ; garde d1-d7, détruit a0
 *   TG_SLOT_HASH, TG_SLOT_BASE, TG_SLOT_COUNT, TG_SLOT_SOFF, TG_SLOT_PGAIN : les 64 cases d'échantillons
 *     (empreinte, adresse de l'image, échantillons par plan, décalage du plan « côté » ou 0, gain Q12 ou 0)
 *   PV_SRC : le son de 100 o que pv_parse construit pour le sample sous le curseur */

#define ACTIVE	0x40a700c4		/* piste active */
#define ARMED	0x40fb5a04		/* son désigné pour l'écoute, ou 0 */
#define NOTES	0x40fb5c0c		/* notes tenues : compteur par (piste << 7) + note, en longs */
#define SEND	0x40081814		/* suite de 0x4008171e : l'événement part au moteur audio */
#define NO_SEND	0x40081878		/* suite « sans envoi » */
#define EPILOG	0x4008190e		/* fin de 0x4008171e */
#define OFF_GO	0x40081464		/* 0x4008145e après les deux instructions déplacées */
#define LOAD	0x400a64fa		/* chargement d'un fichier du navigateur */
#define TAIL	0x4005987e		/* fin de 0x4005979e : movea.l (sp)+,a3 ; rts */
#define USB_MIX	0x40fe4b90		/* mix envoyé à l'USB : 32 × {G, D}, échelle du bus */
#define VEL_K	106			/* gain pour une vélocité : 100 -> 10600, niveau d'une piste par défaut */
/* champs de cue_data */
#define GO	0			/* 1 : l'interruption joue l'écoute */
#define STOP	4			/* ≠ 0 : arrêt demandé (fondu sur un bloc, puis GO = 0) */
#define SLOT	8			/* la case de Model-TG… */
#define HASH	12			/* …son empreinte… */
#define BASE	16			/* …et son adresse au départ */
#define COUNT	20			/* échantillons par plan au départ */
#define SOFF	24			/* décalage du plan « côté », 0 en mono */
#define GAIN	28			/* échantillon 16 bits -> échelle du bus */
#define POS	32			/* prochain échantillon */
#define TRK	36			/* piste des appuis d'écoute tenus */
#define NOTE	40			/* note brute (& 127) de l'appui qui joue */
#define HELD	44			/* notes brutes tenues par des appuis d'écoute, 128 bits */

	.globl	cue_dec, cue_start, cue_held, cue_off, cue_arm, cue_load, cue_out, cue_play, cue_data

/* 0x4008180e, dans 0x4008171e : jmp cue_dec à la place de tst.l 24(fp) ; bne.s 0x40081878.
 * Registres : d2 = piste, d3 = note (après le Scale Lock), d5 = source, a3 ≠ 0 si la piste est la piste active et
 * la source une de celles qui emportent le son désigné, a4 = piste << 7 ; fp+12 = note brute, fp+16 = vélocité,
 * fp+24 = « sans envoi ». d0, d1, a0, a1 sont libres sur les deux suites ; l'épilogue recharge d2-d7/a2-a5. */
	.section .text.cue_dec, "ax"
cue_dec:
	tst.l	24(%fp)
	bne.s	.Lnosend		/* déjà « sans envoi » (pv_note n'a pas pu charger) */
	tst.l	%a3
	beq.s	.Lsend
	moveq	#0x40, %d0
	cmp.l	%d5, %d0
	bne.s	.Lsend			/* seulement les pads et les touches */
	move.l	ARMED, %d0
	beq.s	.Lsend
	movea.l	%d0, %a0		/* le son désigné est-il le sample sous le curseur ? */
	lea	PV_SRC, %a1
	moveq	#24, %d1
1:	move.l	(%a0)+, %d0
	cmp.l	(%a1)+, %d0
	bne.s	.Lsend			/* un preset : son écoute d'origine, sur la piste */
	subq.l	#1, %d1
	bpl.s	1b
	movea.l	ARMED, %a0
	jsr	TG_TOK_OF
	tst.l	%d0
	beq.s	.Lsend
	move.l	%d0, %d1		/* jamais une prise du rééchantillonnage (0x524d00nn) */
	clr.b	%d1
	cmpi.l	#0x524d0000, %d1
	beq.s	.Lnosend
	lea	TG_SLOT_HASH, %a0
	moveq	#63, %d1
2:	cmp.l	(%a0)+, %d0
	beq.s	3f
	subq.l	#1, %d1
	bpl.s	2b
.Lnosend:				/* pas en mémoire : rien ne joue, comme pv_note */
	jmp	NO_SEND
.Lsend:
	jmp	SEND
3:	moveq	#63, %d0
	sub.l	%d1, %d0		/* la case */
	jmp	cue_start

/* Suite de cue_dec (autre masque) : d0 = la case du sample. Démarre l'écoute, puis cue_held. */
	.section .text.cue_start, "ax"
cue_start:
	move.l	%d0, %d4
	move.l	16(%fp), %d6		/* gain = vélocité × VEL_K (× gain de la prise) */
	muls.w	#VEL_K, %d6
	lea	TG_SLOT_PGAIN, %a0
	move.l	(%a0, %d4.l*4), %d0
	beq.s	1f
	muls.l	%d0, %d6
	asr.l	#8, %d6
	asr.l	#4, %d6
1:	move.l	#32767, %d0		/* (milieu ± côté) × gain tient sur 32 bits */
	cmp.l	%d0, %d6
	ble.s	2f
	move.l	%d0, %d6
2:	lea	TG_SLOT_BASE, %a0
	move.l	(%a0, %d4.l*4), %d7
	lea	TG_SLOT_COUNT, %a0
	move.l	(%a0, %d4.l*4), %d1
	lea	TG_SLOT_SOFF, %a0
	movea.l	(%a0, %d4.l*4), %a2
	lea	TG_SLOT_HASH, %a0
	move.l	(%a0, %d4.l*4), %d5
	lea	cue_data, %a1
	move.w	%sr, %d0
	move.w	#0x2700, %sr		/* l'interruption voit tout ou rien */
	move.l	%d4, SLOT(%a1)
	move.l	%d5, HASH(%a1)
	move.l	%d7, BASE(%a1)
	move.l	%d1, COUNT(%a1)
	move.l	%a2, SOFF(%a1)
	move.l	%d6, GAIN(%a1)
	clr.l	POS(%a1)
	clr.l	STOP(%a1)
	moveq	#1, %d1
	move.l	%d1, GO(%a1)
	move.w	%d0, %sr
	jmp	cue_held

/* Suite de cue_start (autre masque), a1 = cue_data : retient l'appui, défait le compteur de notes tenues que
 * 0x4008171e vient d'incrémenter, et sort par l'épilogue : la note n'existe pas pour l'OS (ni moteur audio, ni
 * enregistrement, ni arpège). */
	.section .text.cue_held, "ax"
cue_held:
	cmp.l	TRK(%a1), %d2		/* notes tenues des appuis d'écoute, une piste à la fois */
	beq.s	1f
	move.l	%d2, TRK(%a1)
	clr.l	HELD(%a1)
	clr.l	HELD+4(%a1)
	clr.l	HELD+8(%a1)
	clr.l	HELD+12(%a1)
1:	moveq	#127, %d0
	and.l	12(%fp), %d0
	move.l	%d0, NOTE(%a1)
	move.l	%d0, %d1
	lsr.l	#5, %d1
	lea	HELD(%a1, %d1.l*4), %a0
	move.l	(%a0), %d1
	bset	%d0, %d1
	move.l	%d1, (%a0)
	move.l	%a4, %d0
	add.l	%d3, %d0
	lea	NOTES, %a0
	subq.l	#1, (%a0, %d0.l*4)
	jmp	EPILOG

/* 0x4008145e, relâchement (piste, note, source) : jmp cue_off à la place de link.w fp,#-124 ; moveq #127,d0.
 * d0, d1, a0, a1 sont libres. */
	.section .text.cue_off, "ax"
cue_off:
	moveq	#0x40, %d0
	cmp.l	12(%sp), %d0
	bne.s	.Loff
	lea	cue_data, %a1
	move.l	4(%sp), %d0
	cmp.l	TRK(%a1), %d0
	bne.s	.Loff
	moveq	#127, %d0
	and.l	8(%sp), %d0
	move.l	%d0, %d1
	lsr.l	#5, %d1
	lea	HELD(%a1, %d1.l*4), %a0
	move.l	(%a0), %d1
	btst	%d0, %d1
	beq.s	.Loff			/* pas un appui d'écoute : relâchement d'origine */
	bclr	%d0, %d1
	move.l	%d1, (%a0)
	cmp.l	NOTE(%a1), %d0
	bne.s	1f
	addq.l	#1, STOP(%a1)		/* l'appui qui joue : fondu, puis silence */
1:	rts				/* sa note n'est jamais partie : pas de relâchement */
.Loff:
	link.w	%fp, #-124
	moveq	#127, %d0
	jmp	OFF_GO

/* 0x40081bd6, seul écrivain du son désigné (nouveau son en 4(sp)) : jmp cue_arm à la place de lea 4(sp),a0 et du
 * début de move.l (a0),0x40fb5a04. Garde d0, d1 et a1 (des appelants rendent d0 après l'avoir appelé en jmp). */
	.section .text.cue_arm, "ax"
cue_arm:
	movea.l	4(%sp), %a0
	cmpa.l	ARMED, %a0
	beq.s	1f
	addq.l	#1, cue_data+STOP	/* autre son désigné, ou plus aucun : fin de l'écoute */
1:	lea	4(%sp), %a0
	move.l	(%a0), ARMED
	rts

/* 0x400a6bec : l'adresse de cue_load à la place de 0x400a64fa, la fonction de chargement d'un fichier que le
 * navigateur installe. Ne touche aucun registre. */
cue_load:
	addq.l	#1, cue_data+STOP	/* le fichier chargé arrête l'écoute */
	jmp	LOAD

/* 0x40059878, fin de 0x4005979e (le calcul d'un bloc de 32 trames, dans l'interruption audio) : jmp cue_out à la
 * place de lea 20(sp),sp ; movea.l (sp)+,a2. 0(sp) = la moitié du ring DMA des jacks que l'étage de sortie vient de
 * remplir : 32 × {G, D}, 24 bits signés cadrés à droite, polarité inverse du bus (jacks = -bus / 256). Garder d2-d7 et
 * a4-a6 ; a2 et a3 sont rechargés de la pile. Après rs_out (rééchantillonnage de Model-TG) : l'écoute n'est ni dans le
 * bus, ni dans ce qu'il enregistre, ni dans son seuil de départ. */
	.section .text.cue_out, "ax"
cue_out:
	movea.l	(%sp), %a0		/* la moitié des jacks */
	lea	-28(%sp), %sp
	movem.l	%d2-%d7/%a4, (%sp)
#if CUE_MODE == 1
	movea.l	%a0, %a1		/* split : G = D = (G + D) / 2, la perf en mono */
	moveq	#31, %d2
1:	move.l	(%a1)+, %d0
	add.l	(%a1)+, %d0
	asr.l	#1, %d0
	move.l	%d0, -8(%a1)
	move.l	%d0, -4(%a1)
	subq.l	#1, %d2
	bpl.s	1b
#endif
	lea	cue_data, %a4
	tst.l	GO(%a4)
	beq.s	.Lout
	move.l	SLOT(%a4), %d1		/* la case contient-elle toujours ce sample ? */
	lea	TG_SLOT_HASH, %a1
	move.l	(%a1, %d1.l*4), %d0
	cmp.l	HASH(%a4), %d0
	bne.s	.Lend
	lea	TG_SLOT_BASE, %a1
	move.l	(%a1, %d1.l*4), %d0
	cmp.l	BASE(%a4), %d0
	bne.s	.Lend
	movea.l	%d0, %a2
	lea	TG_SLOT_COUNT, %a1
	move.l	(%a1, %d1.l*4), %d3
	cmp.l	COUNT(%a4), %d3
	bls.s	2f
	move.l	COUNT(%a4), %d3
2:	move.l	POS(%a4), %d4
	sub.l	%d4, %d3		/* échantillons restants */
	ble.s	.Lend
	moveq	#32, %d5
	cmp.l	%d5, %d3
	bge.s	3f
	move.l	%d3, %d5		/* ce bloc : min(32, restants) */
3:	add.l	%d5, POS(%a4)
	lea	64(%a2, %d4.l*2), %a1	/* le plan « milieu » (le seul en mono), après l'en-tête de 64 o */
	jmp	cue_play
.Lend:
	clr.l	GO(%a4)
.Lout:
	movem.l	(%sp), %d2-%d7/%a4
	lea	48(%sp), %sp		/* nos 28 o, puis le lea 20(sp),sp remplacé */
	movea.l	(%sp)+, %a2
	jmp	TAIL

/* Suite de cue_out (autre masque) : a0 = la moitié des jacks, a1 = le premier échantillon du plan « milieu »,
 * d1 = la case, d5 = échantillons de ce bloc, a4 = cue_data. */
	.section .text.cue_play, "ax"
cue_play:
#if CUE_MODE != 1
	moveq	#0, %d2			/* le plan « côté », s'il existe toujours, sinon côté = 0 */
	movea.l	%a1, %a2
	move.l	SOFF(%a4), %d0
	beq.s	4f
	lea	TG_SLOT_SOFF, %a3
	cmp.l	(%a3, %d1.l*4), %d0
	bne.s	4f
	adda.l	%d0, %a2
	moveq	#-1, %d2
4:
#endif
	move.l	GAIN(%a4), %d6
	moveq	#0, %d7
	tst.l	STOP(%a4)
	beq.s	5f
	move.l	%d6, %d7		/* arrêt demandé : fondu jusqu'à 0 sur 32 échantillons */
	asr.l	#5, %d7
5:
#if CUE_MODE == 3
	lea	USB_MIX, %a0
	move.l	#0x7fffffff, %d3
	move.l	#0x80000000, %d4
#else
	move.l	#0x7fffff, %d3
	move.l	#-0x800000, %d4
#endif
#if CUE_MODE == 1
	addq.l	#4, %a0			/* D seulement : la perf + l'écoute (milieu) */
6:	mvs.w	(%a1)+, %d0
	muls.l	%d6, %d0
	asr.l	#8, %d0
	move.l	(%a0), %d1
	sub.l	%d0, %d1
	cmp.l	%d3, %d1
	ble.s	7f
	move.l	%d3, %d1
7:	cmp.l	%d4, %d1
	bge.s	8f
	move.l	%d4, %d1
8:	move.l	%d1, (%a0)
	addq.l	#8, %a0
	sub.l	%d7, %d6
	subq.l	#1, %d5
	bne.s	6b
#else
6:	mvs.w	(%a1)+, %d0		/* milieu */
	mvs.w	(%a2)+, %d1		/* côté */
	and.l	%d2, %d1
	movea.l	%d0, %a3
	add.l	%d1, %d0		/* G = milieu + côté */
	suba.l	%d1, %a3		/* D = milieu - côté */
	muls.l	%d6, %d0
	bsr.s	.Lmix
	move.l	%a3, %d0
	muls.l	%d6, %d0
	bsr.s	.Lmix
	sub.l	%d7, %d6
	subq.l	#1, %d5
	bne.s	6b
#endif
	tst.l	STOP(%a4)
	beq.s	9f
	clr.l	GO(%a4)
9:	movem.l	(%sp), %d2-%d7/%a4
	lea	48(%sp), %sp
	movea.l	(%sp)+, %a2
	jmp	TAIL
#if CUE_MODE == 2
/* d0 = l'écoute à l'échelle du bus ; (a0)+ = jacks - d0 / 256, écrêté à 24 bits */
.Lmix:	asr.l	#8, %d0
	move.l	(%a0), %d1
	sub.l	%d0, %d1
	cmp.l	%d3, %d1
	ble.s	1f
	move.l	%d3, %d1
1:	cmp.l	%d4, %d1
	bge.s	2f
	move.l	%d4, %d1
2:	move.l	%d1, (%a0)+
	rts
#elif CUE_MODE == 3
/* d0 = l'écoute à l'échelle du bus ; (a0)+ = USB + d0, saturé à 32 bits */
.Lmix:	move.l	(%a0), %d1
	add.l	%d0, %d1
	bvc.s	1f
	move.l	%d3, %d1
	tst.l	%d0
	bpl.s	1f
	move.l	%d4, %d1
1:	move.l	%d1, (%a0)+
	rts
#endif

/* Données (champs plus haut), écrites dans l'image (ces masques ne sont pas remis à zéro au démarrage). */
	.section .data.cue, "aw"
	.balign	4
cue_data:
	.long	0, 0, 0, 0, 0, 0, 0, 0, 0	/* GO … POS */
	.long	-1, -1				/* TRK, NOTE */
	.long	0, 0, 0, 0			/* HELD */
