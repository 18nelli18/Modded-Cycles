/* Un seul contributeur non nul : meme MSAC fractionnaire et rampe stock.
 * ABI C : out intercale, plan32echantillons, gain Q31 negatif, delta Q31.
 * MACSR reste audio0xa0 ; ACC0 vide en sortie ; d2/d3/a2/a3 preserves. */
.text
.globl lt_sum1
.globl lt_native_zero,rt_record_pairs
.globl lt_native_one
| Native sparse mixer: preserve incoming ACC0 in the first sample.
lt_native_one:
 lea -16(%sp),%sp
 movem.l %d2-%d3/%a2-%a3,(%sp)
 move.l 20(%sp),%a0
 move.l 24(%sp),%a1
 move.l 28(%sp),%a2
 move.l 32(%sp),%a3
 move.l (%a2),%d1
 move.l (%a3),%d2
 moveq #7,%d3
1:
 .rept 4
 move.l (%a1)+,%d0
 msac.l %d0,%d1,%acc0
 movclr.l %acc0,%d0
 move.l %d0,(%a0)
 addq.l #8,%a0
 add.l %d2,%d1
 .endr
 subq.l #1,%d3
 bpl 1b
 move.l %d1,(%a2)
 movem.l (%sp),%d2-%d3/%a2-%a3
 lea 16(%sp),%sp
 rts
| Exact signed history quantization: live >>15 clamped [-32767,32767].
| Two samples per aligned long store; all history is retained.
rt_record_pairs:
 move.l %d2,-(%sp)
 move.l 8(%sp),%a0
 move.l 12(%sp),%a1
 moveq #15,%d2
1:
 move.l (%a0)+,%d0
 add.l %d0,%d0
 sats.l %d0
 swap %d0
 cmp.w #-32768,%d0
 bne.s 2f
 move.w #-32767,%d0
2:
 move.l (%a0)+,%d1
 add.l %d1,%d1
 sats.l %d1
 swap %d1
 cmp.w #-32768,%d1
 bne.s 3f
 move.w #-32767,%d1
3:
 swap %d0
 move.w %d1,%d0
 move.l %d0,(%a1)+
 subq.l #1,%d2
 bpl.s 1b
 move.l (%sp)+,%d2
 rts
| Native six/seven-input mixers with zero gains/deltas: only the first
| sample can contain the caller's incoming ACC0. Preserve that ABI too.
lt_native_zero:
 move.l 4(%sp),%a0
 movclr.l %acc0,%d0
 move.l %d0,(%a0)
 addq.l #8,%a0
 moveq #30,%d1
0:
 clr.l (%a0)
 addq.l #8,%a0
 subq.l #1,%d1
 bpl 0b
 rts
lt_sum1:
 lea -16(%sp),%sp
 movem.l %d2-%d3/%a2-%a3,(%sp)
 move.l 20(%sp),%a0
 move.l 24(%sp),%a1
 move.l 28(%sp),%a2
 move.l 32(%sp),%a3
 move.l (%a2),%d1
 move.l (%a3),%d2
 moveq #0,%d0
 move.l %d0,%acc0
 moveq #7,%d3
1:
 .rept 4
 move.l (%a1)+,%d0
 msac.l %d0,%d1,%acc0
 movclr.l %acc0,%d0
 move.l %d0,(%a0)
 addq.l #8,%a0
 add.l %d2,%d1
 .endr
 subq.l #1,%d3
 bpl 1b
 move.l %d1,(%a2)
 movem.l (%sp),%d2-%d3/%a2-%a3
 lea 16(%sp),%sp
 rts
