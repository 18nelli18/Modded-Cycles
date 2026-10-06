/* SPDX-License-Identifier: MIT
 * Copyright (c) 2026 Lachlan Fysh
 * Original authored source selected for review. re/tools/coldfire_emu/live_profile_candidate/native_adapter/dst_consumer/consumer.S; lines 1-403.
 * Unresolved integration bindings are documented in DEPENDENCIES.json.
 */
/* Private copied Entry vtable only. Retained constructor-owned O/M/context/root,
 * caller-held lease and transaction-wide exclusion remain preconditions.
 * No allocation, global scratch, exception recovery, or stock Entry changes.
 * D0=value/bool, D1=status; D2-D7/A2-A6 and SR preserved on authored paths.
 * Non-DST paths tail the exact original methods and keep their original ABI.
 */
.text
.globl dc_register_publish,dc_get,dc_detent,dc_calc,dc_validate,dc_edit,consumer_end
.globl dc_canonical_call,dc_refused_edit
dc_register_publish:
 /* Replaces only the authored publish pair, after all constructors succeeded.
  * A2 is unpublished O; no allocation or failure after installing methods. */
 lea %sp@(-12),%sp
 moveml %d0/%a0,%sp@(4)
 movew %sr,%d0
 movel %d0,%sp@
 lea dc_calc(%pc),%a0
 movel %a0,%a2@(100)
 lea dc_validate(%pc),%a0
 movel %a0,%a2@(104)
 lea dc_edit(%pc),%a0
 movel %a0,%a2@(112)
 lea native_lookup(%pc),%a0
 movel %a0,%a2@(132)
 movel %sp@,%d0
 movew %d0,%sr
 moveml %sp@(4),%d0/%a0
 lea %sp@(12),%sp
 /* Exact displaced authored operations; MOVE's final CCR is intentional. */
 movel %a2,OWNER_SLOT
 movel %a2,%d0
 jmp PUBLISH_CONTINUATION

/* dc_get(E): independently admits private storage without requiring a valid
 * current stock profile. Failure never dereferences a malformed E/child.
 * D0=signed original getter result, D1=status, D2.. preserved. */
dc_get:
 linkw %a6,#-36
 moveml %d2-%d3/%a2-%a3,%a6@(-16)
 movew %sr,%d0
 movew %d0,%a6@(-20)
 moveq #10,%d1
 tstl BOOT_STATUS+4
 bne dc_get_fail
 movel OWNER_SLOT,%d2
 beq dc_get_fail
 cmpl BOOT_STATUS,%d2
 bne dc_get_fail
 moveq #1,%d1
 movel %d2,%d0
 andil #3,%d0
 bne dc_get_fail
 cmpil #0x100000000-NA_OWNER_BYTES,%d2
 bhi dc_get_fail
 movel %a6@(8),%d0
 subl %d2,%d0
 bcs dc_get_fail
 subil #680,%d0
 bcs dc_get_fail
 moveq #0,%d3
dc_get_bank:
 cmpil #768,%d0
 bcs dc_get_track
 subil #768,%d0
 addql #1,%d3
 cmpil #3,%d3
 bcc dc_get_fail
 bra dc_get_bank
dc_get_track:
 cmpil #40,%d0
 bhi dc_get_fail
 movel %d0,%d1
 andil #7,%d1
 bne dc_get_geometry
 lsrl #3,%d0
 movel %d0,%a6@(-24)
 moveal %d2,%a2
 moveq #2,%d1
 movel %a2@,%d0
 cmpil #0x4c464f34,%d0
 bne dc_get_fail
 movel %a2@(4),%d0
 cmpil #1,%d0
 bne dc_get_fail
 cmpal %a2@(6444),%a2
 bne dc_get_fail
 movel %a2@(6448),%d0
 cmpil #0x524e4731,%d0
 bne dc_get_fail
 tstl %a2@(6440)
 bne dc_get_fail
 lea %a2@(4400),%a0
 cmpal RUNTIME_SLOT,%a0
 bne dc_get_publication
 moveq #3,%d1
 movel %a2@(72),%d0
 cmpil #1,%d0
 beq dc_get_writer
 tstl %d0
 bne dc_get_fail
 movel %a2@(76),%d0
 cmpil #1,%d0
 bne dc_get_fail
 bra dc_get_lease
dc_get_writer:
 tstl %a2@(76)
 bne dc_get_fail
