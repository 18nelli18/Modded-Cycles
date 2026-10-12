| Chemin annexe commun MIDI/LFO : /ModdedCycles/00-XXXXXXXX/SEQ-00-A.
| ml_store_path(out,cap>=35,identité non nulle,pattern0..95,copie0..1,type0..2,slot0..95).
| type0=SEQ, type1=LFO, type2=WRK (checkpoint non validé). Construction privée ; arguments invalides sans écriture.
| Ne crée aucun dossier, ne lit aucun projet, aucune entrée disque.
    .text
    .globl ml_store_path
ml_store_path:
    lea.l %sp@(-64),%sp
    moveml %d2-%d5/%a2-%a3,%sp@
    moveq #0,%d5
    moveal %sp@(68),%a2
    tstl %a2
    beq .Lpath_done
    movel %sp@(72),%d0
    cmpil #35,%d0
    bcs .Lpath_done
    movel %sp@(76),%d2
    beq .Lpath_done
    movel %sp@(80),%d3
    cmpil #95,%d3
    bhi .Lpath_done
    movel %sp@(84),%d4
    cmpil #1,%d4
    bhi .Lpath_done
    movel %sp@(88),%d0
    cmpil #2,%d0
    bhi .Lpath_done
    movel %sp@(92),%d0
    cmpil #95,%d0
    bhi .Lpath_done
    lea.l %sp@(24),%a3
    lea.l .Lprefix,%a0
    moveq #13,%d1
.Lpath_prefix:
    moveb %a0@+,%a3@+
    subql #1,%d1
    bpl .Lpath_prefix
    movel %sp@(92),%d0
    divuw #10,%d0
    movel %d0,%d1
    andil #65535,%d1
    addil #48,%d1
    moveb %d1,%a3@+
    swap %d0
    addil #48,%d0
    moveb %d0,%a3@+
    moveb #45,%a3@+
    lea.l .Lhex,%a0
    moveq #7,%d1
.Lpath_id:
    movel %d2,%d0
    lsrl #8,%d0
    lsrl #8,%d0
    lsrl #8,%d0
    lsrl #4,%d0
    lsll #4,%d2
    andil #15,%d0
    moveb %a0@(0,%d0:l),%a3@+
    subql #1,%d1
    bpl .Lpath_id
    moveb #47,%a3@+
    lea.l .Lsequence,%a0
    tstl %sp@(88)
    beq .Lpath_kind
    lea.l .Llfo,%a0
    movel %sp@(88),%d0
    cmpil #2,%d0
    bne .Lpath_kind
    lea.l .Lworking,%a0
.Lpath_kind:
    moveb %a0@+,%a3@+
    moveb %a0@+,%a3@+
    moveb %a0@+,%a3@+
    moveb #45,%a3@+
    divuw #10,%d3
    movel %d3,%d0
    andil #65535,%d0
    addil #48,%d0
    moveb %d0,%a3@+
    swap %d3
    addil #48,%d3
    moveb %d3,%a3@+
    moveb #45,%a3@+
    addil #65,%d4
    moveb %d4,%a3@+
    clrb %a3@
    lea.l %sp@(24),%a0
    moveq #34,%d1
.Lpath_copy:
    moveb %a0@+,%a2@+
    subql #1,%d1
    bpl .Lpath_copy
    moveq #1,%d5
.Lpath_done:
    movel %d5,%d0
    moveml %sp@,%d2-%d5/%a2-%a3
    lea.l %sp@(64),%sp
    rts
    .section .rodata
.Lprefix: .ascii "/ModdedCycles/"
.Lhex: .ascii "0123456789ABCDEF"
.Lsequence: .ascii "SEQ"
.Llfo: .ascii "LFO"
.Lworking: .ascii "WRK"
