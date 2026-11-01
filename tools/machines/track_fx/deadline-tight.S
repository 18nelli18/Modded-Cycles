| Pas de vol sur le seul pic93..99% ; garder1/256 pour le bilan/epilogue.
| La moyenne soutenue et les cas pres de la deadline restent proteges.
| Entree native govern : a1=GB, d2=periode, d4=charge soutenue, d5=pic paire.
| d0/CCR scratch ; tous les callee-save intacts si retour anticipe.
.text
.globl ph_govern
ph_govern:
 cmpi.l #220,%d4
 bcc.s .Lnative
 move.l 0x4673207c,%d0
 cmpi.l #255,%d0
 bcc.s .Lnative
 rts
.Lnative:
 lea -64(%sp),%sp
 movem.l %d2-%d7/%a2-%a5,(%sp)
 jmp 0x8000e79c
