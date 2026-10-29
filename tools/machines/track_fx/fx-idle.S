| ABI natifs : caller-save d0/d1/a0/a1 seulement ; a2 reste les parametres.
| Reutiliser le DMA/idle Model-TG existant, sans reentrer les hooks natifs.
.text
.globl idle_voice_begin,idle_delay,idle_reverb,idle_check
idle_voice_begin:
 jsr mf_fx_begin
 jsr idle_present
 jmp 0x401b72c8
idle_delay:
 jmp 0x401b731c
idle_reverb:
 jmp 0x401b739c
idle_check:
 jsr idle_present
 tst.l %d0
 seq %d0
 extb.l %d0
 move.l %d0,0x401b72f8
 jmp 0x401b7336
