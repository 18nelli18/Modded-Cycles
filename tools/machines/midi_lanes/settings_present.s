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
    jmp 0x4007700e

| Le toggle stock ferme les vues sous-jacentes avant present. En B,
| fermer seulement SETTINGS s'il est présent, sinon l'empiler sans replace.
    .globl ml_settings_toggle
ml_settings_toggle:
    tstl mlp_obj
    beq .Lst_native_toggle
    lea %sp@(-12),%sp
    moveml %d2/%a2-%a3,%sp@
    moveal %sp@(16),%a2
    moveal %sp@(20),%a0
    moveal %a0@,%a3
    tstl %a3
    beq .Lst_done
    lea %a2@(20),%a0
    movel %a0,%d2
    moveal %a0@,%a0
.Lst_find:
    cmpal %d2,%a0
    beq .Lst_open
    cmpal %a0@(8),%a3
    beq .Lst_close
    moveal %a0@,%a0
    bra .Lst_find
.Lst_open:
    clrl %sp@-
    movel %sp@(24),%sp@-
    movel %a2,%sp@-
    jsr ml_settings_present
    lea %sp@(12),%sp
    bra .Lst_done
.Lst_close:
    moveal %a3@,%a0
    moveal %a0@(40),%a0
    movel %a3,%sp@-
    jsr %a0@
    addql #4,%sp
.Lst_done:
    moveml %sp@,%d2/%a2-%a3
    lea %sp@(12),%sp
    rts
.Lst_native_toggle:
    jmp 0x40077da8
