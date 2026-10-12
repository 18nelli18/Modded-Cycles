| Note 57 : detour UI du gestionnaire, avant le test de vue sale.
| 0x40006a4a : move.l a2,-(sp); move.l d2,-(sp); move.l 12(sp),d2.
| Le service reste actif avec la vue MIDI fermée et sans rafraîchissement LED.
| Aucun appel depuis IRQ : ml_ui_drain garde IPL=0. Avec ML_WORKER,
| il prépare/réveille la tâche dédiée, sans consommer la file dans l'UI.
    .text
    .globl ml_ui_hook
ml_ui_hook:
    lea.l %sp@(-20),%sp
    movem.l %d0-%d1/%a0-%a1,%sp@
    movew %sr,%d0
    movel %d0,%sp@(16)
    jsr ml_ui_drain
    movel %sp@(16),%d0
    movew %d0,%sr
    movem.l %sp@,%d0-%d1/%a0-%a1
    lea.l %sp@(20),%sp
    movel %a2,%sp@-
    movel %d2,%sp@-
    movel %sp@(12),%d2
    jmp 0x40006a52
