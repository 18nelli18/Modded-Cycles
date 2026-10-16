| Note 99 : copie propre avant clear BSS, puis chainage du bootstrap existant.
    .text
    .globl br_boot,br_boot_source,br_boot_dest,br_boot_size,br_boot_next,br_boot_call,br_boot_end
br_boot:
    lea %sp@(-12),%sp
    moveml %d0/%a0-%a1,%sp@
    moveal br_boot_source(%pc),%a0
    moveal br_boot_dest(%pc),%a1
    movel br_boot_size(%pc),%d0
.Lcopy:
    moveb %a0@+,%a1@+
    subql #1,%d0
    bne .Lcopy
    moveml %sp@,%d0/%a0-%a1
    lea %sp@(12),%sp
    moveal br_boot_next(%pc),%a0
    tstl %a0
    beq .Lnative
    tstl br_boot_call
    beq .Ljump
    pea 0x40000536
.Ljump:
    jmp %a0@
.Lnative:
    jsr 0x400004b2
    lea 0xfc044000,%a0
    jmp 0x4000053a
    .balign 4
br_boot_source: .long 0
br_boot_dest: .long 0
br_boot_size: .long 0
br_boot_next: .long 0
br_boot_call: .long 0
br_boot_end:
