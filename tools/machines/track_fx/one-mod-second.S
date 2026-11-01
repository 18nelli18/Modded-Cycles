| Un seul modulateur utile : phase, interpolation et gain natifs exacts.
| Frame de112octets deja etabli par400a8204 ; epilogue natif400a8330.
| Seule l entree ignoree exige poids et rampe nuls.
.text
.globl om_osc
om_osc:
 tst.l %d4
 bne.s .Ltry_b
 tst.l 104(%sp)
 bne.s .Ltry_b
 move.l %fp,%d0
 bne.s .La_setup
 tst.l 108(%sp)
 beq.w .Ldry
.La_setup:
 move.l 84(%sp),%a1
 move.l 88(%sp),%d4
 move.l (%a2)+,%d2
 moveq #16,%d0
 bra.w .La
.Ltry_b:
 move.l %fp,%d0
 bne.w .Lold
 tst.l 108(%sp)
 bne.w .Lold
 move.l 84(%sp),%a2
 move.l 88(%sp),%fp
 move.l (%a1)+,%d2
 moveq #16,%d0
 bra.w .Lb
.macro OM_SAMPLE source,weight,phase,gain,ramp
 move.l %d7,%acc1
 mac.l \weight,%d2,%acc1
 add.l \ramp(%sp),\weight
 move.l %acc1,%d2
 swap %d2
 andi.l #255,%d2
 movclr.l %acc1,%d6
 andi.l #65535,%d6
 asl.l %d5,%d6
 move.l (%a5,%d2.l*4),%d3
 move.l 4(%a5,%d2.l*4),%d2
 move.l %d3,%acc0
 mac.l %d6,%d2,%acc0
 msac.l %d6,%d3,%acc0
 add.l \phase,%d7
 andi.l #16777215,%d7
 movclr.l %acc0,%d6
 msac.l %d1,%d6,%acc0
 add.l \gain,%d1
 .if \ramp == 104
 move.l \source,%d2
 .endif
 move.l %d6,(%a3)+
 .if \ramp == 108
 move.l \source,%d2
 .endif
 movclr.l %acc0,%d6
 move.l %d6,(%a0)+
.endm
.La:
 .rept 2
 OM_SAMPLE (%a2)+,%fp,%a1,%d4,108
 .endr
 subq.l #1,%d0
 bne.w .La
 jmp 0x400a8330
.Lb:
 .rept 2
 OM_SAMPLE (%a1)+,%d4,%a2,%fp,104
 .endr
 subq.l #1,%d0
 bne.w .Lb
 jmp 0x400a8330
.Ldry:
 jmp om_dry
.Lold:
 jmp om_native


.globl om_second_end
om_second_end:
