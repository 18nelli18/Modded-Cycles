| DUB : reutiliser les deux filtres deja presents dans le delay natif.
| Aucun calcul ajoute dans sa boucle par sample. d1 est ecrase avant sa
| premiere lecture native ; d0/CCR et tous autres registres restent valides.
.text
.globl fx_dub_low_hook,fx_dub_high_hook
fx_dub_low_hook:
 move.l cr_mode,%d1
 cmpi.l #9,%d1
 bne.s 1f
 lea fx_dub_low,%a5
 jmp 0x400574c2
1: lea 0x4013ff84,%a5
 jmp 0x400574c2
fx_dub_high_hook:
 move.l cr_mode,%d1
 cmpi.l #9,%d1
 bne.s 2f
 lea fx_dub_high,%a0
 jmp 0x400574dc
2: lea 0x4013fb84,%a0
 jmp 0x400574dc
.section .rodata
.balign 4
#ifdef FX_DUB_DISTINCT
fx_dub_low: .long 0x7b000000
fx_dub_high: .long 0x7d000000
#else
fx_dub_low: .long 0x74000000
fx_dub_high: .long 0x7e000000
#endif
