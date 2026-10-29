/* tempo-sync: DELAY TIME and LFO SPEED in note values of the tempo (notes/82).
 *
 * SETTINGS held + a turn of DELAY TIME or LFO SPEED switches the parameter between FREE (the stock values) and SYNC
 * (a note value: 1/128 .. 2 BAR for the delay, 1/128 .. 16 BAR per LFO cycle, the sign of the LFO value is its
 * direction). Right: SYNC, left: FREE. In SYNC a plain turn steps through the note values.
 *
 * Storage: the parameter's own 16-bit word, nothing else (kit, sound, LFO 2 record, LFO 3/4 tables as before).
 * Stock words are multiples of 256 (low byte 0), which is FREE. Bit 7 set = SYNC:
 *   DELAY TIME  H << 8 | 0x80 | idx   idx 0..20 into lu[]; H = the nearest FREE value (what an older OS plays)
 *   LFO SPEED   C << 8 | 0x80         C = idx 0..23, + 0x40 when reversed (lfo-plus packs LFO 2 as SPD >> 7: kept)
 * Lengths are in 1/1536 of a bar (lu[]): exact for every value of the ladder, triplets and dotted ones included.
 *
 * Audio: delay length in samples = 900000 * lu / tempo (tempo = BPM x 120, 0x40149310), the stock formula for the
 * stock values, clamped by the OS to 384000 (8 s); LFO phase step per block = +-49152 * tempo / lu (one cycle =
 * 1382400000). The OS smooths every parameter word (0x40058474); a SYNC target is copied as is, so its index is
 * never read half way through a glide.
 *
 * Model-TG symbols (30-model-tg-st.json): SET_HELD, MOD_USED (--defsym). Assembled by tools/gen_tempo_sync.py
 * (m68k gcc -mcpu=54418), every section placed in a freed 48x22 sprite mask.
 */
	TEMPO	= 0x40149310
	MAXD	= 384000
	NDLY	= 21		/* delay: 1/128 .. 2 BAR */
	NLFO	= 24		/* LFO: 1/128 .. 16 BAR */
	ID_DTIME = 0x25
	ID_LSPD	= 0x1d
	ID_LMULT = 0x1e
	FACE_SMALL = 0x40140ab0		/* petite police 5x9 de l'OS (une face, comme 0x401429ec : 16x22) */

	.globl	ts_audio, ts_smooth, ts_lfo, ts_hook, ts_dfmt, ts_lfmt, lu, names, tsf, ts_face, ts_draw, small

/* ---- audio: 0x400581ae, jsr ts_audio ; nop ; nop in place of mvs.w 428(a0),d0 ; lea TEMPO,a0 (a0 = smoothed
 * parameters). FREE: both instructions, back to the stock formula at 0x400581b8. SYNC: d0 = the length, clamped,
 * a0 = TEMPO as stock, and back at 0x400581da, after the stock clamp. FREE keeps d1/d3/d5 (the stock formula's
 * 48000, 10, 900); SYNC may use d1 (reloaded at 0x400581da). */
	.section .text.audio, "ax"
ts_audio:
	mvs.w	428(%a0), %d0
	lea	tsf, %a0
	btst	#6, 3(%a0)
	lea	TEMPO, %a0			/* (lea leaves the flags) */
	bne.s	1f
	rts					/* FREE target: the stock formula, whatever the glide */
1:	andi.l	#0x7f, %d0
	moveq	#NDLY - 1, %d1
	cmp.l	%d1, %d0
	bls.s	2f
	move.l	%d1, %d0
2:	lea	lu, %a0
	mvz.w	(%a0, %d0.l*2), %d0
	move.l	#900000, %d1
	mulu.l	%d1, %d0
	lea	TEMPO, %a0
	divu.l	(%a0), %d0
	cmpi.l	#MAXD, %d0
	bls.s	3f
	move.l	#MAXD, %d0
3:	move.l	#0x400581da, (%sp)
	rts

/* ---- smoothing: 0x400584f6, end of 0x40058474(targets): jsr ts_smooth in place of move.l #0x8000100c,d0.
 * Targets (T, the argument) and smoothed words (0x8000100c) have the same layout: word k of track t at
 * 14 + 66t + 2k. A SYNC word (bit 7) of LFO 1 SPD (k = 1) or LFO 2 SPD (k = 28), tracks 0..5,
 * or of DELAY TIME (k = 9 of the FX block, t = 6) is copied as is. Whether a target is SYNC is kept in tsf (bit t: LFO 1
 * of track t, bit 6: DELAY TIME): the smoothed word of a FREE target may cross bit 7 during a glide, so ts_audio and
 * ts_lfo ask tsf, and FREE stays the stock code to the bit. LFO 2's words are copied by lfo-plus to its own LFO
 * pass, where only the word is seen: for a FREE target bit 7 of the smoothed word is cleared (at most 127/32768 off
 * during a glide of LFO 2 SPD). d0-d1/a0-a1 free. */
	.section .text.smooth, "ax"
ts_smooth:
	movea.l	36(%sp), %a0
	lea	0x8000100c, %a1
	move.l	%d2, -(%sp)
	moveq	#0, %d2				/* tsf being built */
	moveq	#0, %d1				/* t */
1:	move.w	16(%a0), %d0			/* LFO 1 SPD */
	btst	#7, %d0
	beq.s	2f
	move.w	%d0, 16(%a1)
	bset	%d1, %d2
2:	move.w	70(%a0), %d0			/* LFO 2 SPD (lfo-plus) */
	btst	#7, %d0
	beq.s	3f
	move.w	%d0, 70(%a1)
	bra.s	4f
3:	bclr	#7, 71(%a1)			/* FREE: a glide never looks like SYNC to lfo-plus's copy */
4:	lea	66(%a0), %a0
	lea	66(%a1), %a1
	addq.l	#1, %d1
	moveq	#6, %d0
	cmp.l	%d0, %d1
	bne.s	1b
	move.w	32(%a0), %d0			/* t = 6, k = 9: DELAY TIME */
	btst	#7, %d0
	beq.s	5f
	move.w	%d0, 32(%a1)
	bset	#6, %d2
5:	move.l	%d2, tsf
	move.l	(%sp)+, %d2
	move.l	#0x8000100c, %d0
	rts

/* ---- LFO step: 0x40091b38, in the loop of 0x40091ab2 (the 6 LFOs, also run by lfo-plus for LFO 2..4):
 * jsr ts_lfo in place of move.w 6(a4),d3 ; asr.l d2,d7. a4 = the track's words + 22 (SPD at -6; in the OS's
 * smoothed words for LFO 1, in lfo-plus's copy for LFO 2..4), d7 = the stock
 * step before the shift; the tempo argument is at 64(sp) here. SYNC: d7 = +-49152 * tempo / lu, whatever MULT.
 * d1-d2/a0 free (d2 is reloaded at 0x40091b66). */
	.section .text.lfo, "ax"
ts_lfo:
	move.w	6(%a4), %d3
	asr.l	%d2, %d7
	mvz.w	-6(%a4), %d1
	btst	#7, %d1
	beq.s	9f
	move.l	%a4, %d2			/* the OS's own words (LFO 1): SYNC only if the target is */
	subi.l	#0x80001022, %d2
	cmpi.l	#6 * 66, %d2
	bcc.s	0f
	divu.w	#66, %d2
	mvz.w	%d2, %d2
	move.l	%d0, -(%sp)
	move.l	tsf, %d0
	lsr.l	%d2, %d0
	moveq	#1, %d2
	and.l	%d0, %d2
	move.l	(%sp)+, %d0
	tst.l	%d2
	beq.s	9f
0:	lsr.l	#8, %d1
	moveq	#0x3f, %d2
	and.l	%d1, %d2			/* idx */
	moveq	#NLFO - 1, %d7
	cmp.l	%d7, %d2
	bls.s	1f
	move.l	%d7, %d2
