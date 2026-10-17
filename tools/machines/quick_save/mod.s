| Note113 : meme etat SETTINGS et meme ABI ; seul FUNC+long inutilise rejoint le natif.
| LSR place dans C le bit teste ; D1/A1 sont volatils comme dans l original.
.text
.globl qs_mod,qs_end
qs_mod:
 movel %a0@(16),%d1
 lea SET_HELD(%pc),%a1
 btst #5,%d1
 beq.s .Lnormal
 lsrl #2,%d1
 bcc.s KH_EAT
 bra.s .Lused
.Lnormal:
 btst #0,%d1
 beq.s .Lup
 lsrl #4,%d1
 bcs.s .Ldown
 clrl %a1@(4)
.Ldown:
 moveq #1,%d1
 movel %d1,%a1@
 rts
.Lup:
 clrl %a1@
.Lused:
 tstl %a1@(4)
 bne.s KH_EAT
 rts
qs_end:
