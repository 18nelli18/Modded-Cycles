.section .fcentry,"ax"
.globl fc_turn,fc_draw,fc_frame
fc_turn:
 jmp fc_turn_real
.org 16
fc_draw:
 jmp fc_draw_real
.org 32
fc_frame:
 jmp fc_frame_real

#ifdef FILTER_KEYS202
.org 48
.globl fc_key
fc_key:
 jmp fc_key_real
#endif

#ifdef FILTER_NATIVE_KEYS203
.section .fcentry,"ax"
.org 64
.globl fc_prekey,fc_early_key
fc_prekey:
/* Meme contrat que le wrapper global FX : code0 consomme l'evenement. */
fc_early_key:
 lea -16(%sp),%sp
 movem.l %d1/%a0-%a1,(%sp)
 move.l 20(%sp),-(%sp)
 jsr fc_key_real
 addq.l #4,%sp
 tst.l %d0
 beq.s 1f
 move.l 20(%sp),%a0
 clr.l 12(%a0)
 movem.l (%sp),%d1/%a0-%a1
 lea 16(%sp),%sp
 moveq #0,%d0
 rts
1: movem.l (%sp),%d1/%a0-%a1
 lea 16(%sp),%sp
 jmp fc_previous_early_key
#endif

#ifdef FILTER_DEFAULTS208
.section .fcentry,"ax"
.org 256
.globl fc_reset_track,fc_get_type,fc_set_type
fc_reset_track: jmp fc_reset_track_real
.org 272
fc_get_type: jmp fc_get_type_real
.org 288
fc_set_type: jmp fc_set_type_real
#endif
