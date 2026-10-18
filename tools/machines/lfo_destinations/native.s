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

| Prologue LFOMenuView natif : argument this deja corrige pour le sous-objet.
    .globl ld_lfo_key_native
ld_lfo_key_native:
    subql #4,%sp
    movel %a2,%sp@-
    movel %d2,%sp@-
    jmp 0x40024e12