dc_get_lease:
 moveq #1,%d1
 moveal %a6@(8),%a3
 lea %a2@(80),%a0
 cmpal %a3@,%a0
 bne dc_get_fail
 movel %d3,%d0
 movel #768,%d1
 mulul %d1,%d0
 movel %a6@(-24),%d2
 moveq #68,%d1
 mulul %d1,%d2
 addl %d2,%d0
 addil #272,%d0
 lea %a2@(0,%d0:l),%a0
 moveq #1,%d1
 cmpal %a3@(4),%a0
 bne dc_get_fail
 movel %a0@,%d0
 cmpil #0x400fef54,%d0
 bne dc_get_fail
 movel 0x400fef7c,%d0
 cmpil #0x400d5632,%d0
 bne dc_get_fail
 movel #640,%d1
 mulul %d1,%d3
 movel %a6@(-24),%d2
 moveq #100,%d1
 mulul %d1,%d2
 addl %d2,%d3
 addil #2508,%d3
 lea %a2@(0,%d3:l),%a1
 moveq #1,%d1
 cmpal %a0@(16),%a1
 bne dc_get_fail
 movel %a3,%sp@
 moveq #32,%d0
 movel %d0,%sp@(4)
 jsr 0x4000ae20
 moveq #0,%d1
 bra dc_get_done
dc_get_geometry:
 moveq #1,%d1
 bra dc_get_fail
dc_get_publication:
 moveq #10,%d1
dc_get_fail:
 moveq #0,%d0
dc_get_done:
 movew %a6@(-20),%d2
 movew %d2,%sr
 moveml %a6@(-16),%d2-%d3/%a2-%a3
 unlk %a6
 rts

/* dc_detent(E,oldraw,delta): scratch132 at FP-196..FP-65; outgoing12
 * at FP-212..FP-201. safe_enum rejects aliases with this consumer too.
 * Full insertion sort is identical for the six stock unique-key lists.
 * No promise for altered/tied registry mappings. */
dc_detent:
 linkw %a6,#-212
 moveml %d2-%d7/%a2-%a5,%a6@(-40)
 movew %sr,%d0
 movew %d0,%a6@(-44)
 movel %a6@(12),%d2
 movel %a6@(8),%sp@
 bsr dc_get
 tstl %d1
 bne dc_detent_refuse
 cmpl %d2,%d0
 bne dc_stale
 cmpil #0x20ff,%d2
 bhi dc_domain
 movel %d2,%d0
 asrl #8,%d0
 movel %d0,%sp@(4)
 bsr native_lookup
 tstl %d1
 bne dc_detent_refuse
 tstl %d0
 beq dc_missing
 movel %d0,%d3
 movel %d0,%sp@
 jsr 0x4005a85e
 notl %d0
 andil #0x600,%d0
 bne dc_filter
 movel %a6@(16),%d4
 asrl #8,%d4
 beq dc_detent_ok_old
 movel %a6@(8),%sp@
 lea %a6@(-196),%a2
 movel %a2,%sp@(4)
 moveq #33,%d0
 movel %d0,%sp@(8)
 bsr safe_enum
 tstl %d1
 bne dc_detent_refuse
 tstl %d0
 beq dc_missing
 movel %d0,%d5
 lsll #2,%d0
 lea %a2@(0,%d0:l),%a3
 movel %a2,%sp@
 movel %a3,%sp@(4)
 jsr 0x4000afe6
 moveq #0,%d6
dc_find:
 cmpl %a2@(0,%d6:l:4),%d3
 beq dc_found
 addql #1,%d6
 cmpl %d5,%d6
 bcs dc_find
 bra dc_missing
dc_found:
 addl %d4,%d6
 bpl dc_nonnegative
 moveq #0,%d6
dc_nonnegative:
 cmpl %d5,%d6
 bcs dc_selected
 movel %d5,%d6
 subql #1,%d6
dc_selected:
 movel %a2@(0,%d6:l:4),%sp@
 jsr 0x4005a4e8
 lsll #8,%d0
 moveq #0,%d1
 bra dc_detent_done
dc_detent_ok_old:
 movel %d2,%d0
 moveq #0,%d1
 bra dc_detent_done
dc_stale:
 moveq #16,%d1
 bra dc_detent_refuse
dc_domain:
 moveq #6,%d1
 bra dc_detent_refuse
dc_missing:
 moveq #7,%d1
 bra dc_detent_refuse
dc_filter:
 moveq #8,%d1
dc_detent_refuse:
 movel %d2,%d0
dc_detent_done:
 movew %a6@(-44),%d2
 movew %d2,%sr
 moveml %a6@(-40),%d2-%d7/%a2-%a5
 unlk %a6
 rts

