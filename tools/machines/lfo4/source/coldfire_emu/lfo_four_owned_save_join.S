/* SPDX-License-Identifier: MIT
 * Copyright (c) 2026 Lachlan Fysh
 * Original authored source selected for review. re/tools/coldfire_emu/lfo_four_owned_save_join.S; lines 1-112.
 * Unresolved integration bindings are documented in DEPENDENCIES.json.
 */
/* Emulator-linked operation, NOT a firmware installation hook.
 * save_owned(manager, ctx, slot0..95, bypass_byte, progress) -> native writer
 * status0..4 or LFSR/LFOM/LFSE/LFSC. External caller serializes Project edits,
 * publication and teardown throughout the operation. No ISR allocation.
 * One exact MAXIMUM request remains owned until the synchronous writer returns.
 * No cache append, slack borrowing, retained global pointer or async lifetime.
 */
.text
.globl save_owned,save_owned_allocated,save_owned_encoded,save_owned_sealed
.globl save_owned_written,save_owned_cleanup,save_owned_released
save_owned:
 linkw %a6,#0
 lea %sp@(-40),%sp
 moveml %d2-%d7/%a2-%a5,%sp@
 moveal %a6@(12),%a2
 cmpal #ARENA,%a2
 bcs owned_refused
 cmpal #(ARENA_END-CONTEXT_BYTES),%a2
 bhi owned_refused
 movel %a2,%d0
 andil #3,%d0
 bne owned_refused
 movel %a2@,%d0
 cmpil #0x4c465347,%d0
 bne owned_refused
 tstl %a2@(24)
 bne owned_refused
 moveal %a2@(4),%a0
 cmpal OWNER_SLOT,%a0
 bne owned_refused
 movel %a0,%d0
 beq owned_refused
 moveal %a2@(8),%a3
 cmpal #ROOT,%a3
 bne owned_refused
 cmpal ROOT_BINDER,%a3
 bne owned_refused
 movel %a6@(16),%d0
 cmpil #96,%d0
 bcc owned_refused
 jsr VERIFY_CURRENT
 cmpl %a2@(20),%d0
 bne owned_refused
 pea MAXIMUM
 jsr 0x40080064
 addql #4,%sp
 tstl %d0
 beq owned_nomem
 moveal %d0,%a4
save_owned_allocated:
 /* Every transmitted byte has a guest producer, including unused wire tail. */
 pea MAXIMUM
 clrl %sp@-
 movel %a4,%sp@-
 jsr 0x4008f238
 lea %sp@(12),%sp
 movel %a6@(24),%sp@-
 pea -1
 clrl %sp@-
 movel %a3,%sp@-
 movel %a4,%sp@-
 jsr 0x4005d18a
 lea %sp@(20),%sp
 tstb %d0
 beq owned_encode_failed
save_owned_encoded:
 /* Sixth argument pins the actual allocation base in the codec's frame. */
 movel %a4,%sp@-
 pea WIRE_MAX
 moveal %a4,%a0
 addal #STOCK_BYTES,%a0
 movel %a0,%sp@-
 pea STOCK_BYTES
 movel %a4,%sp@-
 movel %a2,%sp@-
 jsr OWNED_CODEC_SAVE
 lea %sp@(24),%sp
 tstl %d0
 beq owned_codec_failed
save_owned_sealed:
 movel %a6@(24),%sp@-
 movel %a6@(20),%sp@-
 movel %a6@(16),%sp@-
 movel %a4,%sp@-
 movel %a6@(8),%sp@-
 jsr 0x4008d712
 lea %sp@(20),%sp
save_owned_written:
 movel %d0,%d6
 bra save_owned_cleanup
owned_encode_failed:
 movel #0x4c465345,%d6
 bra save_owned_cleanup
owned_codec_failed:
 movel #0x4c465343,%d6
save_owned_cleanup:
 movel %a4,%sp@-
 jsr 0x4008026a
 addql #4,%sp
save_owned_released:
 movel %d6,%d0
 bra owned_done
owned_nomem:
 movel #0x4c464f4d,%d0
 bra owned_done
owned_refused:
 movel #0x4c465352,%d0
owned_done:
 moveml %sp@,%d2-%d7/%a2-%a5
 lea %sp@(40),%sp
 unlk %a6
 rts
