/* SPDX-License-Identifier: MIT
 * Copyright (c) 2026 Lachlan Fysh
 * Original authored source selected for review. re/tools/coldfire_emu/lfo_four_persistence_startup_transaction.S; lines 1-26.
 * Unresolved integration bindings are documented in DEPENDENCIES.json.
 */
/* NEW startup-only adjunct to the derived checked owner recipe.
 * Explicit emulator-linked code/data, NOT installed placement. The four-byte
 * slot belongs to this linked component; it is never an anonymous RAM hole.
 * All callers serialize startup before any reader/ISR is installed.
 */
.text
.globl persistence_ready,persistence_context_slot
persistence_ready:
 movel %a2,%sp@-
 moveal %sp@(8),%a2
 jsr VERIFY_CURRENT
 cmpil #-1,%d0
 beq persistence_ready_bad
 /* create() zeroed both full tables. No stock getter/binding is modified. */
 movel %d0,%a2@(20)
 clrl %a2@(24)
 movel %a2,%d0
 bra persistence_ready_done
persistence_ready_bad:
 moveq #0,%d0
persistence_ready_done:
 moveal %sp@+,%a2
 rts
.balign 4
persistence_context_slot:
 .long 0
