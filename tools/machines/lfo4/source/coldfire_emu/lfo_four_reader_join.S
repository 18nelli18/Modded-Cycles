/* SPDX-License-Identifier: MIT
 * Copyright (c) 2026 Lachlan Fysh
 * Original authored source selected for review. re/tools/coldfire_emu/lfo_four_reader_join.S; lines 1-368.
 * Unresolved integration bindings are documented in DEPENDENCIES.json.
 */
/* QEMU-only join over the current owned candidate. No original vtables are
 * invented: constructors retain their contexts/managers and only checked
 * value invokers change. SLOT must name the retained, fully published owner.
 * Owner replacement/free/reset while active remains prohibited.
 */
.text
.equ SLOT,0x40000304
.globl acquire,release,draw_wave,draw_mul,draw_dst,draw_depth
.globl draw_reset,draw_fade,draw_phase,draw_selector,draw_call,draw_release
.globl normal_ctor,setup_ctor,install,readback,readback_get,readback_format
.globl detach
/* acquire(expected_owner, track, force_selector): 1=lease, 0=stock,
 * -1=busy/invalid. IPL7 encloses SLOT identity, metadata and gate test/store.
 * No extra entry/backing/config pointer is loaded before successful admission.
 */
acquire:
 movel %d2,%sp@-
 movew %sr,%d2
 moveq #-1,%d0
 moveal %sp@(8),%a0
 tstl %a0
 beq acquire_stock
 movel %d2,%d1
 oril #0x700,%d1
 movew %d1,%sr
 cmpal SLOT,%a0
 bne acquire_done
 movel %a0@,%d1
 cmpil #0x4c464f34,%d1
 bne acquire_done
 movel %a0@(4),%d1
 cmpil #1,%d1
 bne acquire_done
 movel %sp@(12),%d1
 cmpil #6,%d1
 bcc acquire_done
 movel %a0@(16,%d1:l:4),%d1
 cmpil #1,%d1
 bcs acquire_done
 cmpil #4,%d1
 bhi acquire_done
 tstl %sp@(16)
 bne acquire_gate
 cmpil #1,%d1
 beq acquire_stock
acquire_gate:
.if QUARANTINE_OFFSET
 tstl %a0@(QUARANTINE_OFFSET)
 bne acquire_done
.endif
.if BINDING_OFFSET
 cmpal %a0@(BINDING_OFFSET),%a0
 bne acquire_done
.endif
 tstl %a0@(72)
 bne acquire_done
 tstl %a0@(76)
 bne acquire_done
 moveq #1,%d0
 movel %d0,%a0@(76)
 bra acquire_done
acquire_stock:
 moveq #0,%d0
acquire_done:
 movew %d2,%sr
 movel %sp@+,%d2
 rts
/* release(captured_owner): never clear the slot's new/different owner's gate.
 * Wrong/null/unpublished owner rejects before dereference. No nested reader
 * admission exists, so only the acquiring wrapper calls this operation.
 */
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
 tstl %a0@(72)
 bne release_done
 movel %a0@(76),%d1
 cmpil #1,%d1
 bne release_done
 clrl %a0@(76)
 moveq #1,%d0
release_done:
 movew %d2,%sr
 movel %sp@+,%d2
 rts
/* detach(expected_owner): quiescent task boundary only; no free/reset/rebuild.
 * Refuses both leases and a nonmatching runtime binding. Unpublish before a
 * separately controlled full heap reset. IPL7 is NOT DMA/source quiescence.
 */
detach:
 movel %d2,%sp@-
 movew %sr,%d2
 moveq #0,%d0
 moveal %sp@(8),%a0
 tstl %a0
 beq detach_done
 movel %d2,%d1
 oril #0x700,%d1
 movew %d1,%sr
 cmpal SLOT,%a0
 bne detach_done
 tstl %a0@(72)
 bne detach_done
 tstl %a0@(76)
 bne detach_done
.if QUARANTINE_OFFSET
 tstl %a0@(QUARANTINE_OFFSET)
 bne detach_done
.endif
.if BINDING_OFFSET
 cmpal %a0@(BINDING_OFFSET),%a0
 bne detach_done
.endif
 lea %a0@(4400),%a1
 cmpal SLOT-4,%a1
 bne detach_done
 clrl SLOT
 clrl SLOT-4
 moveq #1,%d0
detach_done:
 movew %d2,%sr
 movel %sp@+,%d2
 rts
.macro draw name,target,force=0
\name:
 movel #\target,%d0
 moveq #\force,%d1
 bra draw_enter
.endm
draw draw_wave,0x40025d28
draw draw_mul,0x400263e8
draw draw_dst,0x400264a2
draw draw_depth,0x40026562
draw draw_reset,0x40026f20
draw draw_fade,0x40027076
draw draw_phase,0x40027124
draw draw_selector,SELECTOR_DRAW,1
draw_enter:
 linkw %a6,#-8
 lea %sp@(-16),%sp
 moveml %d2-%d3/%a2-%a3,%sp@
 moveal %d0,%a3
 movel %d1,%a6@(-8)
 jsr 0x400cf866
 movel %d0,%sp@-
 jsr 0x4000eb90
 movel %d0,%sp@-
 jsr 0x40012412
 addql #8,%sp
 movel %d0,%d2
 moveal SLOT,%a2
 movel %a6@(-8),%sp@-
 movel %d2,%sp@-
 movel %a2,%sp@-
 bsr acquire
 lea %sp@(12),%sp
 movel %d0,%d3
 bmi draw_done
 /* LFO1 enters its original value closure without a read lease. */
 movel %a6@(24),%sp@-
 movel %a6@(20),%sp@-
 movel %a6@(16),%sp@-
 movel %a6@(12),%sp@-
 movel %a6@(8),%sp@-
draw_call:
 jsr %a3@
 lea %sp@(20),%sp
 movel %d0,%a6@(-4)
 tstl %d3
 beq draw_restore_result
 movel %a2,%sp@-
draw_release:
 bsr release
 addql #4,%sp
draw_restore_result:
 movel %a6@(-4),%d0
draw_done:
 moveml %sp@,%d2-%d3/%a2-%a3
 lea %sp@(16),%sp
 unlk %a6
 rts
/* Existing candidate constructors execute first. Validate ALL invokers and
 * menu captures before installing ANY readers; fail closed on template drift.
 */
normal_ctor:
 moveal SLOT,%a0
 tstl %a0
 bne normal_owned
 jmp 0x40025798
normal_owned:
 movel %sp@(4),%sp@-
 jsr NORMAL_CTOR
 addql #4,%sp
 movel %d0,%sp@-
 pea normal_table(%pc)
 movel %sp@(12),%sp@-
 bsr install
 addql #8,%sp
 movel %sp@+,%d0
 rts
setup_ctor:
 moveal SLOT,%a0
 tstl %a0
 bne setup_owned
 jmp 0x40026b4c
setup_owned:
 movel %sp@(4),%sp@-
 jsr SETUP_CTOR
 addql #4,%sp
 movel %d0,%sp@-
 pea setup_table(%pc)
 movel %sp@(12),%sp@-
 bsr install
 addql #8,%sp
 movel %sp@+,%d0
 rts
install:
 linkw %a6,#0
 lea %sp@(-12),%sp
 moveml %a2-%a4,%sp@
 moveal %a6@(8),%a2
 moveal %a6@(12),%a3
 movel %a2@(8),%d0
 subl %a2@(4),%d0
 cmpil #32,%d0
 bne install_bad
 moveal %a2@(4),%a4
 moveal %a3,%a0
