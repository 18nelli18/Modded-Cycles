| Experience non servie : gain natif d6=0x20000000, quatre MAC == sample exact.
| Point milieu amp native : frame/registers prepares ; d0-d3 volatiles ici.
| La voie generique rejoue exactement les trois instructions deplacees.
.text
.globl audit_amp
 audit_amp:
 movel %a0@(672),%d6
 movel %a0@(676),%d7
 cmpil #0x20000000,%d6
 bne .Lnative
 movel %macsr,%d0
 andil #0x60,%d0
 cmpil #0x20,%d0
 bne .Lnative
 jmp audit_unity
.Lnative:
 jmp 0x400a9718
.section .hot,"ax"
.globl audit_unity,audit_unity_end
audit_unity:
 movel %a3@,%d1
 moveq #32,%d0
.Lunity:
 macl %a2,%d7,%acc1
 movclr.l %acc1,%d2
 macl %d2,%d1,%acc0
 movel %a3@(4),%d1
 addal %d5,%a2
 movclr.l %acc0,%d2
 movel %d2,%a3@+
 subql #1,%d0
 bne .Lunity
 jmp 0x400a9744
audit_unity_end:
