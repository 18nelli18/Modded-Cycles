/* SPDX-License-Identifier: MIT
 * Copyright (c) 2026 Lachlan Fysh
 * Original authored source selected for review. re/tools/coldfire_emu/lfo_four_full_native_bank_join.S; lines 1-14.
 * Unresolved integration bindings are documented in DEPENDENCIES.json.
 */
/* New full/native-bank composition interface, no new wrapper algorithm.
 * Preceded by immutable full-derived guest and immutable native-bank wrapper.
 * This profile supports all6720 canonical keys and a698992B context request.
 * native_bank_join executes ORIGINAL40009a1e with its original callbacks.
 * Neither a factory/startup hook nor media transport is installed here.
 */
.if CAPACITY != 6720
.error "full/native bank join requires linked capacity6720"
.endif
.if SIZE != 698992
.error "full/native bank join requires the accepted full context layout"
.endif
.globl full_native_bank_join
.set full_native_bank_join,native_bank_join
