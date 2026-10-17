| Note 107 : recurrence sinus identique, compteur et MAC double simplifies.
| ABI : (out, count, state), d0/d1/a0/a1 volatils, a2 preserve.
.text
.globl swarm_recurrence
swarm_recurrence:
    movel %a2,%sp@-
    moveal %sp@(16),%a0
    moveal %sp@(8),%a2
    movel %sp@(12),%d1
    ble .Ldone
.Lsample:
    moveal %a0@(4),%a1
    movel %a0@(12),%d0
    mac.l %d0,%a1,<<,%acc0
    movclr.l %acc0,%d0
    subl %a0@(8),%d0
    sats.l %d0
    movel %a1,%a0@(8)
    movel %d0,%a0@
    movel %d0,%a0@(4)
    movel %d0,%a2@+
    subql #1,%d1
    bne .Lsample
.Ldone:
    moveal %sp@+,%a2
    rts
