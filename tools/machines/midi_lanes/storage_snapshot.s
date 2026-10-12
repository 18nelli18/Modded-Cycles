| Snapshot UI stable d'une banque, 1584 octets ; aucun I/O ; copie bornée protégée contre Generate en IRQ.
| ml_store_snapshot(pattern,out,1584). L'appelant UI sérialise les éditions
| et changements de pattern ; les IRQ ne doivent que lire cette banque.
| Source/destination alignées, disjointes, sans débordement ; non raccordé.
    .ifdef ML_STORAGE2
    .equ ML_DATA_BYTES,4896
    .equ ML_RECORD_BYTES,4928
    .else
    .equ ML_DATA_BYTES,1584
    .equ ML_RECORD_BYTES,1616
    .endif
    .text
    .globl ml_store_snapshot
ml_store_snapshot:
    moveq #0,%d0
    movew %sr,%d1
    andil #0x700,%d1
    bne .Lsnap_done
    moveal %sp@(4),%a0
    moveal %sp@(8),%a1
    tstl %a0
    beq .Lsnap_done
    tstl %a1
    beq .Lsnap_done
    movel %a0,%d1
    andil #3,%d1
    bne .Lsnap_done
    movel %a1,%d1
    andil #3,%d1
    bne .Lsnap_done
    movel %sp@(12),%d1
    cmpil #ML_DATA_BYTES,%d1
    bne .Lsnap_done
    movel %a0,%d1
    addil #ML_DATA_BYTES,%d1
    bcs .Lsnap_done
    movel %a1,%d0
    addil #ML_DATA_BYTES,%d0
    bcs .Lsnap_bad
    cmpal %a0,%a1
    bcs .Lsnap_below
    cmpal %d1,%a1
    bcs .Lsnap_bad
    bra .Lsnap_copy
.Lsnap_below:
    cmpl %a0,%d0
    bhi .Lsnap_bad
.Lsnap_copy:
    movew %sr,%d0
    movel %d0,%sp@-
    movew #0x2700,%sr
    movel #(ML_DATA_BYTES/4-1),%d1
.Lsnap_loop:
    movel %a0@+,%d0
    movel %d0,%a1@+
    subql #1,%d1
    bpl .Lsnap_loop
    movel %sp@+,%d1
    movew %d1,%sr
    moveq #1,%d0
    rts
.Lsnap_bad:
    moveq #0,%d0
.Lsnap_done:
    rts
