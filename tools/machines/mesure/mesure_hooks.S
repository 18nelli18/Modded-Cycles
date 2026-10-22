/*
 * Firmware de mesure (notes/75) : les sondes de l'interruption audio, le compteur de temps libre de l'interface et
 * les noyaux des essais d'etalonnage. Assemble par tools/gen_mesure.py, place dans des masques de sprites libres
 * avec mesure.c ; les variables (m_site, m_tisr, ...) sont dans mesure.c (fenetre de RAM au-dessus du BSS de l'OS).
 *
 * Chronometre : minuteur DMA 0 (0xfc07000c, compteur libre a 135,168 MHz ; un bloc de 32 trames = 90 112 ticks).
 * Adresses donnees par gen_mesure.py (--defsym), relues et verifiees dans l'OS : T_0..T_11, les cibles des appels
 * sondes ; et dans Model-TG : ISR_PROF (son entree de l'interruption audio), SYS_PG (le numero d'ecran de sa page
 * System), PAGE0 et SYS_R2 (sys_render : ses ecrans 0 et 1), SYS_R_OUT (la fin de sys_render, qui rend d3-d4/a2).
 */
	.equ	DTIM0, 0xfc07000c
	.equ	CACR_ICINV, 0xa40ce100		/* le CACR de l'OS (0x40000548) sans DCINVA : invalide les caches */
						/* d'instructions et de branchements, garde le cache de donnees */

/* ---- m_isr : entree de l'interruption audio (vecteur 0x400002fc, pose en 0x4005966a) ------------------------- *
 * Note l'heure d'entree (m_tisr), invalide le cache d'instructions si ce bloc est un bloc « froid » de l'essai
 * A/B (m_cold), puis passe a l'entree de Model-TG, qui passe a celle de l'OS. Seul d0 sert, rendu tel quel. */
	.section .text.m_isr,"ax"
	.globl	m_isr
m_isr:
	move.l	%d0, -(%sp)
	move.l	DTIM0, %d0
	move.l	%d0, m_tisr
	tst.l	m_cold
	beq.s	1f
	move.l	#CACR_ICINV, %d0
	movec	%d0, %cacr
	nop
1:	move.l	(%sp)+, %d0
	jmp	ISR_PROF

/* ---- les sondes d'appels : chaque jsr de l'OS devient jsr m_w_k ---------------------------------------------- *
 * m_w_k met de cote l'adresse de retour (l'appele voit la pile d'un jsr direct), note l'heure, appelle la cible,
 * note la duree dans m_site (ret[k], t0[k], dur[k]) et revient. Detruit d1 et a1 (libres pour un appel C : aucun de
 * ces appeles n'y lit d'argument, aucun appelant ne les relit apres) ; d0 (la valeur rendue) et le reste sont
 * gardes. Les sondes s'emboitent (la fonction audio contient les autres) : chacune a sa case. */
	.equ	NSITE, 12
	.equ	RET, 0
	.equ	T0, 4 * NSITE
	.equ	DUR, 8 * NSITE

.macro	SITE	k, target
	.section .text.m_w_\k,"ax"
	.globl	m_w_\k
m_w_\k:
	lea	m_site, %a1
	move.l	(%sp)+, RET + 4 * \k(%a1)
	move.l	DTIM0, %d1
	move.l	%d1, T0 + 4 * \k(%a1)
	jsr	\target
	lea	m_site, %a1
	move.l	DTIM0, %d1
	sub.l	T0 + 4 * \k(%a1), %d1
	move.l	%d1, DUR + 4 * \k(%a1)
	move.l	RET + 4 * \k(%a1), -(%sp)
	rts
.endm

/* les sites (gen_mesure.py, SITES) : */
	SITE	0, T_0		/* 0x40059338 : l'audio venu de l'USB */
	SITE	1, T_1		/* 0x40059382 : la fonction audio (par la sonde des moteurs du Syntakt) */
	SITE	2, T_2		/* 0x400597a8 : lissage des parametres */
	SITE	3, T_3		/* 0x400597b4 : modulation de velocite */
	SITE	4, T_4		/* 0x400597c6 : LFO (LFO 2, 3, 4) */
	SITE	5, T_5		/* 0x4005981e : la boucle des voix (fx_early de Model-TG) */
	SITE	6, T_6		/* 0x4005982a : apres les voix (Model-TG, gain de velocite) */
	SITE	7, T_7		/* 0x40059840 : recopie des gains de velocite */
	SITE	8, T_8		/* 0x40059852 : Volume + Dist */
	SITE	9, T_9		/* 0x4005985c : 0x40056ea8 */
	SITE	10, T_10		/* 0x40059872 : l'etage de sortie (mixeur, envois, delay, reverb, master) */

/* 0x40059392 : l'envoi a l'USB, le dernier appel du bloc : la meme sonde, puis m_block_end (mesure.c), qui
 * detruit d0, d1, a0 et a1 : l'interruption n'en relit aucun apres cet appel (0x40059398 : lea, tst, puis d7). */
	.section .text.m_w_11,"ax"
	.globl	m_w_11
m_w_11:
	lea	m_site, %a1
	move.l	(%sp)+, RET + 4 * 11(%a1)
	move.l	DTIM0, %d1
	move.l	%d1, T0 + 4 * 11(%a1)
	jsr	T_11
	lea	m_site, %a1
	move.l	DTIM0, %d1
	sub.l	T0 + 4 * 11(%a1), %d1
	move.l	%d1, DUR + 4 * 11(%a1)
	jsr	m_block_end
	lea	m_site, %a1
	move.l	RET + 4 * 11(%a1), -(%sp)
	rts

