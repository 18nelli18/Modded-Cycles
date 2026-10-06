/* SPDX-License-Identifier: MIT
 * Copyright (c) 2026 Lachlan Fysh
 * Original authored source selected for review. re/tools/coldfire_emu/lfo_four_owned_incoming_join.S; lines 1-271.
 * Unresolved integration bindings are documented in DEPENDENCIES.json.
 */
/* Authored synchronous task boundary, not a production hook.
 * incoming_prepare(manager,live_ctx,slot0..95) -> owned32B handle or0.
 * Caller serializes Project/UI/publication/teardown and owns returned handle.
 * Handle: magic,buffer,private_ctx,stock_len,wire_len,slot,state1,read_status0.
 * Native read/validator + private LF4S decode; NO stock logical mutation or
 * publication. Retain BOTH input and context until incoming_release(handle).
 * Strict extended-v6 scope; no missing-tail-to-defaults conversion.
 */
.text
.globl incoming_prepare,incoming_handle_allocated,incoming_buffer_allocated
.globl incoming_context_allocated,incoming_native_read_done,incoming_decoded
.globl incoming_prepared,incoming_failed,incoming_release,incoming_retired
.globl incoming_stock_validator,incoming_validator_capacity,incoming_validator_admitted
incoming_prepare:
 linkw %a6,#0
 lea %sp@(-40),%sp
 moveml %d2-%d7/%a2-%a5,%sp@
 moveal %a6@(12),%a2
 cmpal #ARENA,%a2
 bcs incoming_refused
 cmpal #(ARENA_END-CONTEXT_BYTES),%a2
 bhi incoming_refused
 cmpal LIVE_CONTEXT_SLOT,%a2
 bne incoming_refused
 movel %a2@,%d0
 cmpil #0x4c465347,%d0
 bne incoming_refused
 tstl %a2@(24)
 bne incoming_refused
 moveal %a2@(4),%a0
 cmpal OWNER_SLOT,%a0
 bne incoming_refused
 cmpal #0,%a0
 beq incoming_refused
 moveal %a2@(8),%a3
 cmpal #ROOT,%a3
 bne incoming_refused
 cmpal ROOT_BINDER,%a3
 bne incoming_refused
 movel %a6@(16),%d0
 cmpil #96,%d0
 bcc incoming_refused
 jsr VERIFY_CURRENT
 cmpl %a2@(20),%d0
 bne incoming_refused
 pea HANDLE_BYTES
 pea 1
 jsr 0x40080238
 addql #8,%sp
 tstl %d0
 beq incoming_refused
 moveal %d0,%a4
incoming_handle_allocated:
 movel %a6@(16),%a4@(20)
 pea MAXIMUM
 jsr 0x40080064
 addql #4,%sp
 tstl %d0
 beq incoming_failed
 movel %d0,%a4@(4)
incoming_buffer_allocated:
 movel %a2@(12),%sp@-
 movel %a2@(8),%sp@-
 movel %a2@(4),%sp@-
 jsr CREATE_PRIVATE
 lea %sp@(12),%sp
 tstl %d0
 beq incoming_failed
 movel %d0,%a4@(8)
incoming_context_allocated:
 /* Zero entire requested destination before the supplied original read. */
 pea MAXIMUM
 clrl %sp@-
 movel %a4@(4),%sp@-
 jsr 0x4008f238
 lea %sp@(12),%sp
 movel %a6@(16),%sp@-
 movel %a4@(4),%sp@-
 movel %a6@(8),%sp@-
 jsr 0x4008c3ee
 lea %sp@(12),%sp
 movel %d0,%a4@(28)
incoming_native_read_done:
 tstl %d0
 bne incoming_failed
 moveal %a4@(4),%a5
 addal #STOCK_BYTES,%a5
 movel %a5@,%d0
 cmpil #0x4c463453,%d0
 bne incoming_failed
 movel %a5@(8),%d5
 cmpil #28,%d5
 bcs incoming_failed
 cmpil #WIRE_MAX,%d5
 bhi incoming_failed
 movel %a4@(4),%sp@-
 movel %d5,%sp@-
 movel %a5,%sp@-
 pea STOCK_BYTES
 movel %a4@(4),%sp@-
 movel %a4@(8),%sp@-
 jsr PRIVATE_DECODE
 lea %sp@(24),%sp
 tstl %d0
 beq incoming_failed
incoming_decoded:
 /* Canonical owned-save padding is also checked, not ignored stale bytes. */
 moveal %a5,%a0
 addal %d5,%a0
 movel #WIRE_MAX,%d0
 subl %d5,%d0
 bsr incoming_padding_zero
 tstl %d0
 beq incoming_failed
 movel #STOCK_BYTES,%d0
 movel %d0,%a4@(12)
 movel %d5,%a4@(16)
 moveq #1,%d0
 movel %d0,%a4@(24)
 movel #0x4c46494e,%d0
 movel %d0,%a4@
incoming_prepared:
 movel %a4,%d0
 bra incoming_prepare_done
incoming_failed:
 /* Unpublished allocations may be discarded in any validation-failure arm. */
 moveal %a4@(8),%a0
 cmpal #0,%a0
 beq incoming_failed_buffer
 movel %a0,%sp@-
 jsr 0x4008026a
 addql #4,%sp
incoming_failed_buffer:
 moveal %a4@(4),%a0
 cmpal #0,%a0
 beq incoming_failed_handle
 movel %a0,%sp@-
 jsr 0x4008026a
 addql #4,%sp
incoming_failed_handle:
 movel %a4,%sp@-
 jsr 0x4008026a
 addql #4,%sp
incoming_refused:
 moveq #0,%d0
incoming_prepare_done:
 moveml %sp@,%d2-%d7/%a2-%a5
 lea %sp@(40),%sp
 unlk %a6
 rts

incoming_padding_zero:
 tstl %d0
 beq incoming_padding_good
incoming_padding_loop:
 tstb %a0@+
 bne incoming_padding_bad
 subql #1,%d0
 bne incoming_padding_loop
incoming_padding_good:
 moveq #1,%d0
 rts
incoming_padding_bad:
 moveq #0,%d0
 rts

/* Caller-owned handle only; no arbitrary pointer/ABA ownership guarantee. */
incoming_release:
 linkw %a6,#0
 lea %sp@(-8),%sp
 moveml %d2/%a2,%sp@
 moveal %a6@(8),%a2
 cmpal #ARENA,%a2
 bcs incoming_release_bad
 cmpal #(ARENA_END-HANDLE_BYTES),%a2
 bhi incoming_release_bad
 movel %a2,%d0
 andil #15,%d0
 bne incoming_release_bad
 movel %a2@,%d0
 cmpil #0x4c46494e,%d0
 bne incoming_release_bad
 movel %a2@(24),%d0
 cmpil #1,%d0
 bne incoming_release_bad
 clrl %a2@
 clrl %a2@(24)
 movel %a2@(8),%sp@-
 jsr 0x4008026a
 addql #4,%sp
 movel %a2@(4),%sp@-
 jsr 0x4008026a
 addql #4,%sp
 movel %a2,%sp@-
 jsr 0x4008026a
 addql #4,%sp
incoming_retired:
 moveq #1,%d0
 bra incoming_release_done
incoming_release_bad:
 moveq #0,%d0
incoming_release_done:
 moveml %sp@,%d2/%a2
 addql #8,%sp
 unlk %a6
 rts

/* Named read's original 4008c496 call is emulator-retargeted HERE. All original
 * validator instructions remain unchanged. Exact raw v6 rejects migration.
 * v6 performs SIX sequential payload+16B-control pairs, freeing each before
 * the next: payload requests 174404,174404,180404,210404,210404,210404 hex.
 * Guard probes the maximum class4MiB+16B pair and returns both before stock.
 * Explicit external allocator exclusion is REQUIRED through this interval.
 * No ISR allocation/mask; this is not a general concurrent-heap OOM fix.
 */
incoming_stock_validator:
 linkw %a6,#0
 lea %sp@(-16),%sp
 moveml %d2/%a2-%a4,%sp@
 moveal %a6@(8),%a2
 cmpal #ARENA,%a2
 bcs incoming_validator_bad
 cmpal #(ARENA_END-MAXIMUM),%a2
 bhi incoming_validator_bad
 movel %a2@,%d0
 cmpil #0xbeefbace,%d0
 bne incoming_validator_bad
 movel %a2@(4),%d0
 cmpil #6,%d0
 bne incoming_validator_bad
 moveal %a2,%a0
 addal #(STOCK_BYTES-4),%a0
 movel %a0@,%d0
 cmpil #0xbacef00c,%d0
 bne incoming_validator_bad
 pea STOCK_BYTES
 jsr 0x40080064
 addql #4,%sp
 tstl %d0
 beq incoming_validator_bad
 moveal %d0,%a3
 pea 16
 jsr 0x40080064
 addql #4,%sp
 moveal %d0,%a4
 cmpal #0,%a4
 beq incoming_validator_payload_release
incoming_validator_capacity:
 movel %a4,%sp@-
 jsr 0x4008026a
 addql #4,%sp
incoming_validator_payload_release:
 movel %a3,%sp@-
 jsr 0x4008026a
 addql #4,%sp
 cmpal #0,%a4
 beq incoming_validator_bad
incoming_validator_admitted:
 movel %a6@(16),%sp@-
 movel %a6@(12),%sp@-
 movel %a2,%sp@-
 jsr 0x4005d9f6
 lea %sp@(12),%sp
 bra incoming_validator_done
incoming_validator_bad:
 moveq #0,%d0
incoming_validator_done:
 moveml %sp@,%d2/%a2-%a4
 lea %sp@(16),%sp
 unlk %a6
 rts
