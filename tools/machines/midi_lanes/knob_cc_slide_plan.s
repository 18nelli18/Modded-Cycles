| Recherche du prochain trig comme Model-TG (TinyGregAudio, MIT).
| Destination marquée slide ; les paramètres glissent depuis le trig précédent.
| find(pattern,voie,pas) -> (distance<<8)|pas_cible, ou-1.
| Aucun appel OS, allocation, état global ni écriture musicale ;63 lectures max.
    .text
    .globl mlkc_slide_find
mlkc_slide_find:
    lea %sp@(-16),%sp
    moveml %d2-%d4/%a2,%sp@
    moveq #-1,%d0
    moveal %sp@(20),%a2
    tstl %a2
    beq .Lsf_done
    movel %sp@(24),%d1
    cmpil #5,%d1
    bhi .Lsf_done
    muluw #264,%d1
    addal %d1,%a2
    moveq #0,%d2
    moveb %a2@(4),%d2
    subql #1,%d2
    cmpil #63,%d2
    bhi .Lsf_done
    addql #1,%d2
    movel %sp@(28),%d3
    cmpl %d2,%d3
    bcc .Lsf_done
    moveq #0,%d4
.Lsf_next:
    addql #1,%d4
    cmpl %d2,%d4
    bcc .Lsf_done
    addql #1,%d3
    cmpl %d2,%d3
    bcs .Lsf_index
    moveq #0,%d3
.Lsf_index:
    movel %d3,%d1
    lsll #2,%d1
    lea %a2@(8,%d1:l),%a0
    btst #0,%a0@(3)
    beq .Lsf_next
    btst #1,%a0@(3)
    beq .Lsf_done
    movel %d4,%d0
    lsll #8,%d0
    orl %d3,%d0
.Lsf_done:
    moveml %sp@,%d2-%d4/%a2
    lea %sp@(16),%sp
    rts

| toggle(pas) -> flags. Un pas vide/trigless devient un vrai slide trig.
| Déjà note : le marqueur est basculé. Écriture alignée d'un octet.
    .globl mlkc_slide_toggle
mlkc_slide_toggle:
    moveal %sp@(4),%a0
    moveq #0,%d0
    moveb %a0@(3),%d0
    btst #0,%d0
    beq .Lst_new
    moveq #2,%d1
    eorl %d1,%d0
    bra .Lst_write
.Lst_new:
    | Nouveau trig note : C5/100/1, sans toucher aux locks CC externes.
    moveq #72,%d1
    moveb %d1,%a0@
    moveq #100,%d1
    moveb %d1,%a0@(1)
    moveq #1,%d1
    moveb %d1,%a0@(2)
    oril #3,%d0
.Lst_write:
    moveb %d0,%a0@(3)
    movel %d2,%sp@-
    movel %d0,%d2
    btst #1,%d0
    beq .Lst_off
    pea .Lst_on_text
    bra .Lst_popup
.Lst_off:
    pea .Lst_off_text
.Lst_popup:
    jsr TG_show_popup
    addql #4,%sp
    movel %d2,%d0
    movel %sp@+,%d2
    rts
.Lst_on_text: .asciz "Slide on"
.Lst_off_text: .asciz "Slide off"
    .balign 4
