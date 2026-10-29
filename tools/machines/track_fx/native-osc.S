| Operateur natif sans modulation : interpolation et gain inchanges.
| Entree interne 400a82cc, pile native112 octets, epilogue400a8330.
| Les deux poids ET leurs rampes doivent etre nuls. Sinon rejouer le hook.
.text
.globl dry_osc
dry_osc:
 tst.l %d4
 bne.w .Lnative
 move.l %fp,%d0
 bne.w .Lnative
 tst.l 104(%sp)
 bne.w .Lnative
 tst.l 108(%sp)
 bne.w .Lnative
 move.l 84(%sp),%a2
 move.l 88(%sp),%a1
 moveq #32,%d0
.Lsample:
 move.l %d7,%acc1
 moveq #16,%d3
 move.l %acc1,%d2
 andi.l #16777215,%d2
 asr.l %d3,%d2
 movclr.l %acc1,%d6
 andi.l #65535,%d6
 asl.l %d5,%d6
 move.l (%a5,%d2.l*4),%d3
 move.l 4(%a5,%d2.l*4),%d2
 move.l %d3,%acc0
 mac.l %d6,%d2,%acc0
 msac.l %d6,%d3,%acc0
 add.l %a2,%d7
 andi.l #16777215,%d7
 movclr.l %acc0,%d6
 msac.l %d1,%d6,%acc0
 add.l %a1,%d1
 move.l %d6,(%a3)+
 movclr.l %acc0,%d6
 move.l %d6,(%a0)+
 subq.l #1,%d0
 bne.w .Lsample
 jmp 0x400a8330
.Lnative:
 move.l %d7,%acc1
 move.l (%a1)+,%d3
 mac.l %d4,%d3,(%a2)+,%d3,%acc1
 jmp 0x400a82d4
