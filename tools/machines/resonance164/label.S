.text
.globl rs_font
/* Remplace PEA font dans le dessin du premier mot du popup natif.
 * Les arguments precedents sont x,y,flags,texte. Registres scratch ABI.
 * Uniquement Resonance emploie la petite police pour tenir dans64pixels. */
rs_font:
 move.l 16(%sp),%a0
 move.l (%a0),%d0
 cmpi.l #0x5265736f,%d0
 bne.s 1f
 move.l 4(%a0),%d0
 cmpi.l #0x6e616e63,%d0
 bne.s 1f
 move.w 8(%a0),%d0
 andi.l #65535,%d0
 cmpi.l #0x6500,%d0
 bne.s 1f
 move.l (%sp)+,%a1
 pea 0x40ea14cc
 jmp (%a1)
1: move.l (%sp)+,%a1
 pea 0x40ea14d4
 jmp (%a1)
