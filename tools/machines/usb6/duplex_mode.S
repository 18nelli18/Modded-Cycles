| Retour USB stereo pendant l'envoi six pistes : 8 cases RX dans la fin
| inutilisee du pool descripteurs feedback (24 dTD suffisent pour 16 amorces
| plus les 6 d'un bloc). SRAM 0x80009600..0x800097c0, avant le ring TX.
| Appele par wf_usb_atomic, IRQ masquees et caches pousses avant retour.
| L'appel original publie les 15 patches ; le dernier octet choisit 24/32 dTD.
.text
.globl ud_copy
ud_copy:
 movel %d2,%sp@-
 movel %sp@(8),%d2
 movel %d2,%sp@-
 jsr ud_copy_original
 addql #4,%sp
 moveq #31,%d0
 tstl %d2
 beqs 1f
 moveq #23,%d0
1:
 moveb %d0,0x400025c9
 pea 0x400025c0
 jsr ud_cache_push
 addql #4,%sp
 movel %sp@+,%d2
 rts
