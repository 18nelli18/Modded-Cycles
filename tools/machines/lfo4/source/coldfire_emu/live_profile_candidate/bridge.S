/* SPDX-License-Identifier: MIT
 * Copyright (c) 2026 Lachlan Fysh
 * Original authored source selected for review. re/tools/coldfire_emu/live_profile_candidate/bridge.S; lines 1-57.
 * Unresolved integration bindings are documented in DEPENDENCIES.json.
 */
/* Explicit prototype bridge, no mutable context or guessed original target.
 * lookup_bridge(O,M,E,b,t,ordinal) creates a call of the native +34 SHAPE
 * lookup_callback(entry,ordinal), with retained context behind its two args.
 * This is NOT installed in a live vtable. A bare two-argument invocation from
 * elsewhere refuses before reading hidden context. Future integration must
 * provide an equivalent admitted caller bridge for every native list lookup.
 */
.text
.equ BRIDGE,9
.globl lookup_bridge,lookup_callback
lookup_bridge:
 linkw %a6,#-32
 moveml %d2,%a6@(-4)
 movew %sr,%d2
 movew %d2,%a6@(-8)
 /* callback stack: return,E,ordinal,O,M,b,t */
 movel %a6@(16),%sp@
 movel %a6@(28),%sp@(4)
 movel %a6@(8),%sp@(8)
 movel %a6@(12),%sp@(12)
 movel %a6@(20),%sp@(16)
 movel %a6@(24),%sp@(20)
 bsr lookup_callback
bridge_return:
 movew %a6@(-8),%d2
 movew %d2,%sr
 moveml %a6@(-4),%d2
 unlk %a6
 rts
lookup_callback:
 linkw %a6,#-32
 moveml %d2,%a6@(-4)
 movew %sr,%d2
 movew %d2,%a6@(-8)
 /* The return label is relative to this NEW component, not a firmware PC. */
 lea bridge_return(%pc),%a0
 cmpal %a6@(4),%a0
 bne bridge_refused
 /* Reorder explicit stack context into checked six-argument ABI. */
 movel %a6@(16),%sp@
 movel %a6@(20),%sp@(4)
 movel %a6@(8),%sp@(8)
 movel %a6@(24),%sp@(12)
 movel %a6@(28),%sp@(16)
 movel %a6@(12),%sp@(20)
 bsr lookup_checked
 bra callback_done
bridge_refused:
 moveq #0,%d0
 moveq #BRIDGE,%d1
 subal %a0,%a0
callback_done:
 movew %a6@(-8),%d2
 movew %d2,%sr
 moveml %a6@(-4),%d2
 unlk %a6
 rts
