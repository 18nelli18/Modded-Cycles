| Prototype CC pour deux LFO par voie B : contexte privé868 octets, initialement nul.
| 72 cases {paquet en attente,dernier retiré,dirty}, curseur à864.
| put(ctx,slot0..11,canal0..15,cc0..127,valeur0..127,port2..4) -> accepté.
| Coalescer par LFO : la modulation rapide ne remplit pas la file de notes.
| take(ctx) -> paquet [status,CC,valeur,port], exclusivement IPL0.
| Aucun appel MIDI, allocation ou attente ; non raccordé au firmware.
    .text
    .globl mlkcq_put,mlkcq_take
mlkcq_put:
    lea.l %sp@(-16),%sp
    moveml %d2-%d4/%a2,%sp@
    moveq #0,%d0
    moveal %sp@(20),%a2
    tstl %a2
    beq .Lput_done
    movel %a2,%d1
    andil #3,%d1
    bne .Lput_done
    movel %sp@(24),%d1
    cmpil #71,%d1
    bhi .Lput_done
    movel %d1,%d2
    lsll #3,%d1
    lsll #2,%d2
    addl %d2,%d1
    addal %d1,%a2
    movel %sp@(28),%d2
    cmpil #15,%d2
    bhi .Lput_done
    oril #0xb0,%d2
    lsll #8,%d2
    movel %sp@(32),%d1
    cmpil #127,%d1
    bhi .Lput_done
    orl %d1,%d2
    lsll #8,%d2
    movel %sp@(36),%d1
    cmpil #127,%d1
    bhi .Lput_done
    orl %d1,%d2
    lsll #8,%d2
    movel %sp@(40),%d1
    cmpil #2,%d1
    bcs .Lput_done
    cmpil #4,%d1
    bhi .Lput_done
    orl %d1,%d2
    movew %sr,%d4
    movew #0x2700,%sr
    movel %d2,%a2@
    moveq #1,%d3
    movel %d3,%a2@(8)
    movew %d4,%sr
    moveq #1,%d0
.Lput_done:
    moveml %sp@,%d2-%d4/%a2
    lea.l %sp@(16),%sp
    rts
mlkcq_take:
    lea.l %sp@(-16),%sp
    moveml %d2-%d3/%a2-%a3,%sp@
    moveq #0,%d0
    movew %sr,%d3
    movel %d3,%d1
    andil #0x700,%d1
    bne .Ltake_done
    moveal %sp@(20),%a2
    tstl %a2
    beq .Ltake_done
    movel %a2,%d1
    andil #3,%d1
    bne .Ltake_done
    movel %a2@(864),%d2
    cmpil #71,%d2
    bhi .Ltake_done
    movew #0x2700,%sr
    moveq #71,%d1
.Lscan:
    movel %d2,%d0
    lsll #3,%d0
    moveal %d0,%a3
    movel %d2,%d0
    lsll #2,%d0
    addal %d0,%a3
    addal %a2,%a3
    addql #1,%d2
    cmpil #72,%d2
    bcs .Lcursor
    moveq #0,%d2
.Lcursor:
    tstl %a3@(8)
    bne .Lfound
    subql #1,%d1
    bpl .Lscan
    moveq #0,%d0
    bra .Lrestore
.Lfound:
    movel %a3,%d1
    subl %a2,%d1
    divuw #12,%d1
    andil #65535,%d1
    movel %d1,mlkcq_taken
    movel %a3@,%d0
    movel %d0,%a3@(4)
    clrl %a3@(8)
    movel %d2,%a2@(864)
.Lrestore:
    movew %d3,%sr
.Ltake_done:
    moveml %sp@,%d2-%d3/%a2-%a3
    lea.l %sp@(16),%sp
    rts
    .data
    .balign 4
    .globl mlkcq_owner,mlkcq_taken
mlkcq_owner: .long 0
mlkcq_taken: .long 0
    .globl mlkc_queue
mlkc_queue:
.Lqueue: .space 868
    .text
    .globl mlkcq_reset,mlkcq_ready,mlkcq_step,mlkcq_worker
mlkcq_reset:
    .ifdef ML_CC_SLIDES
    jsr mlkc_slide_cancel
    .endif
    movew %sr,%d0
    movel %d0,%sp@-
    movew #0x2700,%sr
    lea .Lqueue,%a0
    moveq #0,%d0
    movel #216,%d1
.Lreset_loop:
    movel %d0,%a0@+
    subql #1,%d1
    bpl .Lreset_loop
    clrl mlkcq_owner
    movel %sp@+,%d0
    movew %d0,%sr
    rts
mlkcq_ready:
    lea .Lqueue,%a0
    moveq #71,%d1
.Lready_next:
    tstl %a0@(8)
    bne .Lready_yes
    lea %a0@(12),%a0
    subql #1,%d1
    bpl .Lready_next
    moveq #0,%d0
    rts
.Lready_yes:
    moveq #1,%d0
    rts
