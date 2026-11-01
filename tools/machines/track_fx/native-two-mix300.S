| Mixeur natif deux operateurs,32samples : deux passes EMAC conservees.
| API : input0,input1,out,indices,etat. Deux adresses de gain invariantes.
| Si les ecritures peuvent modifier indices[0..1], deleguer au noyau natif.
| Ordre des lectures audio/ecritures et des additions de gain conserve.
| Registres non volatils, sorties d0/d1/a0/a1, CCR et etat EMAC identiques.
.text
.globl tm_render,tm_end
tm_render:
 move.l 16(%sp),%a0
 move.l 12(%sp),%d0
 sub.l %a0,%d0
 cmpi.l #8,%d0
 bcs.w .Lfallback
 move.l %a0,%d0
 sub.l 12(%sp),%d0
 cmpi.l #128,%d0
 bcs.w .Lfallback
 move.l (%a0),%d0
 move.l 20(%sp),%a1
 lea 24(%a1,%d0.l*4),%a1
 move.l %a1,%d1
 move.l %d1,%d0
 sub.l %a0,%d0
 cmpi.l #8,%d0
 bcs.w .Lfallback
 move.l %a0,%d0
 sub.l %d1,%d0
 cmpi.l #4,%d0
 bcs.w .Lfallback
 move.l 4(%a0),%d0
 move.l 20(%sp),%a1
 lea 24(%a1,%d0.l*4),%a1
 move.l %a1,%d0
 sub.l %a0,%d0
 cmpi.l #8,%d0
 bcs.w .Lfallback
 move.l %a0,%d0
 sub.l %a1,%d0
 cmpi.l #4,%d0
 bcs.w .Lfallback
 lea -52(%sp),%sp
 movem.l %d2-%d7/%a2-%a5,(%sp)
 move.l %d1,%a0
 move.l 56(%sp),%a3
 move.l 60(%sp),%a4
 move.l 64(%sp),%a5
 move.l %a3,40(%sp)
 move.l %a4,44(%sp)
 move.l %a5,48(%sp)
 move.l -16(%a0),%d3
 sub.l (%a0),%d3
 asr.l #5,%d3
 move.l -16(%a1),%d4
 sub.l (%a1),%d4
 asr.l #5,%d4
 moveq #8,%d7
.Lpass1:
 .rept 4
 move.l (%a3)+,%a2
 move.l (%a4)+,%d2
 move.l (%a0),%d5
 move.l (%a1),%d1
 mac.l %d5,%a2,%acc0
 mac.l %d1,%d2,%acc0
 movclr.l %acc0,%d1
 move.l %d1,(%a5)+
 add.l %d3,(%a0)
 add.l %d4,(%a1)
 .endr
 subq.l #1,%d7
 bne.w .Lpass1
 move.l 40(%sp),%a3
 move.l 44(%sp),%a4
 move.l 48(%sp),%a5
 move.l (%a1),%d5
 move.l (%a0),%d6
 move.l (%a3)+,%d1
 moveq #8,%d0
.Lpass2:
 .rept 4
 mac.l %d6,%d1,(%a4)+,%d1,%acc0
 mac.l %d5,%d1,(%a3)+,%d1,%acc0
 add.l %d3,%d6
 add.l %d4,%d5
 movclr.l %acc0,%d2
 move.l %d2,(%a5)+
 .endr
 subq.l #1,%d0
 bne.w .Lpass2
 move.l -16(%a0),(%a0)
 move.l -16(%a1),%d2
 move.l %a1,%a2
 move.l 72(%sp),%a0
 move.l 68(%sp),%a1
 move.l 4(%a1),%d0
 lea 8(%a0,%d0.l*4),%a1
 move.l %d2,(%a2)
 movem.l (%sp),%d2-%d7/%a2-%a5
 lea 52(%sp),%sp
 rts
.Lfallback:
 jmp tm_native
tm_end:
