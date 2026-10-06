/* SPDX-License-Identifier: MIT
 * Copyright (c) 2026 Lachlan Fysh
 * Original authored source selected for review. re/tools/coldfire_emu/lfo_four_selector_append.S; lines 1-109.
 * Unresolved integration bindings are documented in DEPENDENCIES.json.
 */
/* Checked equivalent of native shared-item append for the authored selector.
 * (menu, fully constructed privately owned item). Native Setup's three-row
 * vector may require checked growth to four. Failure leaves it unchanged;
 * caller still owns the unpublished item.
 */
.text
.globl append,append_allocate,append_vector_allocate,append_publish
append:
 linkw %a6,#-4
 lea %sp@(-24),%sp
 moveml %d2-%d3/%a2-%a5,%sp@
 moveq #0,%d0
 moveal %a6@(8),%a2
 moveal %a6@(12),%a3
 tstl %a2
 beq done
 tstl %a3
 beq done
 movel %a2@(4),%d2
 tstl %d2
 beq done
 movel %a2@(8),%d1
 subl %d2,%d1
 cmpil #24,%d1
 bne done
 movel %a2@(12),%d1
 subl %d2,%d1
 cmpil #24,%d1
 beq capacity_ok
 cmpil #32,%d1
 bne done
capacity_ok:
 movel %d2,%d1
 addil #32,%d1
 bcs done
 pea 16
append_allocate:
 jsr 0x400802e0
 addql #4,%sp
 tstl %d0
 beq done
 moveal %d0,%a4
 moveal %d2,%a5
 clrl %a6@(-4)
 movel %a2@(12),%d1
 subl %d2,%d1
 cmpil #32,%d1
 beq initialize_control
 pea 32
append_vector_allocate:
 jsr 0x400802e0
 addql #4,%sp
 tstl %d0
 beq vector_failed
 moveal %d0,%a5
 moveq #1,%d0
 movel %d0,%a6@(-4)
 moveal %d2,%a0
 moveal %a5,%a1
 moveq #6,%d1
copy_rows:
 movel %a0@+,%a1@+
 subql #1,%d1
 bne copy_rows
initialize_control:
 /* Authentic 401087c4 dispose/weak-destroy contract, not a new vtable. */
 movel #0x401087c4,%d0
 movel %d0,%a4@
 moveq #1,%d0
 movel %d0,%a4@(4)
 movel %d0,%a4@(8)
 movel %a3,%a4@(12)
 pea 3
 movel %a3,%sp@-
 jsr 0x4007320a
 addql #8,%sp
 lea %a5@(24),%a0
append_publish:
 movel %a3,%a0@
 movel %a4,%a0@(4)
 /* Publish one moved vector, not copied strong references. */
 movew %sr,%d3
 movel %d3,%d1
 oril #0x700,%d1
 movew %d1,%sr
 movel %a5,%a2@(4)
 lea %a5@(32),%a0
 movel %a0,%a2@(8)
 movel %a0,%a2@(12)
 movew %d3,%sr
 tstl %a6@(-4)
 beq success
 movel %d2,%sp@-
 jsr 0x400802ec
 addql #4,%sp
success:
 moveq #1,%d0
 bra done
vector_failed:
 /* Private uninitialized RC allocation; no dispose callback yet. */
 movel %a4,%sp@-
 jsr 0x400802ec
 addql #4,%sp
 moveq #0,%d0
done:
 moveml %sp@,%d2-%d3/%a2-%a5
 lea %sp@(24),%sp
 unlk %a6
 rts
