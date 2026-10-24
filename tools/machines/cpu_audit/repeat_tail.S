| Remplace seulement jsr render + addq8 du br_audio filtre ; RTS de bypass intact.
| Pile : now,target,retour br_audio ; le C voit son ABI ordinaire apres JSR.
.text
.globl rr_audio_tail
rr_audio_tail:
 jsr rr_render
 addql #8,%sp
 rts
