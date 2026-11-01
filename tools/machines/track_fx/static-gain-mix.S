| Somme native stable : meme ordre EMAC/prefetch et memes valeurs de gain.
| Aucun ACC vide au debut : la premiere sortie conserve l ACC0 entrant.
| Si une rampe existe, ou delta chevauche les sorties, reprendre le noyau stock.
.text
.globl sg_sum6,sg_sum7,sg_static6,sg_static7
sg_sum6:
 movea.l 16(%sp),%a0
 tst.l 0(%a0)
 bne.w .Lfallback6
 tst.l 4(%a0)
 bne.w .Lfallback6
 tst.l 8(%a0)
 bne.w .Lfallback6
 tst.l 12(%a0)
 bne.w .Lfallback6
 tst.l 16(%a0)
 bne.w .Lfallback6
 tst.l 20(%a0)
 bne.w .Lfallback6
 move.l 4(%sp),%d0
 addi.l #252,%d0
 bcs.w .Lfallback6
 cmp.l %a0,%d0
 bls.s sg_static6
 move.l %a0,%d1
 addi.l #24,%d1
 bcs.w .Lfallback6
 cmp.l 4(%sp),%d1
 bhi.w .Lfallback6
sg_static6:
 lea -32(%sp),%sp
 movem.l %d2-%d7/%a2-%a3,(%sp)
 movea.l 36(%sp),%a1
 moveq #8,%d5
 movea.l 40(%sp),%a2
 movea.l 48(%sp),%a3
 movea.l 44(%sp),%a0
 movem.l (%a0),%d0-%d4/%a0
 move.l (%a2)+,%d6
.Lloop6:
 .rept 4
 msac.l %d0,%d6,124(%a2),%d6,%acc0
 msac.l %d1,%d6,252(%a2),%d6,%acc0
 msac.l %d2,%d6,380(%a2),%d6,%acc0
 msac.l %d3,%d6,508(%a2),%d6,%acc0
 msac.l %d4,%d6,636(%a2),%d6,%acc0
 msac.l %a0,%d6,(%a2)+,%d6,%acc0
 movclr.l %acc0,%d7
 move.l %d7,(%a1)+
 addq.l #4,%a1
 .endr
 subq.l #1,%d5
 bgt.w .Lloop6
 movea.l 44(%sp),%a2
 movem.l %d0-%d4/%a0,(%a2)
 movem.l (%sp),%d2-%d7/%a2-%a3
 lea 32(%sp),%sp
 rts
.Lfallback6:
 lea -32(%sp),%sp
 movem.l %d2-%d7/%a2-%a3,(%sp)
 jmp sg_resume6
sg_sum7:
 movea.l 16(%sp),%a0
 tst.l 0(%a0)
 bne.w .Lfallback7
 tst.l 4(%a0)
 bne.w .Lfallback7
 tst.l 8(%a0)
 bne.w .Lfallback7
 tst.l 12(%a0)
 bne.w .Lfallback7
 tst.l 16(%a0)
 bne.w .Lfallback7
 tst.l 20(%a0)
 bne.w .Lfallback7
 tst.l 24(%a0)
 bne.w .Lfallback7
 move.l 4(%sp),%d0
 addi.l #252,%d0
 bcs.w .Lfallback7
 cmp.l %a0,%d0
 bls.s sg_static7
 move.l %a0,%d1
 addi.l #28,%d1
 bcs.w .Lfallback7
 cmp.l 4(%sp),%d1
 bhi.w .Lfallback7
sg_static7:
 lea -40(%sp),%sp
 movem.l %d2-%d7/%a2-%a5,(%sp)
 movea.l 44(%sp),%a3
 moveq #8,%d5
 movea.l 48(%sp),%a4
 movea.l 56(%sp),%a5
 movea.l 52(%sp),%a0
 movem.l (%a0),%d0-%d4/%a0-%a1
 move.l (%a4)+,%d6
.Lloop7:
 .rept 4
 msac.l %d0,%d6,124(%a4),%d6,%acc0
 msac.l %d1,%d6,252(%a4),%d6,%acc0
 msac.l %d2,%d6,380(%a4),%d6,%acc0
 msac.l %d3,%d6,508(%a4),%d6,%acc0
 msac.l %d4,%d6,636(%a4),%d6,%acc0
 msac.l %a0,%d6,764(%a4),%d6,%acc0
 msac.l %a1,%d6,(%a4)+,%d6,%acc0
 movclr.l %acc0,%d7
 move.l %d7,(%a3)+
 addq.l #4,%a3
 .endr
 subq.l #1,%d5
 bgt.w .Lloop7
 movea.l 52(%sp),%a4
 movem.l %d0-%d4/%a0-%a1,(%a4)
 movem.l (%sp),%d2-%d7/%a2-%a5
 lea 40(%sp),%sp
 rts
.Lfallback7:
 lea -40(%sp),%sp
 movem.l %d2-%d7/%a2-%a5,(%sp)
 jmp sg_resume7

.globl sg_mix_end
sg_mix_end:
