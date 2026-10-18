/* Dessin texte adapte du controle lo-fi MIT de18nelli18 (note119). */
 .text
 .globl mf_draw_text
mf_draw_text:
	lea	-24(%sp), %sp
	move.l	%sp, %d0
	move.l	%d0, -(%sp)
	move.l	36(%sp), -(%sp)
	clr.l	-(%sp)
	bsr.w	mf_fmt
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
