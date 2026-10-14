/* Entrée KeyboardView 0x4001a0d2 : les huit octets déplacés par ck_ui_key.
 * La vtable reste intacte : Model-TG appelle cette entrée depuis tick_hook,
 * puis exécute son entretien. Le repli saute le détour sans récursion.
 * Même cadre de 44 octets et mêmes registres sauvegardés que le stock.
 */
    .globl ck_ui_key_original
    .section .text.ck_ui_key_original, "ax"
ck_ui_key_original:
    lea -44(%sp), %sp
    movem.l %d2-%d7/%a2-%a6, (%sp)
    jmp 0x4001a0da

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

/* L'interface secondaire PadEvent présente this+16 au dispatch réel.
 * Même ajustement que le thunk stock 0x4001d3d4 ; aucun registre modifié.
 */
    .globl ck_ui_pad_thunk
    .section .text.ck_ui_pad_thunk, "ax"
ck_ui_pad_thunk:
    subq.l #8, 4(%sp)
    subq.l #8, 4(%sp)
    jmp ck_ui_pad

/* Entrée du dispatch PadEvent 0x4007746c. Une vue devenue prioritaire après
 * l'appui ne doit pas voler la fin d'un geste HARMONY. Le helper ne consomme
 * que les releases capturées : les autres événements reprennent le prologue
 * stock exact (8 o), d2/a2/a3 sauvegardés comme à l'origine. L'appel C conserve
 * les registres non volatils ; ce stub protège aussi d0/d1/a0/a1.
 */
    .globl ck_ui_pad_dispatch_hook
    .section .text.ck_ui_pad_dispatch_hook, "ax"
ck_ui_pad_dispatch_hook:
    lea -16(%sp), %sp
    movem.l %d0-%d1/%a0-%a1, (%sp)
    move.l 24(%sp), -(%sp)
    jsr ck_ui_pad_finish
    addq.l #4, %sp
    tst.l %d0
    beq.s 1f
    movem.l (%sp), %d0-%d1/%a0-%a1
    lea 16(%sp), %sp
    moveq #1, %d0
    rts
1:
    movem.l (%sp), %d0-%d1/%a0-%a1
    lea 16(%sp), %sp
    lea -64(%sp), %sp
    movem.l %d2/%a2-%a3, (%sp)
    jmp 0x40077474
