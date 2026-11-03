| Oscillateur derive de Model-TG / TinyGregAudio, MIT (LICENSE-Model-TG).
| Point garde0x400a8906 ; meme pile/ABI et retour0x400a89d4 (note137).
| Conserver interpolation, ordre des MAC, raw, phases et ramps.
| CHORD_SECOND_FAST : poids PM en registres ; sinon PM -> natif.
| Les poids constants evitent deux lectures au sample. La phase est bornee
| seulement a la sortie ; son index lit toujours les memes8bits utiles.
.text
.globl chord_fast
chord_fast:
#ifdef CHORD_ECO_LOOKUP
 moveq #0,%d0
 movel %d0,%acc0
 movel %d0,%acc2
#endif
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
#ifdef CHORD_SECOND_FAST
 moveq #8,%d0
#else
 moveq #16,%d0
#endif
 tstl %d5
 bnes .Ltwo_test
 tstl %sp@(120)
 bnes .Ltwo_test
 tstl %sp@(116)
 beqw .Lone_const
 braw .Lone_ramp
.Ltwo_test:
#ifdef CHORD_SECOND_FAST
 tstl %d4
 bne.s .Lboth_active
 tstl %sp@(116)
 bne.s .Lboth_active
 tstl %sp@(120)
 beqw chord_second_const
 braw chord_second_ramp
.Lboth_active:
#endif
 tstl %sp@(116)
 bnew .Ltwo_ramp
 tstl %sp@(120)
 bnew .Ltwo_ramp
 braw .Ltwo_const

.macro PHASE
 movel %d7,%d2
 swap %d2
 andil #255,%d2
#ifndef CHORD_ECO_LOOKUP
 mvzw %d7,%d6
 lsll #8,%d6
 lsll #7,%d6
#endif
.endm
.macro TWO ramp
 PHASE
#ifdef CHORD_ECO_LOOKUP
 movel %a1@(0,%d2:l:4),%d6
 movel %a2@(0,%d2:l:4),%d3
 macl %d4,%d6,%acc0
 macl %d5,%d3,%acc0
#else
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
#endif
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
#ifdef CHORD_ECO_LOOKUP
 movel %a1@(0,%d2:l:4),%d6
#else
 movel %a1@(0,%d2:l:4),%d3
 moveal %a1@(4,%d2:l:4),%a5
 movel %d3,%acc0
 macl %d6,%a5,%acc0
 msacl %d6,%d3,%acc0
 movclr.l %acc0,%d6
#endif
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
#ifdef CHORD_SECOND_FAST
.macro SECOND ramp
 PHASE
#ifdef CHORD_ECO_LOOKUP
 movel %a2@(0,%d2:l:4),%d6
#else
 movel %a2@(0,%d2:l:4),%d3
 moveal %a2@(4,%d2:l:4),%a5
 movel %d3,%acc0
 macl %d6,%a5,%acc0
 msacl %d6,%d3,%acc0
 movclr.l %acc0,%d6
#endif
 macl %d5,%d6,%acc0
 .if \ramp
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
.globl chord_second_const,chord_second_ramp
chord_second_const:
 .rept 4
 SECOND 0
 .endr
 subql #1,%d0
 bnew chord_second_const
 braw .Ldone
chord_second_ramp:
 .rept 4
 SECOND 1
 .endr
 subql #1,%d0
 bnew chord_second_ramp
 braw .Ldone
#endif
.Ltwo_const:
 TWO 0
 TWO 0
#ifdef CHORD_SECOND_FAST
 TWO 0
 TWO 0
#endif
 subql #1,%d0
 bnew .Ltwo_const
 braw .Ldone
.Ltwo_ramp:
 TWO 1
 TWO 1
#ifdef CHORD_SECOND_FAST
 TWO 1
 TWO 1
#endif
 subql #1,%d0
 bnew .Ltwo_ramp
 braw .Ldone
.Lone_const:
 ONE 0
 ONE 0
#ifdef CHORD_SECOND_FAST
 ONE 0
 ONE 0
#endif
 subql #1,%d0
 bnew .Lone_const
 braw .Ldone
.Lone_ramp:
 ONE 1
 ONE 1
#ifdef CHORD_SECOND_FAST
 ONE 1
 ONE 1
#endif
 subql #1,%d0
 bnew .Lone_ramp
.Ldone:
 movel #0,%acc2
 andil #0xffffff,%d7
 jmp 0x400a89d4
