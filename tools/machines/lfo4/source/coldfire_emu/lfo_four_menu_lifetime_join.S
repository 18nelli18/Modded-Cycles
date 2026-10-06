/* SPDX-License-Identifier: MIT
 * Copyright (c) 2026 Lachlan Fysh
 * Original authored source selected for review. re/tools/coldfire_emu/lfo_four_menu_lifetime_join.S; lines 1-346.
 * Unresolved integration bindings are documented in DEPENDENCIES.json.
 */
/* Retained single-owner, nonconcurrent menu construction. Fixture registry
 * is initialized once and never recycled. No free/replacement/ABA contract.
 * Bindings come from supplied core/UI/reader symbol maps, not function offsets.
 */
.text
.equ SLOT,0x40000304
.globl lookup,admit,release,normal_ctor,setup_ctor,install
.globl edit_wave,edit_mul,edit_dst,edit_depth,action_rst,edit_fade,edit_phase,selector_edit
.globl draw_wave,draw_mul,draw_dst,draw_depth,draw_reset,draw_fade,draw_phase,draw_selector
.globl callback_call,callback_release,callback_reject,admit_claim,admit_done
/* lookup(item): captured owner or NULL. Exactly eight immutable records. */
lookup:
 moveal #REGISTRY,%a0
 moveq #8,%d1
 moveq #0,%d0
lookup_next:
 movel %a0@,%d0
 cmpl %sp@(4),%d0
 beq lookup_found
 lea %a0@(12),%a0
 subql #1,%d1
 bne lookup_next
 moveq #0,%d0
 rts
lookup_found:
 movel %a0@(8),%d0
 rts
/* admit(expected,gate): -1 or expected with exclusive gate72/76 held.
 * Identity and nonNULL precede every owner dereference. Finite geometry and
 * busy checks occur at IPL7; original caller IPL is restored before work.
 */
admit:
 movel %d2,%sp@-
 movew %sr,%d2
 moveq #-1,%d0
 moveal %sp@(8),%a0
 tstl %a0
 beq admit_done
 movel %d2,%d1
 oril #0x700,%d1
 movew %d1,%sr
 cmpal SLOT,%a0
 bne admit_done
 movel %a0,%d1
 andil #3,%d1
 bne admit_done
 movel %a0@,%d1
 cmpil #0x4c464f34,%d1
 bne admit_done
 movel %a0@(4),%d1
 cmpil #1,%d1
 bne admit_done
.if BINDING_OFFSET
 cmpal %a0@(BINDING_OFFSET),%a0
 bne admit_done
.endif
.if INITIALIZED_OFFSET
 movel %a0@(INITIALIZED_OFFSET),%d1
 cmpil #0x524e4731,%d1
 bne admit_done
.endif
.if QUARANTINE_OFFSET
 tstl %a0@(QUARANTINE_OFFSET)
 bne admit_done
.endif
 tstl %a0@(72)
 bne admit_done
 tstl %a0@(76)
 bne admit_done
 lea %a0@(4400),%a1
 cmpal SLOT-4,%a1
 bne admit_done
 movel %a0@(40),%d1
 cmpil #STOCK_OWNER,%d1
 bne admit_done
 lea %a0@(176),%a1
 cmpal %a0@(44),%a1
 bne admit_done
 lea %a1@(768),%a1
 cmpal %a0@(48),%a1
 bne admit_done
 lea %a1@(768),%a1
 cmpal %a0@(52),%a1
 bne admit_done
 lea %a0@(2508),%a1
 cmpal %a0@(56),%a1
 bne admit_done
 lea %a1@(640),%a1
 cmpal %a0@(60),%a1
 bne admit_done
 lea %a1@(640),%a1
 cmpal %a0@(64),%a1
 bne admit_done
 lea %a0@(16),%a1
 moveq #6,%d0
admit_selection:
 movel %a1@+,%d1
 subql #1,%d1
 cmpil #3,%d1
 bhi admit_bad
 subql #1,%d0
 bne admit_selection
 movel %sp@(12),%d1
 cmpil #72,%d1
 beq admit_claim
 cmpil #76,%d1
 bne admit_bad
