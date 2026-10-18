| Note124 : meme filtre 23 taps, produits signes 16 bits exacts via EMAC entier.
| Entree : a0=x, a1=sortie32, a6=x+128 ; cadre original inchange.
| Les registres de travail sont deja sauves/restaures par macro_render.
| MACSR restaure avant enveloppe/VCA ; ACC0 vide a chaque sortie.
.text
.globl macro_halfband_fast
macro_halfband_fast:
    movel %macsr,%d2
    movel #0,%macsr
    clrl %d0
    movel %d0,%acc0
    movel #0xff3b01b2,%d3
    movel #0xfccc062b,%d4
    movel #0xf3c52857,%d5
    movel #16384,%d6
.Lsample:
    movel %a0@,%d0
    mac.w %d0u,%d3u,%acc0
    movel %a0@(4),%d0
    mac.w %d0u,%d3l,%acc0
    movel %a0@(8),%d0
    mac.w %d0u,%d4u,%acc0
    movel %a0@(12),%d0
    mac.w %d0u,%d4l,%acc0
    movel %a0@(16),%d0
    mac.w %d0u,%d5u,%acc0
    movel %a0@(20),%d0
    mac.w %d0u,%d5l,%acc0
    mac.w %d0l,%d6l,%acc0
    movel %a0@(24),%d0
    mac.w %d0u,%d5l,%acc0
    movel %a0@(28),%d0
    mac.w %d0u,%d5u,%acc0
    movel %a0@(32),%d0
    mac.w %d0u,%d4l,%acc0
    movel %a0@(36),%d0
    mac.w %d0u,%d4u,%acc0
    movel %a0@(40),%d0
    mac.w %d0u,%d3l,%acc0
    movel %a0@(44),%d0
    mac.w %d0u,%d3u,%acc0
    movclr.l %acc0,%d0
    movel %d0,%a1@+
    addql #4,%a0
    cmpal %a6,%a0
    bne.s .Lsample
    movel %d2,%macsr
.if (.-macro_halfband_fast)>162
.error "filtre MACRO plus grand que sa boucle originale"
.endif
.rept (162-(.-macro_halfband_fast))/2
    .word 0x4e71
.endr
