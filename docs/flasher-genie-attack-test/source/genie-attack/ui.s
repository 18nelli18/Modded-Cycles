| Le panneau lampe original, mêmes rectangles que la version validée.
.section .text.panel,"ax"
.globl avg_panel,avg_render_end,avg_led,avg_open_led
avg_render_end:
 movel %d2,%sp@-
 jsr avg_panel
 addql #4,%sp
 moveml %sp@,%d2-%d5/%a2
 lea %sp@(20),%sp
 rts
 .section .text.open_led,"ax"
avg_open_led:
 lea SG_VT,%a1
 movel #avg_typeinfo,%d0
 movel %d0,%a1@(4)
 movel %d0,%a1@(0x54)
 movel %d0,%a1@(0x68)
 movel %d0,%a1@(0x7c)
 movel %d0,%a1@(0x90)
 movel %d0,%a1@(0xa4)
 movel #SG_PAD,%d0
 rts
.section .text.panel_body,"ax"
avg_panel:
 lea %sp@(-16),%sp
 moveml %d2-%d3/%a2-%a3,%sp@
 moveal %sp@(20),%a3
 clrl %sp@-
 pea 63
 pea 38
 clrl %sp@-
 clrl %sp@-
 movel %a3,%sp@-
 jsr 0x40070dea
 lea %sp@(24),%sp
 lea avg_lamp,%a2
 moveq #19,%d3
1: jsr avg_rect
 lea %a2@(4),%a2
 subql #1,%d3
 bpls 1b
 pea avg_title
 pea SG_FMT
 pea 0x12
 pea 46
 pea 19
 pea 0x40ea14cc
 movel %a3,%sp@-
 jsr 0x40071a04
 lea %sp@(28),%sp
 lea avg_box,%a2
 moveq #3,%d3
2: jsr avg_rect
 lea %a2@(4),%a2
 subql #1,%d3
 bpls 2b
 moveml %sp@,%d2-%d3/%a2-%a3
 lea %sp@(16),%sp
 rts
.section .text.led,"ax"
| Peint seulement les pads pendant FUNC ; les pulses et pas natifs restent propriétaires.
avg_led:
 tstl SG_FUNC
 bne.s avg_led_on
 jmp avg_led_done
avg_led_on:
 lea %sp@(-20),%sp
 moveml %d2-%d4/%a2-%a3,%sp@
 moveal %sp@(32),%a2
 jsr 0x400cfaf4
 moveal %d0,%a3
 jsr 0x400cf866
 movel %d0,%sp@-
 jsr 0x4000eb90
 addql #4,%sp
 moveal %d0,%a0
 movel %a0,%sp@-
 jsr 0x4001260c
 addql #4,%sp
 movel %d0,%d4
 moveq #0,%d2
 jmp avg_led_loop
.section .text.ledloop,"ax"
avg_led_loop:
1: movel %d2,%sp@-
 jsr 0x400060bc
 addql #4,%sp
 movel %d0,%d3
 moveq #1,%d1
 movel %d3,%d0
 andil #31,%d0
 lsll %d0,%d1
 orl %d1,%a2@
 moveq #3,%d0
 btst %d2,%d4
 beqs 2f
 movel #260,%d0
2: pea 0x404a8cb8
 movel %d0,%sp@-
 movel %d3,%sp@-
 movel %a3,%sp@-
 jsr 0x40005f86
 lea %sp@(16),%sp
 addql #1,%d2
 cmpil #6,%d2
 bcss 1b
 moveml %sp@,%d2-%d4/%a2-%a3
 lea %sp@(20),%sp
avg_led_done: moveq #0,%d0
 rts
.section .data.panel,"aw"
avg_title: .asciz "S.G."
.balign 4
avg_box: .byte 2,0,36,63, 0,2,1,61, 37,2,38,61, 1,1,1,1
.section .data.lamp,"aw"
avg_lamp:
.byte 10,22,27,22, 8,23,29,23, 7,24,30,25
.byte 6,26,29,27, 8,28,27,29, 10,30,25,31
.byte 12,32,23,32, 15,33,20,33
.byte 29,27,31,28, 30,29,32,30, 31,31,33,31
.byte 12,20,25,20, 16,21,21,21
.byte 11,33,24,33, 14,34,21,34
.byte 5,27,5,29, 4,29,4,31, 5,32,7,32
.byte 7,31,7,31, 17,37,18,38

.section .text.rect,"ax"
avg_rect:
 pea -1
 moveq #0,%d0
 moveb %a2@(3),%d0
 movel %d0,%sp@-
 moveb %a2@(2),%d0
 movel %d0,%sp@-
 moveb %a2@(1),%d0
 movel %d0,%sp@-
 moveb %a2@,%d0
 movel %d0,%sp@-
 movel %a3,%sp@-
 jsr 0x40070dea
 lea %sp@(24),%sp
 rts

.section .data.typeinfo,"aw"
.balign 4
avg_typeinfo:
.long 0x40123f20,avg_typename,0,2
.long 0x401178f8,2,0x400ff970,0x2f0002
avg_led_vt:
.long -0x2f00,avg_typeinfo,avg_ldtor0,avg_ldtor1,avg_led
.section .data.typename,"aw"
avg_typename: .asciz "13GenieLampView"
.section .text.led_dtor,"ax"
avg_ldtor0:
 movel #-0x2f00,%d0
 addl %d0,%sp@(4)
 jmp SG_DTOR0
avg_ldtor1:
 movel #-0x2f00,%d0
 addl %d0,%sp@(4)
 jmp SG_DTOR1

.section .text.alloc_led,"ax"
.globl avg_alloc_led
avg_alloc_led:
 lea avg_led_vt+8,%a0
 movel %a0,%a4@(0x2f00)
 clrl %a4@(0x2f04)
 clrl %a4@(0x2f08)
 lea %a1@(8),%a0
 movel %a0,%a4@
 rts
