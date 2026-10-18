| Presentation UI : prologue natif deplace, pile et registres inchanges.
    .text
    .globl ld_present_native
ld_present_native:
    lea %sp@(-40),%sp
    moveml %d2-%d4/%a2-%fp,%sp@
    jmp 0x40077016

| MACHINES sous LFO : consommer le geste avant toute allocation du selecteur.
    .globl ld_machines_entry
ld_machines_entry:
    lea %sp@(-16),%sp
    moveml %d0-%d1/%a0-%a1,%sp@
    pea 8
    jsr 0x4007faf4
    addql #4,%sp
    tstl %d0
    bne .Lld_machine_modifier
    moveml %sp@,%d0-%d1/%a0-%a1
    lea %sp@(16),%sp
    movel %d3,%sp@-
    lea 0x400724a0,%a3
    jmp 0x4001c25a
.Lld_machine_modifier:
    moveml %sp@,%d0-%d1/%a0-%a1
    lea %sp@(16),%sp
    jmp 0x4001c2a8

| Prologue du vrai quick assign primaire, trois arguments natifs.
    .globl ld_primary_quick_native,ld_secondary_quick_native
ld_primary_quick_native:
    lea %sp@(-60),%sp
    moveq #11,%d0
    jmp 0x4001eaa8
ld_secondary_quick_native:
    lea %sp@(-12),%sp
    moveml %d2-%d4,%sp@
    moveal ld_api+24,%a0
    jmp %a0@
