| TEMPO natif en B : présenter sans fermer B, toggle par type, sortie à l’accueil.
| Emplacement : corps devenu inerte de ml_store_save_notice, entrée RTS conservée.
    .section .text.tempo_dispatch,"ax"
    .globl ml_tempo_dispatch
ml_tempo_dispatch:
    moveq #0,%d0
    bset %d2,%d0
    andil #0x6200,%d0             | REC9, SETTINGS13, TEMPO14
    bnew ml_tempo_global
    nop
    nop
    nop

    .text
    .globl ml_tempo_present,ml_tempo_toggle,ml_tempo_bank_guard
ml_tempo_present:
    tstl mlp_obj
    beq .Lnative_present
    moveal %sp@(8),%a0
    moveal %a0@,%a0
    tstl %a0
    beq .Lnative_present
    movel %a0@,%d0
    cmpil #0x40107a20,%d0         | Settings
    beq .Lkeep_bank
    cmpil #0x40107d50,%d0         | Tempo, constructeur stock 0x4003d50e
    bne .Lnative_present
.Lkeep_bank:
    lea %sp@(-8),%sp
    moveml %d2/%a2,%sp@
    moveal %a0,%a2
    movel %a2@(32),%d2
    movel %a2@(28),%d0
    movel %d0,%a2@(32)            | vecteur de groupes temporairement vide
    movel %sp@(20),%sp@-
    movel %sp@(20),%sp@-
    movel %sp@(20),%sp@-
    jsr ml_settings_native
    lea %sp@(12),%sp
    movel %d2,%a2@(32)
    moveml %sp@,%d2/%a2
    lea %sp@(8),%sp
    rts
.Lnative_present:
    jmp ml_settings_native

ml_tempo_toggle:
    tstl mlp_obj
    beq .Lnative_toggle
    moveal %sp@(4),%a0
    lea %a0@(20),%a0
    movel %a0,%d0
    moveal %a0@,%a1
.Lfind:
    cmpal %d0,%a1
    beq .Lopen
    moveal %a1@(8),%a0
    movel %a0@,%d1
    cmpil #0x40107d50,%d1
    beq .Lclose
    moveal %a1@,%a1
    bra .Lfind
.Lclose:
    moveal %a0@,%a1
    moveal %a1@(40),%a1
    movel %a0,%sp@-
    jsr %a1@
    addql #4,%sp
    rts
.Lopen:
    jmp ml_settings_toggle
.Lnative_toggle:
    jmp 0x40077da8

ml_tempo_bank_guard:
    moveal mlp_obj,%a0           | prologue propre déplacé de ml_toggle
    tstl %a0
    beq .Lcontinue
    moveal 0x40fe4178,%a1        | contexte UI ; ViewManager à +64
    tstl %a1
    beq .Lblocked
    moveal %a1@(88),%a1         | dernier nœud de la liste +20 du manager
    tstl %a1
    beq .Lblocked
    cmpal %a1@(8),%a0           | B doit être la vue au sommet
    bne .Lblocked
.Lcontinue:
    jmp ml_tempo_bank_continue
.Lblocked:
    rts
