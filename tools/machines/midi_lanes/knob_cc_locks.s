| Locks CC B : six voies x64 pas x12 potards x2 octets =9216 octets.
| Mot {CC,valeur}, 0xffff vide. Le numéro est figé au lock, indépendamment
| d'une réassignation future du potard. Aucun accès audio/MIDI/disque ici.
    .text
    .globl mlkc_lock_init,mlkc_lock_at,mlkc_lock_get,mlkc_lock_set
    .globl mlkc_lock_clear,mlkc_lock_copy
mlkc_lock_init:
    moveal %sp@(4),%a0
    moveq #0,%d0
    tstl %a0
    beq .Lli_done
    movel %a0,%d1
    andil #3,%d1
    bne .Lli_done
    movel #2303,%d1
    moveq #-1,%d0
.Lli_loop:
    movel %d0,%a0@+
    subql #1,%d1
    bpl .Lli_loop
    moveq #1,%d0
.Lli_done:
    rts
| at(buf,voie,pas,potard) -> adresse ou0 ; aucun état global.
mlkc_lock_at:
    moveq #0,%d0
    moveal %sp@(4),%a0
    tstl %a0
    beq .Lla_done
    movel %a0,%d1
    andil #3,%d1
    bne .Lla_done
    movel %sp@(8),%d1
    cmpil #5,%d1
    bhi .Lla_done
    muluw #1536,%d1
    addal %d1,%a0
    movel %sp@(12),%d1
    cmpil #63,%d1
    bhi .Lla_done
    muluw #24,%d1
    addal %d1,%a0
    movel %sp@(16),%d1
    cmpil #11,%d1
    bhi .Lla_done
    addl %d1,%d1
    addal %d1,%a0
    movel %a0,%d0
.Lla_done:
    rts
mlkc_lock_get:
    movel %sp@(16),%sp@-
    movel %sp@(16),%sp@-
    movel %sp@(16),%sp@-
    movel %sp@(16),%sp@-
    bsr mlkc_lock_at
    lea %sp@(16),%sp
    tstl %d0
    beq .Llg_bad
    moveal %d0,%a0
    moveq #0,%d0
    movew %a0@,%d0
    rts
.Llg_bad:
    moveq #-1,%d0
    rts
mlkc_lock_set:
    moveq #0,%d0
    movew %sr,%d1
    andil #0x700,%d1
    bne .Lls_done
    movel %sp@(20),%d1
    cmpil #127,%d1
    bhi .Lls_done
    movel %sp@(24),%d1
    cmpil #127,%d1
    bhi .Lls_done
    movel %sp@(16),%sp@-
    movel %sp@(16),%sp@-
    movel %sp@(16),%sp@-
    movel %sp@(16),%sp@-
    bsr mlkc_lock_at
    lea %sp@(16),%sp
    tstl %d0
    beq .Lls_done
    moveal %d0,%a0
    movel %sp@(20),%d1
    lsll #8,%d1
    orl %sp@(24),%d1
    movew %d1,%a0@
    moveq #1,%d0
.Lls_done:
    rts
| clear(buf,voie,pas) ; six longwords sous masque court.
mlkc_lock_clear:
    clrl %sp@-
    movel %sp@(16),%sp@-
    movel %sp@(16),%sp@-
    movel %sp@(16),%sp@-
    bsr mlkc_lock_at
    lea %sp@(16),%sp
    tstl %d0
    beq .Llc_done
    moveal %d0,%a0
    movew %sr,%d0
    movel %d0,%sp@-
    movew #0x2700,%sr
    moveq #-1,%d0
    moveq #5,%d1
.Llc_loop:
    movel %d0,%a0@+
    subql #1,%d1
    bpl .Llc_loop
    movel %sp@+,%d1
    movew %d1,%sr
    moveq #1,%d0
.Llc_done:
    rts
| copy(dst,voie,pas,src,voie,pas), adresses distinctes ou identiques permises.
mlkc_lock_copy:
    movel %a2,%sp@-
    clrl %sp@-
    movel %sp@(20),%sp@-
    movel %sp@(20),%sp@-
    movel %sp@(20),%sp@-
    bsr mlkc_lock_at
    lea %sp@(16),%sp
    tstl %d0
    beq .Llcopy_done
    moveal %d0,%a2
    clrl %sp@-
    movel %sp@(32),%sp@-
    movel %sp@(32),%sp@-
    movel %sp@(32),%sp@-
    bsr mlkc_lock_at
    lea %sp@(16),%sp
    tstl %d0
    beq .Llcopy_done
    moveal %d0,%a0
    movew %sr,%d0
    movel %d0,%sp@-
    movew #0x2700,%sr
    moveq #5,%d1
.Llcopy_loop:
    movel %a0@+,%a2@+
    subql #1,%d1
    bpl .Llcopy_loop
    movel %sp@+,%d1
    movew %d1,%sr
    moveq #1,%d0
.Llcopy_done:
    moveal %sp@+,%a2
    rts