1:	lea	lu, %a0
	mvz.w	(%a0, %d2.l*2), %d2
	move.l	64(%sp), %d7
	movea.l	#49152, %a0
	move.l	%a0, -(%sp)
	mulu.l	(%sp)+, %d7
	divu.l	%d2, %d7
	btst	#6, %d1
	beq.s	9f
	neg.l	%d7
9:	rts

/* ---- knob step: 0x4000a980 (this, id, current, delta) -> new value, the step every parameter turn ends in
 * (0x4000b7d6 -> vtable[20] -> 0x4000c264 / Model-TG's fine_hook -> here). Hooked at 0x4000a986, after its
 * moveq #bound,d0 (the bound of the descriptors, rewritten by the added machines): jsr ts_hook ; nop in place of
 * movem.l d2-d7/a2-a3,(sp) ; movea.l 48(sp),a2. Done here, and back at 0x4000a98e with d0 (the bound) as it was,
 * unless the id is DELAY TIME or LFO SPEED: then the frame is undone and ts_dstep / ts_lstep run with the
 * arguments of 0x4000a980 at 4(sp). The caller clamps to 0..0x7f00 and stores: every word made here stays inside. */
	.section .text.hook, "ax"
ts_hook:
	movem.l	%d2-%d7/%a2-%a3, 4(%sp)
	movea.l	52(%sp), %a2
	move.l	56(%sp), %d1
	cmpi.l	#ID_DTIME, %d1
	beq.s	1f
	cmpi.l	#ID_LSPD, %d1
	beq.s	1f
	rts
1:	movem.l	4(%sp), %d2-%d7/%a2-%a3
	lea	48(%sp), %sp
	cmpi.l	#ID_DTIME, %d1
	bne.s	2f
	jmp	ts_dstep
2:	jmp	ts_lstep
/* the stock step, from its start: the bound is the live operand of 0x4000a984 */
ts_stock:
	lea	-44(%sp), %sp
	movem.l	%d2-%d7/%a2-%a3, (%sp)
	movea.l	48(%sp), %a2
	mvs.b	0x4000a985, %d0
	jmp	0x4000a98e

	.section .text.step, "ax"
/* d0 = the number of ladder steps of a turn: delta / 256, at least one, signed. In: d1 = delta. */
steps:
	move.l	%d1, %d0
	asr.l	#8, %d0
	bne.s	1f
	moveq	#1, %d0
	tst.l	%d1
	bpl.s	1f
	moveq	#-1, %d0
1:	rts

ts_dstep:
	move.l	12(%sp), %d0			/* current */
	move.l	16(%sp), %d1			/* delta */
	tst.l	SET_HELD
	beq.s	0f
	jmp	ds_mode
0:
	btst	#7, %d0
	bne.s	0f
	jmp	ts_stock			/* FREE: stock */
0:
	andi.l	#0x7f, %d0
	move.l	%d0, -(%sp)
	bsr.s	steps
	add.l	(%sp)+, %d0
	bpl.s	1f
	moveq	#0, %d0
1:	moveq	#NDLY - 1, %d1
	cmp.l	%d1, %d0
	ble.s	dly_word
	move.l	%d1, %d0
/* d0 = idx -> d0 = its word (H = the nearest FREE value, 1..127, minus one) */
dly_word:
	move.l	%d2, -(%sp)
	lea	lu, %a0
	mvz.w	(%a0, %d0.l*2), %d1
	addq.l	#6, %d1
	divu.w	#12, %d1			/* round(lu / 12) */
	mvz.w	%d1, %d1
	moveq	#127, %d2
	cmp.l	%d2, %d1
	bls.s	1f
	move.l	%d2, %d1
1:	subq.l	#1, %d1
	bpl.s	2f
	moveq	#0, %d1
2:	lsl.l	#8, %d1
	ori.l	#0x80, %d1
	or.l	%d1, %d0
	move.l	(%sp)+, %d2
	rts

	.section .text.dmode, "ax"
ds_mode:
	moveq	#1, %d1
	move.l	%d1, MOD_USED			/* SETTINGS + this turn: no Config Menu on release */
	move.l	16(%sp), %d1
	btst	#7, %d0
	bne.s	ds_tofree
	tst.l	%d1
	ble.s	ds_keep				/* FREE, turned left: nothing */
	asr.l	#8, %d0				/* FREE -> SYNC: n / 128 bar = 12 n / 1536 */
	andi.l	#0x7f, %d0
	addq.l	#1, %d0
	mulu.w	#12, %d0
	moveq	#NDLY, %d1
	jsr	nearest
	jmp	dly_word
ds_tofree:
	tst.l	%d1
	bge.s	ds_keep				/* SYNC, turned right: nothing */
	andi.l	#0x7f, %d0			/* SYNC -> FREE: the nearest FREE value, round(lu / 12), 1..128 */
	moveq	#NDLY - 1, %d1
	cmp.l	%d1, %d0
	bls.s	1f
	move.l	%d1, %d0
1:	lea	lu, %a0
	mvz.w	(%a0, %d0.l*2), %d0
	addq.l	#6, %d0
	divu.w	#12, %d0
	mvz.w	%d0, %d0
	cmpi.l	#128, %d0
	bls.s	2f
	move.l	#128, %d0
2:	subq.l	#1, %d0
	lsl.l	#8, %d0
	rts
ds_keep:
	move.l	12(%sp), %d0
	rts

	.section .text.near, "ax"
/* nearest(d0 = x, d1 = n) -> d0 = the index of the value of lu[0..n-1] nearest to x by ratio: x^2 against the
 * products of neighbours (geometric middles); x is held below 2 * 24576 so x^2 fits. Keeps d2-d7/a2-a6. */
nearest:
	lea	-12(%sp), %sp
	movem.l	%d2-%d4, (%sp)
	cmpi.l	#49152, %d0
	bls.s	1f
	move.l	#49152, %d0
1:	mulu.l	%d0, %d0			/* x^2 */
	lea	lu, %a0
	subq.l	#1, %d1
	moveq	#0, %d2				/* i */
2:	cmp.l	%d1, %d2
	bcc.s	3f
	mvz.w	(%a0, %d2.l*2), %d3
	mvz.w	2(%a0, %d2.l*2), %d4
	mulu.l	%d4, %d3
	cmp.l	%d3, %d0
	bcs.s	3f				/* x^2 < lu[i] lu[i+1]: lu[i] */
	addq.l	#1, %d2
	bra.s	2b
3:	move.l	%d2, %d0
	movem.l	(%sp), %d2-%d4
	lea	12(%sp), %sp
	rts

/* ---- LFO SPEED */
	.section .text.lstep, "ax"
ts_lstep:
	move.l	12(%sp), %d0
	move.l	16(%sp), %d1
	tst.l	SET_HELD
	beq.s	0f
	jmp	ls_mode
0:
	btst	#7, %d0
	bne.s	0f
	jmp	ts_stock
0:
	lsr.l	#8, %d0				/* position: -1/128 (0) .. -16 BAR (23), +16 BAR (24) .. +1/128 (47) */
	moveq	#0x3f, %d1
	and.l	%d0, %d1
	cmpi.l	#NLFO - 1, %d1
	bls.s	0f
	moveq	#NLFO - 1, %d1
0:
	btst	#6, %d0
	beq.s	1f
	move.l	%d1, %d0			/* reversed: idx */
	bra.s	2f
1:	moveq	#2 * NLFO - 1, %d0
	sub.l	%d1, %d0			/* forward: 2 NLFO - 1 - idx */
2:	move.l	%d0, -(%sp)
	move.l	20(%sp), %d1
	jsr	steps
	add.l	(%sp)+, %d0
	bpl.s	3f
	moveq	#0, %d0
3:	moveq	#2 * NLFO - 1, %d1
	cmp.l	%d1, %d0
	ble.s	4f
	move.l	%d1, %d0
4:	moveq	#NLFO, %d1
	cmp.l	%d1, %d0
	bge.s	5f
	ori.l	#0x40, %d0			/* reversed, idx = position */
	bra.s	lfo_word
5:	moveq	#2 * NLFO - 1, %d1
	sub.l	%d0, %d1
	move.l	%d1, %d0			/* forward, idx = 2 NLFO - 1 - position */
lfo_word:
	lsl.l	#8, %d0
	ori.l	#0x80, %d0
	rts

	.section .text.lmode, "ax"
ls_mode:
	moveq	#1, %d1
	move.l	%d1, MOD_USED
	move.l	16(%sp), %d1
	btst	#7, %d0
	beq.s	0f
	jmp	ls_tofree
0:
	tst.l	%d1
	bgt.s	0f
	jmp	ds_keep
0:
	lea	-16(%sp), %sp
	movem.l	%d2-%d5, (%sp)
	movea.l	4 + 16(%sp), %a1
	jsr	lfo_mult			/* d2 = m', d3 = the tempo it runs on */
	move.l	12 + 16(%sp), %d0
	subi.l	#16384, %d0			/* s */
	moveq	#0, %d5				/* reversed? */
	tst.l	%d0
	bpl.s	1f
	neg.l	%d0
	moveq	#0x40, %d5
1:
	jsr	lfo_len				/* d0 = cycle in 1/1536 bar (held below 49152) */
	moveq	#NLFO, %d1
	jsr	nearest
	or.l	%d5, %d0
	movem.l	(%sp), %d2-%d5
	lea	16(%sp), %sp
	jmp	lfo_word
	.section .text.lfree, "ax"
ls_tofree:
	tst.l	%d1
	blt.s	0f
	jmp	ds_keep
0:
	lea	-24(%sp), %sp
	movem.l	%d2-%d7, (%sp)
	movea.l	4 + 24(%sp), %a1
	jsr	lfo_mult
	move.l	12 + 24(%sp), %d0
	lsr.l	#8, %d0
	moveq	#0x3f, %d1
	and.l	%d0, %d1
	moveq	#NLFO - 1, %d6
	cmp.l	%d6, %d1
	bls.s	1f
	move.l	%d6, %d1
1:	lea	lu, %a0
	mvz.w	(%a0, %d1.l*2), %d4
	mulu.l	%d4, %d4			/* target^2 */
	moveq	#63, %d7			/* the largest |speed| that direction allows */
	btst	#6, %d0
	beq.s	2f
	moveq	#64, %d7
2:	moveq	#1, %d6				/* v */
3:	cmp.l	%d7, %d6
	bcc.s	5f
	move.l	%d6, %d0
	lsl.l	#8, %d0
	jsr	lfo_len
	move.l	%d0, %d5			/* x(v) */
	move.l	%d6, %d0
	addq.l	#1, %d0
	lsl.l	#8, %d0
	jsr	lfo_len				/* x(v + 1) */
	mulu.l	%d5, %d0
	cmp.l	%d0, %d4
	bcc.s	5f				/* target^2 >= x(v) x(v + 1): v */
	addq.l	#1, %d6
	bra.s	3b
5:	lsl.l	#8, %d6
	move.l	12 + 24(%sp), %d0
	btst	#14, %d0
	beq.s	6f
	neg.l	%d6
6:	move.l	%d6, %d0
	addi.l	#16384, %d0
	movem.l	(%sp), %d2-%d7
	lea	24(%sp), %sp
	rts

	.section .text.lmul, "ax"
/* lfo_mult(a1 = this) -> d2 = m' (0..11), d3 = the tempo the stock step uses (the tempo, or 120 BPM = 14400 for the
 * free multipliers 12..23), from MULT of the same LFO page (vtable[28] get, id 0x1e, as the page reads it; on
 * lfo-plus's pages 2..4 its own MULT). Clamped to 0..23 as 0x40091ab2 does. d0-d1/a0-a1 used. */
lfo_mult:
	movea.l	(%a1), %a0
	movea.l	28(%a0), %a0
	pea	ID_LMULT
	move.l	%a1, -(%sp)
	jsr	(%a0)
	addq.l	#8, %sp
	asr.l	#8, %d0
	extb.l	%d0
	bpl.s	1f
	moveq	#0, %d0
