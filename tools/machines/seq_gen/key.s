| SETTINGS + PAGE : nouvelle page ; tous les autres événements vont à Model-TG.
| Même contrat que KeyEvent::code(event) : d0 résultat, d1/a0/a1 détruits,
| tous les registres conservés par l'ABI restent intacts.
| Les symboles TG_* viennent du build ÉPINGLÉ de Model-TG, jamais d'une adresse
| recopiée. L'ouverture est idempotente malgré les multiples lectures du code.
    .section .text.sg_key,"ax"
    .globl sg_key
sg_key:
    moveal %sp@(4),%a0
    movel %a0@(12),%d0
    .ifdef SG_ADVANCED
    cmpil #2,%d0
    beqw sg_sound_key
    .endif
    moveq #15,%d1
    cmpl %d1,%d0
    bnew sg_key_pass
    movel %a0@(16),%d1
    btst #0,%d1
    beqw sg_key_up
    tstl sg_page_taken
    beqs sg_key_fresh
    cmpal sg_page_event,%a0
    bnes sg_key_fresh
    movel %a0@(8),%d0
    cmpl sg_page_time,%d0
    beqw sg_key_eat
sg_key_fresh:
    tstl TG_set_held
    beqw sg_key_pass
    btst #3,%d1
    bnew sg_key_pass
    tstl TG_mm_obj
    bnew sg_key_pass
    tstl TG_rtg_on
    bnew sg_key_pass
    tstl TG_sle_on
    bnew sg_key_pass
    | FUNC : priorité à sa fonction habituelle (menu SCALE).
    btst #1,%d1
    bnew sg_key_pass
    movel %a0,sg_page_event
    movel %a0@(8),%d1
    movel %d1,sg_page_time
    moveq #1,%d1
    movel %d1,sg_page_taken
    movel %d1,TG_mod_used
    movel %a0,%sp@-
    movel %a0@(16),%d1
    oril #8,%d1
    movel %d1,%a0@(16)
    jsr sg_open
    moveal %sp@+,%a0
    braw sg_key_eat
sg_key_up:
    tstl sg_page_taken
    beqs sg_key_pass
    clrl sg_page_taken
    movel %a0,sg_page_event
    movel %a0@(8),%d1
    movel %d1,sg_page_time
    | Relâchement reconnu lors des lectures suivantes, même SETTINGS déjà relevé.
    bras sg_key_eat
sg_key_pass:
    moveal %sp@(4),%a0
    movel %a0@(12),%d0
    moveq #15,%d1
    cmpl %d1,%d0
    bnes sg_key_chain
    cmpal sg_page_event,%a0
    bnes sg_key_chain
    movel %a0@(8),%d0
    cmpl sg_page_time,%d0
    bnes sg_key_chain
    btst #0,%a0@(19)
    beqs sg_key_eat
sg_key_chain:
    jmp TG_key_hook
sg_key_eat:
    movel %a0@(16),%d1
    oril #8,%d1
    movel %d1,%a0@(16)
    moveq #0,%d0
    rts

    .section .data.sg_key,"aw"
    .globl sg_page_taken,sg_page_event,sg_page_time
sg_page_taken: .long 0
sg_page_event: .long 0
sg_page_time: .long 0
