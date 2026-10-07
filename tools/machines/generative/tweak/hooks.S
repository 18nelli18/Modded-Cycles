/* SPDX-License-Identifier: MIT — Copyright (c) 2026 Combust. Voir ../LICENSE. */
/* Points d'entrée en assembleur du tweak generative, par-dessus model-tg (30-model-tg.json, TG 70b39dd), notes/50.
 * Lié en tête de la zone ajoutée en 0x401bf8c0 (fin du bloc de Model-TG). */
	.equ TG_BOOT_HOOK,  0x401bf3d8	/* boot_extra_hook : ACR1, effacement de la BSS sauf [0x401ab750, reserved_end) */
	.equ TG_RESEND_OPD, 0x401bf402	/* opérande de « moveal #0x401bf8c0,%a0 » en 0x401bf400 dans cette accroche */
	.equ TG_KEY_HOOK,   0x401ae968	/* key_hook, où saute 0x4007240c avec model-tg */
	.equ TG_PAD_HOOK,   0x401b3ffc	/* pad_hook, où saute la méthode des pads de PadsView, 0x4001d180 */

	.section .text.boot, "ax"
	.globl ours_boot
/* 0x40000530 « jsr ours_boot » : étend la zone épargnée par l'effacement de la BSS de TG jusqu'à notre fin, puis
 * l'accroche de TG (ne revient pas). */
ours_boot:
	lea	TG_RESEND_OPD, %a0
	move.l	#ours_res_end, (%a0)
	jmp	TG_BOOT_HOOK

	.text
	.globl ours_key_hook
/* 0x4007240c « jmp ours_key_hook ». Contrat de l'accesseur d'origine : (KeyEvent *) en 4(sp), code dans d0,
 * seuls d0/d1/a0/a1 écrasés (le C appelé est compilé par GCC : il garde d2-d7/a2-a6). ours_key rend le code, ou
 * -1 = « pas pour nous » : saut final vers key_hook de TG, avec la pile reçue. */
ours_key_hook:
	move.l	4(%sp), -(%sp)
	jsr	ours_key
	addq.l	#4, %sp
	moveq	#-1, %d1
	cmp.l	%d1, %d0
	beq.s	1f
	rts
1:	jmp	TG_KEY_HOOK

	.globl ours_pad_hook
/* 0x4001d180 « jmp ours_pad_hook » (nous réorientons le jmp de TG). Méthode de PadsView (this, événement) : +16 type
 * (1 = appui), +20 numéro du pad. Page ouverte, chaque événement de pad est à nous et rendu utilisé (d0 = 1, comme la
 * méthode d'origine et pad_hook de TG) : la méthode d'origine (note on/off par 0x4001d05e/0x4001d0fc, choix de
 * piste) ne tourne pas, pas de son. Sinon pad_hook de TG inchangé (sa page retrig, puis la méthode d'origine). */
ours_pad_hook:
	tst.l	pg_obj
	bne.s	1f
	jmp	TG_PAD_HOOK
1:	move.l	8(%sp), -(%sp)
	jsr	ours_pad
	addq.l	#4, %sp
	moveq	#1, %d0
	rts

	.globl pg_dtor0, pg_dtor1, pg_enc_th
/* Notre copie du groupe de vtables de DrumSelect fait pointer ses deux destructeurs ici : oublier la page, puis les
 * destructeurs d'origine (exactement mm_dtor0/mm_dtor1 de TG, model_tg.s:8577-8588). */
pg_dtor0:
	jsr	pg_gone
	jmp	0x400f43ca
pg_dtor1:
	jsr	pg_gone
	jmp	0x400f4486
/* Entrée par la base EncoderHandler (+4) : ajuste this, comme le thunk d'origine 0x400a2926. */
pg_enc_th:
	subq.l	#4, 4(%sp)
	jra	pg_enc
