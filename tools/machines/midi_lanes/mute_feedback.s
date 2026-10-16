| Note 100 : etat pad B, priorite au masque mute pendant FUNC.
.text
.globl ml_feedback_pad,ml_feedback_poll,ml_feedback_last
ml_feedback_pad:
    moveq #1,%d4
    tstl mlp_func
    bne .Lmute
    cmpl mlp_track,%d2
    beq .Lselected
    rts
.Lmute:
    movel %d2,%d0
    muluw #264,%d0
    moveal ml_pattern,%a0
    tstl %a0
    beq .Lpad_done
    tstb %a0@(0,%d0:l)
    beq .Lpad_done
    tstb %a0@(1,%d0:l)
    bne .Lpad_done
    moveq #2,%d4
    rts
.Lselected:
    moveq #3,%d4
.Lpad_done:
    rts
| Le changement FUNC doit invalider les LEDs meme transport arrete.
ml_feedback_poll:
    movel mlp_func,%d0
    cmpl ml_feedback_last,%d0
    beq .Lpoll_continue
    movel %d0,ml_feedback_last
    tstl mlp_obj
    beq .Lpoll_continue
    movel mlp_obj,%sp@-
    jsr 0x400760ba
    addql #4,%sp
.Lpoll_continue:
    jsr ml_feedback_old_tick
    jmp ml_feedback_poll_return
.data
ml_feedback_last: .long -1
