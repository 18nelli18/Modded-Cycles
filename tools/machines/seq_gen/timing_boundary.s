| Frontiere MIDI : meme choix Loop/Page que le menu commun, sans changer D1.
    .text
    .globl timing_boundary
timing_boundary:
    tstl QUEUE_MODE
    beqs loop
    movel %d1,%sp@-
    andil #15,%d1
    beqs page
    movel %sp@+,%d1
    rts
page:
    movel %sp@+,%d1
    jmp BANK_CONT
loop:
    tstl %d1
    bnes done
    jmp BANK_CONT
done:
    rts
