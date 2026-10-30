/* ABI registre du popup PPPCCC et boucle LED propre a Supermodel. */
.text
.globl ts_popup,ts_gest,ts_led
ts_popup:
 move.l %d1,-(%sp)
 jsr ts_notice
 addq.l #4,%sp
 rts
ts_gest:
 /* TRACK doit conserver sa release native pour fermer TrackSelectionView.
  * Seule PAGE est consommee par TSK ; aucun latch du modificateur. */
 rts
/* Appele par JSR au site40021f56 : D3=pas, D2=LED, A5=etat.
 * Page*16 est a SP+60. Les non-selectionnes gardent le helper slide existant. */
ts_led:
 lea -20(%sp),%sp
 movem.l %d0-%d1/%a0-%a1/%a5,(%sp)
 move.l 80(%sp),%d0
 add.l %d3,%d0
 move.l %d0,-(%sp)
 jsr ts_led_value
 addq.l #4,%sp
 tst.l %d0
 beq .Lprevious
 movea.l %d0,%a5
 move.l %d3,-(%sp)
 jsr 0x4000608c
 addq.l #4,%sp
 pea 0x404a8cb8
 move.l %a5,-(%sp)
 move.l %d0,-(%sp)
 move.l %d2,-(%sp)
 jsr 0x40005f86
 lea 16(%sp),%sp
 movem.l (%sp),%d0-%d1/%a0-%a1/%a5
 lea 20(%sp),%sp
 rts
.Lprevious:
 movem.l (%sp),%d0-%d1/%a0-%a1/%a5
 lea 20(%sp),%sp
 jmp ts_old_led
