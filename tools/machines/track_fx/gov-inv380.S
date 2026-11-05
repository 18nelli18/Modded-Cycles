/* D0 conserve la piste ; seule la cle D2 change pour INV. */
.text
.globl gi_rank
gi_rank:
 move.l gi_mode,%d2
 beq.s .Llod
 subq.l #1,%d2
 beq.s .Ltrk
 moveq #5,%d2
 sub.l %d0,%d2
 rts
.Ltrk:
 move.l %d0,%d2
 rts
.Llod:
 jmp gi_lod
