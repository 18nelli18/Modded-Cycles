/* SPDX-License-Identifier: MIT
 * Copyright (c) 2026 Lachlan Fysh
 * Original authored source selected for review. re/tools/coldfire_emu/lfo_four_menu_retirement_join.S; lines 1-10.
 * Unresolved integration bindings are documented in DEPENDENCIES.json.
 */
/* Diagnostic ABI adapter ONLY. No destruction hook or capture retirement.
 * borrow_row(menu,index,result): stock hidden aggregate result is in A0.
 * Original 4007292a copies BOTH shared_ptr words and increments strong count.
 * Do not substitute an imagined vtable target or clear the lifetime registry.
 */
.text
.globl borrow_row
borrow_row:
 moveal %sp@(12),%a0
 jmp 0x4007292a
