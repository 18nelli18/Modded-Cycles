| Fin du panic explicite : finir les amplis stock, garder le gain precedent
| pour le fondu32samples natif. Aucun parametre de son ou choix machine ecrit.
| La premiere note suivante garde le declenchement natif, quiet gate compris.
.text
.globl panic_stock_begin
panic_stock_begin:
 move.l %d2,-(%sp)
 move.l panic_pending,%d2
 jsr panic_previous
 tst.l %d2
 beq.s .Ldone
 lea 0x42308828,%a0
 moveq #5,%d0
 moveq #1,%d1
.Lvoice:
 clr.l 0x38(%a0)
 move.l (%a0),%d2
 cmpi.l #5,%d2
 bhi.s .Lnext
 clr.l 0x230(%a0)
 move.l %d1,0x23c(%a0)
 | Deuxieme enveloppe native, notamment le bruit de SNARE. Etat4 inactif
 | jusqu au prochain trig ; son gain precedent garde aussi le fondu natif.
 clr.l 0x2a8(%a0)
 moveq #4,%d2
 move.l %d2,0x2b0(%a0)
.Lnext:
 lea 0x31c(%a0),%a0
 subq.l #1,%d0
 bpl.s .Lvoice
 clr.l panic_woken
 moveq #2,%d0
 move.l %d0,panic_started
.Ldone:
 move.l (%sp)+,%d2
 rts