| step(pattern,voie,pas) : seulement après un vrai trig accepté par le séquenceur.
mlkcq_step:
    lea %sp@(-28),%sp
    moveml %d2-%d5/%a2-%a4,%sp@
    moveal %sp@(32),%a2
    movel %sp@(36),%d2
    movel %sp@(40),%d3
    cmpil #5,%d2
    bhi .Lqs_done
    cmpil #63,%d3
    bhi .Lqs_done
    clrl %sp@-
    movel %a2,%sp@-
    jsr mlkc_locks_for
    addql #8,%sp
    moveal %d0,%a3
    cmpal mlkcq_owner,%a2
    beq .Lqs_owner
    jsr mlkcq_reset
    movel %a2,mlkcq_owner
.Lqs_owner:
    movel %d2,%d0
    muluw #264,%d0
    addal %d0,%a2
    movel %d2,%d0
    muluw #1536,%d0
    movel %d3,%d1
    muluw #24,%d1
    addl %d1,%d0
    tstl %a3
    beq .Lqs_no_extension
    addal %d0,%a3
.Lqs_no_extension:
    lea mlkc_state,%a4
    movel %d2,%d0
    muluw #24,%d0
    addal %d0,%a4
    movel %d2,%d3
    muluw #12,%d3
    moveq #11,%d5
.Lqs_loop:
    moveq #0,%d4
    tstl %a3
    beq .Lqs_base
    movew %a3@+,%d4
    cmpil #0xffff,%d4
    bne .Lqs_validate
.Lqs_base:
    | Restaurer uniquement sur une vraie note sans lock pour ce potard.
    | Un repos ou un trig de paramètres ne modifie jamais la base.
    movel %sp@(40),%d0
    lsll #2,%d0
    lea %a2@(8,%d0:l),%a0
    btst #0,%a0@(3)
    beq .Lqs_next
    movel %d3,%d0
    muluw #12,%d0
    lea .Lqueue,%a0
    addal %d0,%a0
    tstl %a0@
    beq .Lqs_next
    moveb %a0@(1),%d0
    cmpb %a4@,%d0
    bne .Lqs_next
    movew %a4@,%d4
.Lqs_validate:
    cmpil #0x7f7f,%d4
    bhi .Lqs_next
    movel %d4,%d0
    andil #128,%d0
    bne .Lqs_next
    moveq #0,%d0
    moveb %a2@(3),%d0
    movel %d0,%sp@-
    movel %d4,%d0
    andil #127,%d0
    movel %d0,%sp@-
    lsrl #8,%d4
    movel %d4,%sp@-
    moveq #0,%d0
    moveb %a2@(2),%d0
    movel %d0,%sp@-
    movel %d3,%sp@-
    pea .Lqueue
    jsr mlkcq_put
    lea %sp@(24),%sp
.Lqs_next:
    addql #2,%a4
    addql #1,%d3
    subql #1,%d5
    bpl .Lqs_loop
.Lqs_done:
    .ifdef ML_CC_SLIDES
    movel %sp@(40),%sp@-
    movel %sp@(40),%sp@-
    movel %sp@(40),%sp@-
    jsr mlkc_slide_arm
    lea %sp@(12),%sp
    .endif
    moveml %sp@,%d2-%d5/%a2-%a4
    lea %sp@(28),%sp
    rts
| Huit retraits maximum ; notes/Note Off servis avant cet appel dans worker.
mlkcq_worker:
    lea %sp@(-20),%sp
    moveml %d2-%d3/%a2-%a3,%sp@
    movew %sr,%d0
    andil #0x700,%d0
    bne .Lqw_done
    tstl 0x40fe4228
    beq .Lqw_done
    moveal mlkcq_owner,%a2
    tstl %a2
    beq .Lqw_done
    cmpal ml_play_pattern,%a2
    bne .Lqw_reset
    moveal ml_clock_state,%a0
    tstl %a0
    beq .Lqw_reset
    movel %a0@,%d0
    subql #1,%d0
    bne .Lqw_reset
    moveq #7,%d2
.Lqw_loop:
    pea .Lqueue
    jsr mlkcq_take
    addql #4,%sp
    tstl %d0
    beq .Lqw_done
    movel %d0,%sp@(16)
    movel mlkcq_taken,%d1
    divuw #12,%d1
    andil #65535,%d1
    muluw #264,%d1
    lea %a2@(0,%d1:l),%a3
    tstb %a3@
    beq .Lqw_next
    tstb %a3@(1)
    bne .Lqw_next
    movel %d0,%d1
    lsrl #8,%d1
    lsrl #8,%d1
    lsrl #8,%d1
    andil #15,%d1
    moveq #0,%d3
    moveb %a3@(2),%d3
    cmpl %d3,%d1
    bne .Lqw_next
    andil #255,%d0
    moveq #0,%d1
    moveb %a3@(3),%d1
    cmpl %d1,%d0
    bne .Lqw_next
    lea %sp@(16),%a0
    movel %d0,%sp@-
    movel %a0,%sp@-
    pea 3
    jsr 0x400826b0
    lea %sp@(12),%sp
.Lqw_next:
    subql #1,%d2
    bpl .Lqw_loop
    bra .Lqw_done
.Lqw_reset:
    jsr mlkcq_reset
.Lqw_done:
    moveml %sp@,%d2-%d3/%a2-%a3
    lea %sp@(20),%sp
    rts
