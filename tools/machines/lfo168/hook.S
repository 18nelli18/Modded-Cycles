#ifdef MX_COUNT_OPTION
.section .mxentry,"ax"
.globl mx_count_entry
mx_count_entry: jmp mx_count_set
#endif
.text
.globl mx_wave
/* Meme entree que lp_hook. Les etats primaires/secondaires restent natifs. */
mx_wave:
 lea -12(%sp),%sp
 movem.l %d1-%d2/%a0,(%sp)
 move.l 56(%sp),%d1
 cmpi.l #6,%d1
 bcc.s 5f
 move.l %d1,%d2
 lsl.l #5,%d2
 move.l mx_extra,%a0
 tst.l %a0
 beq.s 5f
 adda.l %d2,%a0
 cmpa.l %a2,%a0
 beq.s 1f
 move.l mx_extra+4,%a0
 adda.l %d2,%a0
 cmpa.l %a2,%a0
 bne.s 5f
 addq.l #6,%d1
1: lea mx_polarity,%a0
 tst.l (%a0,%d1.l*4)
 beq.s 4f
#ifdef LFO_WAVE_SAFE
 asr.l #1,%d0
 move.l %a6,%d2
 add.l %d2,%d0
#else
 move.l %a6,%d2
 addi.l #32767,%d2
 lsr.l #8,%d2
 lsr.l #7,%d2
 add.l %d2,%d0
 asr.l #1,%d0
#endif
4: movem.l (%sp),%d1-%d2/%a0
 lea 12(%sp),%sp
 mvs.b (%a4),%d2
 moveq #32,%d5
 mvs.w %d2,%d1
 jmp 0x40091ce0
5: movem.l (%sp),%d1-%d2/%a0
 lea 12(%sp),%sp
 jmp lp_hook
