/* SPDX-License-Identifier: MIT
 * Copyright (c) 2026 Lachlan Fysh
 * Original authored source selected for review. re/tools/coldfire_emu/lfo_four_project_load_continuation.S; lines 1-39.
 * Unresolved integration bindings are documented in DEPENDENCIES.json.
 */
/* Emulator-only synchronous begin gate; no installation hook or firmware.
 * Caller owns live ctx, serializes stock/UI/allocator work, and retains input.
 * Flush outgoing configuration before stock mutation, then hold existing writer
 * lease and mark outgoing context unavailable. Never publish incoming here.
 */
.text
.globl switch_begin,switch_closed,switch_failed
switch_begin:
 linkw %a6,#-40
 moveml %d2-%d7/%a2-%a5,%sp@
 moveal %a6@(8),%a2
 tstl %a2
 beq switch_failed
 cmpal LIVE_CONTEXT_SLOT,%a2
 bne switch_failed
 movel %a2@,%d0
 cmpil #0x4c465347,%d0
 bne switch_failed
 tstl %a2@(24)
 bne switch_failed
 jsr WRITE_BEGIN
 tstl %d0
 beq switch_failed
 jsr FLUSH
 tstl %d0
 beq switch_flush_failed
 jsr COMMIT
 moveq #1,%d0
 movel %d0,%a2@(24)
switch_closed:
 bra switch_done
switch_flush_failed:
 jsr WRITE_END
switch_failed:
 moveq #0,%d0
switch_done:
 moveml %a6@(-40),%d2-%d7/%a2-%a5
 unlk %a6
 rts