admit_claim:
 moveq #1,%d0
 movel %d0,%a0@(0,%d1:l)
 movel %a0,%d0
 bra admit_done
admit_bad:
 moveq #-1,%d0
admit_done:
 movew %d2,%sr
 movel %sp@+,%d2
 rts
/* release(expected,gate): captured identity, never another owner's lease. */
release:
 movel %d2,%sp@-
 movew %sr,%d2
 moveq #0,%d0
 moveal %sp@(8),%a0
 tstl %a0
 beq release_done
 movel %d2,%d1
 oril #0x700,%d1
 movew %d1,%sr
 cmpal SLOT,%a0
 bne release_done
 movel %sp@(12),%d1
 cmpil #72,%d1
 beq release_gate
 cmpil #76,%d1
 bne release_done
release_gate:
 movel %a0@(0,%d1:l),%d0
 cmpil #1,%d0
 bne release_bad
 clrl %a0@(0,%d1:l)
 bra release_done
release_bad:
 moveq #0,%d0
release_done:
 movew %d2,%sr
 movel %sp@+,%d2
 rts
.macro callback name,target,gate,count
\name:
 movel #\target,%d0
 moveq #\gate,%d1
 moveal #\count,%a0
 bra callback_enter
.endm
callback edit_wave,EDIT_WAVE,72,3
callback edit_mul,EDIT_MUL,72,3
callback edit_dst,EDIT_DST,72,3
callback edit_depth,EDIT_DEPTH,72,3
callback action_rst,ACTION_RST,72,2
callback edit_fade,EDIT_FADE,72,3
callback edit_phase,EDIT_PHASE,72,3
callback selector_edit,SELECTOR_EDIT,72,3
callback draw_wave,0x40025d28,76,5
callback draw_mul,0x400263e8,76,5
callback draw_dst,0x400264a2,76,5
callback draw_depth,0x40026562,76,5
callback draw_reset,0x40026f20,76,5
callback draw_fade,0x40027076,76,5
callback draw_phase,0x40027124,76,5
callback draw_selector,SELECTOR_DRAW,76,5
callback_enter:
 linkw %a6,#-12
 lea %sp@(-8),%sp
 moveml %a2-%a3,%sp@
 moveal %d0,%a3
 movel %d1,%a6@(-4)
 movel %a0,%a6@(-8)
 movel %a6@(12),%sp@-
 bsr lookup
 addql #4,%sp
 movel %a6@(-4),%sp@-
 movel %d0,%sp@-
 bsr admit
 addql #8,%sp
 cmpil #-1,%d0
 beq callback_reject
 moveal %d0,%a2
 /* Forward precisely 2, 3 or 5 original closure arguments. */
 movel %a6@(-8),%d1
 moveal %a6,%a0
 lsll #2,%d1
 lea %a0@(4,%d1:l),%a0
 movel %a6@(-8),%d1
callback_push:
 movel %a0@,%sp@-
 subql #4,%a0
 subql #1,%d1
 bne callback_push
callback_call:
 jsr %a3@
 movel %a6@(-8),%d1
 lsll #2,%d1
 addal %d1,%sp
 movel %d0,%a6@(-12)
 movel %a6@(-4),%sp@-
 movel %a2,%sp@-
callback_release:
 bsr release
 addql #8,%sp
 movel %a6@(-12),%d0
callback_reject:
 moveml %sp@,%a2-%a3
 addql #8,%sp
 unlk %a6
 rts
normal_ctor:
 moveal SLOT,%a0
 tstl %a0
 bne normal_owned
 jmp 0x40025798
normal_owned:
 movel #READER_NORMAL,%d0
 moveal #REGISTRY,%a1
 lea normal_table(%pc),%a0
 bra ctor_enter
setup_ctor:
 moveal SLOT,%a0
 tstl %a0
 bne setup_owned
 jmp 0x40026b4c
