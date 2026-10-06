/* SPDX-License-Identifier: MIT
 * Copyright (c) 2026 Lachlan Fysh
 * Original authored source selected for review. re/tools/coldfire_emu/lfo_four_sound_extension_guest.S; lines 1-1004,1009-1012.
 * Unresolved integration bindings are documented in DEPENDENCIES.json.
 */
/* Newly authored bounded ColdFire persistence milestone, no media hook.
 * create(owner, backing, actualM) -> stock calloc-owned context or0.
 * bank(ctx,index), save(ctx,stock,len,out,cap), load(ctx,stock,len,in,len),
 * read(ctx,key,out48), put(ctx,key,in48), copy_sound(ctx,srcKey,dstKey).
 * CAPACITY defaults64, all6720 keys. Two retained tables stage transactions. Caller
 * serializes stock observers too; existing writer lease excludes known users.
 * bank uses real 40013d88, a declared adapter rather than a40009a1e hook.
 * I/O spans below are explicit emulator contracts, not device RAM admission.
 * Wire: BE magic LF4S,u16 version1,u16 stride52,u32 total length,u16
 * domain6720,u16 count,u32 stock length0x210404,u32 guest stock CRC32;
 * sorted rows=u16 canonical index,u16 reserved0,48B configs XOR defaults;
 * final guest CRC32 covers header+rows. Defaults elide complete rows.
 * No vtable, regional address, phase, selector or status is serialized.
 * 64 rows are a finite milestone profile, NOT arbitrary full-project storage.
 * Context calloc failure returns0 without owner mutation: caller keeps stock
 * behavior. Capacity failure leaves prior binding/pending edits intact; bank
 * marks stock-only-required flag24. Product stock routing hook is not joined.
 * Default tables/payload fit6768B (stock8192B allocation class). CAPACITY6720
 * requests698992B (stock1MiB class); not yet guest capacity-qualified. No malloc
 * during sparse update/load/save. Caller may not persist/accept >CAPACITY dirty
 * Sounds; it must reject the transition or explicitly choose stock-only loss.
 */
.text
.ifndef CAPACITY
.equ CAPACITY,64
.endif
.if CAPACITY < 1
.error "CAPACITY must be1..6720"
.endif
.if CAPACITY > 6720
.error "CAPACITY must be1..6720"
.endif
.equ ROW_BYTES,52
.equ TABLE,32
.equ TABLE_BYTES,CAPACITY*ROW_BYTES
.equ STAGE,TABLE+TABLE_BYTES
.equ PAYLOAD,STAGE+TABLE_BYTES
.equ SIZE,PAYLOAD+80
.equ WIRE_MAX,28+TABLE_BYTES
.equ STOCK_BYTES,0x210404
/* Preserve the measured default instructions; large profiles need long
 * address arithmetic rather than invalid signed16 displacements. */
.macro ctxaddr offset,reg
.if \offset <= 32767
 lea %a2@(\offset),\reg
.else
 moveal %a2,\reg
 addal #\offset,\reg
.endif
.endm
.macro pro
 linkw %a6,#-80
 lea %sp@(-40),%sp
 moveml %d2-%d7/%a2-%a5,%sp@
.endm
.macro epi
 moveml %sp@,%d2-%d7/%a2-%a5
 lea %sp@(40),%sp
 unlk %a6
 rts
.endm
.globl create,bank,save,load,read,put,copy_sound,crc32,crc_end,reseal
create:
 pro
 moveal %a6@(8),%a3
 moveal %a6@(12),%a4
 moveal %a6@(16),%a5
 movel %a3,%d0
 movel %a4,%d1
 orl %d1,%d0
 movel %a5,%d1
 orl %d1,%d0
 andil #3,%d0
 bne create_bad
 cmpal #0x40000000,%a3
 bcs create_bad
 cmpal #0x47ffe000,%a3
 bcc create_bad
 cmpal #0x43800000,%a4
 bcs create_bad
 cmpal #0x44400000,%a4
 bcc create_bad
 cmpal #0x40000000,%a5
 bcs create_bad
 cmpal #0x47fff000,%a5
 bcc create_bad
 cmpal %a3@(40),%a5
 bne create_bad
 movel %a5@,%d0
 cmpil #0x400fcf3c,%d0
 bne create_bad
 pea SIZE
 pea 1
 jsr 0x40080238
 addql #8,%sp
 tstl %d0
 beq create_done
 moveal %d0,%a2
 movel #0x4c465347,%d0
 movel %d0,%a2@
 movel %a3,%a2@(4)
 movel %a4,%a2@(8)
 movel %a5,%a2@(12)
 moveq #-1,%d0
 movel %d0,%a2@(20)
 moveq #1,%d0
 movel %d0,%a2@(24)
 movel %a2,%d0
 bra create_done
create_bad:
 moveq #0,%d0
create_done:
 epi

/* a2=context. Validate before dereference; lease is actual supplied core. */
enter:
 cmpal #0x40000000,%a2
 bcs enter_bad
.if SIZE <= 8192
 cmpal #0x47ffe000,%a2
.else
 cmpal #(0x48000000-SIZE),%a2
.endif
 bcc enter_bad
 movel %a2,%d0
 andil #3,%d0
 bne enter_bad
 movel %a2@,%d0
 cmpil #0x4c465347,%d0
 bne enter_bad
 movel %a2@(16),%d0
 cmpil #CAPACITY,%d0
 bhi enter_bad
 moveal %a2@(4),%a0
 cmpal 0x40000304,%a0
 bne enter_bad
 movel %a0@,%d0
 cmpil #0x4c464f34,%d0
 bne enter_bad
 movel %a0@(4),%d0
 cmpil #1,%d0
 bne enter_bad
 moveal %a2@(12),%a1
 cmpal %a0@(40),%a1
 bne enter_bad
 jsr WRITE_BEGIN
 rts
enter_bad:
 moveq #0,%d0
 rts
leave:
 movel %d0,%sp@-
 jsr WRITE_END
 movel %sp@+,%d0
 rts

/* Original getters execute for all six canonical owners. Returns bank or-1.
 * a2 context; preserves all callee-saved registers. */
verify_current:
 lea %sp@(-24),%sp
 moveml %d2-%d4/%a3-%a5,%sp@
 moveal %a2@(12),%a3
 movel %a3@,%d0
 cmpil #0x400fcf3c,%d0
 bne verify_bad
 moveal %a2@(8),%a4
 addal #0x2cfc5c,%a4
 cmpal %a3@(16),%a4
 bne verify_bad
 movel %a3@(68),%d4
 cmpil #96,%d4
 bcc verify_bad
 movel %d4,%d0
 movel #7094,%d1
 mulu.l %d1,%d0
 addal %d0,%a4
 lea %a4@(28),%a4
 moveq #0,%d2
 lea %a3@(96),%a5
verify_track:
 movel %d2,%d0
 lsll #3,%d0
 lea %a3@(504),%a0
 moveal %a0@(4,%d0:l),%a1
 cmpal %a5,%a1
 bne verify_bad
 movel %a1@,%d0
 cmpil #0x400fef54,%d0
 bne verify_bad
 movel 0x400fef7c,%d0
 cmpil #0x400d5632,%d0
 bne verify_bad
 movel %a1,%sp@-
 jsr 0x400d5632
 addql #4,%sp
 movel %a4,%d1
 cmpl %d1,%d0
 bne verify_bad
 lea %a4@(100),%a4
 lea %a5@(68),%a5
 addql #1,%d2
 cmpil #6,%d2
 bne verify_track
 movel %d4,%d0
 bra verify_done
verify_bad:
 moveq #-1,%d0
verify_done:
 moveml %sp@,%d2-%d4/%a3-%a5
 lea %sp@(24),%sp
 rts

/* a0 -> a1, d0 bounded byte length. Internal disjoint/forward copies. */
bytes_copy:
 tstl %d0
 beq bytes_done
bytes_loop:
 moveb %a0@+,%a1@+
 subql #1,%d0
 bne bytes_loop
bytes_done:
 rts
/* gather pending retained configs, d6 track -> context payload. */
gather:
 lea %sp@(-12),%sp
 moveml %d2/%a3-%a4,%sp@
 moveal %a2@(4),%a3
 movel %d6,%d0
 moveq #100,%d1
 mulu.l %d1,%d0
 lea %a3@(2530),%a3
 addal %d0,%a3
 ctxaddr PAYLOAD,%a4
 moveq #3,%d2
gather_instance:
 moveal %a3,%a0
 moveal %a4,%a1
 moveq #16,%d0
 bsr bytes_copy
 lea %a3@(640),%a3
 lea %a4@(16),%a4
 subql #1,%d2
 bne gather_instance
 moveml %sp@,%d2/%a3-%a4
 lea %sp@(12),%sp
 rts

/* payload validity, d0 valid; d1=0 default, nonzero changed. */
payload_valid:
 movel %d2,%sp@-
 movel %d3,%sp@-
 ctxaddr PAYLOAD,%a0
 lea defaults(%pc),%a1
 moveq #24,%d2
 moveq #0,%d3
payload_word:
 mvzw %a0@+,%d0
 cmpil #0x7f00,%d0
 bhi payload_bad
 mvzw %a1@+,%d1
 eorl %d1,%d0
 orl %d0,%d3
 subql #1,%d2
 bne payload_word
 /* UI-public product admission: byte fields ignore fractional low bytes.
    Generic native DSP destination <=32 is NOT product label admission. */
 ctxaddr PAYLOAD,%a0
 moveq #3,%d2
payload_enum:
 mvzb %a0@(2),%d0
 cmpil #23,%d0
 bhi payload_bad
 mvzb %a0@(6),%d0
 tstl %d0
 beq payload_destination_ok
 cmpil #10,%d0
 blo payload_bad
 cmpil #22,%d0
 bhi payload_bad
payload_destination_ok:
 mvzb %a0@(8),%d0
 cmpil #6,%d0
 bhi payload_bad
 mvzb %a0@(12),%d0
 cmpil #4,%d0
 bhi payload_bad
 lea %a0@(16),%a0
 subql #1,%d2
 bne payload_enum
 moveq #1,%d0
 movel %d3,%d1
 bra payload_done
payload_bad:
 moveq #0,%d0
payload_done:
 movel %sp@+,%d3
 movel %sp@+,%d2
 rts

/* d0 key, a0 table, d1 count -> a0 raw payload or defaults. */
lookup:
 tstl %d1
 beq lookup_default
lookup_row:
 mvzw %a0@,%d2
 cmpl %d0,%d2
 beq lookup_found
 lea %a0@(52),%a0
 subql #1,%d1
 bne lookup_row
lookup_default:
 lea defaults(%pc),%a0
 rts
lookup_found:
 lea %a0@(4),%a0
 rts

/* d0 key and context payload -> staged sorted insertion/removal. */
put_stage:
 lea %sp@(-28),%sp
 moveml %d2-%d5/%a3-%a5,%sp@
 movel %d0,%d4
 cmpil #6720,%d4
 bcc put_bad
 bsr payload_valid
 tstl %d0
 beq put_bad
 movel %d1,%d5
 ctxaddr STAGE,%a3
 movel %a2@(28),%d3
 moveq #0,%d2
put_find:
 cmpl %d3,%d2
 beq put_missing
 mvzw %a3@,%d0
 cmpl %d4,%d0
 beq put_found
 bhi put_missing
 lea %a3@(52),%a3
 addql #1,%d2
 bra put_find
put_found:
 tstl %d5
 bne put_write
 moveal %a3,%a1
 lea %a3@(52),%a0
 subql #1,%d3
 movel %d3,%a2@(28)
 subl %d2,%d3
 moveq #52,%d1
 mulu.l %d1,%d3
 movel %d3,%d0
 bsr bytes_copy
 bra put_good
put_missing:
 tstl %d5
 beq put_good
 cmpil #CAPACITY,%d3
 bcc put_bad
 movel %d3,%d0
 subl %d2,%d0
 moveq #52,%d1
 mulu.l %d1,%d0
 moveal %a3,%a0
 addal %d0,%a0
 lea %a0@(52),%a1
 movel %d3,%d1
 subl %d2,%d1
 moveq #52,%d0
 mulu.l %d0,%d1
 tstl %d1
 beq put_insert
put_shift:
 subql #1,%a0
 subql #1,%a1
 moveb %a0@,%a1@
 subql #1,%d1
 bne put_shift
put_insert:
 addql #1,%a2@(28)
put_write:
 movew %d4,%a3@
 clrw %a3@(2)
 ctxaddr PAYLOAD,%a0
 lea %a3@(4),%a1
 moveq #48,%d0
 bsr bytes_copy
put_good:
 moveq #1,%d0
 bra put_done
put_bad:
 moveq #0,%d0
put_done:
 moveml %sp@,%d2-%d5/%a3-%a5
 lea %sp@(28),%sp
 rts

flush:
 lea %a2@(TABLE),%a0
 ctxaddr STAGE,%a1
 movel %a2@(16),%d0
 movel %d0,%a2@(28)
 moveq #52,%d1
 mulu.l %d1,%d0
 bsr bytes_copy
 movel %a2@(20),%d0
 cmpil #-1,%d0
 beq flush_good
 bsr verify_current
 cmpl %a2@(20),%d0
 bne flush_bad
 /* Two passes reclaim defaults before admitting nondefaults. */
 moveq #0,%d7
flush_pass:
 moveq #0,%d6
flush_track:
 bsr gather
 bsr payload_valid
 tstl %d0
 beq flush_bad
 tstl %d7
 bne flush_changed
 tstl %d1
 bne flush_next
 bra flush_put
flush_changed:
 tstl %d1
 beq flush_next
flush_put:
 movel %a2@(20),%d0
 moveq #70,%d1
 mulu.l %d1,%d0
 addl %d6,%d0
 bsr put_stage
 tstl %d0
 beq flush_bad
flush_next:
 addql #1,%d6
 cmpil #6,%d6
 bne flush_track
 addql #1,%d7
 cmpil #2,%d7
 bne flush_pass
flush_good:
 moveq #1,%d0
 rts
flush_bad:
 moveq #0,%d0
 rts
commit:
 ctxaddr STAGE,%a0
 lea %a2@(TABLE),%a1
 movel %a2@(28),%d0
 movel %d0,%a2@(16)
 moveq #52,%d1
 mulu.l %d1,%d0
 bsr bytes_copy
 rts

/* d6 track; only config words and corresponding volatile state are changed. */
materialize_track:
 lea %sp@(-16),%sp
 moveml %d3/%a3-%a5,%sp@
 movel %a2@(20),%d0
 moveq #70,%d1
 mulu.l %d1,%d0
 addl %d6,%d0
 lea %a2@(TABLE),%a0
 movel %a2@(16),%d1
 bsr lookup
 moveal %a0,%a4
 moveal %a2@(4),%a3
 movel %d6,%d0
 moveq #100,%d1
 mulu.l %d1,%d0
 lea %a3@(2530),%a3
 addal %d0,%a3
 moveal %a2@(4),%a5
 movel %d6,%d0
 lsll #5,%d0
 lea %a5@(4400),%a5
 addal %d0,%a5
 moveq #3,%d3
materialize_instance:
 moveal %a4,%a0
 moveal %a3,%a1
 moveq #16,%d0
 bsr bytes_copy
 moveal %a5,%a0
 moveq #8,%d0
materialize_zero:
 clrl %a0@+
 subql #1,%d0
 bne materialize_zero
 movel #0x3fffffff,%d0
 movel %d0,%a5@(8)
 lea %a4@(16),%a4
 lea %a3@(640),%a3
 lea %a5@(192),%a5
 subql #1,%d3
 bne materialize_instance
 moveml %sp@,%d3/%a3-%a5
 lea %sp@(16),%sp
 rts
materialize:
 moveq #0,%d6
materialize_tracks:
 bsr materialize_track
 addql #1,%d6
 cmpil #6,%d6
 bne materialize_tracks
 moveal %a2@(4),%a0
 lea %a0@(4976),%a0
 movel #357,%d0
materialize_work:
 clrl %a0@+
 subql #1,%d0
 bne materialize_work
 rts

bank:
 pro
 moveal %a6@(8),%a2
 movel %a6@(12),%d0
 cmpil #96,%d0
 bcc api_bad
 bsr enter
 tstl %d0
 beq api_done
 bsr flush
 tstl %d0
 beq bank_fail
 movel %a6@(12),%d4
 moveal %a2@(12),%a3
 moveal %a2@(8),%a4
 movel %d4,%d0
 movel #7094,%d1
 mulu.l %d1,%d0
 addal %d0,%a4
 addal #0x2cfc78,%a4
 lea %a3@(96),%a5
 moveq #6,%d3
bank_bind:
 pea 1
 pea 1
 movel %a4,%sp@-
 movel %a5,%sp@-
 jsr 0x40013d88
 lea %sp@(16),%sp
 lea %a4@(100),%a4
 lea %a5@(68),%a5
 subql #1,%d3
 bne bank_bind
 movel %d4,%a3@(68)
 movel %d4,%a2@(20)
 bsr commit
 bsr materialize
 clrl %a2@(24)
 moveq #1,%d0
 bra api_release
bank_fail:
 moveq #1,%d0
 movel %d0,%a2@(24)
 moveq #0,%d0
 bra api_release

/* Full stock CRC genuinely executed in guest. Caller may continue only this
 * finite pure routine to its real return, reporting interior PCs unmeasured. */
crc32:
 movel %d2,%sp@-
 movel %d3,%sp@-
 movel %d0,%d2
 moveq #-1,%d0
 tstl %d2
 beq crc_end
crc_byte:
 mvzb %a0@+,%d1
 eorl %d1,%d0
 moveq #8,%d3
crc_bit:
 lsrl #1,%d0
 bcc crc_next
 movel #0xedb88320,%d1
 eorl %d1,%d0
crc_next:
 subql #1,%d3
 bne crc_bit
 subql #1,%d2
 bne crc_byte
crc_end:
 notl %d0
 movel %sp@+,%d3
 movel %sp@+,%d2
 rts

/* fixture record span [46100000,47000000), length <=WIRE_MAX */
record_span:
 cmpal #0x46100000,%a0
 bcs span_bad
 movel %a0,%d1
 andil #1,%d1
 bne span_bad
 cmpil #WIRE_MAX,%d0
 bhi span_bad
 movel %a0,%d1
 addl %d0,%d1
 bcs span_bad
 cmpil #0x47000000,%d1
 bhi span_bad
 moveq #1,%d0
 rts
span_bad:
 moveq #0,%d0
 rts
stock_span:
 cmpal #0x44800000,%a0
 bcs span_bad
 cmpal #0x44df0000,%a0
 bcc span_bad
 cmpil #STOCK_BYTES,%d0
 bne span_bad
 moveq #1,%d0
 rts

save:
 pro
 moveal %a6@(8),%a2
 moveal %a6@(12),%a0
 movel %a6@(16),%d0
 bsr stock_span
 tstl %d0
 beq api_bad
 moveal %a6@(20),%a0
 movel %a6@(24),%d0
 bsr record_span
 tstl %d0
 beq api_bad
 bsr enter
 tstl %d0
 beq api_done
 bsr flush
 tstl %d0
 beq api_release
 movel %a2@(28),%d4
 moveq #52,%d0
 mulu.l %d4,%d0
 addil #28,%d0
 movel %d0,%d5
 cmpl %a6@(24),%d0
 bhi api_fail_release
 moveal %a6@(12),%a0
 movel #STOCK_BYTES,%d0
 bsr crc32
 moveal %a6@(20),%a3
 movel %d0,%a3@(20)
 movel #0x4c463453,%d0
 movel %d0,%a3@
 movel #0x00010034,%d0
 movel %d0,%a3@(4)
 movel %d5,%a3@(8)
 movew #6720,%a3@(12)
 movew %d4,%a3@(14)
 movel #STOCK_BYTES,%d0
 movel %d0,%a3@(16)
 ctxaddr STAGE,%a4
 lea %a3@(24),%a3
 tstl %d4
 beq save_crc
save_row:
 movel %a4@+,%a3@+
 lea defaults(%pc),%a1
 moveq #24,%d3
save_word:
 mvzw %a4@+,%d0
 mvzw %a1@+,%d1
 eorl %d1,%d0
 movew %d0,%a3@+
 subql #1,%d3
 bne save_word
 subql #1,%d4
 bne save_row
save_crc:
 moveal %a6@(20),%a0
 movel %d5,%d0
 subql #4,%d0
 bsr crc32
 movel %d0,%a3@
 bsr commit
 movel %d5,%d0
 bra api_release

load:
 pro
 moveal %a6@(8),%a2
 moveal %a6@(12),%a0
 movel %a6@(16),%d0
 bsr stock_span
 tstl %d0
 beq api_bad
 bsr enter
 tstl %d0
 beq api_done
 moveal %a6@(20),%a3
 movel %a6@(24),%d5
 tstl %a3
 bne load_present
 tstl %d5
 bne api_fail_release
 moveq #0,%d4
 bra load_verified
load_present:
 cmpil #28,%d5
 bcs api_fail_release
 moveal %a3,%a0
 movel %d5,%d0
 bsr record_span
 tstl %d0
 beq api_fail_release
 movel %a3@,%d0
 cmpil #0x4c463453,%d0
 bne api_fail_release
 movel %a3@(4),%d0
 cmpil #0x00010034,%d0
 bne api_fail_release
 cmpl %a3@(8),%d5
 bne api_fail_release
 mvzw %a3@(12),%d0
 cmpil #6720,%d0
 bne api_fail_release
 mvzw %a3@(14),%d4
 cmpil #CAPACITY,%d4
 bhi api_fail_release
 moveq #52,%d0
 mulu.l %d4,%d0
 addil #28,%d0
 cmpl %d5,%d0
 bne api_fail_release
 movel %a3@(16),%d0
 cmpil #STOCK_BYTES,%d0
 bne api_fail_release
 moveal %a6@(12),%a0
 movel #STOCK_BYTES,%d0
 bsr crc32
 cmpl %a3@(20),%d0
 bne api_fail_release
 moveal %a3,%a0
 movel %d5,%d0
 subql #4,%d0
 bsr crc32
 lea %a3@(0,%d5:l),%a0
 cmpl %a0@(-4),%d0
 bne api_fail_release
 /* Validate EVERY semantic row before published/live mutation. */
 lea %a3@(24),%a4
 moveq #-1,%d7
 moveq #0,%d6
load_validate:
 cmpl %d4,%d6
 beq load_verified
 mvzw %a4@,%d0
 cmpil #6720,%d0
 bcc api_fail_release
 tstl %d6
 beq load_first
 cmpl %d7,%d0
 bls api_fail_release
load_first:
 movel %d0,%d7
 tstw %a4@(2)
 bne api_fail_release
 lea %a4@(4),%a0
 lea defaults(%pc),%a1
 ctxaddr PAYLOAD,%a5
 moveq #24,%d3
load_decode_word:
 mvzw %a0@+,%d0
 mvzw %a1@+,%d1
 eorl %d1,%d0
 movew %d0,%a5@+
 subql #1,%d3
 bne load_decode_word
 bsr payload_valid
 tstl %d0
 beq api_fail_release
 tstl %d1
 beq api_fail_release
 lea %a4@(52),%a4
 addql #1,%d6
 bra load_validate
load_verified:
 bsr verify_current
 tstl %d0
 bmi api_fail_release
 movel %d0,%a6@(-4)
 movel %d4,%a2@(28)
 lea %a3@(24),%a4
 ctxaddr STAGE,%a5
 tstl %d4
 beq load_publish
 movel %d4,%d6
load_stage_row:
 movel %a4@+,%a5@+
 lea defaults(%pc),%a1
 moveq #24,%d3
load_stage_word:
 mvzw %a4@+,%d0
 mvzw %a1@+,%d1
 eorl %d1,%d0
 movew %d0,%a5@+
 subql #1,%d3
 bne load_stage_word
 subql #1,%d6
 bne load_stage_row
load_publish:
 bsr commit
 movel %a6@(-4),%a2@(20)
 bsr materialize
 clrl %a2@(24)
 moveq #1,%d0
 bra api_release

read:
 pro
 moveal %a6@(8),%a2
 movel %a6@(12),%d0
 cmpil #6720,%d0
 bcc api_bad
 moveal %a6@(16),%a0
 moveq #48,%d0
 bsr record_span
 tstl %d0
 beq api_bad
 bsr enter
 tstl %d0
 beq api_done
 bsr verify_current
 cmpl %a2@(20),%d0
 bne api_fail_release
 moveq #70,%d1
 mulu.l %d1,%d0
 movel %a6@(12),%d6
 subl %d0,%d6
 cmpil #6,%d6
 bcc read_table
 bsr gather
 ctxaddr PAYLOAD,%a0
 bra read_copy
read_table:
 movel %a6@(12),%d0
 lea %a2@(TABLE),%a0
 movel %a2@(16),%d1
 bsr lookup
read_copy:
 moveal %a6@(16),%a1
 moveq #48,%d0
 bsr bytes_copy
 moveq #1,%d0
 bra api_release

put:
 pro
 moveal %a6@(8),%a2
 movel %a6@(12),%d0
 cmpil #6720,%d0
 bcc api_bad
 moveal %a6@(16),%a0
 moveq #48,%d0
 bsr record_span
 tstl %d0
 beq api_bad
 bsr enter
 tstl %d0
 beq api_done
 bsr flush
 tstl %d0
 beq api_release
 moveal %a6@(16),%a0
 ctxaddr PAYLOAD,%a1
 moveq #48,%d0
 bsr bytes_copy
 movel %a6@(12),%d0
 bsr put_stage
 tstl %d0
 beq api_release
 bsr commit
 movel %a6@(12),%d0
 bsr materialize_key
 moveq #1,%d0
 bra api_release

/* d0 key -> canonical Sound a0, all6720 positions, no regional identity. */
key_address:
 movel %d2,%sp@-
 moveq #0,%d2
key_bank_loop:
 cmpil #70,%d0
 bcs key_ordinal
 subil #70,%d0
 addql #1,%d2
 bra key_bank_loop
key_ordinal:
 cmpil #6,%d0
 bcs key_track
 subql #6,%d0
 moveq #100,%d1
 mulu.l %d1,%d0
 addil #694,%d0
 bra key_base
key_track:
 moveq #100,%d1
 mulu.l %d1,%d0
 addil #28,%d0
key_base:
 movel #7094,%d1
 mulu.l %d1,%d2
 addl %d2,%d0
 addil #0x2cfc5c,%d0
 moveal %a2@(8),%a0
 addal %d0,%a0
 movel %sp@+,%d2
 rts
materialize_key:
 movel %d0,%d6
 movel %a2@(20),%d0
 moveq #70,%d1
 mulu.l %d1,%d0
 subl %d0,%d6
 cmpil #6,%d6
 bcc materialize_key_done
 bsr materialize_track
materialize_key_done:
 rts

copy_sound:
 pro
 moveal %a6@(8),%a2
 movel %a6@(12),%d0
 cmpil #6720,%d0
 bcc api_bad
 movel %a6@(16),%d0
 cmpil #6720,%d0
 bcc api_bad
 bsr enter
 tstl %d0
 beq api_done
 bsr flush
 tstl %d0
 beq api_release
 movel %a6@(12),%d0
 ctxaddr STAGE,%a0
 movel %a2@(28),%d1
 bsr lookup
 ctxaddr PAYLOAD,%a1
 moveq #48,%d0
 bsr bytes_copy
 movel %a6@(16),%d0
 bsr put_stage
 tstl %d0
 beq api_release
 movel %a6@(12),%d0
 bsr key_address
 moveal %a0,%a3
 movel %a6@(16),%d0
 bsr key_address
 moveal %a0,%a1
 moveal %a3,%a0
 moveq #100,%d0
 bsr bytes_copy
 bsr commit
 movel %a6@(16),%d0
 bsr materialize_key
 moveq #1,%d0
 bra api_release

/* Only test-fixture semantic-corruption resealing; computation stays guest. */
reseal:
 pro
 moveal %a6@(8),%a3
 movel %a6@(12),%d4
 cmpil #28,%d4
 bcs api_bad
 moveal %a3,%a0
 movel %d4,%d0
 bsr record_span
 tstl %d0
 beq api_bad
 moveal %a3,%a0
 movel %d4,%d0
 subql #4,%d0
 bsr crc32
 lea %a3@(0,%d4:l),%a0
 movel %d0,%a0@(-4)
 moveq #1,%d0
 bra api_done
api_fail_release:
 moveq #0,%d0
api_release:
 bsr leave
 bra api_done
api_bad:
 moveq #0,%d0
api_done:
 epi
.balign 4


.globl contract_layout
.balign 4
contract_layout:
 .long CAPACITY,TABLE,STAGE,PAYLOAD,SIZE,ROW_BYTES,WIRE_MAX,TABLE_BYTES
