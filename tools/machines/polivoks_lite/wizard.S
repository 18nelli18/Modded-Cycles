| Adaptateur ladder_run du Wizard : a1=32 paires, d0=f,d1=q,d4=piste.
| Garde d0-d4/a2-a4, MACSR et ACC0 entier+extensions selon NXP54418RM5.3.1.2.
| Les quatre historiques natifs (stride24) restent echanges par sx_swapf.
| Aucun changement au lecteur PCM, enveloppes, effets ou decimateur.
.text
.globl pw_run,pw_end
pw_run:
 tstl %d0
 beq .Lreturn
 lea %sp@(-48),%sp
 moveml %d0-%d4/%a2-%a4,%sp@
 movel %d4,%sp@(32)
 movel %macsr,%d0
 movel %d0,%sp@(36)
 movel #0,%macsr
 movel %acc0,%d0
 movel %d0,%sp@(40)
 movel %accext01,%d0
 movel %d0,%sp@(44)
 movel %a1,%a2
 movel %d4,%sp@-
 jsr pw_coeff
 addql #4,%sp
 movel %a2,%a1
 moveal %d0,%a0
 movel %a0@(8),%d0
 movel %a0@(12),%d1
 moveal %a0@(16),%a3
 movel #0xa0,%macsr
 movel #0,%acc0
 movel %sp@(32),%d7
 lsll #2,%d7
 lea 0x401bbe8c,%a4
 addal %d7,%a4
 movel %a4@,%d2
 movel %a4@(24),%d3
 movel %a4@(48),%d4
 movel %a4@(72),%d5
 lea %a1@(256),%a2
.Lsample:
 movel %a1@,%d7
 asrl #4,%d7
 movel %d2,%d6
 addl %d6,%d6
 addl %d3,%d6
 addl %d7,%d6
 macl %d0,%d6,%acc0
 msacl %d1,%d4,%acc0
 msacl %a3,%d5,%acc0
 movclr.l %acc0,%d6
 addl %d6,%d6
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
 movel %d6,%a1@+
 cmpal %a2,%a1
 bne .Lsample
 movel %d2,%a4@
 movel %d3,%a4@(24)
 movel %d4,%a4@(48)
 movel %d5,%a4@(72)
 movel #0,%macsr
 movel %sp@(40),%d0
 movel %d0,%acc0
 movel %sp@(44),%d0
 movel %d0,%accext01
 movel %sp@(36),%d0
 movel %d0,%macsr
 moveml %sp@,%d0-%d4/%a2-%a4
 lea %sp@(48),%sp
.Lreturn:
 rts
pw_end:
