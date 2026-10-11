| Prototype LFO 2, note 58. Même ABI que 0x40091ab2 + banque en argument 4.
| Reproduire le prologue natif et ses registres sauvegardés ; l'épilogue natif
| restaure exactement la pile. Aucun état partagé ni instruction réécrite.
    .text
    .globl lf2_update
lf2_update:
    lea.l %sp@(-48),%sp
    movem.l %d2-%d7/%a2-%fp,%sp@
    moveal %sp@(52),%a4
    moveal %sp@(64),%a2
    lea.l %a2@(28),%a3
    jmp 0x40091aca
