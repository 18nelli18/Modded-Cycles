/* SPDX-License-Identifier: MIT
 * Copyright (c) 2026 Lachlan Fysh
 * Original authored source selected for review. re/tools/coldfire_emu/lfo_four_native_engine.S; lines 1-97.
 * Unresolved integration bindings are documented in DEPENDENCIES.json.
 */
/* Bounded guest proof, not an installed render hook.
 * apply(W, scalar VALUE, event-mask VALUE, six-record state): D0=6 or -1.
 * Caller owns disjoint, initialized W[476] and state[192], with render/edit
 * exclusion and MACSR=0x20, zero ACCs. All six lanes validate before mutation.
 * Original engine has no state-pointer ABI. We supply its exact 48-byte frame
 * and A2/A3 bindings and enter unchanged MAIN after its two absolute LEAs.
 * No copied kernel, waveform, fade arithmetic, RNG swap or MAIN overlay.
 */
.text
.ifndef STOCK_CONTINUE
.equ STOCK_CONTINUE,0x40091aca
.endif
.ifndef PERIOD
.equ PERIOD,0x5265c000
.endif
.globl apply, reject, enter_original
apply:
 lea %sp@(-48),%sp
 moveml %d2-%d7/%a2-%a6,%sp@
 moveal %sp@(52),%a4
 moveal %sp@(64),%a2
 movel %a4,%d0
 movel %a2,%d1
 orl %d1,%d0
 andil #3,%d0
 bne reject
 lea %a4@(16),%a0
 moveal %a2,%a1
 moveq #6,%d2
validate_lane:
 mvzw %a0@,%d7
 cmpil #0x7f00,%d7
 bhi reject
 mvzb %a0@(2),%d0
 cmpil #23,%d0
 bhi reject
 mvzw %a0@(4),%d1
 cmpil #0x7f00,%d1
 bhi reject
 mvzb %a0@(6),%d1
 cmpil #32,%d1
 bhi reject
 mvzb %a0@(8),%d1
 cmpil #5,%d1
 bhi reject                 /* Wave 6 mutates stock MAIN RNG globals. */
 mvzw %a0@(10),%d1
 cmpil #0x7f00,%d1
 bhi reject
 mvzb %a0@(12),%d1
 cmpil #4,%d1
 bhi reject
 mvzw %a0@(14),%d1
 cmpil #0x7f00,%d1
 bhi reject
 movel %a1@,%d1
 cmpil #PERIOD,%d1
 bcc reject
 movel %a1@(8),%d1
 cmpil #0x3fffffff,%d1
 bhi reject
 mvzb %a1@(28),%d1
 cmpil #1,%d1
 bhi reject
 mvzb %a1@(29),%d1
 cmpil #1,%d1
 bhi reject
 /* Guard the original signed low-result MULS/ASR and single wrap. */
 movel %sp@(56),%d1
 cmpil #12,%d0
 bcs sync_scalar
 subil #12,%d0
 movel #14400,%d1
sync_scalar:
 subil #0x4000,%d7
 addl %d7,%d7
 muls.l %d1,%d7
 moveq #11,%d3
 subl %d0,%d3
 asrl %d3,%d7
 tstl %d7
 bpl positive_increment
 negl %d7
positive_increment:
 cmpil #PERIOD,%d7
 bcc reject
 lea %a0@(66),%a0
 lea %a1@(32),%a1
 subql #1,%d2
 bne validate_lane
 lea %a2@(28),%a3
enter_original:
 jmp STOCK_CONTINUE
reject:
 moveq #-1,%d0
 moveml %sp@,%d2-%d7/%a2-%a6
 lea %sp@(48),%sp
 rts
