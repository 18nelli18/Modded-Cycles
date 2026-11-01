| Decision seule : 6/7 sends natifs. Aucun sample, EMAC ou registre callee-save touche.
| ABI C identique au native_sum2.75 : tailcall des memes noyaux et arguments.
.text
.globl ns_sum
ns_sum:
 movea.l 12(%sp),%a0
 movea.l 16(%sp),%a1
 moveq #-1,%d0
 tst.l 0(%a0)
 bne.s .Lon0
 tst.l 0(%a1)
 beq.s .Lnext0
.Lon0:
 tst.l %d0
 bpl.w .Lmany
 moveq #0,%d0
.Lnext0:
 tst.l 4(%a0)
 bne.s .Lon1
 tst.l 4(%a1)
 beq.s .Lnext1
.Lon1:
 tst.l %d0
 bpl.w .Lmany
 moveq #1,%d0
.Lnext1:
 tst.l 8(%a0)
 bne.s .Lon2
 tst.l 8(%a1)
 beq.s .Lnext2
.Lon2:
 tst.l %d0
 bpl.w .Lmany
 moveq #2,%d0
.Lnext2:
 tst.l 12(%a0)
 bne.s .Lon3
 tst.l 12(%a1)
 beq.s .Lnext3
.Lon3:
 tst.l %d0
 bpl.w .Lmany
 moveq #3,%d0
.Lnext3:
 tst.l 16(%a0)
 bne.s .Lon4
 tst.l 16(%a1)
 beq.s .Lnext4
.Lon4:
 tst.l %d0
 bpl.w .Lmany
 moveq #4,%d0
.Lnext4:
 tst.l 20(%a0)
 bne.s .Lon5
 tst.l 20(%a1)
 beq.s .Lnext5
.Lon5:
 tst.l %d0
 bpl.w .Lmany
 moveq #5,%d0
.Lnext5:
 moveq #7,%d1
 cmp.l 20(%sp),%d1
 bne.s .Ldone
 tst.l 24(%a0)
 bne.s .Lon6
 tst.l 24(%a1)
 beq.s .Lnext6
.Lon6:
 tst.l %d0
 bpl.w .Lmany
 moveq #6,%d0
.Lnext6:
.Ldone:
 tst.l %d0
 bmi.s .Lzero
 move.l %d0,%d1
 lsl.l #2,%d1
 adda.l %d1,%a0
 adda.l %d1,%a1
 move.l %a0,12(%sp)
 move.l %a1,16(%sp)
 lsl.l #5,%d1
 add.l %d1,8(%sp)
 jmp lt_native_one
.Lzero:
 jmp lt_native_zero
.Lmany:
 moveq #6,%d1
 cmp.l 20(%sp),%d1
 beq.s .Lsix
 jmp mf_old_sum7
.Lsix:
 jmp mf_old_sum6
