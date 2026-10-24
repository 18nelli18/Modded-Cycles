| ACID seulement : +6,02 dB apres le rendu/enveloppe natifs, avant le filtre
| de piste. DRIVE, etat du filtre, slides et fondu de retrig restent intacts.
| ABI render(out[32], voix). Saturation signee : jamais de repliement entier.
.text
.globl acid_gain_render
acid_gain_render:
 lea %sp@(-16),%sp
 moveml %d2/%a2,%sp@
 movel %sp@(20),%a2
 movel %sp@(24),%sp@-
 movel %a2,%sp@-
 jsr acid_render_original
 addql #8,%sp
 movel %d0,%sp@(8)
 moveq #31,%d2
1:
 movel %a2@,%d0
 addl %d0,%d0
 satsl %d0
 movel %d0,%a2@+
 subql #1,%d2
 bpls 1b
 movel %sp@(8),%d0
 moveml %sp@,%d2/%a2
 lea %sp@(16),%sp
 rts
