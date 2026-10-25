| MACRO : memes23coefficients, chargements paralleles EMAC (sans masque).
| Contrat162octets : a0=x, a1=sortie, a6=x+128 ; d2-d6 disponibles.
| MACSR restaure, ACC0 vide, autres accumulateurs et MASK inchanges.
.text
.globl macro_halfband_parallel
macro_halfband_parallel:
 movel %macsr,%d2
 movel #0,%macsr
 clrl %d0
 movel %d0,%acc0
 movel #0xff3b01b2,%d3
 movel #0xfccc062b,%d4
 movel #0xf3c52857,%d5
 movel #16384,%d6
.Lsample:
 movel %a0@+,%d0
 mac.w %d0u,%d3u,%a0@+,%d0,%acc0
 mac.w %d0u,%d3l,%a0@+,%d0,%acc0
 mac.w %d0u,%d4u,%a0@+,%d0,%acc0
 mac.w %d0u,%d4l,%a0@+,%d0,%acc0
 mac.w %d0u,%d5u,%a0@+,%d0,%acc0
 mac.w %d0l,%d6l,%acc0
 mac.w %d0u,%d5l,%a0@+,%d0,%acc0
 mac.w %d0u,%d5l,%a0@+,%d0,%acc0
 mac.w %d0u,%d5u,%a0@+,%d0,%acc0
 mac.w %d0u,%d4l,%a0@+,%d0,%acc0
 mac.w %d0u,%d4u,%a0@+,%d0,%acc0
 mac.w %d0u,%d3l,%a0@+,%d0,%acc0
 mac.w %d0u,%d3u,%acc0
 movclr.l %acc0,%d0
 movel %d0,%a1@+
 lea -44(%a0),%a0
 cmpal %a6,%a0
 bne.s .Lsample
 movel %d2,%macsr
.if (.-macro_halfband_parallel)>162
.error "noyau MACRO depasse162octets"
.endif
.rept (162-(.-macro_halfband_parallel))/2
 .word 0x4e71
.endr
