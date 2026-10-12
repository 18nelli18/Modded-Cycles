| Réglages privés de douze LFO MIDI : 12 × 16 octets, valeurs non décalées.
| Aucun pointeur audio. OFF128 distinct de CC127 ; adaptateur natif à faire.
| cfg_init(ctx), cfg_edit(ctx,lane,lfo,field,value), cfg_get(ctx,lane,lfo,field).
| Champs : speed,mul,fade,CC,wav,start,mode,depth (neutre16384).
    .text
    .globl mlcc_cfg_init,mlcc_cfg_edit,mlcc_cfg_get
mlcc_cfg_init:
    moveq #0,%d0
    moveal %sp@(4),%a0
    tstl %a0
    beq .Lcfg_init_done
    movel %a0,%d1
    andil #3,%d1
    bne .Lcfg_init_done
    movew %sr,%d1
    andil #0x700,%d1
    bne .Lcfg_init_done
    moveq #11,%d1
.Lcfg_init_loop:
    movel #0x40000009,%d0
    movel %d0,%a0@
    movel #0x40000080,%d0
    movel %d0,%a0@(4)
    clrl %a0@(8)
    movel #16384,%d0
    movel %d0,%a0@(12)
    lea.l %a0@(16),%a0
    subql #1,%d1
    bpl .Lcfg_init_loop
    moveq #1,%d0
.Lcfg_init_done:
    rts
mlcc_cfg_get:
    bsr .Lcfg_address
    tstl %d0
    beq .Lcfg_get_bad
    moveq #0,%d0
    movew %a0@,%d0
    rts
.Lcfg_get_bad:
    moveq #-1,%d0
    rts
mlcc_cfg_edit:
    bsr .Lcfg_address
    tstl %d0
    beq .Lcfg_edit_done
    movel %sp@(20),%d1
    moveal #.Lcfg_max,%a1
    movel %sp@(16),%d0
    movew %a1@(0,%d0:l:2),%d0
    andil #65535,%d0
    cmpl %d0,%d1
    bhi .Lcfg_edit_bad
    movew %d1,%a0@
    moveq #1,%d0
.Lcfg_edit_done:
    rts
.Lcfg_edit_bad:
    moveq #0,%d0
    rts
| Appelé par bsr : arguments décalés de quatre octets.
.Lcfg_address:
    moveq #0,%d0
    moveal %sp@(8),%a0
    tstl %a0
    beq .Lcfg_address_done
    movel %a0,%d1
    andil #3,%d1
    bne .Lcfg_address_done
    movew %sr,%d1
    andil #0x700,%d1
    bne .Lcfg_address_done
    movel %sp@(12),%d1
    cmpil #5,%d1
    bhi .Lcfg_address_done
    lsll #5,%d1
    addal %d1,%a0
    movel %sp@(16),%d1
    cmpil #1,%d1
    bhi .Lcfg_address_done
    lsll #4,%d1
    addal %d1,%a0
    movel %sp@(20),%d1
    cmpil #7,%d1
    bhi .Lcfg_address_done
    addl %d1,%d1
    addal %d1,%a0
    moveq #1,%d0
.Lcfg_address_done:
    rts
    .balign 2
.Lcfg_max: .word 32767,23,32767,128,6,32767,4,32767
