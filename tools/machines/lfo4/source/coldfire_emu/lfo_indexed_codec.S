/* SPDX-License-Identifier: MIT
 * Copyright (c) 2026 Lachlan Fysh
 * Original authored source selected for review. re/tools/coldfire_emu/lfo_indexed_codec.S; lines 1-270.
 * Unresolved integration bindings are documented in DEPENDENCIES.json.
 */
/* Separate software-only extension. LFO4,u16version1,u16tracks6, six u8
 * selectors, u16reserved0, 3*6*8 BEu16 native config words, CRC32(first304B).
 * Pointers, stock records and runtime phases are never serialized. Caller
 * must exclude editors/render readers for load; this is not an atomic swap.
 * No original flash/project writer is hooked. */
.text
.equ META,0x41658000
.equ BYTES,308
.globl save,load
save:
 linkw %a6,#0
 lea %sp@(-28),%sp
 moveml %d2-%d5/%a2-%a4,%sp@
 moveal %a6@(8),%a2
 moveal %a6@(12),%a3
 movel %a6@(16),%d0
 cmpil #BYTES,%d0
 bcs fail
 bsr bank_valid
 tstl %d0
 beq fail
 bsr record_valid
 tstl %d0
 beq fail
 moveq #0,%d2
save_validate:
 movel %a2@(16,%d2:l:4),%d0
 subql #1,%d0
 cmpil #3,%d0
 bhi fail
 addql #1,%d2
 cmpil #6,%d2
 bne save_validate
 moveq #0,%d2
save_validate_instance:
 moveal %a2@(56,%d2:l:4),%a4
 moveq #0,%d3
save_validate_track:
 moveq #0,%d4
save_validate_word:
 mvzw %a4@(0x16,%d4:l:2),%d0
 cmpil #0x7f00,%d0
 bhi fail
 addql #1,%d4
 cmpil #8,%d4
 bne save_validate_word
 lea %a4@(100),%a4
 addql #1,%d3
 cmpil #6,%d3
 bne save_validate_track
 addql #1,%d2
 cmpil #3,%d2
 bne save_validate_instance
 movel #0x4c464f34,%d0
 movel %d0,%a3@
 movel #0x00010006,%d0
 movel %d0,%a3@(4)
 clrw %a3@(14)
 moveq #0,%d2
save_select:
 movel %a2@(16,%d2:l:4),%d0
 moveb %d0,%a3@(8,%d2:l)
 addql #1,%d2
 cmpil #6,%d2
 bne save_select
 lea %a3@(16),%a0
 moveq #0,%d2
save_instance:
 moveal %a2@(56,%d2:l:4),%a4
 moveq #0,%d3
save_track:
 moveq #0,%d4
save_word:
 movew %a4@(0x16,%d4:l:2),%a0@+
 addql #1,%d4
 cmpil #8,%d4
 bne save_word
 lea %a4@(100),%a4
 addql #1,%d3
 cmpil #6,%d3
 bne save_track
 addql #1,%d2
 cmpil #3,%d2
 bne save_instance
 bsr crc
 movel %d0,%a3@(304)
 movel #BYTES,%d0
 bra done
load:
 linkw %a6,#0
 lea %sp@(-28),%sp
 moveml %d2-%d5/%a2-%a4,%sp@
 moveal %a6@(8),%a2
 moveal %a6@(12),%a3
 bsr bank_valid
 tstl %d0
 beq fail
 tstl %a3
 bne load_present
 tstl %a6@(16)
 bne fail
 /* Explicit absent-record migration preserves LFO1 and defaults extras. */
 moveq #0,%d2
absent_select:
 moveq #1,%d0
 movel %d0,%a2@(16,%d2:l:4)
 addql #1,%d2
 cmpil #6,%d2
 bne absent_select
 moveq #0,%d2
absent_instance:
 moveal %a2@(56,%d2:l:4),%a4
 moveq #0,%d3
absent_track:
 lea defaults(%pc),%a0
 lea %a4@(0x16),%a1
 moveq #7,%d4
absent_word:
 movew %a0@+,%a1@+
 subql #1,%d4
 bpl absent_word
 lea %a4@(100),%a4
 addql #1,%d3
 cmpil #6,%d3
 bne absent_track
 addql #1,%d2
 cmpil #3,%d2
 bne absent_instance
 bra success
load_present:
 movel %a6@(16),%d0
 cmpil #BYTES,%d0
 bne fail
 bsr record_valid
 tstl %d0
 beq fail
 movel %a3@,%d0
 cmpil #0x4c464f34,%d0
 bne fail
 movel %a3@(4),%d0
 cmpil #0x00010006,%d0
 bne fail
 tstb %a3@(14)
 bne fail
 tstb %a3@(15)
 bne fail
 bsr crc
 cmpl %a3@(304),%d0
 bne fail
 moveq #0,%d2
load_validate_select:
 mvzb %a3@(8,%d2:l),%d0
 subql #1,%d0
 cmpil #3,%d0
 bhi fail
 addql #1,%d2
 cmpil #6,%d2
 bne load_validate_select
 lea %a3@(16),%a0
 movel #144,%d2
load_validate_words:
 mvzw %a0@+,%d0
 cmpil #0x7f00,%d0
 bhi fail
 subql #1,%d2
 bne load_validate_words
 /* All record validation above precedes the first destination mutation. */
 moveq #0,%d2
load_select:
 mvzb %a3@(8,%d2:l),%d0
 movel %d0,%a2@(16,%d2:l:4)
 addql #1,%d2
 cmpil #6,%d2
 bne load_select
 lea %a3@(16),%a0
 moveq #0,%d2
load_instance:
 moveal %a2@(56,%d2:l:4),%a4
 moveq #0,%d3
load_track:
 moveq #0,%d4
load_word:
 movew %a0@+,%a4@(0x16,%d4:l:2)
 addql #1,%d4
 cmpil #8,%d4
 bne load_word
 lea %a4@(100),%a4
 addql #1,%d3
 cmpil #6,%d3
 bne load_track
 addql #1,%d2
 cmpil #3,%d2
 bne load_instance
success:
 addql #1,%a2@(68)
 moveq #1,%d0
 bra done
fail:
 moveq #0,%d0
done:
 moveml %sp@,%d2-%d5/%a2-%a4
 lea %sp@(28),%sp
 unlk %a6
 rts
bank_valid:
 moveq #0,%d0
 cmpal #META,%a2
 bne bank_done
 movel %a2@,%d1
 cmpil #0x4c464f34,%d1
 bne bank_done
 movel %a2@(4),%d1
 cmpil #1,%d1
 bne bank_done
 /* Fixed harness bindings are explicit, not recovered device placement. */
 movel %a2@(56),%d1
 cmpil #0x4190301c,%d1
 bne bank_done
 movel %a2@(60),%d1
 cmpil #0x4190401c,%d1
 bne bank_done
 movel %a2@(64),%d1
 cmpil #0x4190501c,%d1
 bne bank_done
 moveq #1,%d0
bank_done:
 rts
record_valid:
 moveq #0,%d0
 tstl %a3
 beq record_done
 movel %a3,%d1
 andil #1,%d1
 bne record_done
 movel %a3,%d1
 addil #BYTES,%d1
 bcs record_done
 cmpil #0x41650000,%d1
 bls record_sidecars
 cmpal #0x41658100,%a3
 bcs record_done
record_sidecars:
 cmpil #0x41900000,%d1
 bls record_good
 cmpal #0x41906000,%a3
 bcs record_done
record_good:
 moveq #1,%d0
record_done:
 rts
crc:
 moveal %a3,%a1
 moveq #-1,%d0
 movel #304,%d4
crc_byte:
 mvzb %a1@+,%d1
 eorl %d1,%d0
 moveq #8,%d5
crc_bit:
 lsrl #1,%d0
 bcc crc_next
 movel #0xedb88320,%d1
 eorl %d1,%d0
crc_next:
 subql #1,%d5
 bne crc_bit
 subql #1,%d4
 bne crc_byte
 notl %d0
 rts
