/* Construction du libellé std::string : même ABI que 0x4002cc44.
 * a0 = adresse de retour de la chaîne ; 4(sp) = stockage de std::function,
 * contenant un pointeur vers la fermeture de quatre octets, elle-même le texte.
 * Préserve d2 et le cadre d'appel. Aucun hook sur une entrée stock ici.
 */
    .globl ck_ui_item_label
    .section .text.ck_ui_item_label, "ax"
ck_ui_item_label:
    movea.l 4(%sp), %a1
    movea.l (%a1), %a1
    link.w %fp, #-4
    move.l %d2, -(%sp)
    pea -1(%fp)
    move.l (%a1), -(%sp)
    move.l %a0, %d2
    move.l %a0, -(%sp)
    jsr 0x400f980c
    lea 12(%sp), %sp
    move.l %d2, %d0
    move.l -8(%fp), %d2
    unlk %fp
    rts

/* Le dispatch PadEvent emploie l'interface secondaire à PadsView +16,
 * pointeur virtuel 0x401002b0. Comme le thunk stock 0x4001d3d4, corrige this
 * avant d'appeler le consommateur. Le pointeur principal 0x4010025c est aussi
 * redirigé pour les appels qui possèdent déjà le pointeur complet de la vue.
 */
    .globl ck_ui_pad_thunk
    .section .text.ck_ui_pad_thunk, "ax"
ck_ui_pad_thunk:
    moveq #-16, %d0
    add.l %d0, 4(%sp)
    jmp ck_ui_pad
