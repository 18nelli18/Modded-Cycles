| Note115 : B possede ses LEDs de pas ; ignorer les pulses curseur A.
| Les pulses B directs passent par mlp_pad_pulse. ABI volatile d0/a0 seule.
.text
.globl cg_guard,cg_obj,cg_end
cg_guard:
 movel %sp@(4),%d0
 moveal cg_obj(%pc),%a0
 tstl %a0@
 beq.s .Lnative
 cmpil #1,%d0
 bcs.s .Lnative
 cmpil #16,%d0
 bls.s .Ldone
 cmpil #48,%d0
 bcs.s .Lnative
 cmpil #53,%d0
 bls.s .Ldone
.Lnative:
 lea 0x4010abf8,%a0
 jmp 0x4008e8ce
.Ldone:
 rts
.balign 4
cg_obj: .long 0
cg_end:
