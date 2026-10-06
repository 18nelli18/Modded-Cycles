/* SPDX-License-Identifier: MIT
 * Copyright (c) 2026 Lachlan Fysh
 * Original authored source selected for review. re/tools/coldfire_emu/lfo_four_native_bank_join.S; lines 1-65.
 * Unresolved integration bindings are documented in DEPENDENCIES.json.
 */
/* Appended to the frozen guest codec by assembly composition only.
 * native_bank_join(ctx, actualM, bank0..95, flags, flags) -> 1/0.
 * Serialized, disjoint borrowed backing; original stock readers must also be
 * serialized. Existing writer lease spans flush, original operation, restore.
 * No replacement vtables/callbacks; 40009a1e executes its whole native body.
 * Rejecting flush leaves old M, live configs, states and published rows intact.
 * After native entry there is no general stock observer rollback contract.
 */
.text
.globl native_bank_join,join_flushed,join_original,join_returned,join_materialized
.globl join_reject,join_postcondition_failed
native_bank_join:
 pro
 moveal %a6@(8),%a2
 movel %a6@(16),%d0
 cmpil #96,%d0
 bcc join_bad
 bsr enter
 tstl %d0
 beq join_done
 moveal %a6@(12),%a3
 cmpal %a2@(12),%a3
 bne join_reject
 /* Includes actual six getter contracts, bank base and selected index. */
 bsr verify_current
 cmpil #-1,%d0
 beq join_reject
 bsr flush
 tstl %d0
 beq join_reject
 /* Flush is fully admitted before any native selection/backing store. */
 bsr commit
join_flushed:
 movel %a6@(24),%sp@-
 movel %a6@(20),%sp@-
 movel %a6@(16),%sp@-
 movel %a6@(12),%sp@-
join_original:
 jsr 0x40009a1e
 lea %sp@(16),%sp
join_returned:
 /* No assumed D0 success ABI: exact native getters establish the result. */
 bsr verify_current
 cmpl %a6@(16),%d0
 bne join_postcondition_failed
 movel %d0,%a2@(20)
 bsr materialize
 clrl %a2@(24)
join_materialized:
 moveq #1,%d0
 bra join_release
join_postcondition_failed:
 /* Stock call has already happened: extras remain old and routing rejects.
  * Caller must recover stock observer state; never claim old-M rollback here. */
join_reject:
 moveq #1,%d0
 movel %d0,%a2@(24)
 moveq #0,%d0
join_release:
 bsr leave
 bra join_done
join_bad:
 moveq #0,%d0
join_done:
 epi