1:	moveq	#23, %d1
	cmp.l	%d1, %d0
	ble.s	2f
	move.l	%d1, %d0
2:	move.l	TEMPO, %d3
	moveq	#11, %d1
	cmp.l	%d1, %d0
	ble.s	3f
	subi.l	#12, %d0
	move.l	#14400, %d3
3:	move.l	%d0, %d2
	rts

/* lfo_len(d0 = |s| speed - 16384, d2 = m', d3 = tempo used) -> d0 = 49152 * TEMPO / |step|, the cycle in 1/1536
 * bar at the current tempo, held at 49152 (32 bars) when slower. Keeps d1-d7. */
lfo_len:
	lea	-8(%sp), %sp
	movem.l	%d1/%d4, (%sp)
	add.l	%d0, %d0
	mulu.l	%d3, %d0			/* |s| * 2 * tempo used: < 2^31 */
	moveq	#11, %d1
	sub.l	%d2, %d1
	lsr.l	%d1, %d0			/* |step| */
	move.l	TEMPO, %d4
	cmp.l	%d4, %d0
	bhi.s	1f
	move.l	#49152, %d0
	bra.s	2f
1:	movea.l	#49152, %a0
	move.l	%a0, -(%sp)
	mulu.l	(%sp)+, %d4
	divu.l	%d0, %d4
	move.l	%d4, %d0
2:	movem.l	(%sp), %d1/%d4
	lea	8(%sp), %sp
	rts

/* ---- value text: 0x4004dfda (DELAY TIME, (functor, value, buf)): jmp ts_dfmt in place of move.l #256,d0. FREE:
 * the stock text. SYNC: the note value, and " >" when the OS clamps it at this tempo. In SYNC the value window
 * draws with the small face (ts_face) : the note values do not fit the big one. */
	.section .text.fmt, "ax"
ts_dfmt:
	move.l	8(%sp), %d0
	btst	#7, %d0
	bne.s	1f
	clr.b	small
	move.l	#256, %d0
	jmp	0x4004dfe0
1:	moveq	#1, %d1			/* d1 libre ici : le formateur le pose plus bas */
	move.b	%d1, small
	andi.l	#0x7f, %d0
	moveq	#NDLY - 1, %d1
	cmp.l	%d1, %d0
	bls.s	2f
	move.l	%d1, %d0
2:	movea.l	12(%sp), %a1
	move.l	%d0, -(%sp)
	jsr	name
	move.l	(%sp)+, %d0
	lea	lu, %a0
	mvz.w	(%a0, %d0.l*2), %d0
	move.l	#900000, %d1
	mulu.l	%d1, %d0
	lea	TEMPO, %a0
	divu.l	(%a0), %d0
	cmpi.l	#MAXD, %d0
	bls.s	3f
	move.b	#' ', (%a1)+
	move.b	#'>', (%a1)+
	clr.b	(%a1)
3:	rts

	.section .text.lfmt, "ax"
/* 0x4004e00e (LFO SPEED): jmp ts_lfmt in place of move.l #-16384,d0. SYNC: "-" when reversed, the note value. */
ts_lfmt:
	move.l	8(%sp), %d0
	btst	#7, %d0
	bne.s	1f
	clr.b	small
	move.l	#-16384, %d0
	jmp	0x4004e014
1:	moveq	#1, %d1			/* d1 libre ici : le formateur le pose plus bas */
	move.b	%d1, small
	movea.l	12(%sp), %a1
	lsr.l	#8, %d0
	btst	#6, %d0
	beq.s	2f
	move.b	#'-', (%a1)+
2:	andi.l	#0x3f, %d0
	moveq	#NLFO - 1, %d1
	cmp.l	%d1, %d0
	bls.s	name
	move.l	%d1, %d0
/* name(d0 = idx, a1 = buf): copies names[idx], a1 left on its terminating 0 */
name:
	lea	names, %a0
	movea.l	(%a0, %d0.l*4), %a0
1:	move.b	(%a0)+, (%a1)+
	bne.s	1b
	subq.l	#1, %a1
	rts

