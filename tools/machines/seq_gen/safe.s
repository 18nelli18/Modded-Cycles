| Note 56 : pas généré explicitement jouable, sans héritage de vélocité muette.
| a0 = format éditable, d2 = pas, d3 = note ; préserve a0/d1/d2/d3.
    .ifdef SG_SEQUENCE_ONLY
    .section .text.sg_safe_step,"ax"
    .globl sg_safe_step
sg_safe_step:
    lea.l %a0@(128),%a1
    moveq #0,%d0
    moveb %a1@(0,%d2:l),%d0
    cmpil #1,%d0
    blt sg_safe_default
    cmpil #127,%d0
    ble sg_safe_velocity
sg_safe_default:
    moveq #0,%d0
    moveb %a0@(708),%d0
    cmpil #1,%d0
    blt sg_safe_fallback
    cmpil #127,%d0
    ble sg_safe_velocity
sg_safe_fallback:
    moveq #100,%d0
sg_safe_velocity:
    moveb %d0,%a1@(0,%d2:l)
    | 100 est hors des conditions 0..63 : la routine native ne saute pas le trig.
    lea.l %a0@(516),%a1
    moveq #100,%d0
    moveb %d0,%a1@(0,%d2:l)
    | Aucun preset-lock hérité d'un pas vide/corrompu.
    lea.l %a0@(644),%a1
    moveq #-1,%d0
    moveb %d0,%a1@(0,%d2:l)
    rts
    .endif
