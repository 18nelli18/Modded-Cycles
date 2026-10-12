| Note 57 : ordonnanceur privé, appelé une fois par bloc audio après le temps
| musical natif. ml_clock(runtime,pattern,state,now,playing) -> pas traités.
| State 52 octets : mode (0 arrêt, 1 lecture, 2 pause), puis six couples
| deadline/next-step (longs). En pause, deadline devient un délai restant.
| now = heure native 0x8000184c, noire = 21 600 000 unités ; aucun préfetch.
| Vitesses privées 1/4, 1/2, 1, 3/2, 2, 3, 4 ; index 2 = pas de double croche.
| Un pas maximum par voie/appel ; saut tardif resynchronisé sans rafale.
| Écrit seulement la file privée, jamais un port physique ni une piste sonore.
    .text
    .globl ml_clock
ml_clock:
    lea.l %sp@(-40),%sp
    movem.l %d2-%d6/%a2-%a5,%sp@
    movew %sr,%d0
    movel %d0,%sp@(36)
    moveal %sp@(44),%a2
    moveal %sp@(48),%a3
    moveal %sp@(52),%a4
    movel %sp@(56),%d4
    moveq #0,%d6
    tstl %sp@(60)
    beq .Lclock_stop
    movel %sp@(60),%d0
    cmpil #2,%d0
    beq .Lclock_pause
    movel %a4@,%d0
    cmpil #2,%d0
    beq .Lclock_resume
    tstl %a4@
    bne .Lclock_running
    .ifdef ML_CONDITIONS
    pea ml_cond_history
    jsr ml_cond_init
    addql #4,%sp
    .endif
    moveq #1,%d0
    movel %d0,%a4@
    lea.l %a4@(4),%a0
    moveq #5,%d0
.Lclock_start:
    movel %d4,%a0@+
    clrl %a0@+
    subql #1,%d0
    bpl .Lclock_start
    bra .Lclock_running
.Lclock_resume:
    lea.l %a4@(4),%a0
    moveq #5,%d0
.Lclock_resume_loop:
    addl %d4,%a0@
    lea.l %a0@(8),%a0
    subql #1,%d0
    bpl .Lclock_resume_loop
    moveq #1,%d0
    movel %d0,%a4@
.Lclock_running:
    lea.l %a4@(4),%a5
    moveq #0,%d2
.Lclock_lane:
    tstb %a3@
    beq .Lclock_silent
    tstb %a3@(1)
    beq .Lclock_config
.Lclock_silent:
    movel %d2,%sp@-
    movel %a2,%sp@-
    jsr ml_stop
    addql #8,%sp
.Lclock_config:
    moveq #0,%d3
    moveb %a3@(4),%d3
    subql #1,%d3
    cmpil #63,%d3
    bhi .Lclock_release
    moveq #0,%d0
    moveb %a3@(5),%d0
    cmpil #6,%d0
    bhi .Lclock_release
    movel %d4,%d1
    subl %a5@,%d1
    bmi .Lclock_next
    lea.l .Lclock_durations,%a0
    movel %a0@(0,%d0:l:4),%d5
    movel %a5@(4),%d0
    cmpl %d3,%d0
    bls .Lclock_step_valid
    moveq #0,%d0
.Lclock_step_valid:
    movel %d0,%a5@(4)
    movel %d0,%sp@-
    movel %d2,%sp@-
    moveal %sp@(56),%a0
    movel %a0,%sp@-
    movel %a2,%sp@-
    jsr ml_pattern_tick
    lea.l %sp@(16),%sp
    addql #1,%d6
    movel %a5@(4),%d0
    addql #1,%d0
    cmpl %d3,%d0
    bls .Lclock_save_step
    .ifdef ML_CONDITIONS
    movel %d2,%sp@-
    pea ml_cond_history
    jsr ml_cond_advance
    addql #8,%sp
    .endif
    moveq #0,%d0
.Lclock_save_step:
    movel %d0,%a5@(4)
    movel %a5@,%d0
    addl %d5,%d0
    movel %d4,%d1
    subl %d0,%d1
    bmi .Lclock_save_deadline
    movel %d4,%d0
    addl %d5,%d0
.Lclock_save_deadline:
    movel %d0,%a5@
    bra .Lclock_next
.Lclock_release:
    movel %d2,%sp@-
    movel %a2,%sp@-
    jsr ml_stop
    addql #8,%sp
    movel %d4,%a5@
.Lclock_next:
    lea.l %a5@(8),%a5
    lea.l %a3@(264),%a3
    addql #1,%d2
    cmpil #6,%d2
    bne .Lclock_lane
    bra .Lclock_done
.Lclock_pause:
    movel %a4@,%d0
    cmpil #1,%d0
    bne .Lclock_done
    moveq #2,%d0
    movel %d0,%a4@
    lea.l %a4@(4),%a5
    moveq #0,%d2
.Lclock_pause_loop:
    movel %a5@,%d0
    subl %d4,%d0
    bpl .Lclock_remaining
    moveq #0,%d0
.Lclock_remaining:
    movel %d0,%a5@
    movel %d2,%sp@-
    movel %a2,%sp@-
    jsr ml_stop
    addql #8,%sp
    lea.l %a5@(8),%a5
    addql #1,%d2
    cmpil #6,%d2
    bne .Lclock_pause_loop
    bra .Lclock_done
.Lclock_stop:
    tstl %a4@
    beq .Lclock_done
    clrl %a4@
    moveq #0,%d2
.Lclock_stop_loop:
    movel %d2,%sp@-
    movel %a2,%sp@-
    jsr ml_stop
    addql #8,%sp
    addql #1,%d2
    cmpil #6,%d2
    bne .Lclock_stop_loop
.Lclock_done:
    movel %d6,%d0
    movel %sp@(36),%d1
    movem.l %sp@,%d2-%d6/%a2-%a5
    lea.l %sp@(40),%sp
    movew %d1,%sr
    rts
    .balign 4
.Lclock_durations:
    .globl ml_clock_durations
ml_clock_durations:
    .long 21600000,10800000,5400000,3600000,2700000,1800000,1350000
