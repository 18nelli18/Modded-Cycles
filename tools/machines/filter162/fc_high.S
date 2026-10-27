| Lowpass deux poles, feedback non lineaire : trois produits au lieu de 4/6.
| API et quatre historiques natifs reutilises ; seul le lowpass est expose.
| MACSR et accumulateurs1..3 preserves ; ACC0 vide en entree/sortie comme l'ancien.
.text
.globl fc_high,fc_high_end
fc_high:
 movel %sp@(8),%d0
 lea 0x401bbd60,%a0
 tstl %a0@(0,%d0:l:4)
 beq .Lreturn
 moveal %sp@(4),%a0
 moveq #31,%d1
.Lquiet_samples:
 tstl %a0@+
 bne .Lactive
 subql #1,%d1
 bpl .Lquiet_samples
 movel %sp@(8),%d0
 lsll #2,%d0
 lea 0x401bbdb4,%a0
 addal %d0,%a0
 moveq #3,%d1
.Lquiet_states:
 movel %a0@,%d0
 bpl .Lquiet_abs
 negl %d0
.Lquiet_abs:
 cmpil #1024,%d0
 bgt .Lactive
 lea %a0@(28),%a0
 subql #1,%d1
 bpl .Lquiet_states
 lea %a0@(-112),%a0
 moveq #3,%d1
.Lquiet_clear:
 clrl %a0@
 lea %a0@(28),%a0
 subql #1,%d1
 bpl .Lquiet_clear
 rts
.Lactive:
 lea %sp@(-44),%sp
 moveml %d2-%d7/%a2-%a5,%sp@
 movel %macsr,%d0
 movel %d0,%sp@(40)
 movel %sp@(52),%sp@-
 jsr fc_coeff
 addql #4,%sp
 moveal %d0,%a0
 movel %a0@(8),%d0
 movel %a0@(12),%d1
 moveal %a0@(16),%a3
 movel #0xa0,%macsr
 movel #0,%acc0
 movel %sp@(52),%d7
 lsll #2,%d7
 lea 0x401bbdb4,%a4
 addal %d7,%a4
 movel %a4@,%d2
 movel %a4@(28),%d3
 movel %a4@(56),%d4
 movel %a4@(84),%d5
 moveal %sp@(48),%a1
 lea %a1@(128),%a2
#ifdef PF_PAIR_OPT
| Deux samples : alterner les roles x1/x2 et y1/y2 supprime les copies
| d historique. Apres chaque paire les roles ABI habituels sont retrouves.
.Lsample:
 movel %d2,%d6
 addl %d6,%d6
 negl %d6
 addl %d3,%d6
 movel %a1@,%d3
 asrl #4,%d3
 addl %d3,%d6
 macl %d0,%d6,%acc0
 msacl %d1,%d4,%acc0
 msacl %a3,%d5,%acc0
 movclr.l %acc0,%d5
 addl %d5,%d5
 cmpil #134213632,%d5
 ble 1f
 movel #134213632,%d5
1:
 cmpil #-134213632,%d5
 bge 2f
 movel #-134213632,%d5
2:
 movel %d5,%d7
 lsll #4,%d7
 movel %d7,%a1@+
 movel %d3,%d6
 addl %d6,%d6
 negl %d6
 addl %d2,%d6
 movel %a1@,%d2
 asrl #4,%d2
 addl %d2,%d6
 macl %d0,%d6,%acc0
 msacl %d1,%d5,%acc0
 msacl %a3,%d4,%acc0
 movclr.l %acc0,%d4
 addl %d4,%d4
 cmpil #134213632,%d4
 ble 1f
 movel #134213632,%d4
1:
 cmpil #-134213632,%d4
 bge 2f
 movel #-134213632,%d4
2:
 movel %d4,%d7
 lsll #4,%d7
 movel %d7,%a1@+
 cmpal %a2,%a1
 bne .Lsample
#else
.Lsample:
 movel %a1@,%d7
 asrl #4,%d7
 movel %d2,%d6
 addl %d6,%d6
 negl %d6
 addl %d3,%d6
 addl %d7,%d6
 macl %d0,%d6,%acc0
 msacl %d1,%d4,%acc0
 msacl %a3,%d5,%acc0
 movclr.l %acc0,%d6
 addl %d6,%d6
 negl %d6
 cmpil #134213632,%d6
 ble .Lhigh
 movel #134213632,%d6
.Lhigh:
 cmpil #-134213632,%d6
 bge .Llow
 movel #-134213632,%d6
.Llow:
 movel %d4,%d5
 movel %d6,%d4
 movel %d2,%d3
 movel %d7,%d2
 lsll #4,%d6
 movel %d6,%a1@+
 cmpal %a2,%a1
 bne .Lsample
#endif
 movel %d2,%a4@
 movel %d3,%a4@(28)
 movel %d4,%a4@(56)
 movel %d5,%a4@(84)
 movel %sp@(40),%d0
 movel %d0,%macsr
 moveml %sp@,%d2-%d7/%a2-%a5
 lea %sp@(44),%sp
.Lreturn:
 rts
fc_high_end:
