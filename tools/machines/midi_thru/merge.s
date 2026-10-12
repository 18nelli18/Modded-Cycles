| Relais DIN par messages complets, prototype privé (notes/53).
| ctx nul, aligné4, 8256 octets : état32 + huit cases {long longueur, octets1024}.
| Sept messages publiés maximum ; la huitième case appartient au producteur RX.
| feed(ctx,octet) : 2 realtime (à relayer directement), 1 publié, sinon0.
| Canal avec statut explicite, running status reconstruit, commun système,
| SysEx entier <=1024. Débordement : jeter le message entier, compteur+20.
| service(ctx,budget<=8) : IPL0 seulement, writer DIN natif, aucun writer IRQ.
| Une seule tâche consommatrice ; la case reste réservée pendant le writer.
    .section .text.mm_merge,"ax"
    .globl mm_feed,mm_service
mm_feed:
    lea.l %sp@(-24),%sp
    moveml %d2-%d5/%a2-%a3,%sp@
    moveal %sp@(28),%a2
    moveq #0,%d0
    tstl %a2
    beq .Lf_done
    movel %a2,%d1
    andil #3,%d1
    bne .Lf_done
    movel %sp@(32),%d2
    cmpil #255,%d2
    bhi .Lf_done
    cmpil #248,%d2
    bcs .Lf_lock
    moveq #2,%d0
    bra .Lf_done
.Lf_lock:
    movew %sr,%d5
    movew #0x2700,%sr
    movel %a2@(8),%d1
    cmpil #7,%d1
    bhi .Lf_unlock
    movel %d1,%d3
    lsll #8,%d1
    lsll #2,%d1
    lsll #2,%d3
    addl %d3,%d1
    lea %a2@(32),%a3
    addal %d1,%a3
    tstl %a2@(24)
    beq .Lf_regular
    cmpil #247,%d2
    beq .Lf_sysex_end
    cmpil #128,%d2
    bcs .Lf_append
    | Un autre statut annule le SysEx incomplet.
    clrl %a2@(24)
    clrl %a2@(4)
    clrb %a2@(3)
    bra .Lf_status
.Lf_sysex_end:
    bsr .Lf_store
    clrl %a2@(24)
    bra .Lf_publish
.Lf_regular:
    cmpil #128,%d2
    bcc .Lf_status
    tstb %a2@
    beq .Lf_unlock
    tstl %a2@(4)
    bne .Lf_data
    | Début d'un message sous running status : remettre son statut.
    movel %d2,%d4
    moveq #0,%d2
    moveb %a2@,%d2
    bsr .Lf_store
    movel %d4,%d2
.Lf_data:
    bsr .Lf_store
    moveq #0,%d1
    moveb %a2@(2),%d1
    addql #1,%d1
    moveb %d1,%a2@(2)
    cmpb %a2@(1),%d1
    bne .Lf_unlock
    bra .Lf_publish
.Lf_status:
    clrl %a2@(4)
    clrb %a2@(2)
    clrb %a2@(3)
    clrb %a2@
    cmpil #240,%d2
    beq .Lf_sysex_start
    cmpil #240,%d2
    bcc .Lf_system
    moveb %d2,%a2@
    moveq #2,%d3
    movel %d2,%d1
    andil #0xe0,%d1
    cmpil #0xc0,%d1
    bne .Lf_need
    moveq #1,%d3
    bra .Lf_need
.Lf_system:
    moveq #1,%d3
    cmpil #241,%d2
    beq .Lf_system_need
    cmpil #243,%d2
    beq .Lf_system_need
    cmpil #242,%d2
    bne .Lf_single
    moveq #2,%d3
.Lf_system_need:
    moveb %d2,%a2@
.Lf_need:
    moveb %d3,%a2@(1)
    bsr .Lf_store
    bra .Lf_unlock
.Lf_single:
    | F6 et F7 seulement ; F4/F5 indéfinis sont ignorés.
    cmpil #246,%d2
    bcs .Lf_unlock
    bsr .Lf_store
    bra .Lf_publish
.Lf_sysex_start:
    moveq #1,%d1
    movel %d1,%a2@(24)
.Lf_append:
    bsr .Lf_store
    bra .Lf_unlock
.Lf_store:
    tstb %a2@(3)
    bne .Lf_store_ret
    movel %a2@(16),%d1
    cmpil #7,%d1
    bcc .Lf_drop
    movel %a2@(4),%d1
    cmpil #1024,%d1
    bcc .Lf_drop
    moveb %d2,%a3@(4,%d1:l)
    addql #1,%a2@(4)
.Lf_store_ret:
    rts
.Lf_drop:
    moveb #1,%a2@(3)
    addql #1,%a2@(20)
    rts
.Lf_publish:
    tstb %a2@(3)
    bne .Lf_reset
    movel %a2@(4),%a3@
    addql #1,%a2@(16)
    addql #1,%a2@(8)
    movel %a2@(8),%d1
    andil #7,%d1
    movel %d1,%a2@(8)
    moveq #1,%d0
.Lf_reset:
    clrl %a2@(4)
    clrb %a2@(2)
    clrb %a2@(3)
    moveq #0,%d1
    moveb %a2@,%d1
    cmpil #240,%d1
    bcs .Lf_unlock
    clrb %a2@
.Lf_unlock:
    movew %d5,%sr
.Lf_done:
    moveml %sp@,%d2-%d5/%a2-%a3
    lea.l %sp@(24),%sp
    rts
mm_service:
    lea.l %sp@(-20),%sp
    moveml %d2-%d4/%a2-%a3,%sp@
    moveq #0,%d2
    movew %sr,%d0
    andil #0x700,%d0
    bne .Ls_done
    moveal %sp@(24),%a2
    tstl %a2
    beq .Ls_done
    movel %a2,%d0
    andil #3,%d0
    bne .Ls_done
    movel %sp@(28),%d3
    cmpil #8,%d3
    bls .Ls_loop
    moveq #8,%d3
.Ls_loop:
    cmpl %d3,%d2
    beq .Ls_done
    tstl %a2@(16)
    beq .Ls_done
    movel %a2@(12),%d0
    cmpil #7,%d0
    bhi .Ls_done
    movel %d0,%d1
    lsll #8,%d0
    lsll #2,%d0
    lsll #2,%d1
    addl %d1,%d0
    lea %a2@(32),%a3
    addal %d0,%a3
    movel %a3@,%d4
    beq .Ls_done
    cmpil #1024,%d4
    bhi .Ls_done
    pea %a3@(4)
    movel %d4,%sp@-
    jsr 0x40001100
    addql #8,%sp
    movew %sr,%d0
    movew #0x2700,%sr
    addql #1,%a2@(12)
    movel %a2@(12),%d1
    andil #7,%d1
    movel %d1,%a2@(12)
    subql #1,%a2@(16)
    movew %d0,%sr
    addql #1,%d2
    bra .Ls_loop
.Ls_done:
    movel %d2,%d0
    moveml %sp@,%d2-%d4/%a2-%a3
    lea.l %sp@(20),%sp
    rts

    .ifdef ML_MERGE
    .section .data.mm_merge,"aw"
    .balign 4
    .globl mm_context
mm_context: .long 0
mm_preparing: .long 0
    .section .text.mm_merge,"ax"
    .globl mm_rx,mm_prepare
| Allocation hors IRQ ; publication seulement après remise à zéro complète.
mm_prepare:
    movel %a2,%sp@-
    movew %sr,%d0
    andil #0x700,%d0
    bne .Lmp_no
    tstl mm_context
    bne .Lmp_yes
    tstl mm_preparing
    bne .Lmp_no
    moveq #1,%d0
    movel %d0,mm_preparing
    pea 8256
    jsr 0x400802e0
    addql #4,%sp
    moveal %d0,%a2
    tstl %a2
    beq .Lmp_failed
    moveal %a2,%a0
    movel #2064,%d0
.Lmp_zero:
    clrl %a0@+
    subql #1,%d0
    bne .Lmp_zero
    movel %a2,mm_context
    clrl mm_preparing
.Lmp_yes:
    moveq #1,%d0
    bra .Lmp_ret
.Lmp_failed:
    clrl mm_preparing
.Lmp_no:
    moveq #0,%d0
.Lmp_ret:
    movel %sp@+,%a2
    rts

| Remplace le gestionnaire012cc entier ; même argument et tailcall au suivant.
| OUT/pur THRU gardent le chemin natif. Seule la valeur2 utilise la file.
mm_rx:
    movel %d2,%sp@-
    movel %sp@(8),%d2
    moveq #0,%d0
    moveb 0x404e9b50,%d0
    cmpil #2,%d0
    beq .Lrx_merge
    | Ne pas garder un message partiel reçu dans un mode antérieur.
    moveal mm_context,%a0
    tstl %a0
    beq .Lrx_nonmerge
    clrl %a0@
    clrl %a0@(4)
    clrl %a0@(24)
.Lrx_nonmerge:
    tstl %d0
    beq .Lrx_next
    bra .Lrx_byte
.Lrx_merge:
    moveal mm_context,%a0
    tstl %a0
    beq .Lrx_next
    movel %d2,%sp@-
    movel %a0,%sp@-
    jsr mm_feed
    addql #8,%sp
    cmpil #2,%d0
    beq .Lrx_byte
    tstl %d0
    beq .Lrx_next
    jsr ml_worker_kick
    bra .Lrx_next
.Lrx_byte:
    movel %d2,%sp@-
    jsr 0x40001232
    addql #4,%sp
.Lrx_next:
    movel %d2,%sp@(8)
    moveal 0x422fee70,%a1
    movel %sp@+,%d2
    jmp %a1@
    .endif
