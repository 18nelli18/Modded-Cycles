.text
.globl li_store_gate
li_store_gate:
 tst.l li_noapply
 bne.s .Lcollected
 mvs.w (%a0),%d1
 add.l %d1,%d0
 bpl.s .Lpositive
 jmp 0x40091d0a
.Lpositive:
 jmp 0x40091d0e
.Lcollected:
 jmp 0x40091d1e
