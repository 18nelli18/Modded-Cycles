| Note 58 : adaptateur des vtables LFOMenuView (principal / sous-objet +56).
| Un deuxième relâchement LFO sans FUNC ouvre la page secondaire si disponible.
| Le callback UI reçoit this et renvoie 1 si ouvert, 0 sinon (chemin natif).
| Le garde natif +604 protège les gestes LFO+potard. Sans callback : natif exact.
| Aucun pointeur de vtable du firmware n'est encore remplacé par ce prototype.
    .data
    .globl lf2_open_callback
lf2_open_callback:
    .ifdef LF2_INTEGRATED
    .long lf2_launch
    .else
    .long 0
    .endif
    .text
    .globl lf2_key,lf2_key_sub
lf2_key_sub:
    moveq #-56,%d0
    addl %d0,%sp@(4)
    bra lf2_key
lf2_key:
    lea.l %sp@(-12),%sp
    movem.l %d2/%a2-%a3,%sp@
    moveal lf2_open_callback,%a3
    tstl %a3
    beq .Lkey_native
    movew %sr,%d0
    andil #0x0700,%d0
    bne .Lkey_native
    moveal %sp@(16),%a2
    moveal %sp@(20),%a0
    movel %a0@(12),%d0
    cmpil #8,%d0
    bne .Lkey_native
    movel %a0@(16),%d0
    andil #3,%d0
    bne .Lkey_native
    tstb %a2@(604)
    bne .Lkey_native
    movel %a2,%sp@-
    jsr %a3@
    addql #4,%sp
    tstl %d0
    beq .Lkey_native
    moveq #1,%d0
    movem.l %sp@,%d2/%a2-%a3
    lea.l %sp@(12),%sp
    rts
.Lkey_native:
    movem.l %sp@,%d2/%a2-%a3
    lea.l %sp@(12),%sp
    jmp 0x40024e0c
