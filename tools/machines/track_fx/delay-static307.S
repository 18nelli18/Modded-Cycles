| Matrice finale du delay natif. Entree apres preload d5=entree L.
| d0/d1/d2/d3 = deltas ; a0..a3 = gains ; d4=8 groupes de quatre.
| Seul d6 scratch est detruit par le test, puis recharge au premier MAC.
| Rampes : corps original. Stable : memes MAC non nuls, lectures et arrondis.
.text
.globl ds_gate
ds_gate:
 move.l %d0,%d6
 or.l %d1,%d6
 or.l %d2,%d6
 or.l %d3,%d6
 bne.w .Lslow
 move.l %a1,%d6
 bne.s .Lgeneral
 move.l %a2,%d6
 bne.s .Lgeneral
.Ldiagonal:
 .rept 4
 mac.l %a0,%d5,(%a4)+,%d6,%acc0
 mac.l %a3,%d6,(%a5),%d5,%acc1
 mac.l %d7,%d5,4(%a5),%d6,%acc0
 mac.l %d7,%d6,(%a4)+,%d5,%acc1
 movclr.l %acc0,%d6
 move.l %d6,(%a5)+
 movclr.l %acc1,%d6
 move.l %d6,(%a5)+
 .endr
 subq.l #1,%d4
 bne.w .Ldiagonal
 jmp 0x400576fa
.Lgeneral:
 .rept 4
 mac.l %a0,%d5,(%a4)+,%d6,%acc0
 mac.l %a1,%d6,%acc0
 mac.l %a2,%d5,(%a5),%d5,%acc1
 mac.l %d7,%d5,%acc0
 mac.l %a3,%d6,4(%a5),%d6,%acc1
 mac.l %d7,%d6,(%a4)+,%d5,%acc1
 movclr.l %acc0,%d6
 move.l %d6,(%a5)+
 movclr.l %acc1,%d6
 move.l %d6,(%a5)+
 .endr
 subq.l #1,%d4
 bne.w .Lgeneral
 jmp 0x400576fa
.Lslow:
 jmp ds_old
