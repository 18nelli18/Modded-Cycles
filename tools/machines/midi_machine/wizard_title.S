/* Ecran MACHINES : deux lignes natives pour Sample Wizard.
 * Entree 400a2612 : d3=machine, d2=Bitmap*, a2=vue (police a +108).
 * Le masque de l'icone gauche effacerait la premiere ligne : seule la droite
 * est dessinee pour cette machine. Pile rendue a l'etat natif en 400a2680.
 * Les autres machines rejouent exactement le LEA deplace.
 */
 .text
 .globl mx_wizard_selection
mx_wizard_selection:
 cmpi.l #6, %d3
 beq.s 1f
 lea 0x46789000, %a1
 jmp 0x400a2618
1:
 pea mx_wizard_sample
 pea 0x40124b58
 pea 2
 pea 47
 pea 32
 move.l 108(%a2), -(%sp)
 move.l %d2, -(%sp)
 jsr 0x40071a04
 lea 28(%sp), %sp
 pea mx_wizard_word
 pea 0x40124b58
 pea 2
 pea 31
 pea 32
 move.l 108(%a2), -(%sp)
 move.l %d2, -(%sp)
 jsr 0x40071a04
 lea 28(%sp), %sp
 pea 1
 pea 34
 pea 96
 move.l 0x40fe384c, %d0
 addi.l #168, %d0
 move.l %d0, -(%sp)
 move.l %d2, -(%sp)
 jsr 0x40071da4
 lea 20(%sp), %sp
 jmp 0x400a2680
 .globl mx_wizard_title
mx_wizard_title:
 .asciz "Sample Wizard"
mx_wizard_sample:
 .asciz "Sample"
mx_wizard_word:
 .asciz "Wizard"
 .balign 4
