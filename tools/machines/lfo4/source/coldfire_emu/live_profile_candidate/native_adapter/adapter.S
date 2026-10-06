/* SPDX-License-Identifier: MIT
 * Copyright (c) 2026 Lachlan Fysh
 * Original authored source selected for review. re/tools/coldfire_emu/live_profile_candidate/native_adapter/adapter.S; lines 1-259.
 * Unresolved integration bindings are documented in DEPENDENCIES.json.
 */
/* Genuine native +0x34(E,ordinal). Only two longword input arguments.
 * OWNER_SLOT/RUNTIME_SLOT/BOOT_STATUS/CONTEXT_SLOT/ROOT_BINDER are declared
 * readable publication locations, supplied as assembler constants. No storage
 * is defined here. No caller PC, implicit GPR owner, or trailing args are used.
 * Published O, context, full M and root are RETAINED caller preconditions.
 * Numeric spans/tags/lease words cannot prove allocation, lifetime or task.
 * Caller already owns the lease and excludes stock rebind/profile changes,
 * destruction, table changes, unpublication and reset through the transaction.
 * Calls unchanged lookup_checked(O,M,E,b,t,ordinal); no lease acquisition.
 * D0=descriptor (zero may be valid unavailable), D1=status, A0=stock entry.
 * Refusal D0=A0=0. D2-D7/A2-A6, input slots, SP and entry SR preserved.
 * Supervisor ABI, A1 scratch. Native enum/formatter callers IGNORE D1:
 * this is NOT an installation-ready edit/list/formatter safety closure.
 */
.text
.equ NA_OWNER_BYTES,6976
.equ NA_M_BYTES,0x1400
.equ NA_CONTEXT_BYTES,698992
.equ NA_ROOT_BYTES,0x37615c
.equ NA_BANK_BASE,0x2cfc5c
.equ NA_BANK_STRIDE,0x1bb6
.equ NA_PUBLICATION,10
.equ NA_READY,11
.equ NA_CURRENT_BANK,12
.if NA_BANK_BASE+96*NA_BANK_STRIDE > NA_ROOT_BYTES
.error "native bank array exceeds retained root"
.endif
.globl native_lookup,native_lookup_call,native_lookup_end
.globl na_geometry_admitted,na_lease_admitted,na_stock_admitted
/* -44..-21 outgoing six args; -20..-19 SR; -18..-17 unused;
 * -16..-1 saved D2/D3/A2/A3. BSR return is -48..-45, BELOW the frame.
 * LINK and MOVEM do not change CCR: capture SR before the first flag write.
 */
native_lookup:
 linkw %a6,#-44
 moveml %d2-%d3/%a2-%a3,%a6@(-16)
 movew %sr,%d2
 movew %d2,%a6@(-20)
 movel %a6@(12),%d0
 cmpil #33,%d0
 bcc na_bad_domain
 movel %d0,%sp@(20)
 tstl BOOT_STATUS+4
 bne na_bad_publication
 movel OWNER_SLOT,%d2
 beq na_bad_publication
 cmpl BOOT_STATUS,%d2
 bne na_bad_publication
 movel %d2,%d0
 andil #3,%d0
 bne na_bad_geometry
 cmpil #0x100000000-NA_OWNER_BYTES,%d2
 bhi na_bad_geometry
 /* Reject every E outside the 18 exact addresses before *E or *O. */
 movel %a6@(8),%d0
 subl %d2,%d0
 bcs na_bad_geometry
 subil #680,%d0
 bcs na_bad_geometry
 moveq #0,%d3
na_bank_decode:
 cmpil #768,%d0
 bcs na_track_decode
 subil #768,%d0
 addql #1,%d3
 cmpil #3,%d3
 bcc na_bad_geometry
 bra na_bank_decode
na_track_decode:
 cmpil #40,%d0
 bhi na_bad_geometry
 movel %d0,%d1
 andil #7,%d1
 bne na_bad_geometry
 lsrl #3,%d0
 movel %d0,%sp@(16)
 movel %d3,%sp@(12)
 movel %a6@(8),%sp@(8)
 movel %d2,%sp@
 /* Recompute exact E as an independent final alias equality. */
 lsll #3,%d0
 movel #768,%d1
 mulul %d1,%d3
 addl %d3,%d0
 addil #680,%d0
 addl %d2,%d0
 cmpl %a6@(8),%d0
 bne na_bad_geometry
na_geometry_admitted:
 moveal %d2,%a2
 movel %a2@,%d0
 cmpil #0x4c464f34,%d0
 bne na_bad_owner
 movel %a2@(4),%d0
 cmpil #1,%d0
 bne na_bad_owner
 cmpal %a2@(6444),%a2
 bne na_bad_owner
 movel %a2@(6448),%d0
 cmpil #0x524e4731,%d0
 bne na_bad_owner
 tstl %a2@(6440)
 bne na_bad_owner
 lea %a2@(4400),%a0
 cmpal RUNTIME_SLOT,%a0
 bne na_bad_publication
 movel %a2@(72),%d0
 cmpil #1,%d0
 beq na_writer
 tstl %d0
 bne na_bad_lease
 movel %a2@(76),%d0
 cmpil #1,%d0
 bne na_bad_lease
 bra na_lease_admitted
na_writer:
 tstl %a2@(76)
 bne na_bad_lease
na_lease_admitted:
 moveal %a6@(8),%a0
 lea %a2@(80),%a1
 cmpal %a0@,%a1
 bne na_bad_geometry
 movel %sp@(16),%d0
 moveq #68,%d1
 mulul %d1,%d0
 addl %d3,%d0
 addil #272,%d0
 lea %a2@(0,%d0:l),%a1
 cmpal %a0@(4),%a1
 bne na_bad_geometry
 /* Validate the selected routing/config aliases, not mutable selection. */
 lea %a2@(176),%a0
 lea %a0@(0,%d3:l),%a0
 movel %sp@(12),%d0
 cmpal %a2@(44,%d0:l:4),%a0
 bne na_bad_geometry
 movel %d0,%d1
 movel #640,%d0
 mulul %d0,%d1
 lea %a2@(2508),%a0
 lea %a0@(0,%d1:l),%a0
 movel %sp@(12),%d0
 cmpal %a2@(56,%d0:l:4),%a0
 bne na_bad_geometry
 movel %a2@(40),%d0
 beq na_bad_geometry
 movel %d0,%d1
 andil #3,%d1
 bne na_bad_geometry
 cmpil #0x100000000-NA_M_BYTES,%d0
 bhi na_bad_geometry
 moveal %d0,%a3
 movel %d0,%sp@(4)
 movel %a3@,%d0
 cmpil #0x400fcf3c,%d0
 bne na_bad_stock
 /* Slots themselves and their pointees must be retained/readable. */
 movel CONTEXT_SLOT,%d0
 beq na_bad_ready
 movel %d0,%d1
 andil #15,%d1
 bne na_bad_ready
 cmpil #0x100000000-NA_CONTEXT_BYTES,%d0
 bhi na_bad_ready
 moveal %d0,%a0
 movel %a0@,%d0
 cmpil #0x4c465347,%d0
 bne na_bad_ready
 cmpal %a0@(4),%a2
 bne na_bad_ready
 cmpal %a0@(12),%a3
 bne na_bad_ready
 tstl %a0@(24)
 bne na_bad_ready
 movel %a0@(8),%d0
 beq na_bad_bank
 movel %d0,%d1
 andil #3,%d1
 bne na_bad_bank
 cmpil #0x100000000-NA_ROOT_BYTES,%d0
 bhi na_bad_bank
 cmpl ROOT_BINDER,%d0
 bne na_bad_bank
 addil #NA_BANK_BASE,%d0
 cmpl %a3@(16),%d0
 bne na_bad_bank
 movel %a3@(68),%d1
 cmpil #96,%d1
 bcc na_bad_bank
 movel #NA_BANK_STRIDE,%d3
 mulul %d3,%d1
 addl %d1,%d0
 movel %sp@(16),%d1
 moveq #100,%d3
 mulul %d3,%d1
 addl %d1,%d0
 addil #28,%d0
 /* Expected child is inside the retained root, not an old aggregate. */
 movel %sp@(16),%d1
 moveq #68,%d3
 mulul %d3,%d1
 lea %a3@(96,%d1:l),%a1
 cmpl %a1@(16),%d0
 bne na_bad_bank
 movel %a1@,%d0
 cmpil #0x400fef54,%d0
 bne na_bad_stock
 movel 0x400fef7c,%d0
 cmpil #0x400d5632,%d0
 bne na_bad_stock
 movel %sp@(16),%d0
 lsll #3,%d0
 addil #504,%d0
 lea %a3@(0,%d0:l),%a0
 cmpal %a0@(4),%a1
 bne na_bad_stock
 movel %a0@,%d0
 cmpil #0x400fd134,%d0
 bne na_bad_stock
na_stock_admitted:
 /* Checked source remains unchanged; it guards current signed profile and
  * forwards through the original two-argument stock lookup ABI. */
native_lookup_call:
 bsr lookup_checked
 bra na_done
na_bad_geometry:
 moveq #GEOMETRY,%d1
 bra na_refused
na_bad_owner:
 moveq #OWNER_BINDING,%d1
 bra na_refused
na_bad_lease:
 moveq #LEASE,%d1
 bra na_refused
na_bad_stock:
 moveq #STOCK_BINDING,%d1
 bra na_refused
na_bad_domain:
 moveq #DOMAIN,%d1
 bra na_refused
na_bad_publication:
 moveq #NA_PUBLICATION,%d1
 bra na_refused
na_bad_ready:
 moveq #NA_READY,%d1
 bra na_refused
na_bad_bank:
 moveq #NA_CURRENT_BANK,%d1
na_refused:
 moveq #0,%d0
 subal %a0,%a0
na_done:
 movew %a6@(-20),%d2
 movew %d2,%sr
 moveml %a6@(-16),%d2-%d3/%a2-%a3
 unlk %a6
 rts
native_lookup_end:
