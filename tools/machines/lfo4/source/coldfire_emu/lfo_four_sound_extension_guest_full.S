/* SPDX-License-Identifier: MIT
 * Copyright (c) 2026 Lachlan Fysh
 * Original authored source selected for review. re/tools/coldfire_emu/lfo_four_sound_extension_guest_full.S; lines 1-121.
 * Unresolved integration bindings are documented in DEPENDENCIES.json.
 */
/* New pure bounded helpers for the derived full-domain guest build.
 * Accepted cap64 source stays immutable. Each helper has a genuine RTS.
 * Validation: <=6720 rows, 24 words plus 3 enum checks per row; scratch only.
 * Transcoding: <=6720 rows of52B; default-XOR copy, no allocation/callback.
 * Search: <=6720 sorted rows; no publication. Caller stages/commits normally.
 */
.text
.globl full_validate_rows,full_decode_rows,full_encode_rows,full_find_row
.globl prepare_fixture
full_validate_rows:
full_validate_loop:
 cmpl %d4,%d6
 beq full_validate_good
 mvzw %a4@,%d0
 cmpil #6720,%d0
 bcc full_validate_bad
 tstl %d6
 beq full_validate_first
 cmpl %d7,%d0
 bls full_validate_bad
full_validate_first:
 movel %d0,%d7
 tstw %a4@(2)
 bne full_validate_bad
 lea %a4@(4),%a0
 lea defaults(%pc),%a1
 ctxaddr PAYLOAD,%a5
 moveq #24,%d3
full_validate_word:
 mvzw %a0@+,%d0
 mvzw %a1@+,%d1
 eorl %d1,%d0
 movew %d0,%a5@+
 subql #1,%d3
 bne full_validate_word
 bsr payload_valid
 tstl %d0
 beq full_validate_bad
 tstl %d1
 beq full_validate_bad
 lea %a4@(52),%a4
 addql #1,%d6
 bra full_validate_loop
full_validate_good:
 moveq #1,%d0
 rts
full_validate_bad:
 moveq #0,%d0
 rts

full_decode_rows:
 movel %a4@+,%a5@+
 lea defaults(%pc),%a1
 moveq #24,%d3
full_decode_word:
 mvzw %a4@+,%d0
 mvzw %a1@+,%d1
 eorl %d1,%d0
 movew %d0,%a5@+
 subql #1,%d3
 bne full_decode_word
 subql #1,%d6
 bne full_decode_rows
 rts

full_encode_rows:
 movel %a4@+,%a3@+
 lea defaults(%pc),%a1
 moveq #24,%d3
full_encode_word:
 mvzw %a4@+,%d0
 mvzw %a1@+,%d1
 eorl %d1,%d0
 movew %d0,%a3@+
 subql #1,%d3
 bne full_encode_word
 subql #1,%d4
 bne full_encode_rows
 rts

full_find_row:
 cmpl %d3,%d2
 beq full_find_missing
 mvzw %a3@,%d0
 cmpl %d4,%d0
 beq full_find_found
 bhi full_find_missing
 lea %a3@(52),%a3
 addql #1,%d2
 bra full_find_row
full_find_found:
 moveq #1,%d0
 rts
full_find_missing:
 moveq #0,%d0
 rts

/* Trusted EXTERNAL input rows/header are supplied without checksum seeds.
 * prepare_fixture(stock,record,length) computes both input CRCs in guest.
 * The caller compares them independently only AFTER completion. */
prepare_fixture:
 linkw %a6,#0
 lea %sp@(-8),%sp
 moveml %d2/%a3,%sp@
 moveal %a6@(8),%a0
 movel #STOCK_BYTES,%d0
 bsr crc32
 moveal %a6@(12),%a3
 movel %d0,%a3@(20)
 moveal %a3,%a0
 movel %a6@(16),%d2
 movel %d2,%d0
 subql #4,%d0
 bsr crc32
 lea %a3@(0,%d2:l),%a0
 movel %d0,%a0@(-4)
 moveq #1,%d0
 moveml %sp@,%d2/%a3
 lea %sp@(8),%sp
 unlk %a6
 rts
