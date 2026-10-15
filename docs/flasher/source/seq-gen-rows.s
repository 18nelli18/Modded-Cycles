| Conversion des 21 lignes du générateur vers les indices historiques.
    .ifdef SG_SEQUENCE_ONLY
    .globl sg_map_row,sg_unmap_row,sg_ui_last
    .section .text.sg_ui_rows,"ax"
sg_ui_last:
    moveq #20,%d0
    rts
| Générer en première ligne ; Annuler reste en dernière ligne.
sg_map_row:
    tstl %d0
    beqs smap_generate
    subql #1,%d0
    cmpil #19,%d0
    bnes smap_done
    addql #2,%d0
smap_done: rts
smap_generate:
    moveq #20,%d0
    rts
sg_unmap_row:
    cmpil #20,%d0
    beqs sunmap_generate
    bgts sunmap_undo
    addql #1,%d0
    rts
sunmap_generate:
    moveq #0,%d0
    rts
sunmap_undo:
    moveq #20,%d0
    rts
    .endif
