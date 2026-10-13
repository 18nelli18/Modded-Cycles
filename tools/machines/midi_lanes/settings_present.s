| SETTINGS stock : conserver B sous le seul ModelSettingsMenu natif.
| Les autres vues et le mode A passent inchangés au prologue natif.
    .text
    .globl ml_settings_present,ml_settings_native
ml_settings_present:
    tstl mlp_obj
    beq ml_settings_native
    moveal %sp@(8),%a0
    moveal %a0@,%a0
    tstl %a0
    beq ml_settings_native
    movel %a0@,%d0
    cmpil #0x40107a20,%d0
    bne ml_settings_native
    lea %sp@(-8),%sp
    moveml %d2/%a2,%sp@
    moveal %a0,%a2
    movel %a2@(32),%d2
    movel %a2@(28),%d0
    movel %d0,%a2@(32)
    movel %sp@(20),%sp@-
    movel %sp@(20),%sp@-
    movel %sp@(20),%sp@-
    jsr ml_settings_native
    lea %sp@(12),%sp
    movel %d2,%a2@(32)
    moveml %sp@,%d2/%a2
    lea %sp@(8),%sp
    rts
ml_settings_native:
    lea %sp@(-40),%sp
    moveml %d2-%d4/%a2-%a6,%sp@
    jmp 0x40077016
