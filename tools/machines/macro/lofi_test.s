| Adaptation test du routage FUNC+PITCH a un index MACRO configurable.
| Pas/texte/dessin : 18nelli18/Modded-Cycles, d89267a, MIT (cd905ac + 62fb099).
| Le detour original garde exactement sa pile ; seule la combinaison MACRO est interceptee.
    .text
    .globl ml_knob,ml_machine,ml_original
ml_knob:
    move.l 36(%sp),%d0
    cmp.l ml_machine(%pc),%d0
    bne.s 1f
    tst.b %d5
    beq.s 1f
    moveq #2,%d1
    cmp.l %d1,%d2
    bne.s 1f
    move.l #lofi_step,%d1
    move.l %d1,0x40a72870
    move.l #lofi_fmt,%d1
    move.l %d1,0x40a72840
    move.l #lofi_draw,%d1
    move.l %d1,0x40a72850
    moveq #43,%d2
    addq.l #4,%sp
    jmp 0x4001e910
1:  move.l ml_original(%pc),-(%sp)
    rts
    .balign 4
ml_machine: .long 0
ml_original: .long 0

	.globl	lofi_step, lofi_fmt, lofi_draw
lofi_step:
	move.l	8(%sp), %d0
	addi.l	#0x80, %d0
	andi.l	#0xffffff00, %d0
	move.l	12(%sp), %d1
	bpl.s	1f
	neg.l	%d1
	addi.l	#0xff, %d1
	andi.l	#0xffffff00, %d1
	sub.l	%d1, %d0
	bra.s	2f
1:	addi.l	#0xff, %d1
	andi.l	#0xffffff00, %d1
	add.l	%d1, %d0
2:	cmp.l	16(%sp), %d0
	bge.s	3f
	move.l	16(%sp), %d0
3:	cmp.l	20(%sp), %d0
	ble.s	4f
	move.l	20(%sp), %d0
4:	rts
lofi_fmt:
	move.l	8(%sp), %d0
	addi.l	#0x80, %d0
	asr.l	#8, %d0
	bpl.s	1f
	moveq	#0, %d0
1:	moveq	#127, %d1
	cmp.l	%d1, %d0
	ble.s	2f
	move.l	%d1, %d0
2:	moveq	#64, %d1
	sub.l	%d0, %d1
	beq.s	5f
	bmi.s	3f
	lea	lofi_khz, %a0
	mvz.b	-1(%a0,%d1.l), %d0
	lea	lofi_s_k, %a0
	bra.s	4f
3:	moveq	#65, %d1
	sub.l	%d1, %d0
	moveq	#10, %d1
	muls.l	%d1, %d0
	moveq	#62, %d1
	divs.l	%d1, %d0
	moveq	#12, %d1
	sub.l	%d0, %d1
	move.l	%d1, %d0
	lea	lofi_s_b, %a0
4:	move.l	%d0, -(%sp)
	move.l	%a0, -(%sp)
	move.l	20(%sp), -(%sp)
	jsr	0x40000e6e
	lea	12(%sp), %sp
	rts
5:	pea	0x40124b67
	move.l	16(%sp), -(%sp)
	jsr	0x40000e6e
	addq.l	#8, %sp
	rts
lofi_draw:
	lea	-24(%sp), %sp
	move.l	%sp, %d0
	move.l	%d0, -(%sp)
	move.l	36(%sp), -(%sp)
	clr.l	-(%sp)
	bsr.w	lofi_fmt
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
lofi_s_k:	.asciz	"%dK"
lofi_s_b:	.asciz	"%dB"
lofi_khz:	.byte	46, 44, 43, 41, 40, 38, 37, 35, 34, 33, 31, 30, 29, 28, 27, 26, 25, 24, 23, 22, 21, 20, 20, 19, 18, 17, 17, 16, 16, 15, 14, 14, 13, 13, 12, 12, 11, 11, 11, 10, 10, 9, 9, 9, 8, 8, 8, 7, 7, 7, 7, 6, 6, 6, 6, 5, 5, 5, 5, 5, 4, 4, 4, 4
	.balign	2
