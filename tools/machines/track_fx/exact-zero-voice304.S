| Veille stock apres64blocs exactement nuls. Aucun seuil audio ni nouvel etat.
| Les fondus de surcharge et O_FREE restent testes avant ces entrees.
.text
.globl zz_gate,zz_scan
zz_gate:
 move.l 16(%sp),%d1
 lea qt_engines,%a0
 cmpi.l #5,%d1
 bhi.s .Lcache_added
 cmp.l (%a0,%d0.l*4),%d1
 beq.s .Lcache_stock
 clr.b 0x5e(%a1,%d0.l)
.Lcache_stock:
 move.l %d1,(%a0,%d0.l*4)
 mvz.b 0x5e(%a1,%d0.l),%d1
 cmpi.l #64,%d1
 bcc.s .Lsleep
 jmp 0x8000e930
.Lsleep:
 | Un bloc nul peut aussi venir d une annulation ou modulation. Exiger
 | l ampli natif termine, pas une attaque/sustain silencieuse temporaire.
 lea zz_voices,%a0
 movea.l (%a0,%d0.l*4),%a0
 tst.l 0x230(%a0)
 bne.s .Lwake_stock
 tst.l 0x234(%a0)
 bne.s .Lwake_stock
 moveq #1,%d1
 cmp.l 0x23c(%a0),%d1
 bne.s .Lwake_stock
 jmp 0x8000e944
.Lwake_stock:
 clr.b 0x5e(%a1,%d0.l)
 jmp 0x8000e930
.Lcache_added:
 move.l %d1,(%a0,%d0.l*4)
.Ladded_gate:
 mvz.b 0x5e(%a1,%d0.l),%d1
 moveq #64,%d2
 jmp 0x8000e924
zz_scan:
 lea qt_engines,%a2
 move.l (%a2,%d0.l*4),%d1
 cmpi.l #5,%d1
 bhi.s .Ladded_scan
 moveq #7,%d4
.Lscan:
 move.l (%a0)+,%d2
 or.l (%a0)+,%d2
 or.l (%a0)+,%d2
 or.l (%a0)+,%d2
 bne.s .Lnonzero
 subq.l #1,%d4
 bpl.s .Lscan
 lea zz_voices,%a0
 movea.l (%a0,%d0.l*4),%a0
 tst.l 0x230(%a0)
 bne.s .Lnonzero
 tst.l 0x234(%a0)
 bne.s .Lnonzero
 moveq #1,%d1
 cmp.l 0x23c(%a0),%d1
 bne.s .Lnonzero
 mvz.b 0x5e(%a1,%d0.l),%d1
 cmpi.l #64,%d1
 bcc.s .Ldone
 addq.l #1,%d1
 move.b %d1,0x5e(%a1,%d0.l)
.Ldone:
 jmp 0x80007398
.Lnonzero:
 clr.b 0x5e(%a1,%d0.l)
 jmp 0x80007398
.Ladded_scan:
 move.l #8192,%d3
 jmp 0x80007352
.balign 4
zz_voices:
 .long 0x42308828,0x42308b44,0x42308e60,0x4230917c,0x42309498,0x423097b4
