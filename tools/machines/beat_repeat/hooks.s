| Note 99 : ABI du getter cle et appel gain natif conserves, chainage configurable.
    .section .text.br_key_hook,"ax"
    .globl br_key_hook
br_key_hook:
    lea %sp@(-16),%sp
    moveml %d1/%a0-%a1,%sp@
    movel %sp@(20),%sp@-
    jsr br_key
    addql #4,%sp
    tstl %d0
    beq .Lkey_pass
    moveal %sp@(20),%a0
    clrl %a0@(12)
    moveml %sp@,%d1/%a0-%a1
    lea %sp@(16),%sp
    moveq #0,%d0
    rts
.Lkey_pass:
    moveml %sp@,%d1/%a0-%a1
    lea %sp@(16),%sp
    moveal br_old_key,%a0
    tstl %a0
    beq .Lkey_native
    jmp %a0@
.Lkey_native:
    moveal %sp@(4),%a0
    movel %a0@(12),%d0
    rts
    .section .text.br_gain_hook,"ax"
    .globl br_gain_hook
br_gain_hook:
    lea %sp@(-16),%sp
    moveml %d0-%d1/%a0-%a1,%sp@
    jsr br_audio
    moveml %sp@,%d0-%d1/%a0-%a1
    lea %sp@(16),%sp
    moveal br_old_gain,%a0
    jmp %a0@
