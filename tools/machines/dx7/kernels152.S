/* Boucles ColdFire LEGACY152 : memes interpolations Q24 MSFA (Apache2.0,
 * Google2012),32samples. Aucun nouvel accumulateur ni changement d'arrondi.
 * ABI C++ statique : arguments pile, d2-d7/a2-a4 preserves ; ACC0 vide a
 * chaque produit, MACSR gere par wrap.S. Boucle par4, pas de donnee cachee. */
.text
.macro DX_SAMPLE mod,add
 .if \mod
  move.l (%a1)+,%d0
  add.l %d4,%d0
 .else
  move.l %d4,%d0
 .endif
 move.l %d0,%d5
 asr.l %d6,%d5
 and.l #2046,%d5
 and.l #16383,%d0
 lea (%a2,%d5.l*4),%a4
 muls.l (%a4),%d0
 asr.l %d7,%d0
 add.l 4(%a4),%d0
 lsl.l #6,%d0
 add.l %d2,%d1
 mac.l %d0,%d1,<<,%acc0
 movclr.l %acc0,%d0
 .if \add
  add.l %d0,(%a0)+
 .else
  move.l %d0,(%a0)+
 .endif
 add.l %d3,%d4
.endm
.macro DX_LOOP mod,add,label
\label:
 .rept 4
  DX_SAMPLE \mod,\add
 .endr
 cmpa.l %a3,%a0
 bne \label
 movem.l (%sp),%d2-%d7/%a2-%a4
 lea 36(%sp),%sp
 rts
.endm
.globl _ZN10FmOpKernel7computeEPlPKlllllb
.type _ZN10FmOpKernel7computeEPlPKlllllb,@function
_ZN10FmOpKernel7computeEPlPKlllllb:
 lea -36(%sp),%sp
 movem.l %d2-%d7/%a2-%a4,(%sp)
 move.l 40(%sp),%a0
 move.l 44(%sp),%a1
 move.l 48(%sp),%d4
 move.l 52(%sp),%d3
 move.l 56(%sp),%d1
 move.l 60(%sp),%d2
 sub.l %d1,%d2
 add.l #16,%d2
 asr.l #5,%d2
 lea 128(%a0),%a3
 lea sintab,%a2
 moveq #13,%d6
 moveq #14,%d7
 tst.b 67(%sp)
 bne .Lmodadd
 DX_LOOP 1,0,.Lmodset
 DX_LOOP 1,1,.Lmodadd
.size _ZN10FmOpKernel7computeEPlPKlllllb,.-_ZN10FmOpKernel7computeEPlPKlllllb
.globl _ZN10FmOpKernel12compute_pureEPlllllb
.type _ZN10FmOpKernel12compute_pureEPlllllb,@function
_ZN10FmOpKernel12compute_pureEPlllllb:
 lea -36(%sp),%sp
 movem.l %d2-%d7/%a2-%a4,(%sp)
 move.l 40(%sp),%a0
 move.l 44(%sp),%d4
 move.l 48(%sp),%d3
 move.l 52(%sp),%d1
 move.l 56(%sp),%d2
 sub.l %d1,%d2
 add.l #16,%d2
 asr.l #5,%d2
 lea 128(%a0),%a3
 lea sintab,%a2
 moveq #13,%d6
 moveq #14,%d7
 tst.b 63(%sp)
 bne .Lpureadd
 DX_LOOP 0,0,.Lpureset
 DX_LOOP 0,1,.Lpureadd
.size _ZN10FmOpKernel12compute_pureEPlllllb,.-_ZN10FmOpKernel12compute_pureEPlllllb

/* Feedback : d5/d6 gardent exactement les deux sorties precedentes.
 * d6 sert d'indice sinus seulement apres copie de son ancienne valeur. */
.macro DX_FB_SAMPLE add
 move.l %d5,%d0
 add.l %d6,%d0
 asr.l %d7,%d0
 move.l %d6,%d5
 add.l %d4,%d0
 move.l %d0,%d6
 asr.l #8,%d6
 asr.l #5,%d6
 and.l #2046,%d6
 and.l #16383,%d0
 lea (%a2,%d6.l*4),%a4
 muls.l (%a4),%d0
 asr.l #8,%d0
 asr.l #6,%d0
 add.l 4(%a4),%d0
 lsl.l #6,%d0
 add.l %d2,%d1
 mac.l %d0,%d1,<<,%acc0
 movclr.l %acc0,%d6
 .if \add
  add.l %d6,(%a0)+
 .else
  move.l %d6,(%a0)+
 .endif
 add.l %d3,%d4
.endm
.macro DX_FB_LOOP add,label
\label:
 .rept 4
  DX_FB_SAMPLE \add
 .endr
 cmpa.l %a3,%a0
 bne \label
 move.l %d5,(%a1)
 move.l %d6,4(%a1)
 movem.l (%sp),%d2-%d7/%a2-%a4
 lea 36(%sp),%sp
 rts
.endm
.globl _ZN10FmOpKernel10compute_fbEPlllllS0_ib
.type _ZN10FmOpKernel10compute_fbEPlllllS0_ib,@function
_ZN10FmOpKernel10compute_fbEPlllllS0_ib:
 lea -36(%sp),%sp
 movem.l %d2-%d7/%a2-%a4,(%sp)
 move.l 40(%sp),%a0
 move.l 44(%sp),%d4
 move.l 48(%sp),%d3
 move.l 52(%sp),%d1
 move.l 56(%sp),%d2
 sub.l %d1,%d2
 add.l #16,%d2
 asr.l #5,%d2
 move.l 60(%sp),%a1
 move.l (%a1),%d5
 move.l 4(%a1),%d6
 move.l 64(%sp),%d7
 addq.l #1,%d7
 lea 128(%a0),%a3
 lea sintab,%a2
 tst.b 71(%sp)
 bne .Lfbadd
 DX_FB_LOOP 0,.Lfbset
 DX_FB_LOOP 1,.Lfbadd
.size _ZN10FmOpKernel10compute_fbEPlllllS0_ib,.-_ZN10FmOpKernel10compute_fbEPlllllS0_ib
