| Conversion des 21 lignes du générateur vers les indices historiques.
    .ifdef SG_SEQUENCE_ONLY
    .globl sg_map_row,sg_unmap_row,sg_ui_last
    .section .text.sg_ui_rows,"ax"
sg_ui_last:
    moveq #20,%d0
    rts
sg_map_row:
    cmpil #19,%d0
    blts smap_done
    addql #1,%d0
smap_done: rts
sg_unmap_row:
    cmpil #20,%d0
    blts sunmap_done
    subql #1,%d0
sunmap_done: rts
    .endif