install_check:
 movel %a0@+,%d0
 bmi install_write
 moveal %a4@(0,%d0:l:8),%a1
 tstl %a1
 beq install_bad
 movel %a1@(0x38),%d0
 cmpl %a0@+,%d0
 bne install_bad
 tstl %a1@(0x34)
 beq install_bad
 moveal %a1@(0x2c),%a1
 tstl %a1
 beq install_bad
 /* Selector context is inline; the seven native contexts are allocated. */
 cmpil #SELECTOR_DRAW,%d0
 beq install_inline
 cmpal %a1@,%a2
 bne install_bad
 bra install_next
install_inline:
 cmpal %a1,%a2
 bne install_bad
install_next:
 addql #4,%a0
 bra install_check
install_write:
 movel %a3@+,%d0
 bmi install_good
 moveal %a4@(0,%d0:l:8),%a1
 addql #4,%a3
 movel %a3@+,%a1@(0x38)
 bra install_write
install_good:
 moveq #1,%d0
 bra install_done
install_bad:
 moveq #0,%d0
install_done:
 moveml %sp@,%a2-%a4
 lea %sp@(12),%sp
 unlk %a6
 rts
normal_table:
 .long 0,0x40025d28,BASE+(draw_wave-acquire)
 .long 1,0x400263e8,BASE+(draw_mul-acquire)
 .long 2,0x400264a2,BASE+(draw_dst-acquire)
 .long 3,0x40026562,BASE+(draw_depth-acquire)
 .long -1
setup_table:
 .long 0,SELECTOR_DRAW,BASE+(draw_selector-acquire)
 .long 1,0x40026f20,BASE+(draw_reset-acquire)
 .long 2,0x40027076,BASE+(draw_fade-acquire)
 .long 3,0x40027124,BASE+(draw_phase-acquire)
 .long -1
/* readback(expected_owner,track,descriptor,buffer). Selected extra only.
 * Native Entry +1c reads the word via original Regional +28 backing getter;
 * Entry +3c formats it using the real initialized descriptor cache.
 * This is an enclosed copy/string result, never an escaping borrowed pointer.
 */
readback:
 linkw %a6,#0
 lea %sp@(-16),%sp
 moveml %d2-%d3/%a2-%a3,%sp@
 moveal %a6@(8),%a2
 movel %a6@(16),%d2
 subil #29,%d2
 cmpil #7,%d2
 bhi readback_fail
 tstl %a2
 beq readback_fail
 movel %a6@(20),%d0
 beq readback_fail
 movel %d0,%d1
 addil #64,%d1
 bcs readback_fail
 cmpl %a2,%d1
 bls readback_buffer_ok
 lea %a2@(OWNER_BYTES),%a0
 cmpl %a0,%d0
 bcs readback_fail
readback_buffer_ok:
 pea 1
 movel %a6@(12),%sp@-
 movel %a2,%sp@-
 bsr acquire
 lea %sp@(12),%sp
 cmpil #1,%d0
 bne readback_fail
 movel %a6@(12),%d0
 movel %a2@(16,%d0:l:4),%d1
 cmpil #2,%d1
 bcs readback_reject
 subql #2,%d1
 moveal %a2@(44,%d1:l:4),%a3
 lsll #3,%d0
 lea %a3@(504),%a3
 lea %a3@(0,%d0:l),%a3
 movel %a6@(16),%sp@-
 movel %a3,%sp@-
 moveal %a3@,%a0
 moveal %a0@(0x1c),%a0
readback_get:
 jsr %a0@
 addql #8,%sp
 movel %d0,%d3
 movel %a6@(20),%sp@-
 movel %d0,%sp@-
 movel %a6@(16),%sp@-
 movel %a3,%sp@-
 moveal %a3@,%a0
 moveal %a0@(0x3c),%a0
readback_format:
 jsr %a0@
 lea %sp@(16),%sp
 movel %a2,%sp@-
 bsr release
 addql #4,%sp
 movel %d3,%d0
 bra readback_done
readback_reject:
 movel %a2,%sp@-
 bsr release
 addql #4,%sp
readback_fail:
 moveq #-1,%d0
readback_done:
 moveml %sp@,%d2-%d3/%a2-%a3
 lea %sp@(16),%sp
 unlk %a6
 rts
