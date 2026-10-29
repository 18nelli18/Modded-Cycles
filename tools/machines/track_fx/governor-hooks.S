.text
.globl gv_fade_entry
| Entree interne de voice_after : son frame de16octets reste sur la pile.
| Rejoindre son scan apres le fondu ; suivi/reprise gr_finish sont conserves.
gv_fade_entry:
 move.l %a0,-(%sp)
 move.l %d0,-(%sp)
 jsr gv_fade
 addq.l #8,%sp
 move.l %sp@(20),%d0
 movea.l %sp@(24),%a0
 lea 0x46732000,%a1
 jmp 0x80007346
