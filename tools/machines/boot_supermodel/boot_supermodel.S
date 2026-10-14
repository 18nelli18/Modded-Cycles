/* Écran SUPERMODEL, fonte originale et signature « by A.V. ».
 * Même tâche, minuteur50Hz,80images+10ticks et sémaphore que boot_anim.
 * Écriture seulement dans le framebuffer natif ; aucun LED ni tas.
 * Géométrie et colonnes propres générées par gen_boot_supermodel.py.
 */
    .include "supermodel.inc"
    .equ TIMER_ADD,0x40002144
    .equ TIMER_DEL,0x40002200
    .equ SEM_WAIT,0x40001aca
    .equ SEM_POST,0x40001c80
    .equ SEM_TAKE,0x40001b3e
    .equ TICK_CB,0x400539b8
    .equ SEM_TICK,0x40a78618
    .equ SEM_DONE,0x40a78620
    .equ GET_BUF,0x4008e728
    .equ FLUSH,0x4008e622
    .equ BLANK,0x4008e6ba
    .section .text.boot_anim,"ax"
    .globl ba_task
ba_task:
    jsr BLANK
    pea 2.w
    pea TICK_CB
    jsr TIMER_ADD
    addql #8,%sp
    moveq #0,%d7
.Lframe:
    jsr GET_BUF
    moveal %d0,%a3
    moveal %d0,%a0
    movel #256,%d0
.Lclear:
    clrl %a0@+
    subql #1,%d0
    bne .Lclear
    movel %d7,%d0
    subil #TITLE_START,%d0
    bmi .Lunderline
    lsrl #1,%d0
    addql #1,%d0
    cmpil #TITLE_COUNT,%d0
    ble .Ltitle_count
    moveq #TITLE_COUNT,%d0
.Ltitle_count:
    lea title_ends,%a0
    moveq #0,%d5
    moveb %a0@(-1,%d0:l),%d5
    lea title_cols,%a1
    moveq #TITLE_X,%d1
    moveq #TITLE_Y,%d0
    moveq #TITLE_H,%d3
    bsr .Lblit
.Lunderline:
    movel %d7,%d5
    subil #LINE_START,%d5
    bmi .Lsignature
    muluw #6,%d5
    addql #1,%d5
    cmpil #TITLE_WIDTH,%d5
    ble .Lline_count
    moveq #TITLE_WIDTH,%d5
.Lline_count:
    moveq #TITLE_X,%d1
    moveq #LINE_Y,%d0
.Lline:
    bsr .Lpset
    addql #1,%d1
    subql #1,%d5
    bne .Lline
.Lsignature:
    movel %d7,%d0
    subil #CREDIT_START,%d0
    bmi .Lpresent
    lsrl #1,%d0
    addql #1,%d0
    cmpil #CREDIT_COUNT,%d0
    ble .Lcredit_count
    moveq #CREDIT_COUNT,%d0
.Lcredit_count:
    lea credit_ends,%a0
    moveq #0,%d5
    moveb %a0@(-1,%d0:l),%d5
    lea credit_cols,%a1
    moveq #CREDIT_X,%d1
    moveq #CREDIT_Y,%d0
    moveq #CREDIT_H,%d3
    bsr .Lblit
.ifdef EDITION_ENABLED
    movel %d7,%d0
    subil #EDITION_START,%d0
    bmi .Lpresent
    lsrl #1,%d0
    addql #1,%d0
    cmpil #EDITION_COUNT,%d0
    ble .Ledition_count
    moveq #EDITION_COUNT,%d0
.Ledition_count:
    lea edition_ends,%a0
    moveq #0,%d5
    moveb %a0@(-1,%d0:l),%d5
    lea edition_cols,%a1
    moveq #EDITION_X,%d1
    moveq #EDITION_Y,%d0
    moveq #EDITION_H,%d3
    bsr .Lblit
.endif
.Lpresent:
    pea SEM_TICK
    jsr SEM_WAIT
    addql #4,%sp
    jsr FLUSH
    addql #1,%d7
    cmpil #NF,%d7
    blt .Lframe
    moveq #10,%d2
.Lhold:
    pea SEM_TICK
    jsr SEM_WAIT
    addql #4,%sp
    subql #1,%d2
    bne .Lhold
    pea SEM_DONE
    jsr SEM_POST
    pea TICK_CB
    jsr TIMER_DEL
    addql #8,%sp
.Ldone:
    pea SEM_TICK
    jsr SEM_TAKE
    addql #4,%sp
    bra .Ldone

/* a1=colonnes16bits alignées en haut, d5=largeur, d0=y,d1=x,d3=hauteur. */
.Lblit:
    lea %sp@(-8),%sp
    movel %d0,%sp@
    movel %d3,%sp@(4)
.Lcolumn:
    moveq #0,%d2
    movew %a1@+,%d2
    movel %sp@,%d0
    movel %sp@(4),%d3
.Lrow:
    btst #15,%d2
    beq .Loff
    bsr .Lpset
.Loff:
    addl %d2,%d2
    addql #1,%d0
    subql #1,%d3
    bne .Lrow
    addql #1,%d1
    subql #1,%d5
    bne .Lcolumn
    lea %sp@(8),%sp
    rts
/* Repère natif inversé verticalement : y0 en haut,8octets par colonne. */
.Lpset:
    movel %d1,%d4
    lsll #3,%d4
    lea %a3@(7,%d4:l),%a0
    movel %d0,%d4
    lsrl #3,%d4
    subal %d4,%a0
    bset %d0,%a0@
    rts
    .section .rodata.boot_anim,"a"
    .include "supermodel_data.inc"
