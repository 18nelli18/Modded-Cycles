| Adaptation de roterodamus/Model-TG 0c567d8, src/model_tg.s, MIT TinyGregAudio.
| Conserver les adresses de la base épinglée : quatre raccords dans sa charge
| propre, helpers dans un masque de sprite, table dans l'ancien pitch_thr TG.
| Ne jamais employer le préfixe TG : c'est le tampon zéro du système de fichiers.
| Contrats des raccords : d2 = voix, d4 = piste ; d0/d1/a0 temporaires.
| select remplace le calcul de tranche (a1 n’est pas encore vivant).
| speed_gate reçoit les drapeaux du cmpi #2 et rejoue le chemin non-Slice.
| seq : a1 = données de piste, a3 = motif, d2 = piste, d3 = pas ; a5 libre.
| Le pending reste intact : le code TG d’origine le consomme au réamorçage.
    .text
    .globl tgsv_select,tgsv_speed_gate,tgsv_seq,tgsv_slice_note,tgsv_pitch_ctr
tgsv_select:
    lea slice_pending,%a0
    tstb %a0@(0,%d4:l)
    beq .Lhave_note
    lea live_note,%a0
    moveq #0,%d0
    moveb %a0@(0,%d4:l),%d0
    lea tgsv_slice_note,%a0
    moveb %d0,%a0@(0,%d4:l)
.Lhave_note:
    lea tgsv_slice_note,%a0
    moveq #0,%d1
    moveb %a0@(0,%d4:l),%d1
    subil #52,%d1
    jmp tgsv_select_return

tgsv_speed_gate:
    beq .Lslice
    moveal %d2,%a0
    movel %a0@(232),%d1
    jmp tgsv_speed_return
.Lslice:
    moveal %d2,%a0
    movel %a0@(232),%d1
    beq .Ldefault
    lea tgsv_slice_note,%a0
    moveq #0,%d0
    moveb %a0@(0,%d4:l),%d0
    subil #36,%d0
    bpl .Llo
    moveq #0,%d0
.Llo:
    cmpil #47,%d0
    ble .Lhi
    moveq #47,%d0
.Lhi:
    lea tgsv_pitch_ctr,%a0
    movel %a0@(0,%d0:l:4),%d0
    cmpil #0x3ffff,%d1
    ble .Lok
    movel #0x3ffff,%d1
.Lok:
    lsll #8,%d1
    lsll #6,%d1
    divul %d0,%d1
    lsll #2,%d1
    bne .Lstep
.Ldefault:
    jmp sv_defstep
.Lstep:
    jmp sv_havestep

tgsv_seq:
    lea %a1@(580),%a5
    mvsb %a5@(0,%d3:l),%d0
    bpl .Lnote_ok
    mvsb %a1@(712),%d0
.Lnote_ok:
    lea live_note,%a5
    moveb %d0,%a5@(0,%d2:l)
    tstb %a3@(30667)
    beq .Lshared
    jmp tgsv_seq_return
.Lshared:
    jmp sq_plen

    .balign 4
tgsv_slice_note:
    .byte 52,52,52,52,52,52,52,52
    .section .rodata.tgsv_pitch_ctr,"a"
tgsv_pitch_ctr:
    .long 11428,12107,12827,13590,14398,15254,16161,17122,18140,19219,20361,21572
    .long 22855,24214,25654,27179,28795,30508,32322,34244,36280,38437,40723,43144
    .long 45710,48428,51308,54359,57591,61016,64644,68488,72560,76875,81446,86289
    .long 91420,96856,102615,108717,115182,122031,129287,136975,145120,153750,162892,172578
