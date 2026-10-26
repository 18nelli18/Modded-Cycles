.text
.globl lp_hook
/* Entree a91cda : d0 onde bipolaire, a2 etat32octets, sp+44 piste.
 * Ne convertir que la contribution ; l'etat onde/fade reste natif. */
lp_hook:
 lea -12(%sp),%sp
 movem.l %d1-%d2/%a0,(%sp)
 move.l 56(%sp),%d1
 cmpi.l #6,%d1
 bcc.s 4f
 move.l %d1,%d2
 lsl.l #5,%d2
 lea 0x40fde838,%a0
 adda.l %d2,%a0
 cmpa.l %a2,%a0
 beq.s 1f
 move.l lp_context,%a0
 tst.l %a0
 beq.s 4f
 adda.l %d2,%a0
 cmpa.l %a2,%a0
 bne.s 4f
 lea lp_two,%a0
 bra.s 2f
1: lea lp_one,%a0
2: tst.l (%a0,%d1.l*4)
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
