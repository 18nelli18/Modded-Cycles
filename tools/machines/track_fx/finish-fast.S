| gb_finish(now) : memes statistiques et bornes, d0/d1/a0/a1 seulement.
| La division elapsed/352 est identique a elapsed*256/90112 sous la borne901120.
#include "finish-offsets.inc"
.text
.globl fg_finish
fg_finish:
 lea fg_base,%a0
 tst.l (%a0)
 beq.w .Ldone
 move.l 4(%sp),%d1
 sub.l FG_T0(%a0),%d1
 move.l %d1,FG_TOTAL(%a0)
 move.l FG_BUDGET(%a0),%d0
 beq.s .Lstats
 move.l 4(%sp),%d0
 sub.l FG_BUDGET(%a0),%d0
 cmpi.l #90112,%d0
 bls.s .Ltail
 move.l #90112,%d0
.Ltail:
 move.l %d0,FG_TAIL(%a0)
.Lstats:
 lea fg_dxbase,%a1
 tst.l (%a1)
 beq.w .Lclear
 move.l 0x40a7883c,%d0
 subq.l #1,%d0
 bne.w .Lclear
 move.l FG_PEAK(%a1),%d0
 cmp.l %d0,%d1
 bls.s .Lover
 move.l %d1,FG_PEAK(%a1)
.Lover:
 cmpi.l #90112,%d1
 bls.s .Laverage
 move.l FG_OVER(%a1),%d0
 cmpi.l #9999,%d0
 bcc.s .Laverage
 addq.l #1,%d0
 move.l %d0,FG_OVER(%a1)
.Laverage:
 move.l FG_BLOCKS(%a1),%d0
 cmpi.l #1000000,%d0
 bcc.s .Lclear
 addq.l #1,%d0
 move.l %d0,FG_BLOCKS(%a1)
 cmpi.l #901120,%d1
 bhi.s .Lclamp
 move.l #352,%d0
 divu.l %d0,%d1
 bra.s .Lsum
.Lclamp:
 move.l #2560,%d1
.Lsum:
 move.l FG_SUM(%a1),%d0
 add.l %d1,%d0
 move.l %d0,FG_SUM(%a1)
.Lclear:
 clr.l (%a0)
 clr.l FG_BUDGET(%a0)
 clr.l FG_T0(%a0)
.Ldone:
 rts
