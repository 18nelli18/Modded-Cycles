| IRQ audio uniquement : stubs rares, contrat du frame natif inchange.
| gr_trig remplace seulement les deux clear du vrai chemin trig.
| d0 piste, d2 protection Sampler/capture, a1 base regulateur ; d2 preserve.
.text
.globl gr_trig,gr_record,gr_recover_entry,gr_load
gr_trig:
 tstl %d2
 bne.s 2f
 tstb %a1@(0x46,%d0:l)
 beq.s 2f
 tstb %a1@(0x58,%d0:l)
 bne.s 1f
 tstb %a1@(0x4c,%d0:l)
 beq.s 2f
1:
 moveq #-127,%d1
 moveb %d1,%a1@(0x46,%d0:l)
 bra.s 3f
2:
 clrb %a1@(0x46,%d0:l)
3:
 clrb %a1@(0x58,%d0:l)
 clrb %a1@(0x4c,%d0:l)
 jmp 0x8000e8f8
| Dernier sample apres le vrai fondu ; aucune synthese ou voix ajoutee.
gr_record:
 moveal %sp@(24),%a0
 movel %a0@(124),%d1
 lea gr_last,%a2
 movel %d1,%a2@(0,%d0:l:4)
 moveq #1,%d1
 moveb %d1,%a1@(0x46,%d0:l)
 jmp gr_epilogue
| Le frame natif sauvegarde deja d2-d4/a2 ; le C respecte d2-d7/a2-a6.
gr_recover_entry:
 movel %sp@(24),%sp@-
 movel %d0,%sp@-
 jsr gr_recover
 addql #8,%sp
 jmp gr_epilogue
| Le temps entre appels ne doit pas agrandir le budget 32 samples.
gr_load:
 cmpil #90112,%d2
 bls.s 1f
 movel #90112,%d2
1:
 lsll #8,%d1
 divu.l %d2,%d1
 rts