dc_calc:
 movew %sr,%d1
 movel %sp@(8),%d0
 cmpil #32,%d0
 beq dc_calc_dst
 movew %d1,%sr
 jmp 0x4000c264
dc_calc_dst:
 movew %d1,%sr
 /* Rewrite only our outgoing copy, never the original four input slots. */
 linkw %a6,#-16
 movew %d1,%a6@(-4)
 movel %a6@(8),%sp@
 movel %a6@(16),%sp@(4)
 movel %a6@(20),%sp@(8)
 movew %a6@(-4),%d1
 movew %d1,%sr
 bsr dc_detent
 unlk %a6
 rts

dc_validate:
 movew %sr,%d1
 movel %sp@(8),%d0
 cmpil #32,%d0
 beq dc_validate_dst
 movew %d1,%sr
 jmp 0x4000c0a6
dc_validate_dst:
 movew %d1,%sr
 linkw %a6,#-28
 moveml %d2/%a2,%a6@(-8)
 movew %sr,%d0
 movew %d0,%a6@(-12)
 movel %a6@(16),%d2
 movel %a6@(8),%sp@
 bsr dc_get
 tstl %d1
 bne dc_validate_bad
 cmpil #0x20ff,%d2
 bhi dc_validate_domain
 asrl #8,%d2
 movel %d2,%sp@(4)
 bsr native_lookup
 tstl %d1
 bne dc_validate_bad
 tstl %d0
 beq dc_validate_missing
 movel %d0,%sp@
 jsr 0x4005a85e
 notl %d0
 andil #0x600,%d0
 bne dc_validate_filter
 moveq #1,%d0
 moveq #0,%d1
 bra dc_validate_done
dc_validate_domain:
 moveq #6,%d1
 bra dc_validate_bad
dc_validate_missing:
 moveq #7,%d1
 bra dc_validate_bad
dc_validate_filter:
 moveq #8,%d1
dc_validate_bad:
 moveq #0,%d0
dc_validate_done:
 movew %a6@(-12),%d2
 movew %d2,%sr
 moveml %a6@(-8),%d2/%a2
 unlk %a6
 rts

dc_edit:
 movew %sr,%d1
 movel %sp@(8),%d0
 cmpil #32,%d0
 beq dc_edit_dst
 movew %d1,%sr
 jmp 0x4000b7d6
dc_edit_dst:
 movew %d1,%sr
 linkw %a6,#-40
 moveml %d2-%d3/%a2,%a6@(-12)
 movew %sr,%d0
 movew %d0,%a6@(-16)
 movel %a6@(8),%sp@
 bsr dc_get
 movel %d0,%d2
 tstl %d1
 bne dc_refused_edit
 /* Editing needs writer, not just reader; no p-lock/changed-pointer branch
  * is implemented by this private ordinary-menu consumer. */
 moveal OWNER_SLOT,%a2
 moveq #3,%d1
 movel %a2@(72),%d0
 cmpil #1,%d0
 bne dc_refused_edit
 moveq #17,%d1
 tstb %a6@(27)
 bne dc_refused_edit
 tstl %a6@(28)
 bne dc_refused_edit
 movel %a6@(8),%d0
 subl %a2,%d0
 subil #680,%d0
dc_edit_track:
 cmpil #768,%d0
 bcs dc_edit_track_done
 subil #768,%d0
 bra dc_edit_track
dc_edit_track_done:
 lsrl #3,%d0
 cmpl %a6@(20),%d0
 bne dc_refused_edit
 movel %d2,%sp@(4)
 movel %a6@(16),%sp@(8)
 bsr dc_detent
 tstl %d1
 bne dc_refused_edit
 movel %d0,%sp@(8)
 movel %a6@(8),%sp@
 moveq #32,%d0
 movel %d0,%sp@(4)
 movel %a6@(20),%sp@(12)
 mvzb %a6@(35),%d0
 movel %d0,%sp@(16)
 mvzb %a6@(39),%d0
 movel %d0,%sp@(20)
dc_canonical_call:
 jsr 0x4000b274
 moveq #0,%d1
 bra dc_edit_done
dc_refused_edit:
 /* No canonical setter, store, notifier or changed-pointer access. */
 movel %d2,%d0
dc_edit_done:
 movew %a6@(-16),%d2
 movew %d2,%sr
 moveml %a6@(-12),%d2-%d3/%a2
 unlk %a6
 rts
consumer_end:
