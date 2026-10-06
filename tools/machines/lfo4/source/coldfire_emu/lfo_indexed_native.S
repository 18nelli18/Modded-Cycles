/* SPDX-License-Identifier: MIT
 * Copyright (c) 2026 Lachlan Fysh
 * Original authored source selected for review. re/tools/coldfire_emu/lfo_indexed_native.S; lines 63-420.
 * Unresolved integration bindings are documented in DEPENDENCIES.json.
 */
selected_track:
 jsr 0x400cf866
 movel %d0,%sp@-
 jsr 0x4000eb90
 movel %d0,%sp@-
 jsr 0x40012412
 addql #8,%sp
 rts
/* Guarded callbacks tail-enter the original function with its original stack.
 * Extra instances reject held-step/special UI modes before original mutation.
 * Stock LFO1 bypasses this guard and retains all stock context behavior. */
.macro guarded name,target
\name:
 movel #\target,%d0
 bra guard
.endm
guarded edit_wave,0x40025eba
guarded edit_mul,0x40025f6a
guarded edit_dst,0x4002601a
guarded edit_depth,0x400260ca
guarded action_rst,0x40026eac
guarded edit_fade,0x40026fb2
guarded edit_phase,0x40027014
guard:
 movel %d0,%sp@-
 clrl META+8
 bsr selected_track
 cmpil #6,%d0
 bcc guard_bad_track
 moveal #META,%a0
 movel %a0@(16,%d0:l:4),%d0
 cmpil #1,%d0
 beq guard_pass
 cmpil #2,%d0
 bcs guard_bad_instance
 cmpil #4,%d0
 bhi guard_bad_instance
 jsr 0x400cf9a8
 movel %d0,%sp@-
 jsr 0x4006bdfe
 addql #4,%sp
 tstb %d0
 bne guard_bad_mode
 bra guard_extra
guard_pass:
 moveal %sp@+,%a0
 jmp %a0@
/* Use the constructor-checked value-draw context for Menu ownership.
 * Forward the original callback arguments, then invalidate its own native
 * View. This replaces stock-root notification for extra config edits. */
guard_extra:
 moveal %sp@+,%a0
 movel %a2,%sp@-
 moveal %sp@(12),%a2
 moveal %a2@(0x2c),%a2
 moveal %a2@,%a2
 movel %sp@(16),%sp@-
 movel %sp@(16),%sp@-
 movel %sp@(16),%sp@-
 jsr %a0@
 lea %sp@(12),%sp
 movel %d0,%sp@-
 pea %a2@(0x38)
 jsr 0x40076082
 addql #4,%sp
 movel %sp@+,%d0
 moveal %sp@+,%a2
 rts
guard_bad_track:
 moveq #2,%d0
 bra guard_blocked
guard_bad_instance:
 moveq #1,%d0
 bra guard_blocked
guard_bad_mode:
 moveq #3,%d0
guard_blocked:
 movel %d0,META+8
 addql #4,%sp
 moveq #-1,%d0
 rts
/* Checked callback replacement: table entries(row,offset,original,wrapper).
 * Validate all entries before any replacement, avoiding partial registration. */
install_guards:
 linkw %a6,#0
 lea %sp@(-20),%sp
 moveml %d2-%d3/%a2-%a4,%sp@
 moveal %a6@(8),%a2
 moveal %a6@(12),%a3
 movel %a2@(8),%d0
 subl %a2@(4),%d0
 cmpl %a6@(16),%d0
 bne install_bad
 moveal %a2@(4),%a4
 moveal %a3,%a0
check_loop:
 movel %a0@+,%d2
 bmi checked
 movel %a0@+,%d3
 moveal %a4@(0,%d2:l:8),%a1
 tstl %a1
 beq install_bad
 movel %a1@(0,%d3:l),%d0
 cmpl %a0@+,%d0
 bne install_bad
 /* Every stock value-draw closure captures this Menu, even when its edit
  * closure is an empty functor (Fade/StartPhase). Check that ownership. */
 moveal %a1@(0x2c),%a1
 tstl %a1
 beq install_bad
 movel %a1@,%d1
 cmpl %a2,%d1
 bne install_bad
 addql #4,%a0
 bra check_loop
