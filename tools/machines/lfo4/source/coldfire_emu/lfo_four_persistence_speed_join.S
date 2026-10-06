/* SPDX-License-Identifier: MIT
 * Copyright (c) 2026 Lachlan Fysh
 * Original authored source selected for review. re/tools/coldfire_emu/lfo_four_persistence_speed_join.S; lines 1-182.
 * Unresolved integration bindings are documented in DEPENDENCIES.json.
 */
/* OWNER: borrowed pointers require the authentic native consumer frame.
 * Retained boot owner; serialized trusted UI callers, no replacement/free.
 * Direct getters may route LFO1 after admission, but cannot export extras.
 * No mutable scratch token, no lease acquired then dropped around a pointer.
 */
owner_route:
 movel %sp@(12),%d0
 cmpil #29,%d0
 bne stock_owner
 tstl SLOT
 beq stock_owner
 linkw %a6,#-4
 lea %sp@(-12),%sp
 moveml %d2/%a2-%a3,%sp@
 clrl %a6@(-4)
 moveal SLOT,%a3
 /* These literal native helpers preserve the consumer's A6. Check their
  * return first, before inspecting any frame supplied by a direct getter. */
 movel %a6@(4),%d0
 cmpil #0x4001ddd8,%d0
 beq owner_borrow
 cmpil #0x4001de38,%d0
 beq owner_borrow
 cmpil #0x4001de72,%d0
 beq owner_borrow
 pea 72
 movel %a3,%sp@-
 jsr ADMIT
 addql #8,%sp
 cmpil #-1,%d0
 beq owner_denied
 moveq #1,%d0
 movel %d0,%a6@(-4)
 bra owner_track
owner_borrow:
 moveal %a6@,%a0
 movel %a0,%d0
 subl %a6,%d0
 cmpil #1024,%d0
 bhi owner_denied
 cmpil #88,%d0
 bcs owner_denied
 movel %a0,%d0
 andil #3,%d0
 bne owner_denied
 movel %a0@(4),%d0
 cmpil #SPEED_BASE+consume_return,%d0
 bne owner_denied
 /* D2 was saved by our unchanged stock_consume prologue, before native
  * code reuses it. It is the owner captured by this consumer's admission. */
 cmpal %a0@(-84),%a3
 bne owner_denied
 cmpal SLOT,%a3
 bne owner_denied
 movel %a3@(72),%d0
 cmpil #1,%d0
 bne owner_denied
 tstl %a3@(76)
 bne owner_denied
 moveal %a3,%a0
 CONTEXT_CHECK owner_denied
owner_track:
 movel %a6@(12),%d2
 cmpil #6,%d2
 bcs owner_selected
 bsr selected_track
 movel %d0,%d2
owner_selected:
 cmpil #6,%d2
 bcc owner_denied
 movel %a3@(16,%d2:l:4),%d0
 cmpil #1,%d0
 beq owner_original
 cmpil #2,%d0
 bcs owner_denied
 cmpil #4,%d0
 bhi owner_denied
 /* A direct getter owns only its short local lease. It must not return
  * a pointer whose use would outlive that lease. */
 tstl %a6@(-4)
 bne owner_denied
 moveal %a3@(36,%d0:l:4),%a2
 movel %d2,%d0
 lsll #3,%d0
 addil #504,%d0
 lea %a2@(0,%d0:l),%a2
 movel %a2,%d0
 bra owner_done
owner_denied:
 moveq #0,%d0
owner_done:
 movel %d0,%sp@-
 bsr owner_release
 movel %sp@+,%d0
 moveml %a6@(-16),%d2/%a2-%a3
 unlk %a6
 rts
owner_original:
 bsr owner_release
 moveml %a6@(-16),%d2/%a2-%a3
 unlk %a6
 bra stock_owner
owner_release:
 tstl %a6@(-4)
 beq owner_release_done
 pea 72
 movel %a3,%sp@-
 jsr RELEASE
 addql #8,%sp
owner_release_done:
 rts
/* CONSUMER: admission encloses context check and gate store at IPL7.
 * D2 captures the lease owner across every original callee. Rejection before
 * admission changes no diagnostics, accumulator, callbacks or backing.
 */
.globl speed_claim,consume_dispatch,consume_return,consume_reject
speed_claim:
 pea 72
 movel SLOT,%sp@-
 jsr ADMIT
 addql #8,%sp
 rts
speed_consume:
 linkw %a6,#0
 lea %sp@(-8),%sp
 moveml %d2/%a2,%sp@
 moveq #0,%d2
 movel %a6@(12),%sp@-
 jsr 0x4006f762
 addql #4,%sp
 cmpil #10,%d0
 bne consume_original
 tstl SLOT
 beq consume_original
 bsr speed_claim
 cmpil #-1,%d0
 beq consume_reject
 movel %d0,%d2
 moveal %d2,%a2
 clrl %a2@(8)
 bsr selected_track
 cmpil #6,%d0
 bcc consume_locked
 movel %a2@(16,%d0:l:4),%d0
 cmpil #1,%d0
 beq consume_original
 /* admit checked all six selectors and routing geometries. */
 jsr 0x400cf9a8
 movel %d0,%sp@-
 jsr 0x4006bdfe
 addql #4,%sp
 tstb %d0
 bne consume_locked
consume_original:
 movel %a6@(12),%sp@-
 movel %a6@(8),%sp@-
consume_dispatch:
 bsr stock_consume
consume_return:
 addql #8,%sp
 bra consume_done
consume_locked:
 /* Historical lock/track diagnostic, only while our own lease is held. */
 moveal %d2,%a2
 moveq #3,%d0
 movel %d0,%a2@(8)
consume_reject:
 moveq #0,%d0
consume_done:
 tstl %d2
 beq consume_restore
 movel %d0,%sp@-
 pea 72
 movel %d2,%sp@-
 jsr RELEASE
 addql #8,%sp
 movel %sp@+,%d0
consume_restore:
 moveml %sp@,%d2/%a2
 lea %sp@(8),%sp
 unlk %a6
 rts
