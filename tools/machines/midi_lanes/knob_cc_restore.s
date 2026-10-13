| Restauration CC au Note Off physique, jamais au pas suivant.
| UI : take/sent/off. Producteur : remember, sans API MIDI ni allocation.
    .data
    .balign 4
.Lpending: .space 576
.Lactive: .space 576
.Ltaken: .space 8
.Lhistory:
    .rept 768
    .byte 255
    .endr
    .text
    .globl mlkcr_remember,mlkcr_take,mlkcr_sent,mlkcr_off
| remember(slot,CC) : capturer la note tenue et la base connue avant le lock.
mlkcr_remember:
    lea %sp@(-16),%sp
    moveml %d2-%d3/%a2-%a3,%sp@
    movel %sp@(20),%d2
    cmpil #71,%d2
    bhi .Lremember_done
    movel %d2,%d0
    lsll #3,%d0
    lea .Lpending,%a2
    addal %d0,%a2
    clrl %a2@
    clrl %a2@(4)
    divuw #12,%d2
    andil #65535,%d2
    movel %d2,%d0
    lsll #3,%d0
    moveal ml_runtime,%a0
    tstl %a0
    beq .Lremember_done
    lea %a0@(272),%a0
    movel %a0@(0,%d0:l),%d3
    tstl %d3
    beq .Lremember_done
    movel %d2,%d0
    muluw #128,%d0
    addl %sp@(24),%d0
    lea .Lhistory,%a3
    addal %d0,%a3
    movel %sp@(20),%d0
    addl %d0,%d0
    lea mlkc_state,%a0
    addal %d0,%a0
    moveq #0,%d0
    moveb %a0@,%d0
    cmpl %sp@(24),%d0
    bne .Lremember_history
    moveb %a0@(1),%a3@
.Lremember_history:
    moveq #0,%d0
    moveb %a3@,%d0
    cmpil #127,%d0
    bhi .Lremember_done
    movel %d3,%a2@
    | Paquet de base : canal et port de la note réellement acceptée.
    andil #0x0f0000ff,%d3
    oril #0xb0000000,%d3
    lsll #8,%d0
    orl %d0,%d3
    movel %sp@(24),%d0
    swap %d0
    orl %d0,%d3
    movel %d3,%a2@(4)
.Lremember_done:
    moveml %sp@,%d2-%d3/%a2-%a3
    lea %sp@(16),%sp
    rts
| Appelé sous le verrou de take ; d1=slot, d0=paquet préservés.
mlkcr_take:
    movel %d1,%sp@-
    lsll #3,%d1
    lea .Lpending,%a0
    addal %d1,%a0
    movel %a0@,%d1
    movel %d1,.Ltaken
    movel %a0@(4),%d1
    movel %d1,.Ltaken+4
    movel %sp@+,%d1
    rts
| Après envoi réel du lock ; publication cohérente, IRQ ne lit pas active.
mlkcr_sent:
    movel mlkcq_taken,%d0
    lsll #3,%d0
    lea .Lactive,%a0
    addal %d0,%a0
    movel .Ltaken,%d0
    movel %d0,%a0@
    movel .Ltaken+4,%d0
    movel %d0,%a0@(4)
    rts
| off(paquet) : worker séquence seulement ; conserver tous les registres.
mlkcr_off:
    lea %sp@(-32),%sp
    moveml %d2-%d4/%a2,%sp@
    movel %sp@(36),%d2
    movel %d2,%d0
    andil #0xf0000000,%d0
    cmpil #0x80000000,%d0
    bne .Loff_done
    andil #0xffff00ff,%d2
    lea .Lactive,%a2
    moveq #71,%d3
.Loff_loop:
    cmpl %a2@,%d2
    bne .Loff_next
    movel %a2@(4),%d4
    clrl %a2@
    clrl %a2@(4)
    tstl %d4
    beq .Loff_next
    movel %d4,%sp@(20)
    andil #255,%d4
    lea %sp@(20),%a0
    movel %d4,%sp@-
    movel %a0,%sp@-
    pea 3
    jsr 0x400826b0
    lea %sp@(12),%sp
.Loff_next:
    lea %a2@(8),%a2
    subql #1,%d3
    bpl .Loff_loop
.Loff_done:
    moveml %sp@,%d2-%d4/%a2
    lea %sp@(32),%sp
    rts