checked:
 movel %a3@+,%d2
 bmi install_good
 movel %a3@+,%d3
 moveal %a4@(0,%d2:l:8),%a1
 addql #4,%a3
 movel %a3@+,%d0
 movel %d0,%a1@(0,%d3:l)
 bra checked
install_good:
 moveq #0,%d0
 bra install_done
install_bad:
 moveq #1,%d0
install_done:
 movel %d0,META+12
 moveml %sp@,%d2-%d3/%a2-%a4
 lea %sp@(20),%sp
 unlk %a6
 rts
normal_ctor:
 movel %sp@(4),%sp@-
 jsr 0x40025798
 addql #4,%sp
 movel %d0,%sp@-
 pea 32
 pea normal_table(%pc)
 movel %sp@(16),%sp@-
 bsr install_guards
 lea %sp@(12),%sp
 movel %sp@+,%d0
 rts
normal_table:
 .long 0,0x48,0x40025eba,BASE+(edit_wave-resolve)
 .long 1,0x48,0x40025f6a,BASE+(edit_mul-resolve)
 .long 2,0x48,0x4002601a,BASE+(edit_dst-resolve)
 .long 3,0x48,0x400260ca,BASE+(edit_depth-resolve)
 .long -1
setup_table:
 .long 0,0x28,0x40026eac,BASE+(action_rst-resolve)
 .long 1,0x48,0x40026fb2,BASE+(edit_fade-resolve)
 .long 2,0x48,0x40027014,BASE+(edit_phase-resolve)
 .long -1
setup_ctor:
 linkw %a6,#-64
 lea %sp@(-16),%sp
 moveml %d2-%d3/%a2-%a3,%sp@
 moveal %a6@(8),%a2
 movel %a2,%sp@-
 jsr 0x40026b4c
 addql #4,%sp
 movel %d0,%d3
 pea 24
 pea setup_table(%pc)
 movel %a2,%sp@-
 bsr install_guards
 lea %sp@(12),%sp
 tstl %d0
 bne setup_done
 /* Four inline std::function contexts; their manager owns no allocation. */
 lea %a6@(-64),%a0
 moveq #0,%d2
func_loop:
 movel %a2,%a0@+
 clrl %a0@+
 movel #BASE+(manager-resolve),%a0@+
 movel %d2,%d0
 lsll #2,%d0
 lea selector_functions(%pc),%a1
 movel %a1@(0,%d0:l),%a0@+
 addql #1,%d2
 cmpil #4,%d2
 bne func_loop
 pea 84
 jsr 0x400802e0
 addql #4,%sp
 tstl %d0
 beq setup_done
 moveal %d0,%a3
 pea 8
 pea -1
 pea %a6@(-16)
 pea %a6@(-32)
 pea %a6@(-48)
 pea %a6@(-64)
 movel %a3,%sp@-
 jsr 0x400734b0
 lea %sp@(28),%sp
 pea 1
 movel %a3,%sp@-
 jsr 0x400732d6
 addql #8,%sp
 movel %a3,%sp@-
 movel %a2,%sp@-
 jsr 0x40072ce6
 addql #8,%sp
 /* Move the newly owned last shared_ptr to the front without altering refs. */
 moveal %a2@(4),%a0
 movel %a0@(24),%d0
 movel %a0@(28),%d1
 movel %a0@(16),%a0@(24)
 movel %a0@(20),%a0@(28)
 movel %a0@(8),%a0@(16)
 movel %a0@(12),%a0@(20)
 movel %a0@,%a0@(8)
 movel %a0@(4),%a0@(12)
 movel %d0,%a0@
 movel %d1,%a0@(4)
 moveq #0,%d2