/* ---- la police de la fenêtre de valeur : 0x4001d8ae, dans 0x4001d818 (slot 144 de ParameterPageView), à la place
 * de move.l sp,d4 ; add.l #60,d4. La fenêtre vient de formater sa valeur par vt[60] (notre ts_dfmt / ts_lfmt), qui
 * met small à 1 pour une valeur de note : celles-ci ne tiennent pas dans la grande police (« 3/16 » 48 px, « 1 BAR »
 * 65 px, « -16 BAR » 82 px mesurés, pour une plaque de 60 px ; aussi, deux glyphes de large en plus débordent sur le
 * bord). La face a été empilée en 0x4001d8a8 (pea 0x401429ec) : elle est remplacée sur place, puis d4 = sp + 60
 * comme le code stock (l'objet police se construit là). */
	.section .text.face, "ax"
ts_face:
	tst.b	small
	beq.s	1f
	move.l	#FACE_SMALL, %d4		/* d4 est de toute façon écrasé, comme par le stock */
	move.l	%d4, 4(%sp)			/* la face empilée est sous l'adresse de retour du jsr */
1:	move.l	%sp, %d4
	add.l	#64, %d4			/* sp + 4 (retour) + 60 : le sp + 60 du stock */
	rts

/* ---- même fenêtre, 0x4001d8d6 : jsr 0x40071a04 (DRAW_TEXT) -> jsr ts_draw. La ligne de 9 px se poserait en haut
 * de la case de 22 px : +6 la centre sur la ligne de la grande police (34..55 -> 34..42 devient 40..48). Et le
 * drapeau est remis à zéro : la fenêtre suivante (un autre paramètre, ou FREE) reprend la grande police. */
	.section .text.draw2, "ax"
ts_draw:
	tst.b	small
	beq.s	1f
	addq.l	#6, 16(%sp)			/* le y empilé par pea 0x22 */
1:	clr.b	small
	jmp	0x40071a04

	.section .data.flag, "aw"
small:	.byte	0				/* 1 : la fenêtre de valeur affiche une valeur de note (petite police) */

	.section .data.tab, "aw"
	.balign	2
/* the ladder, in 1/1536 bar: the retrig's 16 values (Model-TG rtg_divs, 1/64 .. 1 BAR), 1/128 and 1/96 below,
 * 4/3, 3/2, 2 BAR above (the delay stops there: 2 BAR fits the line from 60 BPM), and 4, 8, 16 BAR for the LFOs */
lu:	.short	12, 16, 24, 32, 48, 64, 96, 128, 192, 256, 288, 384, 512, 576, 768, 1024, 1152, 1536
	.short	2048, 2304, 3072, 6144, 12288, 24576
	.balign	4
names:	.long	n0, n1, n2, n3, n4, n5, n6, n7, n8, n9, n10, n11, n12, n13, n14, n15, n16, n17
	.long	n18, n19, n20, n21, n22, n23

	.balign	4
tsf:	.long	0				/* SYNC targets seen by ts_smooth: bit t LFO 1 of track t, bit 6 delay */

	.section .data.str, "aw"
n0:	.asciz	"1/128"
n1:	.asciz	"1/96"
n2:	.asciz	"1/64"
n3:	.asciz	"1/48"
n4:	.asciz	"1/32"
n5:	.asciz	"1/24"
n6:	.asciz	"1/16"
n7:	.asciz	"1/12"
n8:	.asciz	"1/8"
n9:	.asciz	"1/6"
n10:	.asciz	"3/16"
n11:	.asciz	"1/4"
n12:	.asciz	"1/3"
n13:	.asciz	"3/8"
n14:	.asciz	"1/2"
n15:	.asciz	"2/3"
n16:	.asciz	"3/4"
n17:	.asciz	"1 BAR"
n18:	.asciz	"4/3"
n19:	.asciz	"3/2"
n20:	.asciz	"2 BAR"
n21:	.asciz	"4 BAR"
n22:	.asciz	"8 BAR"
n23:	.asciz	"16 BAR"
