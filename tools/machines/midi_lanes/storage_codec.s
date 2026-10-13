| Codec MBK1 ColdFire : équivalent du format C hôte, sans libc/alloc/E/S.
| Buffers non chevauchants, alignés sur 4 ; snapshots/staging privés UI.
| MBK2 ajoute locks retrigger/chance3120 et configurations LFO MIDI192.
    .ifdef ML_STORAGE3
    .equ ML_DATA_BYTES,4992
    .equ ML_RECORD_BYTES,5024
    .ifdef ML_LIVE_REC
    .equ ML_RECORD_MAGIC,0x4d424b34
    .equ ML_RECORD_VERSION,4
    .else
    .equ ML_RECORD_MAGIC,0x4d424b33
    .equ ML_RECORD_VERSION,3
    .endif
    .else
    .ifdef ML_STORAGE2
    .equ ML_DATA_BYTES,4896
    .equ ML_RECORD_BYTES,4928
    .equ ML_RECORD_MAGIC,0x4d424b32
    .equ ML_RECORD_VERSION,2
    .else
    .equ ML_DATA_BYTES,1584
    .equ ML_RECORD_BYTES,1616
    .equ ML_RECORD_MAGIC,0x4d424b31
    .equ ML_RECORD_VERSION,1
    .endif
    .endif
    .text
    .globl ml_record_crc,ml_record_encode,ml_record_decode
ml_record_crc:
    movel %d2,%sp@-
    moveal %sp@(8),%a0
    movel %sp@(12),%d0
    moveq #-1,%d1
.Lcrc_byte:
    tstl %d0
    beq .Lcrc_done
    moveq #0,%d2
    moveb %a0@+,%d2
    eorl %d2,%d1
    moveq #7,%d2
.Lcrc_bit:
    lsrl #1,%d1
    bcc .Lcrc_next
    eoril #0xedb88320,%d1
.Lcrc_next:
    subql #1,%d2
    bpl .Lcrc_bit
    subql #1,%d0
    bra .Lcrc_byte
.Lcrc_done:
    notl %d1
    movel %d1,%d0
    movel %sp@+,%d2
    rts

| a0=payload ; d0=valide. Validation entière avant publication.
.Lvalid:
    lea.l %sp@(-8),%sp
    moveml %d2-%d3,%sp@
    moveq #6,%d2
.Lvalid_lane:
    moveq #0,%d1
    moveb %a0@,%d1
    cmpil #1,%d1
    bhi .Lvalid_bad
    moveq #0,%d1
    moveb %a0@(1),%d1
    cmpil #1,%d1
    bhi .Lvalid_bad
    moveq #0,%d1
    moveb %a0@(2),%d1
    cmpil #15,%d1
    bhi .Lvalid_bad
    moveq #0,%d1
    moveb %a0@(3),%d1
    cmpil #2,%d1
    bcs .Lvalid_bad
    moveq #0,%d1
    moveb %a0@(3),%d1
    cmpil #4,%d1
    bhi .Lvalid_bad
    moveq #0,%d1
    moveb %a0@(4),%d1
    cmpil #1,%d1
    bcs .Lvalid_bad
    moveq #0,%d1
    moveb %a0@(4),%d1
    cmpil #64,%d1
    bhi .Lvalid_bad
    moveq #0,%d1
    moveb %a0@(5),%d1
    cmpil #6,%d1
    bhi .Lvalid_bad
    moveq #0,%d1
    moveb %a0@(6),%d1
    extbl %d1
    cmpil #-60,%d1
    blt .Lvalid_bad
    cmpil #60,%d1
    bgt .Lvalid_bad
    moveq #0,%d1
    moveb %a0@(7),%d1
    cmpil #127,%d1
    bhi .Lvalid_bad
    addql #8,%a0
    moveq #63,%d3
.Lvalid_step:
    moveq #0,%d1
    moveb %a0@,%d1
    cmpil #127,%d1
    bhi .Lvalid_bad
    moveq #0,%d1
    moveb %a0@(1),%d1
    cmpil #1,%d1
    bcs .Lvalid_bad
    moveq #0,%d1
    moveb %a0@(1),%d1
    cmpil #127,%d1
    bhi .Lvalid_bad
    moveq #0,%d1
    moveb %a0@(2),%d1
    cmpil #1,%d1
    bcs .Lvalid_bad
    moveq #0,%d1
    moveb %a0@(2),%d1
    cmpil #64,%d1
    bhi .Lvalid_bad
    moveq #0,%d1
    moveb %a0@(3),%d1
    .ifndef ML_LIVE_REC
    cmpil #3,%d1
    bhi .Lvalid_bad
    .endif
    addql #4,%a0
    subql #1,%d3
    bpl .Lvalid_step
    addql #1,%d2
    cmpil #12,%d2
    bcs .Lvalid_lane
    .ifdef ML_STORAGE2
    | 390 groupes : six défauts et384locks. Bornes par champ.
    movel #389,%d2
.Lvalid_repeat:
    lea .Lrepeat_max,%a1
    moveq #7,%d3
.Lvalid_repeat_byte:
    moveq #0,%d0
    moveb %a0@+,%d0
    moveq #0,%d1
    moveb %a1@+,%d1
    cmpl %d1,%d0
    bhi .Lvalid_bad
    subql #1,%d3
    bpl .Lvalid_repeat_byte
    tstb %a0@(-3)
    beq .Lvalid_bad
    subql #1,%d2
    bpl .Lvalid_repeat
    | Douze LFO, huit mots chacun ; aucun pointeur/phase sérialisé.
    moveq #11,%d2
.Lvalid_lfo:
    lea .Llfo_max,%a1
    moveq #7,%d3
.Lvalid_lfo_word:
    moveq #0,%d0
    movew %a0@+,%d0
    moveq #0,%d1
    movew %a1@+,%d1
    cmpl %d1,%d0
    bhi .Lvalid_bad
    subql #1,%d3
    bpl .Lvalid_lfo_word
    subql #1,%d2
    bpl .Lvalid_lfo
    .ifdef ML_STORAGE3
    moveq #5,%d2
.Lvalid_audio_lfo:
    lea .Laudio_lfo_max,%a1
    moveq #7,%d3
.Lvalid_audio_word:
    moveq #0,%d0
    movew %a0@+,%d0
    moveq #0,%d1
    movew %a1@+,%d1
    cmpil #4,%d3
    bne .Laudio_bound
    cmpil #0x7f00,%d0
    beq .Laudio_enum
.Laudio_bound:
    cmpl %d1,%d0
    bhi .Lvalid_bad
    cmpil #6,%d3
    beq .Laudio_enum
    cmpil #4,%d3
    beq .Laudio_enum
    cmpil #3,%d3
    beq .Laudio_enum
    cmpil #1,%d3
    bne .Laudio_next
.Laudio_enum:
    andil #255,%d0
    bne .Lvalid_bad
.Laudio_next:
    subql #1,%d3
    bpl .Lvalid_audio_word
    subql #1,%d2
    bpl .Lvalid_audio_lfo
    .endif
    .endif
    moveq #1,%d0
    bra .Lvalid_exit
.Lvalid_bad:
    moveq #0,%d0
.Lvalid_exit:
    moveml %sp@,%d2-%d3
    addql #8,%sp
    rts

ml_record_encode:
    lea.l %sp@(-16),%sp
    moveml %d2-%d3/%a2-%a3,%sp@
    moveal %sp@(20),%a2
    moveal %sp@(28),%a3
    movel %sp@(24),%d0
    cmpil #ML_RECORD_BYTES,%d0
    bne .Lenc_bad
    movel %sp@(32),%d2
    cmpil #95,%d2
    bhi .Lenc_bad
    movel %sp@(36),%d3
    cmpil #95,%d3
    bhi .Lenc_bad
    bsr .Lbuffers
    tstl %d0
    beq .Lenc_bad
    moveal %a3,%a0
    bsr .Lvalid
    tstl %d0
    beq .Lenc_bad
    movel #ML_RECORD_MAGIC,%a2@
    moveq #ML_RECORD_VERSION,%d0
    movel %d0,%a2@(4)
    movel #ML_DATA_BYTES,%d0
    movel %d0,%a2@(8)
    movel %d2,%a2@(12)
    movel %d3,%a2@(16)
    movel %sp@(40),%d0
    movel %d0,%a2@(20)
    moveal %a3,%a0
    lea.l %a2@(32),%a1
    bsr .Lcopy
    pea ML_DATA_BYTES
    pea %a2@(32)
    bsr ml_record_crc
    addql #8,%sp
    movel %d0,%a2@(24)
    pea 28
    movel %a2,%sp@-
    bsr ml_record_crc
    addql #8,%sp
    movel %d0,%a2@(28)
    moveq #1,%d0
    bra .Lcodec_done
.Lenc_bad:
    moveq #0,%d0
.Lcodec_done:
    moveml %sp@,%d2-%d3/%a2-%a3
    lea.l %sp@(16),%sp
    rts

ml_record_decode:
    lea.l %sp@(-16),%sp
    moveml %d2-%d3/%a2-%a3,%sp@
    moveal %sp@(20),%a3
    moveal %sp@(24),%a2
    movel %sp@(28),%d0
    cmpil #ML_RECORD_BYTES,%d0
    bne .Lenc_bad
    movel %sp@(32),%d2
    cmpil #95,%d2
    bhi .Lenc_bad
    movel %sp@(36),%d3
    cmpil #95,%d3
    bhi .Lenc_bad
    bsr .Lbuffers
    tstl %d0
    beq .Lenc_bad
    movel %a2@,%d0
    .ifdef ML_STORAGE3
    cmpil #0x4d424b32,%d0
    beq .Ldecode_v2
    .endif
    .ifdef ML_LIVE_REC
    cmpil #0x4d424b33,%d0
    bne .Ldecode_current
    movel %a2@(4),%d0
    cmpil #3,%d0
    bne .Lenc_bad
    | Ancien MBK3 : les bits réservés doivent toujours être zéro.
    lea %a2@(32),%a0
    moveq #5,%d0
.Ldecode_v3_lane:
    lea %a0@(8),%a0
    moveq #63,%d1
.Ldecode_v3_step:
    moveb %a0@(3),%d2
    andil #252,%d2
    bne .Lenc_bad
    addql #4,%a0
    subql #1,%d1
    bpl .Ldecode_v3_step
    subql #1,%d0
    bpl .Ldecode_v3_lane
    movel %sp@(32),%d2
    bra .Ldecode_payload
.Ldecode_current:
    .endif
    cmpil #ML_RECORD_MAGIC,%d0
    bne .Lenc_bad
    movel %a2@(4),%d0
    cmpil #ML_RECORD_VERSION,%d0
    bne .Lenc_bad
.Ldecode_payload:
    movel %a2@(8),%d0
    cmpil #ML_DATA_BYTES,%d0
    bne .Lenc_bad
    cmpl %a2@(12),%d2
    bne .Lenc_bad
    cmpl %a2@(16),%d3
    bne .Lenc_bad
    pea 28
    movel %a2,%sp@-
    bsr ml_record_crc
    addql #8,%sp
    cmpl %a2@(28),%d0
    bne .Lenc_bad
    pea ML_DATA_BYTES
    pea %a2@(32)
    bsr ml_record_crc
    addql #8,%sp
    cmpl %a2@(24),%d0
    bne .Lenc_bad
    lea.l %a2@(32),%a0
    bsr .Lvalid
    tstl %d0
    beq .Lenc_bad
    lea.l %a2@(32),%a0
    moveal %a3,%a1
    bsr .Lcopy
    moveq #1,%d0
    bra .Lcodec_done
    .ifdef ML_STORAGE3
.Ldecode_v2:
    movel %d3,%sp@-
    movel %d2,%sp@-
    pea 4928
    movel %a2,%sp@-
    movel %a3,%sp@-
    jsr ml_record_decode_v2
    lea %sp@(20),%sp
    tstl %d0
    beq .Lenc_bad
    pea %a3@(4896)
    jsr ml_audio_lfo_init
    addql #4,%sp
    moveq #1,%d0
    bra .Lcodec_done
    .section .rodata
.Laudio_lfo_max: .word 32767,5888,32767,8192,1536,32767,1024,32767
    .text
    .endif
.Lcopy:
    movel #(ML_DATA_BYTES/4-1),%d0
.Lcopy_loop:
    movel %a0@+,%d1
    movel %d1,%a1@+
    subql #1,%d0
    bpl .Lcopy_loop
    rts
.Lbuffers:
    moveq #0,%d0
    tstl %a2
    beq .Lbuf_done
    tstl %a3
    beq .Lbuf_done
    movel %a2,%d1
    movel %a3,%d0
    orl %d1,%d0
    andil #3,%d0
    bne .Lbuf_bad
    addil #ML_RECORD_BYTES,%d1
    bcs .Lbuf_bad
    cmpal %a2,%a3
    bcs .Lbuf_below
    cmpal %d1,%a3
    bcs .Lbuf_bad
    bra .Lbuf_ok
.Lbuf_below:
    movel %a3,%d1
    addil #ML_DATA_BYTES,%d1
    bcs .Lbuf_bad
    cmpal %d1,%a2
    bcs .Lbuf_bad
.Lbuf_ok:
    moveq #1,%d0
    rts
.Lbuf_bad:
    moveq #0,%d0
.Lbuf_done:
    rts

    .globl ml_record_select
| Deux copies validées dans un staging privé ; destination publiée seulement
| après choix de la génération. Compteur modulo 2^32, égalité favorise A.
| ml_record_select(dest,A,Asize,B,Bsize,slot,pattern) -> 0/1/2.
ml_record_select:
    lea.l %sp@(-ML_RECORD_BYTES),%sp
    moveml %d2-%d5/%a2-%a4,%sp@
    moveal %sp@(ML_RECORD_BYTES+4),%a2
    moveal %sp@(ML_RECORD_BYTES+8),%a3
    moveal %sp@(ML_RECORD_BYTES+16),%a4
    movel %sp@(ML_RECORD_BYTES+24),%d2
    movel %sp@(ML_RECORD_BYTES+28),%d3
    movel %sp@(ML_RECORD_BYTES+12),%d0
    movel %d3,%sp@-
    movel %d2,%sp@-
    movel %d0,%sp@-
    movel %a3,%sp@-
    lea.l %sp@(44),%a0
    movel %a0,%sp@-
    bsr ml_record_decode
    lea.l %sp@(20),%sp
    movel %d0,%d4
    movel %sp@(ML_RECORD_BYTES+20),%d0
    movel %d3,%sp@-
    movel %d2,%sp@-
    movel %d0,%sp@-
    movel %a4,%sp@-
    lea.l %sp@(44),%a0
    movel %a0,%sp@-
    bsr ml_record_decode
    lea.l %sp@(20),%sp
    movel %d0,%d5
    tstl %d4
    bne .Lselect_has_a
    tstl %d5
    beq .Lselect_done
    bra .Lselect_b
.Lselect_has_a:
    moveq #1,%d4
    tstl %d5
    beq .Lselect_publish
    movel %a4@(20),%d0
    subl %a3@(20),%d0
    beq .Lselect_publish
    cmpil #0x80000000,%d0
    bcc .Lselect_publish
.Lselect_b:
    moveal %a4,%a3
    moveq #2,%d4
.Lselect_publish:
    movel %d3,%sp@-
    movel %d2,%sp@-
    pea ML_RECORD_BYTES
    movel %a3,%sp@-
    movel %a2,%sp@-
    bsr ml_record_decode
    lea.l %sp@(20),%sp
    tstl %d0
    bne .Lselect_done
    moveq #0,%d4
.Lselect_done:
    movel %d4,%d0
    moveml %sp@,%d2-%d5/%a2-%a4
    lea.l %sp@(ML_RECORD_BYTES),%sp
    rts

    .ifdef ML_STORAGE2
    .section .rodata
.Lrepeat_max: .byte 1,16,127,255,5,4,63,165
    .balign 2
.Llfo_max: .word 32767,23,32767,128,6,32767,4,32767
    .endif