#ifdef CHORD_SECOND_FAST
.macro PM_CONST one=0,ramp=0
 macl %fp,%d3,%acc1
 addl %sp@(100),%d4
 addal %sp@(104),%fp
 movel %acc1,%d2
 swap %d2
 andil #255,%d2
 movclr.l %acc1,%d6
#ifdef CHORD_ECO_LOOKUP
 .if \one == 2
 moveal %sp@(72),%a5
 .else
 moveal %sp@(68),%a5
 .endif
 movel %a5@(0,%d2:l:4),%d6
 .if \one == 0
 moveal %sp@(72),%a5
 movel %a5@(0,%d2:l:4),%d3
 .endif
#else
 mvzw %d6,%d6
 lsll #8,%d6
 lsll #7,%d6
 .if \one == 2
 moveal %sp@(72),%a5
 .else
 moveal %sp@(68),%a5
 .endif
 movel %a5@(0,%d2:l:4),%d3
 moveal %a5@(4,%d2:l:4),%a5
 movel %d3,%acc0
 macl %d6,%a5,%acc0
 .if \one == 0
 msacl %d6,%d3,%sp@(72),%a5,%acc0
 movel %a5@(0,%d2:l:4),%d3
 moveal %a5@(4,%d2:l:4),%a5
 movel %d3,%acc2
 macl %d6,%a5,%acc2
 msacl %d6,%d3,%acc2
 .else
 msacl %d6,%d3,%acc0
 .endif
 movclr.l %acc0,%d6
#endif
 .if \one == 2
 macl %a4,%d6,%acc0
 .else
 macl %d5,%d6,%acc0
 .endif
 .if \one == 0
#ifndef CHORD_ECO_LOOKUP
 movclr.l %acc2,%d3
#endif
 macl %a4,%d3,%acc0
 .endif
 .if \ramp
 addl %sp@(116),%d5
 addal %sp@(120),%a4
 .endif
 addl %sp@(80),%d7
 andil #0xffffff,%d7
 movel %d7,%acc1
 movclr.l %acc0,%d6
 msacl %d1,%d6,%a1@+,%d3,%acc0
 addl %sp@(84),%d1
 movel %d6,%a3@+
 macl %d4,%d3,%a2@+,%d3,%acc1
 movclr.l %acc0,%d6
 movel %d6,%a0@+
.endm
.globl chord_pm_const
chord_pm_const:
 | Reproduire l etat temporaire initial ; publier les poids finaux au retour.
 moveal #0x8000caa8,%a4
 moveq #15,%d5
 movel %d5,%a4@
 moveq #16,%d5
 movel %d5,%a4@(4)
 movel %sp@(68),%d5
 movel %d5,%a4@(8)
 movel %sp@(72),%d5
 movel %d5,%a4@(12)
 movel %sp@(108),%d5
 movel %d5,%a4@(16)
 movel %sp@(112),%d0
 movel %d0,%a4@(20)
 moveal %d0,%a4
 movel %d7,%acc1
 movel %a1@+,%d3
 macl %d4,%d3,%a2@+,%d3,%acc1
 movel %sp@(116),%d0
 orl %sp@(120),%d0
 bnew chord_pm_ramp
 movel %a4,%d0
 beqw chord_pm_first
 tstl %d5
 beqw chord_pm_second
 moveq #8,%d0
.Lpm_loop:
 .rept 4
 PM_CONST 0,0
 .endr
 subql #1,%d0
 bnew .Lpm_loop
 braw .Lpm_finish
.globl chord_pm_first,chord_pm_second,chord_pm_ramp
chord_pm_first:
 moveq #16,%d0
 movel #0,%acc2
.Lpm_first_loop:
 .rept 2
 PM_CONST 1,0
 .endr
 subql #1,%d0
 bnew .Lpm_first_loop
 braw .Lpm_finish
chord_pm_second:
 moveq #16,%d0
 movel #0,%acc2
.Lpm_second_loop:
 .rept 2
 PM_CONST 2,0
 .endr
 subql #1,%d0
 bnew .Lpm_second_loop
 braw .Lpm_finish
chord_pm_ramp:
 moveq #8,%d0
.Lpm_ramp_loop:
 .rept 4
 PM_CONST 0,1
 .endr
 subql #1,%d0
 bnew .Lpm_ramp_loop
.Lpm_finish:
 movel %d5,0x8000cab8
 movel %a4,0x8000cabc
 jmp 0x400a89d4
#endif
.Lstock:
#ifdef CHORD_SECOND_FAST
 braw chord_pm_const
#endif
 moveal #0x8000caa8,%a4
 jmp 0x400a890c
