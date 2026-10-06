/* SPDX-License-Identifier: MIT
 * Copyright (c) 2026 Lachlan Fysh
 * Original authored source selected for review. re/tools/coldfire_emu/live_profile_candidate/lookup.S; lines 1-212.
 * Unresolved integration bindings are documented in DEPENDENCIES.json.
 */
/* NEW explicit-context ABI, deliberately NOT a two-argument vtable method.
 * lookup_checked(O,M,E,b,t,ordinal), dst_edit_preflight(O,M,E,b,t,rawDST).
 * O is admitted/retained, M is retained stock control, b=0..2, t=0..5.
 * Caller owns writer72 or reader76; preflight requires writer72. Caller
 * excludes stock rebind/child destruction and holds the same context through
 * native lookup/list/edit/readback. No acquisition, release or config copy.
 * D0=native descriptor (including valid zero for lookup); D1=explicit status.
 * A0=stockEntry on success, zero on refusal. D2-D7/A2-A6, SP and entry SR
 * preserved. Supervisor ABI: reading/restoring SR is privileged. A1 scratch.
 * No writable static state. All object pointers must be readable/live as
 * promised by the caller; numeric checks cannot prove pointer lifetime.
 */
.text
/* Numeric nonwrap/admission prefixes, NOT full allocations. Actual retained
 * owner6976 and live M0x1400 spans/lifetimes are caller-owned contracts. */
.equ OWNER_BYTES,4688
.equ STOCK_BYTES,552
.equ CHILD_BYTES,100
.equ OK,0
.equ GEOMETRY,1
.equ OWNER_BINDING,2
.equ LEASE,3
.equ STOCK_BINDING,4
.equ PROFILE,5
.equ DOMAIN,6
.equ MISSING,7
.equ FILTER,8
.globl lookup_checked,dst_edit_preflight

/* Frame: -52..-13 callee saves, -12 SR word, -8 mode, -4 ordinal.
 * Capture SR before any flag-changing instruction, including mode setup.
 */
lookup_checked:
 linkw %a6,#-52
 moveml %d2-%d7/%a2-%a5,%sp@
 movew %sr,%d0
 movew %d0,%a6@(-12)
 clrl %a6@(-8)
 bra checked
dst_edit_preflight:
 linkw %a6,#-52
 moveml %d2-%d7/%a2-%a5,%sp@
 movew %sr,%d0
 movew %d0,%a6@(-12)
 moveq #1,%d0
 movel %d0,%a6@(-8)
checked:
 movel %a6@(8),%d2
 movel %a6@(12),%d3
 movel %a6@(20),%d4
 movel %a6@(24),%d5
 tstl %d2
 beq fail_geometry
 movel %d2,%d0
 andil #3,%d0
 bne fail_geometry
 cmpil #0x100000000-OWNER_BYTES,%d2
 bhi fail_geometry
 tstl %d3
 beq fail_geometry
 movel %d3,%d0
 andil #3,%d0
 bne fail_geometry
 cmpil #0x100000000-STOCK_BYTES,%d3
 bhi fail_geometry
 cmpil #3,%d4
 bcc fail_geometry
 cmpil #6,%d5
 bcc fail_geometry
 moveal %d2,%a2
 moveal %d3,%a3
 movel %a2@,%d0
 cmpil #0x4c464f34,%d0
 bne fail_owner
 movel %a2@(4),%d0
 cmpil #1,%d0
 bne fail_owner
 cmpal %a2@(40),%a3
 bne fail_owner
 /* A held lease is evidence of protocol state, not proof of who holds it. */
 movel %a2@(72),%d0
 cmpil #1,%d0
 beq writer_lease
 tstl %d0
 bne fail_lease
 tstl %a6@(-8)
 bne fail_lease
 movel %a2@(76),%d0
 cmpil #1,%d0
 bne fail_lease
 bra geometry
writer_lease:
 tstl %a2@(76)
 bne fail_lease
geometry:
 movel %d4,%d6
 movel #768,%d1
 mulul %d1,%d6
 movel %d5,%d0
 lsll #3,%d0
 addl %d6,%d0
 addil #680,%d0
 lea %a2@(0,%d0:l),%a5
 cmpal %a6@(16),%a5
 bne fail_geometry
 /* Exact owned regional: O+272+768*b+68*t, not a guessed bank base. */
 movel %d5,%d0
 moveq #68,%d1
 mulul %d1,%d0
 addl %d6,%d0
 addil #272,%d0
 lea %a2@(0,%d0:l),%a0
 cmpal %a5@(4),%a0
 bne fail_geometry
 lea %a2@(80),%a0
 cmpal %a5@,%a0
 bne fail_geometry
 movel %d5,%d0
 lsll #3,%d0
 addil #504,%d0
 lea %a3@(0,%d0:l),%a4
 movel %d5,%d0
 moveq #68,%d1
 mulul %d1,%d0
 lea %a3@(96,%d0:l),%a0
 cmpal %a4@(4),%a0
 bne fail_binding
 movel %a0@,%d0
 cmpil #0x400fef54,%d0
 bne fail_binding
 movel 0x400fef7c,%d0
 cmpil #0x400d5632,%d0
 bne fail_binding
 moveal %a4@(4),%a0
 movel %a0@(16),%d7
 beq fail_binding
 movel %d7,%d0
 /* Native bank stride0x1bb6 admits even, not necessarily long-aligned
  * Sound records. Only the signed profile byte is read below. */
 andil #1,%d0
 bne fail_binding
 cmpil #0x100000000-CHILD_BYTES,%d7
 bhi fail_binding
 moveal %d7,%a0
 mvsb %a0@(38),%d0
 cmpil #6,%d0
 bcc fail_profile
 movel %a6@(28),%d0
 tstl %a6@(-8)
 beq ordinal_input
 /* Native C140 uses signed ASR8. Admit its enumerated 0..32 domain;
  * low fractional byte is intentionally accepted, never rewritten. */
 cmpil #0x20ff,%d0
 bhi fail_domain
 asrl #8,%d0
ordinal_input:
 cmpil #33,%d0
 bcc fail_domain
 movel %d0,%a6@(-4)
 movel %d0,%sp@-
 movel %a4,%sp@-
 /* The only original lookup target. No overlay or replacement body. */
 jsr 0x4000a830
 addql #8,%sp
 movel %d0,%d6
 tstl %a6@(-8)
 beq success
 tstl %d6
 beq fail_missing
 movel %d6,%sp@-
 jsr 0x4005a85e
 addql #4,%sp
 notl %d0
 andil #0x600,%d0
 bne fail_filter
success:
 movel %d6,%d0
 moveq #OK,%d1
 moveal %a4,%a0
 bra finish
fail_geometry:
 moveq #GEOMETRY,%d1
 bra refused
fail_owner:
 moveq #OWNER_BINDING,%d1
 bra refused
fail_lease:
 moveq #LEASE,%d1
 bra refused
fail_binding:
 moveq #STOCK_BINDING,%d1
 bra refused
fail_profile:
 moveq #PROFILE,%d1
 bra refused
fail_domain:
 moveq #DOMAIN,%d1
 bra refused
fail_missing:
 moveq #MISSING,%d1
 bra refused
fail_filter:
 moveq #FILTER,%d1
refused:
 moveq #0,%d0
 subal %a0,%a0
finish:
 movew %a6@(-12),%d7
 movew %d7,%sr
 moveml %sp@,%d2-%d7/%a2-%a5
 unlk %a6
 rts
