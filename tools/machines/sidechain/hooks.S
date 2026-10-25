/* Entree native six voix : C ne change que le pending, ABI/SR preserves.
 * Rejouer le prologue natif dans du_native_voice avant sa continuation. */
.text
.globl du_voice_hook
du_voice_hook:
 lea -20(%sp),%sp
 movem.l %d0-%d1/%a0-%a1,(%sp)
 move.w %sr,%d0
 move.l %d0,16(%sp)
 move.l 32(%sp),-(%sp)
 jsr du_voice_triggers
 addq.l #4,%sp
 move.l 16(%sp),%d0
 move.w %d0,%sr
 movem.l (%sp),%d0-%d1/%a0-%a1
 lea 20(%sp),%sp
 jmp du_native_voice
