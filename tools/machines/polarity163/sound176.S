.text
.globl lp_sound_pack_entry,lp_sound_unpack_entry
/* pack : a2 record, a3 son ; seul d0 libre. Aucun format natif change hors88..91. */
lp_sound_pack_entry:
 lea -16(%sp),%sp
 movem.l %d1-%d2/%a0-%a1,(%sp)
 move.l %a3,-(%sp)
 jsr lp_sound_pack
 addq.l #4,%sp
 tst.l %d0
 beq.s 1f
 move.w 94(%a3),92(%a2)
 move.l %d0,88(%a2)
 movem.l (%sp),%d1-%d2/%a0-%a1
 lea 16(%sp),%sp
 rts
1: movem.l (%sp),%d1-%d2/%a0-%a1
 lea 16(%sp),%sp
 jmp lp_old_sound_pack
/* unpack : a2 son, a3 record ; d0/d1/a1 libres, a0 doit pointer la table native. */
lp_sound_unpack_entry:
 move.l 88(%a3),-(%sp)
 move.l %a2,-(%sp)
 jsr lp_sound_unpack
 addq.l #8,%sp
 tst.l %d0
 beq.s 2f
 lea 0x4010eea8,%a0
 rts
2: jmp lp_old_sound_unpack

.globl lp_sound_init_entry
/* Le reset d'un son audio remet les deux polarites a Bi ; init MIDI inchangee. */
lp_sound_init_entry:
 jsr lp_old_sound_init
 moveq #0,%d0
 move.b 38(%a2),%d0
 cmpi.l #17,%d0
 beq.s 3f
 moveq #-96,%d0
 move.b %d0,79(%a2)
3: rts