renumber:
 moveal %a2@(4),%a0
 movel %d2,%sp@-
 movel %a0@(0,%d2:l:8),%sp@-
 jsr 0x4007320a
 addql #8,%sp
 addql #1,%d2
 cmpil #4,%d2
 bne renumber
 /* Generic native menu's visible-row count is at +0x20 (ctor argument3). */
 moveq #4,%d0
 movel %d0,%a2@(0x20)
setup_done:
 movel %d3,%d0
 moveml %sp@,%d2-%d3/%a2-%a3
 lea %sp@(16),%sp
 unlk %a6
 rts
selector_functions:
 .long BASE+(selector_label-resolve),0x40024d1e,BASE+(selector_draw-resolve),BASE+(selector_edit-resolve)
manager:
 moveal %sp@(4),%a0
 moveal %sp@(8),%a1
 movel %sp@(12),%d0
 cmpil #2,%d0
 beq manager_copy
 cmpil #1,%d0
 bne manager_done
 movel %a1,%a0@
 bra manager_done
manager_copy:
 movel %a1@,%a0@
manager_done:
 moveq #0,%d0
 rts
selector_label:
 linkw %a6,#-8
 movel %a2,%sp@-
 moveal %a0,%a2
 movel #0x4c464f00,%d0
 movel %d0,%a6@(-8)
 pea %a6@(-1)
 pea %a6@(-8)
 movel %a2,%sp@-
 jsr 0x400f980c
 lea %sp@(12),%sp
 movel %a2,%d0
 moveal %sp@+,%a2
 unlk %a6
 rts
selector_edit:
 linkw %a6,#0
 lea %sp@(-12),%sp
 moveml %d2/%a2-%a3,%sp@
 movel %a6@(16),%d2
 bsr selected_track
 cmpil #6,%d0
 bcc selector_done
 moveal #META,%a3
 lea %a3@(16,%d0:l:4),%a3
 movel %a3@,%d0
 addl %d2,%d0
 cmpil #1,%d0
 bge selector_upper
 moveq #1,%d0
selector_upper:
 cmpil #4,%d0
 ble selector_publish
 moveq #4,%d0
selector_publish:
 movel %d0,%a3@
 moveal %a6@(8),%a0
 moveal %a0@,%a2
 pea %a2@(0x38)
 jsr 0x40076082
 addql #4,%sp
selector_done:
 moveml %sp@,%d2/%a2-%a3
 lea %sp@(12),%sp
 unlk %a6
 rts
selector_draw:
 linkw %a6,#-4
 bsr selected_track
 cmpil #6,%d0
 bcc selector_draw_bad
 moveal #META,%a0
 movel %a0@(16,%d0:l:4),%d0
 addil #48,%d0
 bra selector_draw_text
selector_draw_bad:
 moveq #63,%d0
selector_draw_text:
 moveb %d0,%a6@(-4)
 clrb %a6@(-3)
 pea %a6@(-4)
 pea 0
 movel %a6@(24),%sp@-
 movel %a6@(20),%d0
 addql #3,%d0
 movel %d0,%sp@-
 pea 0x40ea14cc
 movel %a6@(16),%sp@-
 jsr 0x40071a04
 lea %sp@(24),%sp
 unlk %a6
 rts
.globl initialize_selection
initialize_selection:
 moveal #META,%a0
 movel #0x4c464f34,%d0
 movel %d0,%a0@
 moveq #1,%d0
 movel %d0,%a0@(4)
 clrl %a0@(8)
 clrl %a0@(12)
 moveq #0,%d1
init_select:
 movel %d0,%a0@(16,%d1:l:4)
 addql #1,%d1
 cmpil #6,%d1
 bne init_select
 rts
/* Extra entries own their update generation. Keep the native canonical store,
 * suppress its stock-root notification and its stock MIDI notifier. A later
 * indexed render/storage adapter must consume this project generation. */
.globl extra_store,extra_notifier
extra_store:
 clrl %sp@(20)
 addql #1,META+68
 jmp 0x4000ba7a
extra_notifier:
 moveq #0,%d0
 rts