setup_owned:
 movel #READER_SETUP,%d0
 moveal #REGISTRY+48,%a1
 lea setup_table(%pc),%a0
ctor_enter:
 linkw %a6,#-8
 lea %sp@(-12),%sp
 moveml %a2-%a4,%sp@
 moveal %d0,%a4
 moveal %a1,%a3
 movel %a0,%a6@(-8)
 tstl %a3@
 bne ctor_bad
 pea 72
 movel SLOT,%sp@-
 bsr admit
 addql #8,%sp
 cmpil #-1,%d0
 beq ctor_bad
 moveal %d0,%a2
 movel %a6@(8),%sp@-
 jsr %a4@
 addql #4,%sp
 movel %d0,%a6@(-4)
 movel %a2,%sp@-
 movel %a3,%sp@-
 movel %a6@(-8),%sp@-
 movel %a6@(8),%sp@-
 bsr install
 lea %sp@(16),%sp
 moveal %d0,%a4
 pea 72
 movel %a2,%sp@-
 bsr release
 addql #8,%sp
 tstl %a4
 beq ctor_bad
 movel %a6@(-4),%d0
 bra ctor_done
ctor_bad:
 moveq #-1,%d0
ctor_done:
 moveml %sp@,%a2-%a4
 lea %sp@(12),%sp
 unlk %a6
 rts
/* install(menu,table,records,owner). Validate every row before writes. */
install:
 linkw %a6,#0
 lea %sp@(-16),%sp
 moveml %d2/%a2-%a4,%sp@
 moveal %a6@(8),%a2
 moveal %a6@(12),%a3
 moveal %a2@(4),%a4
 movel %a2@(8),%d0
 subl %a4,%d0
 cmpil #32,%d0
 bne install_bad
 moveal %a3,%a0
install_check:
 movel %a0@+,%d2
 bmi install_write_begin
 moveal %a4@(0,%d2:l:8),%a1
 tstl %a1
 beq install_bad
 movel %a1@(0x38),%d0
 cmpl %a0@+,%d0
 bne install_bad
 addql #4,%a0
 movel %a0@+,%d2
 movel %a1@(0,%d2:l),%d0
 cmpl %a0@+,%d0
 bne install_bad
 addql #4,%a0
 bra install_check
install_write_begin:
 moveal %a6@(16),%a0
install_write:
 movel %a3@+,%d2
 bmi install_good
 moveal %a4@(0,%d2:l:8),%a1
 movel %a1,%a0@+
 movel %a2,%a0@+
 movel %a6@(20),%a0@+
 addql #4,%a3
 movel %a3@+,%a1@(0x38)
 movel %a3@+,%d2
 addql #4,%a3
 movel %a3@+,%a1@(0,%d2:l)
 bra install_write
install_good:
 moveq #1,%d0
 bra install_done
install_bad:
 moveq #0,%d0
install_done:
 moveml %sp@,%d2/%a2-%a4
 lea %sp@(16),%sp
 unlk %a6
 rts
.macro row index,reader,draw,offset,edit,wrapper
 .long \index,\reader,BASE+(\draw-lookup),\offset,\edit,BASE+(\wrapper-lookup)
.endm
normal_table:
 row 0,READER_WAVE,draw_wave,0x48,EDIT_WAVE,edit_wave
 row 1,READER_MUL,draw_mul,0x48,EDIT_MUL,edit_mul
 row 2,READER_DST,draw_dst,0x48,EDIT_DST,edit_dst
 row 3,READER_DEPTH,draw_depth,0x48,EDIT_DEPTH,edit_depth
 .long -1
setup_table:
 row 0,READER_SELECTOR,draw_selector,0x48,SELECTOR_EDIT,selector_edit
 row 1,READER_RESET,draw_reset,0x28,ACTION_RST,action_rst
 row 2,READER_FADE,draw_fade,0x48,EDIT_FADE,edit_fade
 row 3,READER_PHASE,draw_phase,0x48,EDIT_PHASE,edit_phase
 .long -1
