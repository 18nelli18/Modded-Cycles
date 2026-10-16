| Attack partagée sans filtre ni modification des moteurs stock.
.section .text.attack_pre,"ax"
.globl ava_pre,ava_post,ava_run,ava_save,ava_load,ava_boot
ava_pre:
 lea %sp@(-8),%sp
 moveml %d0/%d4,%sp@
 mvsb %a2@(18),%d0
 cmpil #6,%d0
 bne.s 7f
 jmp ava_pre_done
7:
 mvzw %a2@(46),%d0
 lea ATK_KEY,%a0
 cmpl %a0@(0,%d2:l:4),%d0
 bne.s 6f
 jmp ava_pre_trigger
6:
 movel %d0,%a0@(0,%d2:l:4)
 tstl %d0
 beqs 2f
 movel %d0,%d4
 addl %d0,%d0
 addl %d4,%d0
 movel #16777216,%d4
 divul %d0,%d4
 bnes 3f
 moveq #1,%d4
 bras 3f
2: moveq #0,%d4
3: lea ATK_STEP,%a0
 movel %d4,%a0@(0,%d2:l:4)
jmp ava_pre_trigger
.section .text.attack_trigger,"ax"
ava_pre_trigger:
4: tstl %a5@
 beqs 8f
 tstl %a3@
 bnes 8f
 lea ATK_GAIN,%a0
 clrl %a0@(0,%d2:l:4)
ava_pre_done:
8: moveml %sp@,%d0/%d4
 addql #8,%sp
 jmp SAMPLER_PRE
.section .text.attack_post,"ax"
ava_post:
 movel %sp@(8),%sp@-
 movel %sp@(8),%sp@-
 jsr 0x40056f58
 addql #8,%sp
 lea %sp@(-8),%sp
 moveml %d2/%a2,%sp@
 moveal %sp@(12),%a2
 moveq #0,%d2
1: movel %d2,%sp@-
 movel %a2,%sp@-
 jsr ava_run
 addql #8,%sp
 lea %a2@(128),%a2
 addql #1,%d2
 cmpil #6,%d2
 bcss 1b
 moveml %sp@,%d2/%a2
 addql #8,%sp
 rts
.section .text.attack_run,"ax"
ava_run:
 lea %sp@(-16),%sp
 moveml %d2-%d3/%a2-%a3,%sp@
 movel %sp@(24),%d2
 lea TRK_MACH,%a0
 moveq #6,%d0
 cmpl %a0@(0,%d2:l:4),%d0
 beqs 9f
 lea ATK_STEP,%a0
 movel %a0@(0,%d2:l:4),%d3
 beqs 9f
 lea ATK_GAIN,%a3
 movel %a3@(0,%d2:l:4),%d1
 cmpil #16777216,%d1
 bccs 9f
 moveal %sp@(20),%a2
 moveq #31,%d0
 movel %d0,%sp@-
1: movel %a2@,%d0
 asrl #8,%d0
 asrl #8,%d0
 movel %d1,%sp@-
 lsrl #8,%d1
 mulsl %d1,%d0
 movel %d0,%a2@+
 movel %sp@+,%d1
 addl %d3,%d1
 cmpil #16777216,%d1
 bcss 2f
 movel #16777216,%d1
2: subql #1,%sp@
 bpls 1b
 addql #4,%sp
 movel %d1,%a3@(0,%d2:l:4)
9: moveml %sp@,%d2-%d3/%a2-%a3
 lea %sp@(16),%sp
 rts
.section .text.attack_codec,"ax"
ava_save:
 moveal %sp@(4),%a1
 mvzb %a1@(38),%d1
 cmpil #6,%d1
 beqs 1f
 moveal %sp@,%a0
 movew %a1@(66),%d1
 movew %d1,%a0@(76)
 addql #8,%sp
 rts
1: jmp SAVE_FULL
ava_load:
 moveal %sp@,%a1
 mvzb %a1@(38),%d1
 cmpil #6,%d1
 beqs 2f
 moveal %sp@(4),%a0
 movew %a0@(76),%d1
 movew %d1,%a1@(66)
 addql #8,%sp
 rts
2: jmp LOAD_FULL
.section .text.attack_boot,"ax"
ava_boot:
 moveal 0x4005a2de,%a0
 cmpal #0x4010dce0,%a0
 beqs 2f
 lea %a0@(728),%a0
 lea 0x4010dfb8,%a1
 moveq #13,%d0
1: movel %a1@+,%a0@+
 subql #1,%d0
 bpls 1b
2: jmp 0x4005a274
.section .text.attack_objects,"ax"
.globl ava_objects
ava_objects:
 lea 0x40a71c88,%a0
 movel #0x400456c8,%d0
 movel %d0,%a0@
 clrl %a0@(12)
 jmp 0x4001e814
