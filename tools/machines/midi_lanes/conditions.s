| Conditions B isolées : aucune lecture/écriture de piste native.
| eval(kind,a,b,phase,fill,prev,nei,sample) -> bool.
| kind : 0=%,1=FILL,2=!FILL,3=PRE,4=!PRE,5=NEI,6=!NEI,
| 7=1ST,8=!1ST,9=A:B. phase est zéro-indexée ; A:B exige phase<B.
| L'appelant conserve historique et compteurs : PRE ne les remplace pas.
| Test3 : décision appelée une fois par trig B avant armement retrigger.
    .ifdef ML_CONDITION_COMPACT
    .section .text.ml_condition_eval,"ax"
    .else
    .text
    .endif
    .globl ml_condition_eval
ml_condition_eval:
    movel %sp@(4),%d0
    cmpil #9,%d0
    bhi .Lcond_false
    tstl %d0
    beq .Lcond_percent
    cmpil #3,%d0
    bcs .Lcond_fill
    cmpil #5,%d0
    bcs .Lcond_prev
    cmpil #7,%d0
    bcs .Lcond_nei
    cmpil #9,%d0
    bcs .Lcond_first
    | Ratios bornés au domaine stock 1:1..8:8, phase privée modulo B.
    movel %sp@(12),%d1
    subql #1,%d1
    cmpil #7,%d1
    bhi .Lcond_false
    movel %sp@(8),%d0
    subql #1,%d0
    cmpl %d1,%d0
    bhi .Lcond_false
    movel %sp@(16),%d1
    cmpl %sp@(12),%d1
    bcc .Lcond_false
    cmpl %d1,%d0
    beq .Lcond_true
    bra .Lcond_false
.Lcond_percent:
    movel %sp@(8),%d0
    cmpil #100,%d0
    bhi .Lcond_false
    movel %sp@(32),%d1
    cmpil #99,%d1
    bhi .Lcond_false
    cmpl %d0,%d1
    bcs .Lcond_true
    bra .Lcond_false
.Lcond_fill:
    movel %sp@(20),%d1
    bra .Lcond_bool
.Lcond_prev:
    movel %sp@(24),%d1
    subql #2,%d0
    bra .Lcond_bool
.Lcond_nei:
    movel %sp@(28),%d1
    subql #4,%d0
.Lcond_bool:
    tstl %d1
    sne %d1
    andil #1,%d1
    cmpil #2,%d0
    bne .Lcond_return_bool
    moveq #1,%d0
    eorl %d0,%d1
.Lcond_return_bool:
    movel %d1,%d0
    rts
.Lcond_first:
    movel %sp@(16),%d1
    tstl %d1
    seq %d1
    andil #1,%d1
    cmpil #8,%d0
    bne .Lcond_return_bool
    moveq #1,%d0
    eorl %d0,%d1
    bra .Lcond_return_bool
.Lcond_true:
    moveq #1,%d0
    rts
.Lcond_false:
    moveq #0,%d0
    rts
