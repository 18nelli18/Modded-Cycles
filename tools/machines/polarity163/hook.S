.text
.globl lp_hook
/* Entree a91cda : d0 onde bipolaire, a2 etat32octets, sp+44 piste.
 * Ne convertir que la contribution ; l'etat onde/fade reste natif. */
lp_hook:
 lea -12(%sp),%sp
 movem.l %d1-%d2/%a0,(%sp)
 move.l 56(%sp),%d1
 cmpi.l #6,%d1
#ifdef LFO_SOUND_POL
 bcc 4f
#else
 bcc.s 4f
#endif
 move.l %d1,%d2
 lsl.l #5,%d2
 lea 0x40fde838,%a0
 adda.l %d2,%a0
 cmpa.l %a2,%a0
 beq.s 1f
 move.l lp_context,%a0
 tst.l %a0
#ifdef LFO_SOUND_POL
 beq 4f
#else
 beq.s 4f
#endif
 adda.l %d2,%a0
 cmpa.l %a2,%a0
#ifdef LFO_SOUND_POL
 bne 4f
#else
 bne.s 4f
#endif
 lea lp_two,%a0
 bra.s 2f
1: lea lp_one,%a0
2:
#ifdef LFO_SOUND_POL
 moveq #0,%d2
 move.b 51(%a4),%d2
 andi.l #0xfc,%d2
 cmpi.l #0xa0,%d2
 beq .Lframe_tag
 move.l 0x40a78888,%d2
 tst.l %d2
 beq .Llegacy
 move.l %d2,%a0
 move.l %d1,%d2
 mulu.w #100,%d2
 adda.l %d2,%a0
 moveq #0,%d2
 move.b 107(%a0),%d2
 andi.l #0xfc,%d2
 cmpi.l #0xa0,%d2
 bne .Llegacy_reselect
 move.b 107(%a0),%d2
 bra .Ltag_bits
.Lframe_tag:
 move.b 51(%a4),%d2
.Ltag_bits:
 /* L etat choisit le bit, independamment du pointeur UI selectionne. */
 lea 0x40fde838,%a0
 move.l %d1,-(%sp)
 lsl.l #5,%d1
 adda.l %d1,%a0
 move.l (%sp)+,%d1
 cmpa.l %a2,%a0
 beq .Lprimary_bit
 lsr.l #1,%d2
.Lprimary_bit:
 andi.l #1,%d2
 tst.l %d2
 beq 4f
 bra .Lconvert
.Llegacy_reselect:
 lea lp_two,%a0
 lea 0x40fde838,%a0
 move.l %d1,%d2
 lsl.l #5,%d2
 adda.l %d2,%a0
 cmpa.l %a2,%a0
 beq .Lselect_one
 lea lp_two,%a0
 bra .Llegacy
.Lselect_one:
 lea lp_one,%a0
.Llegacy:
#endif
 tst.l (%a0,%d1.l*4)
#ifdef LFO_SOUND_POL
 beq 4f
#else
 beq.s 4f
#endif
.Lconvert:
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
