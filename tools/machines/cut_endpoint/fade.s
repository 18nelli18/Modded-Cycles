| Note136 : extinction atteignant exactement zero au dernier sample.
| Entree a2=buffer, d4=gain original, d1=pas256/1024, d3=31.
| Flens natifs8 et2 ; aucun EMAC, d2 preserve.
.text
.globl cf_fade,cf_end
cf_fade:
 movel %d2,%sp@-
 cmpil #256,%d1
 bne 1f
 lsrl #8,%d4
 movel #257,%d1
 bra 2f
1:
 moveq #10,%d2
 lsrl %d2,%d4
 movel #1040,%d1
2:
 subql #1,%d4
 mulul %d1,%d4
3:
 mvsw %a2@,%d0
 mulsl %d4,%d0
 mvzw %a2@(2),%d2
 mulul %d4,%d2
 swap %d2
 andil #65535,%d2
 addl %d2,%d0
 movel %d0,%a2@+
 subl %d1,%d4
 subql #1,%d3
 bpl 3b
 movel %sp@+,%d2
 rts
cf_end:
