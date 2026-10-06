/* SPDX-License-Identifier: MIT
 * Copyright (c) 2026 Lachlan Fysh
 * Original authored source selected for review. re/tools/coldfire_emu/lfo_four_clear_shim.S; lines 1-32,34-36.
 * Unresolved integration bindings are documented in DEPENDENCIES.json.
 */
/* Authored standalone clear-call wrapper, emulator construction proof only.
 * The six-byte absolute JSR at40000530 replaces stock PC-relative JSR plus
 * the first word of the next LEA. Its return40000536 must not be executed.
 * Clear all stock BSS except the declared owned blob, replay the full LEA,
 * discard that return word, then resume4000053a with the original caller SP.
 * No cache/control-register/MMIO operations in this component.
 */
.text
.globl entry,prefix_loop,tail_loop,resume
entry:
 lea %sp@(-16),%sp
 moveml %d4-%d7,%sp@
 moveal #0x4019b590,%a0
 movel #(BLOB_START-0x4019b590)/16,%d1
 clrl %d4
 clrl %d5
 clrl %d6
 clrl %d7
prefix_loop:
 moveml %d4-%d7,%a0@
 lea %a0@(16),%a0
 subql #1,%d1
 bnes prefix_loop
 moveal #BLOB_END,%a0
 movel #(0x423380b0-BLOB_END)/16,%d1
tail_loop:
 moveml %d4-%d7,%a0@
 lea %a0@(16),%a0
 subql #1,%d1
 bnes tail_loop
 moveml %sp@,%d4-%d7
 lea %sp@(16),%sp


 addql #4,%sp
resume:
 jmp 0x4000053a
