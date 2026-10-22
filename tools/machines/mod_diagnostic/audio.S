/* Conserver D1 lu au timer et le retour du regulateur natif.
 * OFF : aucun appel compteur ; ON : observation avant/apres seulement. */
.text
.globl dx_audio_end
dx_audio_end:
 movel 0xfc07000c,%d1
 tstl dx_enabled
 bne.s 1f
 tstl %d1
 jmp 0x8000e6e6
1:
 lea %sp@(-16),%sp
 moveml %d0-%d1/%a0-%a1,%sp@
 movel %d1,%sp@-
 jsr dx_before
 addql #4,%sp
 moveml %sp@,%d0-%d1/%a0-%a1
 lea %sp@(16),%sp
 pea .Lafter
 pea 0x8000e6e6
 rts
.Lafter:
 lea %sp@(-16),%sp
 moveml %d0-%d1/%a0-%a1,%sp@
 jsr dx_after
 moveml %sp@,%d0-%d1/%a0-%a1
 lea %sp@(16),%sp
 rts
