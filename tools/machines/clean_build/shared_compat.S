| Interfaces partagees conservees sans implementation ChordKeys.
| Retour de l'ancien pont de pad : frame d2-d3/a2-a3 deja reserve.
.section .midi_return,"ax"
.globl rebuild_midi_return
rebuild_midi_return:
 movem.l (%sp),%d2-%d3/%a2-%a3
 lea 16(%sp),%sp
 rts

| Identifiant disque27 -> slot RAM26 : codec de parametre commun.
| Tous les autres identifiants retrouvent le decodeur OS inchange.
.section .parameter_codec,"ax"
.globl rebuild_parameter_codec
rebuild_parameter_codec:
 move.l 4(%sp),%d0
 cmpi.l #6,%d0
 bcc.s 1f
 move.l 8(%sp),%d0
 cmpi.l #27,%d0
 bne.s 1f
 moveq #26,%d0
 rts
1:
 move.l %d2,-(%sp)
 moveq #6,%d2
 move.l 8(%sp),%d1
 jmp 0x4005aa22

.section .banner_off,"ax"
.globl rebuild_banner_off
rebuild_banner_off:
 moveq #0,%d0
 rts
