| Assemble un snapshot MBK2 depuis trois blocs privés UI, jamais depuis IRQ.
| pack(notes1584,locks3120,lfo192,out4896) ->0/1.
| Toutes les sources et la destination sont alignées ; aucune source ne peut
| chevaucher la sortie. Validation complète des plages avant la première copie.
    .text
    .globl ml_store_pack
ml_store_pack:
    lea.l %sp@(-24),%sp
    moveml %d2-%d3/%a2-%a4,%sp@
    moveq #0,%d0
    movew %sr,%d1
    andil #0x700,%d1
    bne .Lpack_done
    moveal %sp@(40),%a2
    tstl %a2
    beq .Lpack_done
    movel %a2,%d2
    movel %d2,%d1
    andil #3,%d1
    bne .Lpack_done
    addil #4896,%d2
    bcs .Lpack_done
    lea.l %sp@(28),%a3
    lea.l .Lpack_sizes,%a4
    moveq #2,%d3
.Lpack_check:
    moveal %a3@+,%a0
    tstl %a0
    beq .Lpack_bad
    movel %a0,%d1
    andil #3,%d1
    bne .Lpack_bad
    movel %a0,%d1
    addl %a4@+,%d1
    bcs .Lpack_bad
    cmpal %a2,%a0
    bcs .Lpack_below
    cmpal %d2,%a0
    bcs .Lpack_bad
    bra .Lpack_next
.Lpack_below:
    cmpl %a2,%d1
    bhi .Lpack_bad
.Lpack_next:
    subql #1,%d3
    bpl .Lpack_check
    lea.l %sp@(28),%a3
    lea.l .Lpack_sizes,%a4
    moveq #2,%d3
.Lpack_block:
    moveal %a3@+,%a0
    movel %a4@+,%d1
    lsrl #2,%d1
.Lpack_copy:
    movel %a0@+,%d0
    movel %d0,%a2@+
    subql #1,%d1
    bne .Lpack_copy
    subql #1,%d3
    bpl .Lpack_block
    moveq #1,%d0
    bra .Lpack_done
.Lpack_bad:
    moveq #0,%d0
.Lpack_done:
    moveml %sp@,%d2-%d3/%a2-%a4
    lea.l %sp@(24),%sp
    rts
    .section .rodata
.Lpack_sizes: .long 1584,3120,192
