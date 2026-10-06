/* SPDX-License-Identifier: MIT
 * Copyright (c) 2026 Lachlan Fysh
 * Original authored source selected for review. re/tools/coldfire_emu/lfo_four_menu_transaction_join.S; lines 1-45,62-145.
 * Unresolved integration bindings are documented in DEPENDENCIES.json.
 */
/* Boot-retained owner; one serialized UI task. No owner replacement API.
 * STATUS is zeroed once before first menu. Detached owner is terminal until
 * reboot. Menu retirement precedes every native nondeleting destructor.
 */
.text
.globl terminal_disable,retire_menu,normal_destroy,setup_destroy
.globl restore_normal,restore_setup,stock_noop
terminal_disable:
 movel %d2,%sp@-
 movew %sr,%d2
 movel %d2,%d1
 oril #0x700,%d1
 movew %d1,%sr
 moveq #1,%d0
 movel %d0,STATUS+4
 clrl SLOT
 clrl SLOT-4
 movew %d2,%sr
 movel %sp@+,%d2
 rts
/* retire_menu(menu): revoke item identities while references may survive.
 * This is ingress revocation, not a callback-drain or owner-free operation.
 */
retire_menu:
 movel %d2,%sp@-
 movew %sr,%d2
 movel %d2,%d1
 oril #0x700,%d1
 movew %d1,%sr
 moveal #REGISTRY,%a0
 moveq #8,%d1
retire_next:
 movel %a0@(4),%d0
 cmpl %sp@(8),%d0
 bne retire_skip
 clrl %a0@(8)
 clrl %a0@
 clrl %a0@(4)
retire_skip:
 lea %a0@(12),%a0
 subql #1,%d1
 bne retire_next
 movew %d2,%sr
 movel %sp@+,%d2
 rts


/* restore_* apply only to successfully built native menus. Constructors
 * themselves still require the native allocation contract. No second build
 * or extra allocation is performed on the fallback path.
 */
restore_normal:
 moveal %sp@(4),%a0
 moveal %a0@(4),%a1
 moveal %a1@,%a0
 movel #0x40025d28,%d0
 movel %d0,%a0@(0x38)
 movel #0x40025eba,%d0
 movel %d0,%a0@(0x48)
 moveal %a1@(8),%a0
 movel #0x400263e8,%d0
 movel %d0,%a0@(0x38)
 movel #0x40025f6a,%d0
 movel %d0,%a0@(0x48)
 moveal %a1@(16),%a0
 movel #0x400264a2,%d0
 movel %d0,%a0@(0x38)
 movel #0x4002601a,%d0
 movel %d0,%a0@(0x48)
 moveal %a1@(24),%a0
 movel #0x40026562,%d0
 movel %d0,%a0@(0x38)
 movel #0x400260ca,%d0
 movel %d0,%a0@(0x48)
 rts
restore_setup:
 lea %sp@(-12),%sp
 moveml %d2/%a2-%a3,%sp@
 moveal %sp@(16),%a2
 moveal %a2@(4),%a3
 movel %a2@(8),%d0
 subl %a3,%d0
 cmpil #32,%d0
 bne restore_setup_three
 /* The authored selector is first. Release its native shared control
  * before shifting the three original rows back; no raw item free. */
 pea %a3@(4)
 jsr 0x400cf23c
 addql #4,%sp
 movel %a3@(8),%a3@
 movel %a3@(12),%a3@(4)
 movel %a3@(16),%a3@(8)
 movel %a3@(20),%a3@(12)
 movel %a3@(24),%a3@(16)
 movel %a3@(28),%a3@(20)
 clrl %a3@(24)
 clrl %a3@(28)
 subql #8,%a2@(8)
 moveq #3,%d0
 movel %d0,%a2@(0x20)
restore_setup_three:
 moveal %a3@,%a0
 movel #0x40026f20,%d0
 movel %d0,%a0@(0x38)
 movel #0x40026eac,%d0
 movel %d0,%a0@(0x28)
 moveal %a3@(8),%a0
 movel #0x40027076,%d0
 movel %d0,%a0@(0x38)
 movel #0x40026fb2,%d0
 movel %d0,%a0@(0x48)
 moveal %a3@(16),%a0
 movel #0x40027124,%d0
 movel %d0,%a0@(0x38)
 movel #0x40027014,%d0
 movel %d0,%a0@(0x48)
 moveq #0,%d2
restore_renumber:
 movel %d2,%sp@-
 movel %a3@(0,%d2:l:8),%sp@-
 jsr 0x4007320a
 addql #8,%sp
 addql #1,%d2
 cmpil #3,%d2
 bne restore_renumber
 moveml %sp@,%d2/%a2-%a3
 lea %sp@(12),%sp
 rts
stock_noop:
 moveq #0,%d0
 rts
