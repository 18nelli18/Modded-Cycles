/* SPDX-License-Identifier: MIT
 * Copyright (c) 2026 Lachlan Fysh
 * Original authored source selected for review. re/tools/coldfire_emu/lfo_four_sound_extension.S; lines 1-64.
 * Unresolved integration bindings are documented in DEPENDENCIES.json.
 */
/* Authored CPU primitives for the declared native contract fixture.
 * gather(owner6976, track, out48) / scatter(owner6976, track, in48):
 * exact candidate config words only; pointers/vtables/state stay in RAM.
 * Caller owns disjoint buffers and holds existing write exclusion. Invalid
 * track rejects before memory access. Validation/transaction engine is native
 * C in lfo_four_sound_extension.py, not falsely claimed as guest computation.
 */
.text
.globl gather,scatter,copy48
gather:
 moveq #0,%d1
 bra transfer
scatter:
 moveq #1,%d1
transfer:
 lea %sp@(-16),%sp
 moveml %d2-%d3/%a2-%a3,%sp@
 movel %sp@(24),%d0
 cmpil #6,%d0
 bcc reject
 moveq #100,%d2
 mulu.l %d2,%d0
 moveal %sp@(20),%a2
 lea %a2@(2530),%a2
 lea %a2@(0,%d0:l),%a2
 moveal %sp@(28),%a3
 moveq #3,%d2
instance:
 moveal %a2,%a0
 moveq #8,%d3
 tstl %d1
 bne input
output:
 movew %a0@+,%a3@+
 subql #1,%d3
 bne output
 bra next
input:
 movew %a3@+,%a0@+
 subql #1,%d3
 bne input
next:
 lea %a2@(640),%a2
 subql #1,%d2
 bne instance
 moveq #1,%d0
 bra done
reject:
 moveq #0,%d0
done:
 moveml %sp@,%d2-%d3/%a2-%a3
 lea %sp@(16),%sp
 rts
/* A bounded CPU copy witness, not a Sound identity/copy lifecycle by itself. */
copy48:
 moveal %sp@(4),%a0
 moveal %sp@(8),%a1
 moveq #24,%d0
copyword:
 movew %a0@+,%a1@+
 subql #1,%d0
 bne copyword
 moveq #1,%d0
 rts
