/* SPDX-License-Identifier: MIT
 * Copyright (c) 2026 Lachlan Fysh
 * Original authored source selected for review. re/tools/coldfire_emu/lfo_owned_lifecycle.S; lines 1-283.
 * Unresolved integration bindings are documented in DEPENDENCIES.json.
 */
/* Boot-retained software owner. SLOT/code addresses are emulator bindings.
 * One calloc owns metadata, routing blocks, native regional owners/entries,
 * config and render state. Routing blocks are NOT full stock parents.
 * Full reload ends lifetime; never free/reallocate under live readers.
 */
.text
.equ SLOT,0x40000304
.equ RUNTIME_SLOT,0x40000300
.equ BASE,0x41680000
.equ CODEC,0x41690000
.equ PUBLISH,0x416a0000
.equ TOTAL,4688
.globl setup,setup_publish,read_begin,read_end,write_begin,write_end
.globl edit_native,save_record,load_record,render_event,extra_store,extra_notifier
setup:
 linkw %a6,#0
 lea %sp@(-40),%sp
 moveml %d2-%d7/%a2-%a5,%sp@
 movel SLOT,%d0
 bne setup_done
 pea TOTAL
 pea 1
 jsr 0x40080238
 addql #8,%sp
 tstl %d0
 beq setup_done
 moveal %d0,%a2
 movel #0x4c464f34,%d0
 movel %d0,%a2@
 moveq #1,%d0
 movel %d0,%a2@(4)
 moveq #0,%d2
setup_select:
 movel %d0,%a2@(16,%d2:l:4)
 addql #1,%d2
 cmpil #6,%d2
 bne setup_select
 movel %a6@(8),%a2@(40)
 /* Copy the real entry vtable and replace only own notifications/store. */
 moveal #0x400fd134,%a0
 lea %a2@(80),%a1
 moveq #24,%d2
setup_vtable:
 movel %a0@+,%a1@+
 subql #1,%d2
 bne setup_vtable
 movel #BASE+(extra_notifier-setup),%d0
 movel %d0,%a2@(80+0x48)
 movel #BASE+(extra_store-setup),%d0
 movel %d0,%a2@(80+0x5c)
 lea %a2@(176),%a3
 lea %a2@(2480+28),%a4
 moveq #0,%d2
setup_instance:
 movel %a3,%a2@(44,%d2:l:4)
 movel %a4,%a2@(56,%d2:l:4)
 moveq #0,%d3
setup_track:
 movel %d3,%d0
 moveq #68,%d1
 mulu.l %d1,%d0
 lea %a3@(96,%d0:l),%a5
 pea 0
 pea 0
 movel %a5,%sp@-
 jsr 0x40014588
 lea %sp@(12),%sp
 movel %d3,%d0
 lsll #3,%d0
 addil #504,%d0
 lea %a3@(0,%d0:l),%a5
 pea 0
 movel %a5,%sp@-
 jsr 0x4000b8bc
 addql #8,%sp
 movel %d3,%d0
 moveq #68,%d1
 mulu.l %d1,%d0
 lea %a3@(96,%d0:l),%a0
 movel %a0,%sp@-
 movel %a5,%sp@-
 jsr 0x4000b8ce
 addql #8,%sp
 movel %d3,%d0
 moveq #68,%d1
 mulu.l %d1,%d0
 lea %a3@(96,%d0:l),%a0
 pea 1
 pea 1
 movel %a4,%sp@-
 movel %a0,%sp@-
 jsr 0x40013d88
 lea %sp@(16),%sp
 lea %a2@(80),%a0
 movel %a0,%a5@
 lea defaults(%pc),%a0
 lea %a4@(22),%a1
 moveq #8,%d0
setup_defaults:
 movew %a0@+,%a1@+
 subql #1,%d0
 bne setup_defaults
 moveb %d3,%a4@(38)
 lea %a4@(100),%a4
 addql #1,%d3
 cmpil #6,%d3
 bne setup_track
 lea %a3@(768),%a3
 lea %a4@(40),%a4
 addql #1,%d2
 cmpil #3,%d2
 bne setup_instance
 lea %a2@(4400),%a0
 movel %a0,RUNTIME_SLOT
setup_publish:
 movel %a2,SLOT
 movel %a2,%d0
setup_done:
 moveml %sp@,%d2-%d7/%a2-%a5
 lea %sp@(40),%sp
 unlk %a6
 rts
/* Nonblocking single-core exclusion. Only test/store gate has IPL7;
 * caller IPL is restored before allocation, editing, codec or rendering.
 * Known protocol users only: UI draw/native outer readers remain unjoined.
 */
