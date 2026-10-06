/* SPDX-License-Identifier: MIT
 * Copyright (c) 2026 Lachlan Fysh
 * Original authored source selected for review. re/tools/coldfire_emu/lfo_four_production_backing.S; lines 1-14.
 * Unresolved integration bindings are documented in DEPENDENCIES.json.
 */
/* NEW admission rule, not a firmware image. create's owner/M bounds and
 * installed-parent checks execute first. Require the original logical-root
 * binder and the original parent bank-array binding to agree, before calloc.
 * Fixed production root, NOT an anonymous RAM interval or an allocation hole.
 */
 cmpal #0x406fa024,%a4
 bne create_bad
 cmpal 0x404d2974,%a4
 bne create_bad
 moveal %a4,%a0
 addal #0x2cfc5c,%a0
 cmpal %a5@(16),%a0
 bne create_bad
