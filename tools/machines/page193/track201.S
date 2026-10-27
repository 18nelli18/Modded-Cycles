/* Garde de chaque piste dans les trois boucles natives : notes, compteurs,
 * lookahead. D2 est la piste sauf lookahead (D0). Registres/CCR rejoues. */
.text
.globl pt_note_hook,pt_counter_hook,pt_look_hook
.macro pt_save
 lea -16(%sp),%sp
 movem.l %d0-%d1/%a0-%a1,(%sp)
.endm
.macro pt_restore
 movem.l (%sp),%d0-%d1/%a0-%a1
 lea 16(%sp),%sp
.endm
pt_note_hook:
 pt_save
 move.l %d2,-(%sp)
 jsr wp_track_due
 addq.l #4,%sp
 tst.l %d0
 beq.s 1f
 pt_restore
 movea.l %d3,%a0
 moveq #1,%d5
 addq.l #4,%d3
 jmp 0x40055114
1: pt_restore
 addq.l #4,%d3
 jmp 0x40055270
pt_counter_hook:
 pt_save
 move.l %d2,-(%sp)
 jsr wp_track_due
 addq.l #4,%sp
 tst.l %d0
 beq.s 2f
 pt_restore
 movea.l %d6,%a0
 moveq #1,%d3
 addq.l #4,%d6
 jmp 0x400552ba
2: pt_restore
 addq.l #4,%d6
 jmp 0x4005536a
pt_look_hook:
 pt_save
 move.l %d0,-(%sp)
 jsr wp_track_due
 addq.l #4,%sp
 tst.l %d0
 beq.s 3f
 pt_restore
 move.b (%a0),%d1
 movea.l %a0,%a4
 bmi.s 4f
 jmp 0x400558dc
4: jmp 0x400558b0
3: pt_restore
 addq.l #1,%a0
 jmp 0x400558c8
