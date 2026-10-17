| Note113 : terminer la vue mute via son close natif avant le menu save.
| ABI key(self,event) : conserver d2/a2/a3 et le resultat du handler precedent.
.text
.globl qs_exit
qs_exit:
 lea %sp@(-16),%sp
 moveml %d2/%a2-%a3,%sp@
 moveal %sp@(20),%a2
 moveal %sp@(24),%a3
 movel %a3,%sp@-
 movel %a2,%sp@-
 jsr 0x40148744
 addql #8,%sp
 movel %d0,%sp@(12)
 movel %a3,%sp@-
 jsr 0x4007240c
 addql #4,%sp
 cmpil #13,%d0
 bne.s .Ldone
 movel %a3@(16),%d0
 andil #34,%d0
 cmpil #34,%d0
 bne.s .Ldone
 movel %a2,%sp@-
 jsr 0x40076126
 addql #4,%sp
.Ldone:
 movel %sp@(12),%d0
 moveml %sp@,%d2/%a2-%a3
 lea %sp@(16),%sp
 rts
