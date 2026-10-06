/* SPDX-License-Identifier: MIT
 * Copyright (c) 2026 Lachlan Fysh
 * Original authored source selected for review. re/tools/coldfire_emu/lfo_four_incoming_finish.S; lines 1-160.
 * Unresolved integration bindings are documented in DEPENDENCIES.json.
 */
/* Bounded synchronous caller entry, NOT a Project completion implementation.
 * incoming_finish(handle, retained_live_ctx, native_completed1) -> D0=1/0.
 * native_completed1 is caller attestation: stock load SUCCESS and ALL native
 * bindings completed on the same retained input. It cannot prove completion.
 * Caller owns the prepared immutable handle/input/private context and excludes
 * stock/UI/publication/teardown/allocator users. Owner writer72 already1,
 * readers76=0; NEVER reacquire write_begin. Bounds/magic do NOT prove ownership
 * or protect against a stale/forged handle, ABA, or unknown protocol users.
 * Rejection before copy changes nothing, including the caller's held lease.
 * After copy, rejection keeps live24=1 and writer72=1, retains the handle for
 * caller recovery, and makes NO stock rollback claim. Success copies into the
 * retained live allocation, never publishes the private pointer; then retires
 * private ctx/input/handle exactly once while held, ready and writer-end last.
 * No allocation, global, stock write, EMAC access, or persistence schema change.
 */
.text
.macro bounded base,size
 movel \base,%d0
 andil #15,%d0
 bne finish_bad
 cmpal #ARENA,\base
 bcs finish_bad
 cmpal #(ARENA_END-\size),\base
 bhi finish_bad
.endm
.macro disjoint left,lsize,right,rsize
 movel \left,%d0
 addil #\lsize,%d0
 movel \right,%d1
 cmpl %d1,%d0
 bls .Lseparate\@
 addil #\rsize,%d1
 movel \left,%d0
 cmpl %d0,%d1
 bhi finish_bad
.Lseparate\@:
.endm
.macro context_header base
 movel \base@,%d0
 cmpil #0x4c465347,%d0
 bne finish_bad
 cmpal \base@(4),%a3
 bne finish_bad
 movel \base@(8),%d0
 cmpil #ROOT,%d0
 bne finish_bad
 movel \base@(12),%d0
 cmpil #STOCK_OWNER,%d0
 bne finish_bad
 movel \base@(24),%d0
 cmpil #1,%d0
 bne finish_bad
 movel \base@(16),%d0
 cmpil #CAPACITY,%d0
 bhi finish_bad
 cmpl \base@(28),%d0
 bne finish_bad
.endm
.globl incoming_finish,finish_checked,finish_copied,finish_materialized
.globl finish_released,finish_ready,finish_done,finish_bad
incoming_finish:
 linkw %a6,#-40
 moveml %d2-%d7/%a2-%a5,%sp@
 movel %a6@(16),%d0
 cmpil #1,%d0
 bne finish_bad
 moveal %a6@(8),%a4
 moveal %a6@(12),%a2
 bounded %a4,HANDLE_BYTES
 bounded %a2,CONTEXT_BYTES
 cmpal LIVE_CONTEXT_SLOT,%a2
 bne finish_bad
 moveal OWNER_SLOT,%a3
 bounded %a3,OWNER_BYTES
 movel %a3@,%d0
 cmpil #0x4c464f34,%d0
 bne finish_bad
 movel %a3@(4),%d0
 cmpil #1,%d0
 bne finish_bad
 movel %a3@(40),%d0
 cmpil #STOCK_OWNER,%d0
 bne finish_bad
 movel %a3@(72),%d0
 cmpil #1,%d0
 bne finish_bad
 tstl %a3@(76)
 bne finish_bad
 movel ROOT_BINDER,%d0
 cmpil #ROOT,%d0
 bne finish_bad
 context_header %a2
 movel %a4@,%d0
 cmpil #0x4c46494e,%d0
 bne finish_bad
 movel %a4@(24),%d0
 cmpil #1,%d0
 bne finish_bad
 tstl %a4@(28)
 bne finish_bad
 movel %a4@(12),%d0
 cmpil #STOCK_BYTES,%d0
 bne finish_bad
 movel %a4@(20),%d0
 cmpil #96,%d0
 bcc finish_bad
 moveal %a4@(8),%a5
 bounded %a5,CONTEXT_BYTES
 moveal %a4@(4),%a0
 bounded %a0,MAXIMUM
 movel %a0,%d5
 context_header %a5
 movel %a5@(20),%d0
 cmpil #-1,%d0
 bne finish_bad
 movel %a5@(16),%d0
 moveq #52,%d1
 mulu.l %d1,%d0
 addil #28,%d0
 cmpl %a4@(16),%d0
 bne finish_bad
 /* Generated complete pairwise span checks appear here. */
 FINISH_DISTINCT
 jsr VERIFY_CURRENT
 tstl %d0
 bmi finish_bad
 movel %d0,%d4
finish_checked:
 pea CONTEXT_BYTES
 movel %a5,%sp@-
 movel %a2,%sp@-
 jsr 0x4008f1f0
 lea %sp@(12),%sp
finish_copied:
 /* Header identities and unready flag were checked, hence remain valid.
  * Private selected=-1 must not become the published bank. */
 movel %d4,%a2@(20)
 jsr VERIFY_CURRENT
 cmpl %d4,%d0
 bne finish_bad
 jsr MATERIALIZE
finish_materialized:
 movel %a4,%sp@-
 jsr INCOMING_RELEASE
 addql #4,%sp
 cmpil #1,%d0
 bne finish_bad
finish_released:
 clrl %a2@(24)
finish_ready:
 jsr WRITE_END
 /* write_end has no D0 ABI: produce success AFTER it returns. */
 moveq #1,%d0
 bra finish_done
finish_bad:
 moveq #0,%d0
finish_done:
 moveml %a6@(-40),%d2-%d7/%a2-%a5
 unlk %a6
 rts
