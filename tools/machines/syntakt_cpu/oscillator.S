/* Oscillateur Syntakt a deux entrees PM, notes/137.
 * Contrat : (operateur, voix), stride128, 32samples. Meme interpolation et
 * ordre EMAC, gains/ramps/phases/post-etats ; aucun operateur supprime.
 * Cas PM-B cible ET courant nuls : omet seulement ses produits nuls.
 * Corps resident dans les340octets de la fonction originale ; aucun detour
 * de rendu vers SDRAM. Les entrees appelees restent a la meme adresse.
 */
.text
.globl st_osc_fast
st_osc_fast:
 lea -56(%sp),%sp
 movem.l %d2-%d7/%a2-%a6,12(%sp)
 move.l 60(%sp),%d0
 movea.l 64(%sp),%a4
 lsl.l #7,%d0
 adda.l %d0,%a4
 move.l 0x80(%a4),%d1
 move.l 0x7c(%a4),%d0
 sub.l %d1,%d0
 asr.l #5,%d0
 move.l %d0,(%sp)
 move.l 0x94(%a4),%d4
 move.l 0x8c(%a4),%d0
 sub.l %d4,%d0
 asr.l #5,%d0
 move.l %d0,4(%sp)
 movea.l 0x98(%a4),%a6
 move.l 0x90(%a4),%d0
 sub.l %a6,%d0
 asr.l #5,%d0
 move.l %d0,8(%sp)
 movea.l 0x9c(%a4),%a1
 movea.l 0xa0(%a4),%a2
 movea.l 0xb0(%a4),%a5
 movea.l 0xc8(%a4),%a0
 movea.l 0xcc(%a4),%a3
 move.l 0x6c(%a4),%d7
 moveq #15,%d5
 move.l %d7,%acc1
 move.l %a6,%d0
 or.l 0x90(%a4),%d0
 beq.s .Lno_b
 move.l (%a1)+,%d3
 mac.l %d4,%d3,(%a2)+,%d3,%acc1
 moveq #32,%d0
.Lfull:
 mac.l %a6,%d3,%acc1
 add.l 4(%sp),%d4
 adda.l 8(%sp),%a6
 move.l %acc1,%d2
 swap %d2
 mvz.b %d2,%d2
 movclr.l %acc1,%d6
 mvz.w %d6,%d6
 asl.l %d5,%d6
 move.l (%a5,%d2.l*4),%d3
 move.l 4(%a5,%d2.l*4),%d2
 move.l %d3,%acc0
 mac.l %d6,%d2,%acc0
 msac.l %d6,%d3,%acc0
 add.l 0x78(%a4),%d7
 and.l #0xffffff,%d7
 move.l %d7,%acc1
 movclr.l %acc0,%d6
 msac.l %d1,%d6,(%a1)+,%d3,%acc0
 add.l (%sp),%d1
 move.l %d6,(%a3)+
 mac.l %d4,%d3,(%a2)+,%d3,%acc1
 movclr.l %acc0,%d6
 move.l %d6,(%a0)+
 subq.l #1,%d0
 bne.s .Lfull
 bra.s .Ldone
.Lno_b:
 moveq #32,%d0
.Lonly_a:
 move.l (%a1)+,%d3
 mac.l %d4,%d3,%acc1
 add.l 4(%sp),%d4
 move.l %acc1,%d2
 swap %d2
 mvz.b %d2,%d2
 movclr.l %acc1,%d6
 mvz.w %d6,%d6
 asl.l %d5,%d6
 move.l (%a5,%d2.l*4),%d3
 move.l 4(%a5,%d2.l*4),%d2
 move.l %d3,%acc0
 mac.l %d6,%d2,%acc0
 msac.l %d6,%d3,%acc0
 add.l 0x78(%a4),%d7
 and.l #0xffffff,%d7
 move.l %d7,%acc1
 movclr.l %acc0,%d6
 msac.l %d1,%d6,%acc0
 add.l (%sp),%d1
 move.l %d6,(%a3)+
 movclr.l %acc0,%d6
 move.l %d6,(%a0)+
 subq.l #1,%d0
 bne.s .Lonly_a
.Ldone:
 movclr.l %acc1,%a0
 move.l %d7,0x6c(%a4)
 move.l 0x7c(%a4),%d2
 move.l %d2,0x80(%a4)
 lea 0x94(%a4),%a0
 lea 0x8c(%a4),%a1
 move.l (%a1),(%a0)
 lea 0x98(%a4),%a0
 lea 0x90(%a4),%a1
 move.l (%a1),(%a0)
 movem.l 12(%sp),%d2-%d7/%a2-%a6
 lea 56(%sp),%sp
 rts
.globl st_osc_end
st_osc_end:
