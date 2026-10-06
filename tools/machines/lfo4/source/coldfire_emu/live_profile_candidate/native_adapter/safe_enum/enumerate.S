/* SPDX-License-Identifier: MIT
 * Copyright (c) 2026 Lachlan Fysh
 * Original authored source selected for review. re/tools/coldfire_emu/live_profile_candidate/native_adapter/safe_enum/enumerate.S; lines 1-156.
 * Unresolved integration bindings are documented in DEPENDENCIES.json.
 */
/* safe_enum(E, owned_words, capacity_words): three longword stack arguments.
 * Success D0=count (0..33), D1=0; refusal D0=0, D1=native status or 13/14/15.
 * No list/header/publication. Scratch may be dirty on refusal; never consume it.
 * Caller retains exclusive writable capacity span and all native retained
 * objects, holds reader/writer lease, excludes rebind/profile/table mutation,
 * destruction/reset/unpublication through enumeration AND consumption.
 * Numeric checks do not prove mapping/lifetime. Supervisor ABI; preserves
 * D2-D7/A2-A6, entry SR, input slots and stack; D0/D1/A0/A1 scratch.
 * Assemble after unchanged lookup.S and adapter.S. MAIN_BYTES exact binding.
 */
.text
.globl safe_enum,safe_enum_end,se_lookup,se_flags,se_store
.macro se_guard start,size
 movel #\start,%d0
 movel #\size,%d1
 bsr se_overlap
 tstl %d0
 bne se_alias
.endm
safe_enum:
 linkw %a6,#-64
 moveml %d2-%d7/%a2-%a5,%a6@(-40)
 movew %sr,%d0
 movew %d0,%a6@(-44)
 movel %a6@(12),%d2
 beq se_buffer
 movel %d2,%d0
 andil #3,%d0
 bne se_buffer
 movel %a6@(16),%d3
 cmpil #33,%d3
 bcs se_capacity
 cmpil #0x3fffffff,%d3
 bhi se_buffer
 lsll #2,%d3
 addl %d2,%d3
 bcs se_buffer
 moveal %d2,%a2
 moveq #0,%d4
 moveq #0,%d5
 movel %a6@(8),%sp@
 movel %d4,%sp@(4)
 bsr native_lookup
 tstl %d1
 bne se_refuse
 movel %d0,%d7
 /* Only read admitted native pointees after genuine lookup admission. */
 movel OWNER_SLOT,%d0
 movel #NA_OWNER_BYTES,%d1
 bsr se_overlap
 tstl %d0
 bne se_alias
 moveal OWNER_SLOT,%a0
 movel %a0@(40),%d0
 movel #NA_M_BYTES,%d1
 bsr se_overlap
 tstl %d0
 bne se_alias
 movel CONTEXT_SLOT,%d0
 movel #NA_CONTEXT_BYTES,%d1
 bsr se_overlap
 tstl %d0
 bne se_alias
 moveal CONTEXT_SLOT,%a0
 movel %a0@(8),%d0
 movel #NA_ROOT_BYTES,%d1
 bsr se_overlap
 tstl %d0
 bne se_alias
 se_guard OWNER_SLOT,4
 se_guard RUNTIME_SLOT,4
 se_guard BOOT_STATUS,8
 se_guard CONTEXT_SLOT,4
 se_guard ROOT_BINDER,4
 se_guard 0x40000400,MAIN_BYTES
 /* Original materializer lookup tables, 33+48 longwords. */
 se_guard 0x40a79394,324
 lea lookup_checked(%pc),%a0
 lea safe_enum_end(%pc),%a1
 movel %a0,%d0
 movel %a1,%d1
 subl %d0,%d1
 bsr se_overlap
 tstl %d0
 bne se_alias
 /* Includes input slots and conservative nested call stack (256 bytes
  * below frame base); this helper's checked closure needs less than that. */
 movel %sp,%d0
 subil #256,%d0
 bcs se_buffer
 movel %a6,%d1
 addil #20,%d1
 bcs se_buffer
 subl %d0,%d1
 bsr se_overlap
 tstl %d0
 bne se_alias
 bra se_filter
se_lookup:
 movel %a6@(8),%sp@
 movel %d4,%sp@(4)
 bsr native_lookup
 tstl %d1
 bne se_refuse
 movel %d0,%d7
se_filter:
 tstl %d7
 beq se_next
 movel %d7,%sp@
se_flags:
 jsr 0x4005a85e
 notl %d0
 andil #0x600,%d0
 bne se_next
se_store:
 movel %d7,%a2@+
 addql #1,%d5
se_next:
 addql #1,%d4
 cmpil #33,%d4
 bcs se_lookup
 movel %d5,%d0
 moveq #0,%d1
 bra se_done
se_capacity:
 moveq #13,%d1
 bra se_refuse
se_buffer:
 moveq #14,%d1
 bra se_refuse
se_alias:
 moveq #15,%d1
se_refuse:
 moveq #0,%d0
se_done:
 movew %a6@(-44),%d6
 movew %d6,%sr
 moveml %a6@(-40),%d2-%d7/%a2-%a5
 unlk %a6
 rts
/* d0=start, d1=length of previously validated retained span. No memory
 * access. d2/d3 are output half-open endpoints. Carry permits end==2^32. */
se_overlap:
 addl %d0,%d1
 bcs se_overlap_top
 cmpl %d1,%d2
 bcc se_disjoint
se_overlap_top:
 cmpl %d0,%d3
 bls se_disjoint
 moveq #1,%d0
 rts
se_disjoint:
 moveq #0,%d0
 rts
safe_enum_end:
