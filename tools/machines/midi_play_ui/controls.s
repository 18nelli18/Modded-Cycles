| REC montre les pas B ; le curseur reste indépendant. Un getter UI par frame.
    .text
    .globl mpu_led_begin,mpu_led_state,mpu_pad,mpu_grid
mpu_led_begin:
    movel %d0,%d5
    jsr 0x400cf9a8
    tstl %d0
    beq .Lgrid_none
    movel %d0,%sp@-
    jsr 0x4006b978
    addql #4,%sp
    tstb %d0
    sne %d0
    andil #1,%d0
.Lgrid_none:
    movel %d0,mpu_grid
    movel MLP_TRACK,%d0
    rts
mpu_led_state:
    moveq #1,%d4
    tstl mpu_grid
    bne .Lstate_grid
    | Hors REC : les touches live tenues restent visibles, pas le pattern.
    movel MLP_HELD,%d0
    btst %d2,%d0
    beq .Lstate_done
    moveq #3,%d4
    rts
.Lstate_grid:
    btst #0,%a2@(3)
    bne .Lstate_note
    btst #1,%a2@(3)
    beq .Lstate_done
    movel #260,%d4
    rts
.Lstate_note:
    moveq #3,%d4
    btst #1,%a2@(3)
    beq .Lstate_done
    jsr TG_PHASE
    tstl %d0
    beq .Lstate_done
    moveq #1,%d4
.Lstate_done:
    rts
| Sans TRIG physique : retrouver PadsView natif. Fin des captures HARMONY gardée.
mpu_pad:
    lea %sp@(-8),%sp
    moveml %d2/%a2,%sp@
    moveal %sp@(16),%a2
    movel %a2@(12),%d0
    cmpil #1,%d0
    bne .Lpad_chord
    movel %a2@(20),%d0
    subql #1,%d0
    cmpil #5,%d0
    bhi .Lpad_chord
    lea CK_HELD_PADS,%a0
    tstb %a0@(0,%d0:l)
    bne .Lpad_chord
    moveq #16,%d2
.Lphysical:
    movel %d2,%sp@-
    jsr 0x4007faf4
    addql #4,%sp
    tstl %d0
    bne .Lpad_chord
    addql #1,%d2
    cmpil #32,%d2
    bcs .Lphysical
    moveml %sp@,%d2/%a2
    lea %sp@(8),%sp
    jmp 0x4001d180
.Lpad_chord:
    moveml %sp@,%d2/%a2
    lea %sp@(8),%sp
    jmp CK_PAD
    .data
    .balign 4
mpu_grid: .long 0
