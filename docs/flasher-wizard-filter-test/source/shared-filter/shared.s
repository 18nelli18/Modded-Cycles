| Filtre ladder Wizard partagé ; aucun sampler/FX supplémentaire.
.section .text.avf_pre,"ax"
.globl avf_pre,avf_post,avf_objects,avf_boot
avf_pre:
 movel %d1,%sp@-
 lea VOICE_PTR,%a0
 movel %fp,%a0@(0,%d2:l:4)
 mvsb %a2@(18),%d1
 jsr FILTER_COEF
 movel %sp@+,%d1
 jmp SAMPLER_PRE
.section .text.avf_post,"ax"
avf_post:
 movel %sp@(8),%sp@-
 movel %sp@(8),%sp@-
 jsr 0x40056f58
 addql #8,%sp
 lea %sp@(-8),%sp
 moveml %d2/%a2,%sp@
 moveal %sp@(12),%a2
 moveq #0,%d2
1:
 movel %d2,%sp@-
 movel %a2,%sp@-
 jsr FILTER_RUN
 addql #8,%sp
 lea %a2@(128),%a2
 addql #1,%d2
 cmpil #6,%d2
 bnes 1b
 moveml %sp@,%d2/%a2
 addql #8,%sp
 rts
.section .text.avf_objects,"ax"
avf_objects:
 lea 0x40a71ba0,%a0
 movel #0x400456c8,%d0
 movel %d0,%a0@(32)
 clrl %a0@(44)
 movel %d0,%a0@(132)
 clrl %a0@(144)
 jmp 0x4001e814
.section .text.avf_boot,"ax"
avf_boot:
 moveal 0x4005a2de,%a0
 cmpal #0x4010dce0,%a0
 beqs 2f
 lea %a0@(616),%a0
 lea 0x4010df48,%a1
 moveq #27,%d0
1: movel %a1@+,%a0@+
 subql #1,%d0
 bpls 1b
2: jmp 0x4005a274
| Indices fichier des locks étendus, sans table débordante de 23 entrées.
.section .text.avf_maps,"ax"
.globl avf_lock_save,avf_lock_update,avf_lock_conv
avf_lock_save:
 cmpil #23,%d0
 bcss 1f
 addql #1,%d0
 moveb %d0,%a3@
 subql #1,%d0
 bras 2f
1: moveb %a5@(3,%d4:l),%a3@
2: moveb %d2,%a3@(1)
 rts
avf_lock_update:
 cmpil #23,%d3
 bcss 1f
 moveal %d3,%a4
 addql #1,%a4
 bras 2f
1: moveal %a1@(0,%d3:l:4),%a4
2: moveq #-1,%d0
 rts
.section .text.avf_conv,"ax"
avf_lock_conv:
 moveq #23,%d2
 cmpl %d0,%d2
 bccs 1f
 moveq #33,%d2
 cmpl %d0,%d2
 bcss 2f
 subql #1,%d0
 jmp 0x4005aa50
1: jmp 0x4005aa46
2: jmp 0x4005aa3a
