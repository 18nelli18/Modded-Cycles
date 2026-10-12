| Note 57 : contexte unique 1956 octets : pattern 1584, runtime 320,
| horloge 52. Allocation UI seule ; publication ml_context en dernier.
| Le futur hook audio doit lire ml_context et dériver ses sous-structures,
| jamais interpréter les pointeurs UI intermédiaires comme un contexte prêt.
    .data
    .globl ml_context,ml_clock_state,ml_preparing
ml_context: .long 0
ml_clock_state: .long 0
ml_preparing: .long 0
    .text
    .globl ml_prepare
ml_prepare:
    subql #4,%sp
    movem.l %a2,%sp@
    movew %sr,%d0
    andil #0x0700,%d0
    bne .Lmp_refuse
    tstl ml_context
    bne .Lmp_ready
    tstl ml_preparing
    bne .Lmp_refuse
    moveq #1,%d0
    movel %d0,ml_preparing
    .ifdef ML_PATTERN_BANKS
    .ifdef ML_STORAGE2
    pea 12132                   | contexte/table + deux banques4896
    .else
    pea 3924                    | contexte + table 96 pointeurs + banque vide
    .endif
    .else
    pea 1956
    .endif
    jsr 0x400802e0
    addql #4,%sp
    moveal %d0,%a2
    tstl %a2
    beq .Lmp_failed
    movel %a2,%sp@-
    jsr ml_init
    addql #4,%sp
    tstl %d0
    beq .Lmp_free
    lea.l %a2@(1584),%a0
    moveq #92,%d0
.Lmp_clear:
    clrl %a0@+
    subql #1,%d0
    bpl .Lmp_clear
    .ifdef ML_PATTERN_BANKS
    lea.l %a2@(1956),%a0
    moveq #95,%d0
.Lmp_banks_zero:
    clrl %a0@+
    subql #1,%d0
    bpl .Lmp_banks_zero
    .ifdef ML_STORAGE2
    pea %a2@(2340)
    jsr ml_store_bank_init
    addql #4,%sp
    pea %a2@(7236)
    jsr ml_store_bank_init
    addql #4,%sp
    lea.l %a2@(7236),%a0
    movel %a0,ml_bank_empty
    lea.l %a2@(1956),%a0
    lea.l %a2@(2340),%a1
    movel %a1,%a0@
    movel %a0,ml_bank_table
    movel %a1,ml_play_pattern
    .else
    pea %a2@(2340)
    jsr ml_init
    addql #4,%sp
    lea.l %a2@(2340),%a0
    movel %a0,ml_bank_empty
    lea.l %a2@(1956),%a0
    movel %a2,%a0@              | pattern 0 utilise le bloc initial
    movel %a0,ml_bank_table
    movel %a2,ml_play_pattern
    .endif
    .endif
    .ifdef ML_STORAGE2
    lea.l %a2@(2340),%a0
    movel %a0,ml_pattern
    .else
    movel %a2,ml_pattern
    .endif
    lea.l %a2@(1584),%a0
    movel %a0,ml_runtime
    lea.l %a2@(1904),%a0
    movel %a0,ml_clock_state
    movel %a2,ml_context
    clrl ml_preparing
.Lmp_ready:
    moveq #1,%d0
    bra .Lmp_done
.Lmp_free:
    movel %a2,%sp@-
    jsr 0x400802ec
    addql #4,%sp
.Lmp_failed:
    clrl ml_preparing
.Lmp_refuse:
    moveq #0,%d0
.Lmp_done:
    movem.l %sp@,%a2
    addql #4,%sp
    rts
