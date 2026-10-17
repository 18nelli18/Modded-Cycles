| Note115 : conserver le contrat du tick, puis rejoindre son code precedent.
.text
.globl phase_tick
phase_tick:
 jsr 0x40053330
 lea %sp@(-20),%sp
 moveml %d0-%d1/%a0-%a1,%sp@
 movew %sr,%d0
 movel %d0,%sp@(16)
 jsr phase_join
 movel %sp@(16),%d0
 movew %d0,%sr
 moveml %sp@,%d0-%d1/%a0-%a1
 lea %sp@(20),%sp
 rts
