/* SPDX-License-Identifier: MIT
 * Copyright (c) 2026 Lachlan Fysh
 * Original authored source selected for review. re/tools/coldfire_emu/lfo_four_random_join.S; lines 1-421,427-431.
 * Unresolved integration bindings are documented in DEPENDENCIES.json.
 */
/* Recoverable RANDOM variant, emulator bindings only. Boot-retained owner.
 * F = wrapper entry SP - 1264. F[96..1172) checkpoints W476/state576/seeds24.
 * Authenticated helper H = F-76 (five arguments + return + engine48 + return).
 * No shared active-frame pointer. An untrusted frame cannot request rollback.
 * CORE fragments are spliced into the checked lifecycle by the new builder.
 */
.ifdef INIT
 movel %a2,%a2@(6444)        /* Constructor self-binding, before SLOT. */
 lea %a2@(6416),%a1
 moveq #3,%d0
random_init_pair:
 /* Read initial MAIN pair once per bank; never replace MAIN seeds. */
 movel 0x4014931c,%d1
 movel %d1,%a1@+
 movel 0x40149320,%d1
 movel %d1,%a1@+
 subql #1,%d0
 bne random_init_pair
 clrl %a2@(6440)
 movel #0x524e4731,%d0
 movel %d0,%a2@(6448)       /* Declared initialized RNG1 marker. */
.endif
.ifdef SHELL
.globl render_after_wrapper,render_release,render_bypass
render_event:
 lea %sp@(-68),%sp
 moveml %d0-%d7/%a0-%a6,%sp@
 movew %sr,%d0
 movew %d0,%sp@(60)
 bsr read_begin
 tstl %d0
 beq render_bypass
 movel %a0,%sp@(64)        /* This invocation's successful acquisition. */
 movel %a0,%sp@-
 movel %sp@(80),%sp@-
 movel %sp@(80),%sp@-
 movew %sp@(72),%d0
 movew %d0,%sr
 moveml %sp@(12),%d0-%d7/%a0-%a6
 jsr 0x43790000
render_after_wrapper:
 lea %sp@(12),%sp
 moveml %d0-%d7/%a0-%a6,%sp@
 movew %sr,%d0
 movew %d0,%sp@(60)
 moveal %sp@(64),%a0
render_release:
 clrl %a0@(76)             /* Acquired retained owner, never a new SLOT. */
 movew %sp@(60),%d0
 movew %d0,%sr
 moveml %sp@,%d0-%d7/%a0-%a6
 lea %sp@(68),%sp
 rts
render_bypass:
 movew %sp@(60),%d0
 movew %d0,%sr
 moveml %sp@,%d0-%d7/%a0-%a6
 lea %sp@(68),%sp
 jmp 0x40056e24
.endif
.ifndef FRAGMENT
.text
.equ SLOT,0x40000304
.equ ENGINE,0x43690000
.equ BASE,0x43790000
.globl wrapper,after_stock,engine_call,engine_return,publish_destination
.globl rollback,wrapper_done,dispatch,private_claim,private_load,private_store
.globl private_release,owned_reject,auth_fault,preflight,preflight_done
wrapper:
 lea %sp@(-64),%sp
 moveml %d0-%d7/%a0-%a6,%sp@
 movew %sr,%d0
 movew %d0,%sp@(60)
 movel %sp@(72),%sp@-
 movel %sp@(72),%sp@-
 movew %sp@(68),%d0
 movew %d0,%sr
 moveml %sp@(8),%d0-%d7/%a0-%a6
 jsr 0x40056e24
 lea %sp@(8),%sp
after_stock:
 lea %sp@(-1200),%sp
 moveml %d0-%d7/%a0-%a6,%sp@
 movew %sr,%d0
 movew %d0,%sp@(60)
 movel %macsr,%d0
 movel %d0,%sp@(64)
 andil #0xf0,%d0
 cmpil #0x20,%d0
 bne wrapper_done
 movel %acc0,%d0
 movel %d0,%sp@(68)
 movel %acc1,%d0
 movel %d0,%sp@(72)
 movel %acc2,%d0
 movel %d0,%sp@(76)
 movel %acc3,%d0
 movel %d0,%sp@(80)
 movel %accext01,%d0
 movel %d0,%sp@(84)
 movel %accext23,%d0
 movel %d0,%sp@(88)
 /* F = S-1264: initial64 + checkpoint1200. */
 moveal %sp@(1276),%a2     /* Owner supplied by acquired shell token. */
 cmpal SLOT,%a2
 bne restore_emac
 tstl %a2
 beq restore_emac
 cmpal %a2@(6444),%a2
 bne restore_emac
 movel %a2@(6448),%d0
 cmpil #0x524e4731,%d0
 bne restore_emac
 movel %a2@,%d0
 cmpil #0x4c464f34,%d0
 bne restore_emac
 movel %a2@(4),%d0
 cmpil #1,%d0
 bne restore_emac
 movel %a2@(76),%d0
 cmpil #1,%d0
 bne restore_emac
 tstl %a2@(72)
 bne restore_emac
 tstl %a2@(6440)
 bne restore_emac
 moveal %sp@(1268),%a3
 movel %a2,%sp@(1172)
 movel %a3,%sp@(1176)
 movel %sp,%sp@(1180)
 movel %sp,%d0
 movel %a2,%d1
 eorl %d1,%d0
 eoril #0x524a4f49,%d0
 movel %d0,%sp@(1184)
 /* Check exact config pointers before dereferencing any bank. */
 lea %a2@(2508),%a0
 cmpal %a2@(56),%a0
 bne restore_emac
 lea %a0@(640),%a0
 cmpal %a2@(60),%a0
 bne restore_emac
 lea %a0@(640),%a0
 cmpal %a2@(64),%a0
 bne restore_emac
 /* Whole invocation checkpoint, never MAIN seed bytes. */
 moveal %a3,%a0
 lea %sp@(96),%a1
 moveq #119,%d1
 bsr copy_words
 lea %a2@(4400),%a0
 movel #144,%d1
 bsr copy_words
 lea %a2@(6416),%a0
 moveq #6,%d1
 bsr copy_words
 moveq #0,%d2