read_begin:
 moveq #76,%d0
 bra begin
write_begin:
 moveq #72,%d0
begin:
 movel %d2,%sp@-
 moveal SLOT,%a0
 tstl %a0
 beq begin_fail_unmasked
 movew %sr,%d1
 movel %d1,%d2
 oril #0x700,%d2
 movew %d2,%sr
 tstl %a0@(72)
 bne begin_fail
 tstl %a0@(76)
 bne begin_fail
 moveq #1,%d2
 movel %d2,%a0@(0,%d0:l)
 movew %d1,%sr
 moveq #1,%d0
 bra begin_done
begin_fail:
 movew %d1,%sr
begin_fail_unmasked:
 moveq #0,%d0
begin_done:
 movel %sp@+,%d2
 rts
read_end:
 moveal SLOT,%a0
 clrl %a0@(76)
 rts
write_end:
 moveal SLOT,%a0
 clrl %a0@(72)
 rts
/* Already-converted native field write, not a physical UI ingress. */
edit_native:
 linkw %a6,#0
 lea %sp@(-16),%sp
 moveml %d2-%d3/%a2-%a3,%sp@
 bsr write_begin
 tstl %d0
 beq edit_done
 moveal SLOT,%a2
 movel %a6@(8),%d2
 cmpil #6,%d2
 bcc edit_fail
 movel %a6@(12),%d3
 subql #2,%d3
 cmpil #2,%d3
 bhi edit_fail
 movel %a6@(16),%d0
 subil #29,%d0
 cmpil #7,%d0
 bhi edit_fail
 movel %a6@(20),%d0
 cmpil #0x7f00,%d0
 bhi edit_fail
 moveal %a2@(44,%d3:l:4),%a3
 movel %d2,%d0
 lsll #3,%d0
 addil #504,%d0
 lea %a3@(0,%d0:l),%a3
 pea 0
 pea 0
 pea 0
 pea 0
 pea 0
 movel %d2,%sp@-
 movel %a6@(20),%sp@-
 movel %a6@(16),%sp@-
 movel %a3,%sp@-
 jsr 0x4000b274
 lea %sp@(36),%sp
 /* The native setter returns the resulting word. Report exact acceptance,
  * including idempotent writes, rather than success after a rejected/clamp. */
 cmpl %a6@(20),%d0
 seq %d2
 andil #1,%d2
 bra edit_release
edit_fail:
 moveq #0,%d2
edit_release:
 bsr write_end
 movel %d2,%d0
edit_done:
 moveml %sp@,%d2-%d3/%a2-%a3
 lea %sp@(16),%sp
 unlk %a6
 rts
save_record:
 movel #CODEC,%d0
 bra codec_call
load_record:
 movel #CODEC+LOAD_OFFSET,%d0
codec_call:
 linkw %a6,#0
 lea %sp@(-8),%sp
 moveml %d2/%a2,%sp@
 movel %d0,%d2
 bsr write_begin
 tstl %d0
 beq codec_done
 moveal %d2,%a2
 movel %a6@(12),%sp@-
 movel %a6@(8),%sp@-
 movel SLOT,%sp@-
 jsr %a2@
 lea %sp@(12),%sp
 movel %d0,%d2
 bsr write_end
 movel %d2,%d0
codec_done:
 moveml %sp@,%d2/%a2
 lea %sp@(8),%sp
 unlk %a6
 rts
render_event:
 lea %sp@(-64),%sp
 moveml %d0-%d7/%a0-%a6,%sp@
 bsr read_begin
 tstl %d0
 beq render_bypass
 jsr PUBLISH
 moveml %sp@,%d0-%d7/%a0-%a6
 lea %sp@(64),%sp
 movel %sp@(8),%sp@-
 movel %sp@(8),%sp@-
 jsr 0x40000000
 addql #8,%sp
 lea %sp@(-64),%sp
 moveml %d0-%d7/%a0-%a6,%sp@
 movew %sr,%d2
 movew %d2,%sp@(60)
 bsr read_end
 movew %sp@(60),%d2
 movew %d2,%sr
 moveml %sp@,%d0-%d7/%a0-%a6
 lea %sp@(64),%sp
 rts
render_bypass:
 moveml %sp@,%d0-%d7/%a0-%a6
 lea %sp@(64),%sp
 jmp 0x40056e24
extra_store:
 movel %a0,%sp@-
 moveal SLOT,%a0
 addql #1,%a0@(68)
 movel %sp@+,%a0
 clrl %sp@(20)
 jmp 0x4000ba7a
extra_notifier:
 moveq #0,%d0
 rts
