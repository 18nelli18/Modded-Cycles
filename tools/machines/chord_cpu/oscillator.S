| Oscillateur derive de Model-TG / TinyGregAudio, MIT (LICENSE-Model-TG).
| Point garde0x400a8906 ; meme pile/ABI et retour0x400a89d4 (note137).
| Conserver interpolation, ordre des MAC, raw, phases et ramps. PM -> natif.
| Les poids constants evitent deux lectures au sample. La phase est bornee
| seulement a la sortie ; son index lit toujours les memes8bits utiles.
.text
.globl chord_fast
chord_fast:
 tstl %d4
 bnew .Lstock
 movel %fp,%d0
 bnew .Lstock
 tstl %sp@(100)
 bnew .Lstock
 tstl %sp@(104)
 bnew .Lstock
 moveal %sp@(68),%a1
 moveal %sp@(72),%a2
 movel %sp@(108),%d4
 movel %sp@(112),%d5
 moveal %sp@(80),%a4
 moveal %sp@(84),%fp
 moveq #16,%d0
 tstl %d5
 bnes .Ltwo_test
 tstl %sp@(120)
 bnes .Ltwo_test
 tstl %sp@(116)
 beqw .Lone_const
 braw .Lone_ramp
.Ltwo_test:
 tstl %sp@(116)
 bnew .Ltwo_ramp
 tstl %sp@(120)
 bnew .Ltwo_ramp
 braw .Ltwo_const

.macro PHASE
 movel %d7,%d2
 swap %d2
 andil #255,%d2
 mvzw %d7,%d6
 lsll #8,%d6
 lsll #7,%d6
.endm
.macro TWO ramp
 PHASE
 movel %a1@(0,%d2:l:4),%d3
 moveal %a1@(4,%d2:l:4),%a5
 movel %d3,%acc0
 macl %d6,%a5,%acc0
 msacl %d6,%d3,%acc0
 movel %a2@(0,%d2:l:4),%d3
 moveal %a2@(4,%d2:l:4),%a5
 movel %d3,%acc2
 macl %d6,%a5,%acc2
 msacl %d6,%d3,%acc2
 movclr.l %acc0,%d6
 macl %d4,%d6,%acc0
 movclr.l %acc2,%d3
 macl %d5,%d3,%acc0
 .if \ramp
 addl %sp@(116),%d4
 addl %sp@(120),%d5
 .endif
 addl %a4,%d7
 movclr.l %acc0,%d6
 msacl %d1,%d6,%acc0
 addl %fp,%d1
 movel %d6,%a3@+
 movclr.l %acc0,%d6
 movel %d6,%a0@+
.endm
.macro ONE ramp
 PHASE
 movel %a1@(0,%d2:l:4),%d3
 moveal %a1@(4,%d2:l:4),%a5
 movel %d3,%acc0
 macl %d6,%a5,%acc0
 msacl %d6,%d3,%acc0
 movclr.l %acc0,%d6
 macl %d4,%d6,%acc0
 .if \ramp
 addl %sp@(116),%d4
 .endif
 addl %a4,%d7
 movclr.l %acc0,%d6
 msacl %d1,%d6,%acc0
 addl %fp,%d1
 movel %d6,%a3@+
 movclr.l %acc0,%d6
 movel %d6,%a0@+
.endm
.Ltwo_const:
 TWO 0
 TWO 0
 subql #1,%d0
 bnew .Ltwo_const
 braw .Ldone
.Ltwo_ramp:
 TWO 1
 TWO 1
 subql #1,%d0
 bnew .Ltwo_ramp
 braw .Ldone
.Lone_const:
 ONE 0
 ONE 0
 subql #1,%d0
 bnew .Lone_const
 braw .Ldone
.Lone_ramp:
 ONE 1
 ONE 1
 subql #1,%d0
 bnew .Lone_ramp
.Ldone:
 movel #0,%acc2
 andil #0xffffff,%d7
 jmp 0x400a89d4
.Lstock:
 moveal #0x8000caa8,%a4
 jmp 0x400a890c
