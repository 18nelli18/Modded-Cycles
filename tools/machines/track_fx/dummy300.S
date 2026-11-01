| Dummy28 : sortie nulle avant toute initialisation/update/render de voix.
| Point7d96 : d2 piste, d3 sortie, a2 parametres, fp voix, a4 voix+4.
| Le pointeur de note sp+44 doit avancer comme dans le chemin natif.
| Le reste des pistes garde exactement le trampoline deplace.
.text
.globl dy_voice,dy_names,dy_left,dy_right,dy_increment,dy_marks,dy_amp_gate,dy_lfo_gate,dy_shown
dy_voice:
 moveq #0,%d0
 move.b 18(%a2),%d0
 cmpi.l #28,%d0
 beq.w .Ldummy
 move.l %d5,%d0
 asr.l %d2,%d0
 moveq #1,%d1
 jmp 0x400a7d9c
.Ldummy:
 move.l %d3,%a0
 .rept 32
 clr.l (%a0)+
 .endr
 moveq #28,%d0
 move.l %d0,(%fp)
 move.l %d0,(%a4)
 lea dy_gov_quiet,%a0
 moveq #-1,%d1
 move.b %d1,(%a0,%d2.l)
 lea dy_gov_cost,%a0
 clr.l (%a0,%d2.l*4)
 lea dy_gov_peak,%a0
 clr.l (%a0,%d2.l*4)
 lea 0x4673204c,%a0
 clr.b (%a0,%d2.l)
 lea 0x46732058,%a0
 clr.b (%a0,%d2.l)
 lea 0x46732046,%a0
 clr.b (%a0,%d2.l)
 lea dy_qt_engines,%a0
 move.l %d0,(%a0,%d2.l*4)
 movea.l dy_side_on,%a0
 move.l %a0,%d1
 beq.s 1f
 clr.l (%a0,%d2.l*4)
1:
 lea 0x401bbdb4,%a0
 clr.l (%a0,%d2.l*4)
 lea 28(%a0),%a0
 clr.l (%a0,%d2.l*4)
 lea 28(%a0),%a0
 clr.l (%a0,%d2.l*4)
 lea 28(%a0),%a0
 clr.l (%a0,%d2.l*4)
 addq.l #4,44(%sp)
 jmp 0x400a7e38

dy_names:
 cmpi.l #28,%d3
 bne.s 1f
 pea dy_name
 jmp 0x400a261c
1: jmp dy_fallback_names

dy_left:
 cmpi.l #28,%d3
 bne.s 1f
 lea dy_stats_bitmap,%a1
 suba.l %d4,%a1
 jmp 0x4678812a
1: jmp dy_fallback_left

dy_right:
 cmpi.l #28,%d3
 bne.s 1f
 move.l #dy_icon_bitmap,%d4
 jmp 0x46788144
1: jmp dy_fallback_right

dy_shown:
 cmpi.l #28,%d0
 bne.s 1f
 moveq #0,%d0
 rts
1: jmp dy_fallback_shown

dy_amp_gate:
 cmpi.l #28,%d2
 bne.s 1f
 moveq #0,%d2
1: jmp dy_fallback_amp_gate

dy_lfo_gate:
 cmpi.l #28,%d2
 bne.s 1f
 moveq #0,%d2
1: jmp dy_fallback_lfo_gate

dy_increment:
 lea -8(%sp),%sp
 movem.l %a0-%a1,(%sp)
 move.l %d5,-(%sp)
 move.l %d0,-(%sp)
 jsr mb_step
 addq.l #8,%sp
 movem.l (%sp),%a0-%a1
 lea 8(%sp),%sp
 moveq #-1,%d1
 jmp 0x400148bc

dy_marks:
 move.l %d3,-(%sp)
 move.l %d2,-(%sp)
 jsr dy_draw_marks
 addq.l #8,%sp
 jmp 0x400a26f2

.globl dy_display_hook
dy_display_hook:
 lea -16(%sp),%sp
 movem.l %d0-%d1/%a0-%a1,(%sp)
 move.l %a2,-(%sp)
 move.l %d3,-(%sp)
 jsr mb_display_machine
 addq.l #8,%sp
 move.l %d0,%d3
 movem.l (%sp),%d0-%d1/%a0-%a1
 lea 16(%sp),%sp
 moveq #28,%d0
 lea 0x40071a04,%a0
 jmp 0x400a25e8
