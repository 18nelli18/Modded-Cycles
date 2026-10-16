| Filtre continu après Attack ; pas de reset sur le flag de nouvelle voix.
.section .text.filter_pre,"ax"
.globl avfc_pre,avfc_run,avfc_objects
avfc_pre:
 movel %d1,%sp@-
 mvsb %a2@(18),%d1
 jsr FILTER_COEF
 movel %sp@+,%d1
 jmp ATTACK_PRE
.section .text.filter_run,"ax"
avfc_run:
 movel %sp@(8),%sp@-
 movel %sp@(8),%sp@-
 jsr ATTACK_RUN
 addql #8,%sp
 jmp FILTER_RUN
.section .text.filter_objects,"ax"
avfc_objects:
 lea 0x40a71ba0,%a0
 movel #0x400456c8,%d0
 movel %d0,%a0@(32)
 clrl %a0@(44)
 movel %d0,%a0@(132)
 clrl %a0@(144)
 jmp ATTACK_OBJECTS
