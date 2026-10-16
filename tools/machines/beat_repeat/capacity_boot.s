| Copie Wizard depuis le payload commun decompresse, puis init moteurs originale.
    .text
    .globl capacity_stage,capacity_source,capacity_dest,capacity_count,capacity_init
capacity_stage:
    lea %sp@(-12),%sp
    moveml %d0/%a0-%a1,%sp@
    moveal capacity_source(%pc),%a0
    moveal capacity_dest(%pc),%a1
    movel capacity_count(%pc),%d0
copy:
    movel %a0@+,%a1@+
    subql #1,%d0
    bnes copy
    moveml %sp@,%d0/%a0-%a1
    lea %sp@(12),%sp
capacity_init:
    jmp 0xf0010000
    .balign 4
capacity_source: .long 0
capacity_dest: .long 0
capacity_count: .long 0
