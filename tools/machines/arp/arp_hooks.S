/* Accroches de l'arpégiateur (notes/32), liées avec arp.c dans deux masques de sprites libérés (arp.ld).
 * Les écritures sur l'OS sont dans tools/gen_arp.py (HOOKS). */
	.globl	arp_filter_hook, arp_rate_d3, arp_rate_d2, arp_menu_tail, item_label, arp_post_on

	.section .text.audio_hook, "ax"

/* 0x40058e28 (10 o) : jsr arp_filter_hook ; nop ; nop. a2 = l'événement de note. arp_filter (C) garde d2-d7/a2-a6 ;
 * puis on refait les trois instructions remplacées, et le traitement reprend en 0x40058e32 (cmp.l d0,d1). */
arp_filter_hook:
	move.l	%a2, -(%sp)
	jsr	arp_filter
	addq.l	#4, %sp
	moveq	#-1, %d1
	move.l	8(%a2), %d2
	move.l	12(%a2), %d0
	rts

/* 0x4001a1c4 et 0x4001d25e (6 o chacun) : jsr arp_rate_d3 / arp_rate_d2 à la place de jsr 0x40016086 (Rte de la
 * piste) quand une note est jouée. L'objet de la piste est en 4(sp) ; son numéro dans d3 (0x4001a0xx) ou d2
 * (0x4001d1xx). arp_rate (C) rend Rte et note le réglage de l'arpège de cette piste. */
arp_rate_d3:
	move.l	%d3, -(%sp)
	bra.s	1f
arp_rate_d2:
	move.l	%d2, -(%sp)
1:	move.l	8(%sp), -(%sp)
	jsr	arp_rate
	addq.l	#8, %sp
	rts

	.section .text.post_hook, "ax"
/* 0x40081908 (6 o), dans 0x4008171e : jsr arp_post_on à la place de jsr 0x40080bf6 ; addq.l #4,sp (envoi à
 * l'interface du message de la note, empilé par l'appelant). arp_ui_post (C) l'envoie ou non ; puis on dépile ce
 * message comme l'addq remplacé. 24(fp) : 5e argument de 0x4008171e (pas tenus). d0-d1/a0-a1 sont libres ensuite
 * (0x4008190e restaure d2-d7/a2-a5 et revient). */
arp_post_on:
	move.l	24(%fp), -(%sp)
	move.l	8(%sp), -(%sp)
	jsr	arp_ui_post
	addq.l	#8, %sp
	movea.l	(%sp)+, %a0
	addq.l	#4, %sp
	jmp	(%a0)

	.section .text.menu_hook, "ax"
/* 0x4002d480 (6 o) : jmp arp_menu_tail, à la place de movem.l 24(sp),d2-d6/a2-a6, en fin du constructeur de
 * RetrigPadsMenuView ; a2 = le menu. Nos deux lignes, puis l'épilogue d'origine. */
arp_menu_tail:
	move.l	%a2, -(%sp)
	jsr	arp_menu_add
	addq.l	#4, %sp
	movem.l	24(%sp), %d2-%d6/%a2-%a6
	lea	128(%sp), %sp
	rts

/* Libellé d'une ligne, comme 0x4002cc44 : la chaîne rendue (std::string) est construite à l'adresse de a0, depuis le
 * texte gardé dans la fermeture de la std::function (4(sp) : son stockage ; arp.c, arp_menu_add). */
item_label:
	movea.l	4(%sp), %a1
	movea.l	(%a1), %a1
	link.w	%fp, #-4
	move.l	%d2, -(%sp)
	pea	-1(%fp)
	move.l	(%a1), -(%sp)
	move.l	%a0, %d2
	move.l	%a0, -(%sp)
	jsr	0x400f980c
	lea	12(%sp), %sp
	move.l	%d2, %d0
	move.l	-8(%fp), %d2
	unlk	%fp
	rts