/* ---- m_idle : la boucle d'attente de la tache de priorite 0 (0x4000543a) ------------------------------------- *
 * Le compteur de temps libre de l'etude « systeme » (prouve en emulation, notes/70) : cumule les petits ecarts du
 * minuteur (< 128 ticks, moins d'une µs) ; un grand ecart, c'est que la tache a ete interrompue : non compte.
 * d0-d2 sont sauves par le changement de contexte (0x4000041e). */
	.section .text.m_idle,"ax"
	.globl	m_idle
m_idle:
	lea	24(%sp), %sp		/* ce que faisait l'original */
	move.l	DTIM0, %d1
1:	move.l	DTIM0, %d0
	move.l	%d0, %d2
	sub.l	%d1, %d2
	move.l	%d0, %d1
	cmpi.l	#128, %d2
	bhi.s	1b
	add.l	%d2, m_idle_acc
	bra.s	1b

/* ---- m_sys : le choix de l'ecran de la page System de Model-TG (sys_render, 0x401b6fb6) ----------------------- *
 * Ecrans 0 et 1 : les siens ; 2, 3, 4 : les notres (m_render). d2 = l'ecran (bitmap) ; d3, d4, a2 sont deja sauves
 * par sys_render, que SYS_R_OUT termine. */
	.section .text.m_sys,"ax"
	.globl	m_sys
m_sys:
	move.l	SYS_PG, %d0
	beq.s	1f
	subq.l	#1, %d0
	beq.s	2f
	move.l	%d0, -(%sp)		/* 1, 2, 3 : nos ecrans */
	move.l	%d2, -(%sp)
	jsr	m_render
	addq.l	#8, %sp
	jmp	SYS_R_OUT
1:	jmp	PAGE0
2:	jmp	SYS_R2

/* ---- les essais d'etalonnage --------------------------------------------------------------------------------- *
 * u32 m_time(const void *code, void *data) : le temps d'un appel de code (en ticks du minuteur), a0 = data. Le code
 * peut detruire d0-d7, a0, a1 ; il rend les accumulateurs de l'EMAC vides et ne touche pas a MACSR. */
	.section .text.m_time,"ax"
	.globl	m_time
m_time:
	lea	-44(%sp), %sp
	movem.l	%d2-%d7/%a2-%a6, (%sp)
	movea.l	48(%sp), %a2		/* code */
	movea.l	52(%sp), %a0		/* data */
	move.l	DTIM0, %a3
	jsr	(%a2)
	move.l	DTIM0, %d0
	sub.l	%a3, %d0
	movem.l	(%sp), %d2-%d7/%a2-%a6
	lea	44(%sp), %sp
	rts

/* void m_icinv(void) : invalide les caches d'instructions et de branchements (garde celui de donnees) */
	.section .text.m_icinv,"ax"
	.globl	m_icinv
m_icinv:
	nop
	move.l	#CACR_ICINV, %d0
	movec	%d0, %cacr
	nop
	rts

/* Les noyaux : du code sans adresse absolue ni saut hors de lui-meme, recopiable en SRAM (k_xxx .. k_xxx_end). */
	.section .text.k_clk,"ax"
	.globl	k_clk, k_clk_end
k_clk:					/* 16 x (64 addq + subq + bne) = 1 056 instructions d'un cycle */
	moveq	#16, %d7
1:	.rept	64
	addq.l	#1, %d0
	.endr
	subq.l	#1, %d7
	bne.w	1b
	rts
k_clk_end:

	.section .text.k_alu,"ax"
	.globl	k_alu, k_alu_end
k_alu:					/* 8 x (64 + 2) = 528 instructions de calcul */
	moveq	#8, %d7
1:	.rept	16
	add.l	%d1, %d0
	eor.l	%d0, %d2
	lsl.l	#1, %d3
	sub.l	%d2, %d4
	.endr
	subq.l	#1, %d7
	bne.w	1b
	rts
k_alu_end:

	.section .text.k_mac,"ax"
	.globl	k_mac, k_mac_end
k_mac:					/* 8 x (40 + 2) = 336 instructions, l'allure d'un filtre : lecture, */
	lea	512(%a0), %a1		/* produits, ecriture ; a0 : 128 o lus, puis 128 o en a0 + 512 */
	moveq	#8, %d7
1:	.rept	4
	move.l	(%a0)+, %d0
	mac.l	%d0, %d1, %acc0
	mac.l	%d0, %d2, %acc1
	movclr.l %acc0, %d3
	add.l	%d3, %d4
	mac.l	%d4, %d5, %acc2
	movclr.l %acc1, %d6
	add.l	%d6, (%a1)+
	movclr.l %acc2, %d3
	add.l	%d3, %d5
	.endr
	subq.l	#1, %d7
	bne.w	1b
	rts
k_mac_end:

	.section .text.k_mem,"ax"
	.globl	k_mem, k_mem_end
k_mem:					/* 8 x (32 + 2) = 272 instructions : 1 Ko recopie, a0 -> a0 + 1 024 */
	lea	1024(%a0), %a1
	moveq	#8, %d7
1:	.rept	32
	move.l	(%a0)+, (%a1)+
	.endr
	subq.l	#1, %d7
	bne.w	1b
	rts
k_mem_end:

/* k_rd : lit les 4 mots de chacune des 64 lignes de 16 o en a0 (1 Ko) : 256 lectures */
	.section .text.k_rd,"ax"
	.globl	k_rd, k_rd_end
k_rd:
	moveq	#16, %d7
1:	.rept	4
	movem.l	(%a0), %d0-%d3
	lea	16(%a0), %a0
	.endr
	subq.l	#1, %d7
	bne.w	1b
	rts
k_rd_end:
