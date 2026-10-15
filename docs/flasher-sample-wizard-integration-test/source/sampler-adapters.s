| Sampler seul : capture de la note au trig, sans moteur de slides TG.
| Les six arguments et le résultat du constructeur natif restent exacts.
    .text
    .globl sm_seq_capture,sm_live_note_capture
sm_seq_capture:
    movel %sp@(24),%sp@-
    movel %sp@(24),%sp@-
    movel %sp@(24),%sp@-
    movel %sp@(24),%sp@-
    movel %sp@(24),%sp@-
    movel %sp@(24),%sp@-
    jsr 0x400548ce
    lea %sp@(24),%sp
    lea %sp@(-28),%sp
    moveml %d0-%d3/%a0-%a2,%sp@
    tstl %d0
    beq .Lseq_done
    movel %sp@(32),%d2
    cmpil #5,%d2
    bhi .Lseq_done
    movel %sp@(44),%d3
    cmpil #63,%d3
    bhi .Lseq_done
    moveal %sp@(36),%a0
    tstl %a0
    beq .Lseq_done
    movel %d2,%d1
    muluw #722,%d1
    addal %d1,%a0
    lea %a0@(580),%a1
    mvsb %a1@(0,%d3:l),%d0
    bpl .Lseq_note
    mvsb %a0@(712),%d0
.Lseq_note:
    lea live_note,%a1
    moveb %d0,%a1@(0,%d2:l)
.Lseq_done:
    moveml %sp@,%d0-%d3/%a0-%a2
    lea %sp@(28),%sp
    moveal %sp@+,%a1
    lea %sp@(24),%sp
    jmp %a1@

| Note-on natif : conserver la note jouée sans installer Scale Lock TG.
sm_live_note_capture:
    cmpl %d3,%d0
    bcs.w .Llive_reject
    lea %sp@(-8),%sp
    moveml %d1/%a0,%sp@
    cmpil #5,%d2
    bhi .Llive_done
    cmpil #127,%d3
    bhi .Llive_done
    lea live_note,%a0
    moveb %d3,%a0@(0,%d2:l)
.Llive_done:
    moveml %sp@,%d1/%a0
    lea %sp@(8),%sp
    cmpl %d3,%d0
    bcc .Llive_native
.Llive_reject:
    jmp 0x4008190e
.Llive_native:
    jmp 0x40081742
