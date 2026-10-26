.text
.globl bq_snap,bq_advance_scale,bq_advance_key
/* snap_note recoit piste d2 / note d3. Le caller distingue On/Off.
 * Tous les registres sauf d3 sont restaures ; aucun calcul DSP ici. */
bq_snap:
 lea -60(%sp),%sp
 movem.l %d0-%d7/%a0-%a6,(%sp)
 moveq #0,%d1
 move.l 60(%sp),%d0
 cmpi.l #bq_off_return,%d0
 bne.s 1f
 moveq #1,%d1
1: move.l %d1,-(%sp)
 move.l %d3,-(%sp)
 move.l %d2,-(%sp)
 jsr bq_note
 lea 12(%sp),%sp
 move.l %d0,12(%sp)
 movem.l (%sp),%d0-%d7/%a0-%a6
 lea 60(%sp),%sp
 rts
.macro advance name,state,max
\name:
 moveq #0,%d1
 move.b \state,%d1
 add.l %d0,%d1
 tst.l %d1
 bge.s 2f
 moveq #\max,%d1
 bra.s 3f
2: cmpi.l #\max,%d1
 ble.s 3f
 moveq #0,%d1
3: move.b %d1,\state
 lea -16(%sp),%sp
 movem.l %d0-%d1/%a0-%a1,(%sp)
#ifdef BQ_STARTUP_SAFE
 moveq #1,%d1
 move.b %d1,bq_dirty
#endif
 jsr bq_refresh
 movem.l (%sp),%d0-%d1/%a0-%a1
 lea 16(%sp),%sp
 rts
.endm
advance bq_advance_scale,bq_scale,18
advance bq_advance_key,bq_key,11

.globl bq_advance_mode
advance bq_advance_mode,bq_mode,2