preflight:
 bsr prepare_bank
 /* Product destinations only, before any numerical engine. */
 lea %a4@(22),%a0
 moveq #6,%d3
validate_destination:
 mvzb %a0@,%d0
 beq destination_valid
 cmpil #10,%d0
 bcs rollback
 cmpil #22,%d0
 bhi rollback
destination_valid:
 lea %a0@(66),%a0
 subql #1,%d3
 bne validate_destination
 pea 1
 bsr engine_arguments
 jsr ENGINE
 lea %sp@(20),%sp
 cmpil #6,%d0
 bne rollback
 addql #1,%d2
 cmpil #3,%d2
 bne preflight
preflight_done:
 moveq #0,%d2
engine_loop:
 movel %d2,%sp@(1188)
 bsr prepare_bank
 moveq #0,%d0
 movel %d0,%acc0
 movel %d0,%acc1
 movel %d0,%acc2
 movel %d0,%acc3
 movel #0x20,%macsr
 pea 0
 bsr engine_arguments
engine_call:
 jsr ENGINE
engine_return:
 lea %sp@(20),%sp
 cmpil #6,%d0
 bne rollback
 lea %a4@(22),%a0
 lea %a4@(14),%a1
 lea %a3@(14),%a6
 moveq #6,%d3
publication_lane:
 mvzb %a0@,%d0
 beq publication_next
 mvzw %a0@(8),%d1
 cmpil #0x4000,%d1
 beq publication_next
 movew %a1@(0,%d0:l:2),%d1
publish_destination:
 movew %d1,%a6@(0,%d0:l:2)
publication_next:
 lea %a0@(66),%a0
 lea %a1@(66),%a1
 lea %a6@(66),%a6
 subql #1,%d3
 bne publication_lane
 addql #1,%d2
 cmpil #3,%d2
 bne engine_loop
 bra restore_emac
/* BSR return is removed, then arguments built at the wrapper's F. */
engine_arguments:
 moveal %sp@+,%a0
 movel %a5,%sp@-
 moveal %sp@(52),%a1      /* F+44 saved post-stock A3/root. */
 movel %a1@(4),%sp@-
 movel 0x40149310,%sp@-
 movel %a4,%sp@-
 jmp %a0@
prepare_bank:
 movel %d2,%d0
 movel #476,%d1
 mulu.l %d1,%d0
 lea %a2@(4976),%a4
 lea %a4@(0,%d0:l),%a4
 moveal %a3,%a0
 moveal %a4,%a1
 moveq #119,%d1
 bsr copy_words
 moveal %a2@(56,%d2:l:4),%a0
 lea %a4@(16),%a1
 moveq #6,%d3
copy_lane:
 lea %a0@(22),%a6
 moveq #8,%d4
copy_control:
 movew %a6@+,%a1@+
 subql #1,%d4
 bne copy_control
 lea %a1@(50),%a1
 lea %a0@(100),%a0
 subql #1,%d3
 bne copy_lane
 movel %d2,%d0
 movel #192,%d1
 mulu.l %d1,%d0
 lea %a2@(4400),%a5
 lea %a5@(0,%d0:l),%a5
 rts
copy_words:
 movel %a0@+,%a1@+
 subql #1,%d1
 bne copy_words
 rts
rollback:
 moveal %sp@(1172),%a2
 lea %sp@(96),%a0
 moveal %sp@(1176),%a1
 moveq #119,%d1
 bsr copy_words
 lea %a2@(4400),%a1
 movel #144,%d1
 bsr copy_words
 lea %a2@(6416),%a1
 moveq #6,%d1
 bsr copy_words
restore_emac:
 movel %sp@(68),%d0
 movel %d0,%acc0
 movel %sp@(72),%d0
 movel %d0,%acc1
 movel %sp@(76),%d0
 movel %d0,%acc2
 movel %sp@(80),%d0
 movel %d0,%acc3
 movel %sp@(84),%d0
 movel %d0,%accext01
 movel %sp@(88),%d0
 movel %d0,%accext23
wrapper_done:
 movel %sp@(64),%d0
 movel %d0,%macsr
 movew %sp@(60),%d0
 movew %d0,%sr
 moveml %sp@,%d0-%d7/%a0-%a6
 lea %sp@(1264),%sp
 rts

dispatch:
 /* Stock A2/return bypass every private gate, including a foreign busy. */
 lea %sp@(-24),%sp
 moveml %d2-%d3/%a0-%a1/%a4-%a5,%sp@
 movew %sr,%d3
 movel %sp@(24),%d1
 cmpil #0x40091cce,%d1
 bne stock_fallback
 movel %a2,%d2
 subil #0x40fde838,%d2
 cmpil #192,%d2
 bcc authenticate
 movel %d2,%d1
 andil #31,%d1
 beq stock_fallback
authenticate:
 /* F = (H-24)+100. Validate bounds before reading its token. */
 lea %sp@(100),%a4
 cmpal #STACK_LOW,%a4
 bcs auth_fault
 cmpal #STACK_HIGH-1352,%a4
 bhi auth_fault
 movel %a4,%d1
 andil #3,%d1
 bne auth_fault
 cmpal %a4@(1180),%a4
 bne auth_fault
 movel %a4@(1264),%d1
 cmpil #SHELL_RETURN,%d1
 bne auth_fault
 movel %sp@(76),%d1      /* H+52 engine return. */
 cmpil #BASE+(engine_return-wrapper),%d1
 bne auth_fault
 moveal %a4@(1172),%a0
 cmpal %a4@(1276),%a0
 bne auth_fault
 cmpal %a4@(1344),%a0    /* Shell's protected acquired-owner token. */
 bne auth_fault
 cmpal SLOT,%a0
 bne auth_fault
 cmpal %a0@(6444),%a0
 bne auth_fault
 movel %a4,%d1
 movel %a0,%d2
 eorl %d2,%d1
 eoril #0x524a4f49,%d1
 cmpl %a4@(1184),%d1
 bne auth_fault
 movel %a4@(1188),%d2
 cmpil #2,%d2
 bhi auth_fault
 movel #192,%d1
 mulu.l %d1,%d2
 lea %a0@(4400),%a1
 lea %a1@(0,%d2:l),%a1
 movel %a2,%d1
 subl %a1,%d1
 cmpil #192,%d1
 bcc auth_fault
 andil #31,%d1
 bne auth_fault
 cmpal %sp@(92),%a1      /* H+68 exact supplied state. */
 bne auth_fault
 movel %a4@(1188),%d2
 movel #476,%d1
 mulu.l %d1,%d2
 lea %a0@(4976),%a1
 lea %a1@(0,%d2:l),%a1
 cmpal %sp@(80),%a1      /* H+56 exact supplied W. */
 bne auth_fault
 tstl %sp@(96)           /* H+72 real engine flag, not validator. */
 bne auth_fault
 movel %d3,%d1
 oril #0x700,%d1
 movew %d1,%sr
 movel %a0@,%d1
 cmpil #0x4c464f34,%d1
 bne owned_reject
 movel %a0@(4),%d1
 cmpil #1,%d1
 bne owned_reject
 movel %a0@(6448),%d1
 cmpil #0x524e4731,%d1
 bne owned_reject
 tstl %a0@(72)
 bne owned_reject
 movel %a0@(76),%d1
 cmpil #1,%d1
 bne owned_reject
 tstl %a0@(6440)
 bne owned_reject
 movel %a4@(1188),%d2
 lsll #3,%d2
 lea %a0@(6416),%a1
 lea %a1@(0,%d2:l),%a1
 moveq #1,%d1
private_claim:
 movel %d1,%a0@(6440)
private_load:
 movel %a1@(4),%d1
 movel %d1,%d0
 addl %a1@,%d0
private_store:
 movel %d1,%a1@
 movel %d0,%a1@(4)
 movew %sr,%d2
 andil #0xff,%d2
 andil #0xff00,%d3
 orl %d3,%d2
private_release:
 clrl %a0@(6440)
 movew %d2,%sr
 moveml %sp@,%d2-%d3/%a0-%a1/%a4-%a5
 lea %sp@(24),%sp
 rts
owned_reject:
 /* No numerical return/sample; leave foreign guard/writer intact. */
 moveal %a4,%sp
 bra rollback


auth_fault:
 /* Corrupt/unrelated caller cannot authenticate recovery authority.
  * Explicit unresolved containment edge: stopped fail-closed, no sample. */
 bra auth_fault
.endif
