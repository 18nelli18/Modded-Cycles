| IRQ audio uniquement ; classification dans les chemins gate deja necessaires.
| Aucun moteur exempte des vrais fondus ; conserver cout, fondu et reprise.
.text
.globl qt_trig,qt_cached_gate,qt_scan_gate
qt_trig:
 move.l 16(%sp),%d1
 lea qt_engines,%a0
 move.l %d1,(%a0,%d0.l*4)
 jmp qt_old_trig
qt_cached_gate:
 move.l 16(%sp),%d1
 lea qt_engines,%a0
 move.l %d1,(%a0,%d0.l*4)
 moveq #5,%d1
 cmp.l 16(%sp),%d1
 bcs.s .Ladded_gate
 clr.b 0x5e(%a1,%d0.l)
 jmp 0x8000e930
.Ladded_gate:
 mvz.b 0x5e(%a1,%d0.l),%d1
 moveq #64,%d2
 jmp 0x8000e924
| Le test O_FREE original reste execute en SRAM avant cette entree.
qt_scan_gate:
 lea qt_engines,%a2
 move.l (%a2,%d0.l*4),%d1
 cmpi.l #5,%d1
 bhi.s .Ladded_scan
 clr.b 0x5e(%a1,%d0.l)
 jmp 0x80007398
.Ladded_scan:
 move.l #8192,%d3
 jmp 0x80007352
.bss
.balign 4
.globl qt_engines
qt_engines: .space 24
