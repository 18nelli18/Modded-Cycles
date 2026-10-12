| Raccordement du vrai ml_pattern_tick sous ML_REPEAT.
| locked_step(runtime,lane,packet,gate_steps,step) ; réglages du pattern publié.
| Pas sans lock actif : chemin MIDI normal. Repos : laisser finir le retrigger.
| Nouveau pas joué : terminer l'ancien propriétaire avant d'armer le nouveau.
    .text
    .globl ml_repeat_locked_step
ml_repeat_locked_step:
    lea.l %sp@(-56),%sp
    movem.l %d2-%d5/%a2-%a5,%sp@
    movew %sr,%d0
    movel %d0,%sp@(32)
    movew #0x2700,%sr
    moveal %sp@(60),%a2
    movel %sp@(64),%d2
    movel %sp@(68),%d3
    movel %sp@(72),%d4
    cmpil #5,%d2
    bhi .Lstep_normal
    lea.l ml_repeat_states,%a3
    movel %d2,%d0
    muluw #20,%d0
    addal %d0,%a3
    tstl %d3
    bne .Lstep_note
    tstl %a3@
    beq .Lstep_normal
    moveq #1,%d0
    bra .Lstep_done
.Lstep_note:
    moveal ml_repeat_play_settings,%a4
    tstl %a4
    beq .Lstep_cancel_normal
    movel %d2,%d0
    muluw #520,%d0
    addal %d0,%a4
    .ifdef ML_CHANCE
    | Décision unique par trig, avant armement ; jamais à chaque répétition.
    lea.l ml_chance_seeds,%a0
    movel %d2,%d0
    lsll #2,%d0
    addal %d0,%a0
    movel %a0,%sp@-
    jsr ml_chance_sample
    addql #4,%sp
    .ifdef ML_CONDITIONS
    movel %d0,%d5
    movel %sp@(76),%d0
    lsll #3,%d0
    lea.l %a4@(8),%a0
    clrl %sp@(48)
    moveq #0,%d1
    moveb %a0@(7,%d0:l),%d1
    beq .Lstep_condition_default
    moveq #1,%d0
    movel %d0,%sp@(48)
    bra .Lstep_condition_value
.Lstep_condition_default:
    moveb %a4@(7),%d1
.Lstep_condition_value:
    cmpil #102,%d1
    bcs .Lstep_percent
    cmpil #165,%d1
    bhi .Lstep_percent
    subil #102,%d1
    | FILL momentané B et latch/état natifs lus sans effet sur les pistes A.
    lea.l 0x40fde812,%a0
    moveq #0,%d0
    moveb %a0@(0,%d2:l),%d0
    moveq #0,%d4
    moveb 0x40fde818,%d4
    orl %d4,%d0
    orl ml_cond_fill,%d0
    movel %sp@(72),%d4
    movel %d5,%sp@-
    movel %d0,%sp@-
    movel %d1,%sp@-
    movel %d2,%sp@-
    pea ml_cond_history
    jsr ml_condition_run
    lea.l %sp@(20),%sp
    bra .Lstep_decided
.Lstep_percent:
    .ifdef ML_CONDITION_COMPACT
    moveq #1,%d0
    tstl %d1
    beq .Lstep_percent_done
    subql #1,%d1
    cmpl %d1,%d5
    scs %d0
    andil #1,%d0
.Lstep_percent_done:
    bra .Lstep_percent_ready
    .endif
    movel %d5,%d0
    .endif
    .ifndef ML_CONDITION_COMPACT
    movel %d0,%sp@-
    movel %sp@(80),%sp@-
    pea %a4@(8)
    movel %a4,%sp@-
    jsr ml_chance_accept
    lea.l %sp@(16),%sp
    .endif
    .ifdef ML_CONDITION_COMPACT
.Lstep_percent_ready:
    .endif
    .ifdef ML_CONDITIONS
    | Une probabilité explicitement verrouillée nourrit PRE/NEI ; pas l'héritage.
    tstl %sp@(48)
    beq .Lstep_decided
    movel %d0,%d5
    movel %d5,%sp@-
    clrl %sp@-
    movel %d2,%sp@-
    pea ml_cond_history
    jsr ml_cond_remember
    lea.l %sp@(16),%sp
    movel %d5,%d0
    .endif
.Lstep_decided:
    tstl %d0
    bne .Lstep_chance_yes
    | Un refus termine l'ancien repeat, mais ne crée aucun nouveau Note On.
    moveq #0,%d3
    bra .Lstep_cancel_normal
.Lstep_chance_yes:
    .endif
    pea %sp@(36)
    movel %sp@(80),%sp@-
    pea %a4@(8)
    movel %a4,%sp@-
    jsr ml_repeat_resolve
    lea.l %sp@(16),%sp
    tstl %d0
    beq .Lstep_cancel_normal
    tstb %sp@(36)
    beq .Lstep_cancel_normal
    moveal ml_play_pattern,%a0
    tstl %a0
    beq .Lstep_cancel_normal
    movel %d2,%d0
    muluw #264,%d0
    addal %d0,%a0
    moveq #0,%d0
    moveb %a0@(5),%d0
    cmpil #6,%d0
    bhi .Lstep_cancel_normal
    lea.l ml_clock_durations,%a0
    movel %a0@(0,%d0:l:4),%d1
    movel %d4,%d0
    andil #0x7fffffff,%d0
    cmpil #1,%d0
    bcs .Lstep_cancel_normal
    cmpil #64,%d0
    bhi .Lstep_cancel_normal
    mulul %d1,%d0
    movel 0x40149310,%sp@-
    movel %d0,%sp@-
    moveq #0,%d0
    moveb %sp@(46),%d0
    movel %d0,%sp@-
    jsr ml_repeat_duration
    lea.l %sp@(12),%sp
    tstl %d0
    beq .Lstep_cancel_normal
    movel %d0,%d5
    movel %d2,%sp@-
    movel %a3,%sp@-
    movel %a2,%sp@-
    jsr ml_repeat_cancel
    lea.l %sp@(12),%sp
    movel %d5,%sp@-
    moveq #0,%d0
    moveb %sp@(41),%d0
    movel %d0,%sp@-
    movel %d3,%sp@-
    movel 0x8000184c,%sp@-
    movel %d2,%sp@-
    movel %a3,%sp@-
    movel %a2,%sp@-
    jsr ml_repeat_arm
    lea.l %sp@(28),%sp
    tstl %d0
    beq .Lstep_done
    moveal ml_repeat_arp_bank,%a5
    tstl %a5
    beq .Lstep_accepted
    movel %d2,%d0
    muluw #40,%d0
    addal %d0,%a5
    movel %a5@(24),%d0
    movel %d0,%sp@(44)
    moveq #0,%d0
    moveb %sp@(40),%d0
    movel %d0,%a5@
    moveq #0,%d0
    moveb %sp@(41),%d0
    movel %d0,%a5@(4)
    pea %a5@(8)
    jsr ml_arp_init
    addql #4,%sp
    movel %sp@(44),%d0
    beq .Lstep_seed_ready
    movel %d0,%a5@(24)
.Lstep_seed_ready:
    movel %d3,%d0
    swap %d0
    andil #127,%d0
    pea 1
    movel %d0,%sp@-
    pea %a5@(8)
    jsr ml_arp_held
    lea.l %sp@(12),%sp
.Lstep_accepted:
    moveq #1,%d0
    bra .Lstep_done
.Lstep_cancel_normal:
    tstl %a3@
    beq .Lstep_normal
    movel %d2,%sp@-
    movel %a3,%sp@-
    movel %a2,%sp@-
    jsr ml_repeat_cancel
    lea.l %sp@(12),%sp
.Lstep_normal:
    movel %d4,%sp@-
    movel %d3,%sp@-
    movel %d2,%sp@-
    movel %a2,%sp@-
    jsr ml_step
    lea.l %sp@(16),%sp
.Lstep_done:
    movel %sp@(32),%d1
    movem.l %sp@,%d2-%d5/%a2-%a5
    lea.l %sp@(56),%sp
    movew %d1,%sr
    rts

    .ifdef ML_CHANCE
    .data
    .balign 4
ml_chance_seeds:
    .long 0x13579bdf,0x2468ace1,0x31415927,0x27182819,0xabcdef01,0x10203041
    .endif
