/* SPDX-License-Identifier: MIT
 * Copyright (c) 2026 Lachlan Fysh
 * Original authored source selected for review. re/tools/coldfire_emu/lfo_four_bank_detour_join.S; lines 1-124,131-154.
 * Unresolved integration bindings are documented in DEPENDENCIES.json.
 */
/* Software BANK ingress only. STACK96 is invocation-owned, no global token.
 * A published owner requires a ready context and exclusive writer admission.
 * Admission refusal returns new LFBR D0, restoring other inputs/SR/stack.
 * LFBR is a new BANK ABI result, never an interpretation of native D0.
 * External bank callers serialize against publication/teardown/stock observers.
 */
.text
.globl bank_detour,bank_stock_only,bank_rejected,bank_restore,stock_trampoline
bank_detour:
 lea %sp@(-96),%sp
 moveml %d0-%d7/%a0-%a6,%sp@
 movew %sr,%d0
 movew %d0,%sp@(60)
 clrw %sp@(82)           /* Native-returned marker, invocation-local only. */
 movel %sp@(104),%d0
 cmpil #96,%d0
 bcc bank_rejected
 moveal OWNER_SLOT,%a0
 tstl %a0
 beq bank_stock_only
 cmpal #0x40000000,%a0
 bcs bank_rejected
 cmpal #(0x48000000-6976),%a0
 bcc bank_rejected
 movel %a0,%d0
 andil #3,%d0
 bne bank_rejected
 movel %a0@,%d0
 cmpil #0x4c464f34,%d0
 bne bank_rejected
 movel %a0@(4),%d0
 cmpil #1,%d0
 bne bank_rejected
 /* Check leases even when context is missing/unready. No stock escape. */
 tstl %a0@(72)
 bne bank_rejected
 tstl %a0@(76)
 bne bank_rejected
 tstl %a0@(6440)
 bne bank_rejected
 tstl TRANSACTION_STATUS+4
 bne bank_rejected
 movel %a0@(40),%d0
 cmpl %sp@(100),%d0
 bne bank_rejected
 moveal CONTEXT_SLOT,%a1
 tstl %a1
 beq bank_rejected
 cmpal #0x40000000,%a1
 bcs bank_rejected
 cmpal #(0x48000000-CONTEXT_SIZE),%a1
 bcc bank_rejected
 movel %a1,%d0
 andil #3,%d0
 bne bank_rejected
 cmpal %a1@(4),%a0
 bne bank_rejected
 tstl %a1@(24)
 bne bank_rejected
 lea %sp@(64),%a0
 movel %a0,%sp@-        /* Sixth wrapper argument: native live-out snapshot. */
 movel %sp@(116),%sp@- /* flag2: entry SP+16 */
 movel %sp@(116),%sp@- /* flag1: entry SP+12 */
 movel %sp@(116),%sp@- /* bank: entry SP+8 */
 movel %sp@(116),%sp@- /* M: entry SP+4 */
 movel %a1,%sp@-
 /* Native gets original GPR/SR inputs; EMAC remains naturally live. */
 movew %sp@(84),%d0
 movew %d0,%sr
 moveml %sp@(24),%d0-%d7/%a0-%a6
 jsr NATIVE_JOIN
 lea %sp@(24),%sp
 tstl %d0
 beq bank_join_failed
bank_restore:
 /* Propagate tail writes from the native copy to ORIGINAL caller arguments. */
 movel %sp@(84),%d0
 movel %d0,%sp@(100)
 movel %sp@(88),%d0
 movel %d0,%sp@(104)
 movel %sp@(64),%d0
 movel %d0,%sp@
 movel %sp@(68),%d0
 movel %d0,%sp@(4)
 movel %sp@(72),%d0
 movel %d0,%sp@(32)
 movel %sp@(76),%d0
 movel %d0,%sp@(36)
 movew %sp@(80),%d0
 movew %d0,%sr
 moveml %sp@,%d0-%d7/%a0-%a6
 lea %sp@(96),%sp
 rts
bank_stock_only:
 movew %sp@(60),%d0
 movew %d0,%sr
 moveml %sp@,%d0-%d7/%a0-%a6
 lea %sp@(96),%sp
 jmp STOCK_TRAMPOLINE
bank_rejected:
 /* Pre-native admission failure: no leases acquired, bank/args untouched. */
 movel #BANK_REFUSED,%d0
 movel %d0,%sp@
 movew %sp@(60),%d0
 movew %d0,%sr
 moveml %sp@,%d0-%d7/%a0-%a6
 lea %sp@(96),%sp
 rts
bank_join_failed:
 /* Inner wrapper may have staged a failed flush or already executed stock.
  * These are FAILED results, not admission refusal or old-M rollback. */
 tstw %sp@(82)
 bne bank_native_failed
 movel #BANK_FAILED,%d0
 movel %d0,%sp@
 movew %sp@(60),%d0
 movew %d0,%sr
 moveml %sp@,%d0-%d7/%a0-%a6
 lea %sp@(96),%sp
 rts
bank_native_failed:
 movel #BANK_FAILED,%d0
 movel %d0,%sp@(64)
 bra bank_restore


/* Called immediately after native JSR, before cleanup/verification/lease end.
 * No BSR: those instructions would shift the native caller arguments. */
.macro snapshot_native
 moveml %d0-%d1/%a0-%a1,%a6@(-80)
 movew %sr,%d0
 movew %d0,%a6@(-64)
 moveal %a6@(28),%a0
 movel %a6@(-80),%d0
 movel %d0,%a0@
 movel %a6@(-76),%d0
 movel %d0,%a0@(4)
 movel %a6@(-72),%d0
 movel %d0,%a0@(8)
 movel %a6@(-68),%d0
 movel %d0,%a0@(12)
 movew %a6@(-64),%d0
 movew %d0,%a0@(16)
 movel %sp@,%d0
 movel %d0,%a0@(20)
 movel %sp@(4),%d0
 movel %d0,%a0@(24)
 moveq #1,%d0
 movew %d0,%a0@(18)
.endm
