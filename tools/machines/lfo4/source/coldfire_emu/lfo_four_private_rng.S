/* SPDX-License-Identifier: MIT
 * Copyright (c) 2026 Lachlan Fysh
 * Original authored source selected for review. re/tools/coldfire_emu/lfo_four_private_rng.S; lines 1-91,98-103.
 * Unresolved integration bindings are documented in DEPENDENCIES.json.
 */
/* Standalone, scoped RNG interposition proof. Never installs firmware.
 * Entry replaces the first six bytes of 40091a96 with JMP dispatch.
 * Stock fallback executes the displaced load verbatim then continues at
 * 40091a9c. Private eligibility is native return PC + exact owned A2 row,
 * published owner magic/version/read lease and no writer. No active-context
 * pointer and no swapping the two stock MAIN seeds.
 * OWNER_EXPECTED is this proof's positively declared allocation binding;
 * Main must bind it to its retained allocator result and prove its lifetime.
 * Owned offset6440 is a helper guard, NOT an engine-selection context.
 * Gate/busy failures restore SP/callee saves/SR and reach reject_fault.
 * reject_fault is intentionally nonreturning: Main needs explicit abort/
 * lease cleanup, not an invented numerical sample. This proof never admits
 * Wave6 through the existing native adapter.
 */
.text
.globl dispatch,stock_fallback,private_load,private_add,private_store
.globl private_claim,private_release,stock_displaced_load,reject_fault
dispatch:
 lea %sp@(-16),%sp
 moveml %d2-%d3/%a0-%a1,%sp@
 movew %sr,%d3
 movel %sp@(16),%d1
 cmpil #0x40091cce,%d1
 bne stock_fallback
 /* Native stock rows bypass every owned-owner/lease/guard read. */
 movel %a2,%d2
 subil #0x40fde838,%d2
 cmpil #192,%d2
 bcc candidate
 movel %d2,%d1
 andil #31,%d1
 beq stock_fallback
candidate:
 movel %d3,%d1
 oril #0x700,%d1
 movew %d1,%sr
 moveal SLOT,%a0
 cmpal #OWNER_EXPECTED,%a0
 bne reject_masked
 movel %a2,%d2
 subl %a0,%d2
 subil #4400,%d2
 cmpil #576,%d2
 bcc reject_masked
 movel %d2,%d1
 andil #31,%d1
 bne reject_masked
 movel %a0@,%d1
 cmpil #0x4c464f34,%d1
 bne reject_masked
 movel %a0@(4),%d1
 cmpil #1,%d1
 bne reject_masked
 tstl %a0@(72)
 bne reject_masked
 movel %a0@(76),%d1
 cmpil #1,%d1
 bne reject_masked
 tstl %a0@(6440)
 bne reject_masked
 /* Bank-major six rows each; exactly one pair per engine, stock semantics. */
 lea %a0@(6416),%a1
 cmpil #192,%d2
 bcs bank_bound
 addql #8,%a1
 cmpil #384,%d2
 bcs bank_bound
 addql #8,%a1
bank_bound:
 moveq #1,%d1
private_claim:
 movel %d1,%a0@(6440)
private_load:
 movel %a1@(4),%d1
 movel %d1,%d0
private_add:
 addl %a1@,%d0
private_store:
 movel %d1,%a1@
 movel %d0,%a1@(4)
 /* Keep the recurrence's exact CCR, restore caller IPL/supervisor bits. */
 movew %sr,%d2
 andil #0xff,%d2
 andil #0xff00,%d3
 orl %d3,%d2
private_release:
 clrl %a0@(6440)
 movew %d2,%sr
 moveml %sp@,%d2-%d3/%a0-%a1
 lea %sp@(16),%sp
 rts


reject_masked:
 movew %d3,%sr
 moveml %sp@,%d2-%d3/%a0-%a1
 lea %sp@(16),%sp
reject_fault:
 illegal
