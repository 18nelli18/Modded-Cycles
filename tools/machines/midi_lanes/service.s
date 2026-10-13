| Note 57 : pont UI entre file privée et routeur MIDI natif OS 1.13.
| ml_service(runtime,budget) -> nombre de paquets retirés (maximum huit).
| Refuse tout IPL non nul et singleton MIDI absent, sans retirer de paquet.
| Aucun verrou privé conservé pendant le routeur, qui peut attendre côté UI.
| Le budget borne le nombre de messages, pas la durée des sorties physiques.
    .text
    .globl ml_service
ml_service:
    lea.l %sp@(-32),%sp
    movem.l %d2-%d4/%a2,%sp@
    movew %sr,%d0
    movel %d0,%sp@(16)
    andil #0x0700,%d0
    bne .Lservice_refuse
    tstl 0x40fe4228
    beq .Lservice_refuse
    moveal %sp@(36),%a2
    movel %sp@(40),%d3
    cmpil #8,%d3
    bls .Lservice_budget
    moveq #8,%d3
.Lservice_budget:
    moveq #0,%d2
.Lservice_loop:
    cmpl %d3,%d2
    beq .Lservice_done
    movel %a2,%sp@-
    jsr ml_take
    addql #4,%sp
    tstl %d0
    beq .Lservice_done
    movel %d0,%sp@(20)
    andil #255,%d0
    lea.l %sp@(20),%a0
    movel %d0,%sp@-
    movel %a0,%sp@-
    movel #3,%sp@-
    jsr 0x400826b0
    lea.l %sp@(12),%sp
    .ifdef ML_KNOB_LOCKS
    moveal ml_runtime,%a0
    cmpal %a0,%a2
    bne .Lservice_not_sequence
    movel %sp@(20),%sp@-
    jsr mlkcr_off
    addql #4,%sp
.Lservice_not_sequence:
    .endif
    addql #1,%d2
    bra .Lservice_loop
.Lservice_refuse:
    moveq #0,%d2
.Lservice_done:
    movel %d2,%d0
    movel %sp@(16),%d1
    movem.l %sp@,%d2-%d4/%a2
    movew %d1,%sr
    lea.l %sp@(32),%sp
    rts
