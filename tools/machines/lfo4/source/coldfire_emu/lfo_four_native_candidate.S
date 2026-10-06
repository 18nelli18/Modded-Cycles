/* SPDX-License-Identifier: MIT
 * Copyright (c) 2026 Lachlan Fysh
 * Original authored source selected for review. re/tools/coldfire_emu/lfo_four_native_candidate.S; lines 1-165.
 * Unresolved integration bindings are documented in DEPENDENCIES.json.
 */
/* Owned native-engine join. Addresses are explicit emulator bindings, NOT
 * physical placements. Called under the checked owner's render read lease.
 * Stock event executes first, with every original input register restored.
 * Three extra engines then read independently owned controls/state. Each
 * publishes its destination after the preceding engine's stock clamp, so
 * simultaneous contributions have a documented LFO2,LFO3,LFO4 ordering.
 * NONE/neutral DEPTH advance the engine but do not publish to live storage.
 * Only product destinations 10..22 are published; no LFO control aliasing.
 */
.text
.equ SLOT,0x40000304
.equ ENGINE,0x43690000
.globl wrapper,after_stock,private_engine_call,publish_destination,wrapper_done
wrapper:
 lea %sp@(-60),%sp
 moveml %d0-%d7/%a0-%a6,%sp@
 movel %sp@(68),%sp@-
 movel %sp@(68),%sp@-
 moveml %sp@(8),%d0-%d7/%a0-%a6
 jsr 0x40056e24
 lea %sp@(8),%sp
after_stock:
 /* Preserve the STOCK live-out, not an approximation of callee-save rules. */
 lea %sp@(-96),%sp
 moveml %d0-%d7/%a0-%a6,%sp@
 movew %sr,%d0
 movew %d0,%sp@(60)
 movel %macsr,%d0
 movel %d0,%sp@(64)
 andil #0xf0,%d0
 cmpil #0x20,%d0
 bne wrapper_done             /* Other EMAC modes are not admitted. */
 movel %acc0,%d0
 movel %d0,%sp@(68)
 movel %acc1,%d0
 movel %d0,%sp@(72)
 movel %acc2,%d0
 movel %d0,%sp@(76)
 movel %acc3,%d0
 movel %d0,%sp@(80)
 movel %accext01,%d0
 movel %d0,%sp@(84)
 movel %accext23,%d0
 movel %d0,%sp@(88)
 moveal SLOT,%a2
 tstl %a2
 beq wrapper_done
 tstl %a2@(76)
 beq wrapper_done
 tstl %a2@(72)
 bne wrapper_done
 moveal %sp@(160),%a3         /* Original W argument. */
 moveq #0,%d2
engine_loop:
 movel %d2,%d0
 moveq #119,%d1
 mulu.l %d1,%d0
 lsll #2,%d0
 lea %a2@(4976),%a4
 lea %a4@(0,%d0:l),%a4       /* Three private W[476] buffers. */
 moveal %a3,%a0
 moveal %a4,%a1
 moveq #119,%d1
copy_compact:
 movel %a0@+,%a1@+
 subql #1,%d1
 bne copy_compact
 moveal %a2@(56,%d2:l:4),%a0
 lea %a4@(16),%a1
 moveq #6,%d3
copy_lane:
 lea %a0@(22),%a5
 moveq #8,%d4
copy_control:
 movew %a5@+,%a1@+
 subql #1,%d4
 bne copy_control
 lea %a1@(50),%a1
 lea %a0@(100),%a0
 subql #1,%d3
 bne copy_lane
 /* Reject non-product destinations before state/compact mutation. */
 lea %a4@(22),%a0
 moveq #6,%d3
validate_destination:
 mvzb %a0@,%d0
 beq destination_valid
 cmpil #10,%d0
 bcs next_engine
 cmpil #22,%d0
 bhi next_engine
destination_valid:
 lea %a0@(66),%a0
 subql #1,%d3
 bne validate_destination
 movel %d2,%d0
 movel #192,%d1
 mulu.l %d1,%d0
 lea %a2@(4400),%a5
 lea %a5@(0,%d0:l),%a5
 /* The original engine's MAC arithmetic expects a zero accumulator. */
 moveq #0,%d0
 movel %d0,%acc0
 movel %d0,%acc1
 movel %d0,%acc2
 movel %d0,%acc3
 movel #0x20,%macsr
 movel %a5,%sp@-
 moveal %sp@(48),%a0         /* Post-stock A3 is the root context. */
 movel %a0@(4),%sp@-
 movel 0x40149310,%sp@-
 movel %a4,%sp@-
private_engine_call:
 jsr ENGINE
 lea %sp@(16),%sp
 cmpil #6,%d0
 bne next_engine
 /* Copy only musical destination values, never private control slots. */
 lea %a4@(22),%a0
 lea %a4@(14),%a1
 lea %a3@(14),%a6
 moveq #6,%d3
publication_lane:
 mvzb %a0@,%d0
 beq publication_next
 /* Stock clamps even with delta=0. Never apply that unrelated clamp when
  * the extra is neutral; preserve phase/state via the call above. */
 mvzw %a0@(8),%d1
 cmpil #0x4000,%d1
 beq publication_next
 movew %a1@(0,%d0:l:2),%d1
publish_destination:
 movew %d1,%a6@(0,%d0:l:2)
publication_next:
 lea %a0@(66),%a0
 lea %a1@(66),%a1
 lea %a6@(66),%a6
 subql #1,%d3
 bne publication_lane
next_engine:
 addql #1,%d2
 cmpil #3,%d2
 bne engine_loop
 /* Restore complete fractional accumulator centers and extension pairs.
  * OMC/rounding modes reject before snapshot: no saturated-read ambiguity. */
 movel %sp@(68),%d0
 movel %d0,%acc0
 movel %sp@(72),%d0
 movel %d0,%acc1
 movel %sp@(76),%d0
 movel %d0,%acc2
 movel %sp@(80),%d0
 movel %d0,%acc3
 movel %sp@(84),%d0
 movel %d0,%accext01
 movel %sp@(88),%d0
 movel %d0,%accext23
wrapper_done:
 movel %sp@(64),%d0
 movel %d0,%macsr
 movew %sp@(60),%d0
 movew %d0,%sr
 moveml %sp@,%d0-%d7/%a0-%a6
 lea %sp@(156),%sp
 rts
