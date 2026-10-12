| Note 57 : prototype de consommateur dédié, sans dépendance au rendu UI.
| Contexte privé 16 octets : sémaphore natif (8), pending (4), runtime (4).
| Initialiser avant publication ; un seul consommateur. ML_WORKER ajoute
| création/réveil depuis UI/audio ; placement firmware reste à intégrer.
| notify est borné et utilisable depuis l'IRQ :
| 40001bb0 est aussi appelé par l'IRQ native 400020d4 ; aucune attente/trap.
| once est réservé à la tâche IPL0, huit paquets au plus. La boucle de tâche
| attendra 40001aca puis once ; les écritures physiques restent hors IRQ/UI.
    .text
    .globl ml_worker_init,ml_worker_notify,ml_worker_once
ml_worker_init:
    movew %sr,%d1
    moveal %sp@(4),%a0
    clrl %a0@
    clrl %a0@(4)
    clrl %a0@(8)
    movel %sp@(8),%a0@(12)
    movew %d1,%sr
    rts
ml_worker_notify:
    lea.l %sp@(-8),%sp
    movem.l %a2,%sp@
    movew %sr,%d0
    movel %d0,%sp@(4)
    movew #0x2700,%sr
    moveal %sp@(12),%a2
    | Aucun réarmement en boucle tant que le routeur MIDI est indisponible.
    | UI/audio réessaient le réveil dès que son singleton est publié.
    tstl 0x40fe4228
    beq .Lwn_done
    tstl %a2@(8)
    bne .Lwn_done
    moveal %a2@(12),%a0
    tstl %a0@
    beq .Lwn_done
    moveq #1,%d0
    movel %d0,%a2@(8)
    movel %a2,%sp@-
    jsr 0x40001bb0
    addql #4,%sp
.Lwn_done:
    movel %sp@(4),%d0
    movew %d0,%sr
    movel %sp@,%a2
    addql #8,%sp
    rts
ml_worker_once:
    lea.l %sp@(-12),%sp
    movem.l %d2/%a2,%sp@
    movew %sr,%d0
    movel %d0,%sp@(8)
    andil #0x0700,%d0
    bne .Lwo_refuse
    moveal %sp@(16),%a2
    pea 8
    movel %a2@(12),%sp@-
    jsr ml_service
    addql #8,%sp
    movel %d0,%d2
    movew #0x2700,%sr
    clrl %a2@(8)
    | Réarmer si huit paquets n'ont pas suffi, sans fenêtre de réveil perdu.
    movel %a2,%sp@-
    jsr ml_worker_notify
    addql #4,%sp
    bra .Lwo_done
.Lwo_refuse:
    moveq #0,%d2
.Lwo_done:
    movel %d2,%d0
    movel %sp@(8),%d1
    movem.l %sp@,%d2/%a2
    movew %d1,%sr
    lea.l %sp@(12),%sp
    rts

    .ifdef ML_WORKER
    .data
    .balign 4
    .globl ml_worker_context,ml_worker_preparing
ml_worker_context: .long 0
ml_worker_preparing: .long 0
    .text
    .globl ml_worker_prepare,ml_worker_run,ml_worker_kick
| Allocation UI unique : 16 contexte + 84 TCB natif + 16 KiB pile.
| Priorité 5, sous l'UI (6), pour qu'un writer plein ne monopolise pas l'UI.
ml_worker_prepare:
    lea.l %sp@(-12),%sp
    movem.l %d2/%a2-%a3,%sp@
    movew %sr,%d0
    andil #0x0700,%d0
    bne .Lwp_fail
    tstl ml_worker_context
    bne .Lwp_ready
    tstl ml_worker_preparing
    bne .Lwp_fail
    moveal ml_context,%a3
    tstl %a3
    beq .Lwp_fail
    moveq #1,%d0
    movel %d0,ml_worker_preparing
    pea 16484
    jsr 0x400802e0
    addql #4,%sp
    moveal %d0,%a2
    tstl %a2
    beq .Lwp_failed
    | Zéro avant toute publication ou ajout de la tâche au scheduler.
    moveal %a2,%a0
    moveq #24,%d0
.Lwp_zero:
    clrl %a0@+
    subql #1,%d0
    bpl .Lwp_zero
    pea %a3@(1584)
    movel %a2,%sp@-
    jsr ml_worker_init
    addql #8,%sp
    pea 16384
    pea %a2@(100)
    pea 5
    pea ml_worker_run
    pea %a2@(16)
    jsr 0x400019ec
    lea.l %sp@(20),%sp
    movel %a2,ml_worker_context
    pea %a2@(16)
    jsr 0x40001a38
    addql #4,%sp
    clrl ml_worker_preparing
.Lwp_ready:
    moveq #1,%d0
    bra .Lwp_done
.Lwp_failed:
    clrl ml_worker_preparing
.Lwp_fail:
    moveq #0,%d0
.Lwp_done:
    movem.l %sp@,%d2/%a2-%a3
    lea.l %sp@(12),%sp
    rts
ml_worker_run:
    moveal ml_worker_context,%a2
.Lwr_wait:
    movel %a2,%sp@-
    jsr 0x40001aca
    addql #4,%sp
    movel %a2,%sp@-
    jsr ml_worker_once
    addql #4,%sp
    bra .Lwr_wait
ml_worker_kick:
    moveal ml_worker_context,%a0
    tstl %a0
    beq .Lwk_done
    movel %a0,%sp@-
    jsr ml_worker_notify
    addql #4,%sp
.Lwk_done:
    rts
    .endif
