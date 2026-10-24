/* Resonateur deux poles, meme recurrence, saturation et post-etat SRAM.
 * ABI(out,count,state), place native62octets. Coefficient constant par appel,
 * courant garde dans d0 ; pas de retour SDRAM ni d oscillateur supprime.
 * A1 final reproduit la valeur precedente, y compris pour les appelants natifs. */
.text
.globl st_resonator_fast
st_resonator_fast:
 move.l %a2,-(%sp)
 move.l 16(%sp),%a0
 move.l 8(%sp),%a2
 move.l 12(%sp),%d1
 ble.s .Ldone
 move.l 12(%a0),%a1
 move.l 4(%a0),%d0
.Lsample:
 mac.l %d0,%a1,<<,%acc0
 movclr.l %acc0,%d0
 sub.l 8(%a0),%d0
 sats.l %d0
 move.l 4(%a0),8(%a0)
 move.l %d0,(%a0)
 move.l %d0,4(%a0)
 move.l %d0,(%a2)+
 subq.l #1,%d1
 bne.s .Lsample
 move.l 8(%a0),%a1
.Ldone:
 move.l (%sp)+,%a2
 rts
