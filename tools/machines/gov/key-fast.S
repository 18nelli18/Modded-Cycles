| Classement gouverneur exact : memes arrondis et complements, aucun EMAC.
| ABI : d0 piste conserve ; d2 resultat ; d3/d6/d7/a2-a6 preserves.
| Gains audio IRQ stables : cle nulle sans lire les samples si gain quantifie nul.
.text
.globl kg_key
kg_key:
 move.l %d0,%d4
 lsl.l #2,%d4
 lea GOV_GAINS,%a0
 moveq #0,%d5
.Lgain:
 move.l (%a0)+,%d1
 beq.s .Lgain_done
 movea.l %d1,%a1
 move.l (%a1,%d4.l),%d1
 bpl.s .Lpositive_gain
 neg.l %d1
.Lpositive_gain:
 cmp.l %d5,%d1
 bls.s .Lgain
 move.l %d1,%d5
 bra.s .Lgain
.Lgain_done:
 lsr.l #8,%d5
 lsr.l #8,%d5
 beq.s .Lzero
 move.l %d0,%d4
 lsl.l #7,%d4
 lea 0x80001858,%a0
 adda.l %d4,%a0
 moveq #0,%d2
 moveq #7,%d4
.Lsamples:
 .rept 4
 move.l (%a0)+,%d1
 bpl.s 1f
 not.l %d1
1:
 lsr.l #8,%d1
 add.l %d1,%d2
 .endr
 subq.l #1,%d4
 bpl.s .Lsamples
 lsr.l #8,%d2
 lsr.l #4,%d2
 mulu.l %d5,%d2
 rts
.Lzero:
 moveq #0,%d2
 rts
