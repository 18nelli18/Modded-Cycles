| Presentation UI : prologue natif deplace, pile et registres inchanges.
    .text
    .globl ld_present_native
ld_present_native:
    lea %sp@(-40),%sp
    moveml %d2-%d4/%a2-%fp,%sp@
    jmp 0x40077016
