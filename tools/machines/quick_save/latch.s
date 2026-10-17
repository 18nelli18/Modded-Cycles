| Note113 : le save long termine le verrouillage mute derriere son menu.
.text
.globl qs_latch
qs_latch:
 movel %a0@(16),%d1
 lea SET_HELD,%a1
 btst #5,%d1
 beq.s .Lnormal
 lsrl #2,%d1
 bcc.s .Leat
 tstl %a1@(4)
 bne.s .Leat
 clrw 0x401487ec
 rts
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
 tstl %a1@(4)
 bne.s .Leat
 rts
.Leat:
 moveq #0,%d0
 rts
