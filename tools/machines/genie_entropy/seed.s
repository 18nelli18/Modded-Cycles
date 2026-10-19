| Note132 : graine initiale variable au premier tirage valide, aucune IRQ ajoutee.
.text
.globl ge_seed,ge_initialized,ge_resume,ge_end
ge_seed:
 movel %a2@(24),%d7
 tstl ge_initialized
 bne 1f
 movel 0xfc07000c,%d0
 eorl %d0,%d7
 moveq #1,%d0
 movel %d0,ge_initialized
1:
 tstl %d7
 bne 2f
 movel #0x6d2b79f5,%d7
2:
 movel ge_resume,-(%sp)
 rts
.balign 4
ge_initialized: .long 0
ge_resume: .long 0
ge_end:
