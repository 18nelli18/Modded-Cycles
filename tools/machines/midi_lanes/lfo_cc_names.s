| Noms CC pour menus B uniquement. 0..127 CC, 128 OFF ; autres valeurs ERR.
| mlcc_name(destination) -> chaîne constante ; aucune dépendance au moteur audio.
    .text
    .globl mlcc_name
mlcc_name:
    movel %sp@(4),%d0
    cmpil #128,%d0
    bhi .Lbad
    lea.l .Lnames,%a0
    movel %a0@(0,%d0:l:4),%d0
    rts
.Lbad:
    lea.l .Lerr,%a0
    movel %a0,%d0
    rts
    .balign 4
.Lnames:
    .long .Lcc0
    .long .Lcc1
    .long .Lcc2
    .long .Lcc3
    .long .Lcc4
    .long .Lcc5
    .long .Lcc6
    .long .Lcc7
    .long .Lcc8
    .long .Lcc9
    .long .Lcc10
    .long .Lcc11
    .long .Lcc12
    .long .Lcc13
    .long .Lcc14
    .long .Lcc15
    .long .Lcc16
    .long .Lcc17
    .long .Lcc18
    .long .Lcc19
    .long .Lcc20
    .long .Lcc21
    .long .Lcc22
    .long .Lcc23
    .long .Lcc24
    .long .Lcc25
    .long .Lcc26
    .long .Lcc27
    .long .Lcc28
    .long .Lcc29
    .long .Lcc30
    .long .Lcc31
    .long .Lcc32
    .long .Lcc33
    .long .Lcc34
    .long .Lcc35
    .long .Lcc36
    .long .Lcc37
    .long .Lcc38
    .long .Lcc39
    .long .Lcc40
    .long .Lcc41
    .long .Lcc42
    .long .Lcc43
    .long .Lcc44
    .long .Lcc45
    .long .Lcc46
    .long .Lcc47
    .long .Lcc48
    .long .Lcc49
    .long .Lcc50
    .long .Lcc51
    .long .Lcc52
    .long .Lcc53
    .long .Lcc54
    .long .Lcc55
    .long .Lcc56
    .long .Lcc57
    .long .Lcc58
    .long .Lcc59
    .long .Lcc60
    .long .Lcc61
    .long .Lcc62
    .long .Lcc63
    .long .Lcc64
    .long .Lcc65
    .long .Lcc66
    .long .Lcc67
    .long .Lcc68
    .long .Lcc69
    .long .Lcc70
    .long .Lcc71
    .long .Lcc72
    .long .Lcc73
    .long .Lcc74
    .long .Lcc75
    .long .Lcc76
    .long .Lcc77
    .long .Lcc78
    .long .Lcc79
    .long .Lcc80
    .long .Lcc81
    .long .Lcc82
    .long .Lcc83
    .long .Lcc84
    .long .Lcc85
    .long .Lcc86
    .long .Lcc87
    .long .Lcc88
    .long .Lcc89
    .long .Lcc90
    .long .Lcc91
    .long .Lcc92
    .long .Lcc93
    .long .Lcc94
    .long .Lcc95
    .long .Lcc96
    .long .Lcc97
    .long .Lcc98
    .long .Lcc99
    .long .Lcc100
    .long .Lcc101
    .long .Lcc102
    .long .Lcc103
    .long .Lcc104
    .long .Lcc105
    .long .Lcc106
    .long .Lcc107
    .long .Lcc108
    .long .Lcc109
    .long .Lcc110
    .long .Lcc111
    .long .Lcc112
    .long .Lcc113
    .long .Lcc114
    .long .Lcc115
    .long .Lcc116
    .long .Lcc117
    .long .Lcc118
    .long .Lcc119
    .long .Lcc120
    .long .Lcc121
    .long .Lcc122
    .long .Lcc123
    .long .Lcc124
    .long .Lcc125
    .long .Lcc126
    .long .Lcc127
    .long .Lcc128
.Lcc0: .asciz "CC0"
.Lcc1: .asciz "CC1 Mod"
.Lcc2: .asciz "CC2"
.Lcc3: .asciz "CC3"
.Lcc4: .asciz "CC4"
.Lcc5: .asciz "CC5"
.Lcc6: .asciz "CC6"
.Lcc7: .asciz "CC7 Volume"
.Lcc8: .asciz "CC8"
.Lcc9: .asciz "CC9"
.Lcc10: .asciz "CC10 Pan"
.Lcc11: .asciz "CC11 Expr"
.Lcc12: .asciz "CC12"
.Lcc13: .asciz "CC13"
.Lcc14: .asciz "CC14"
.Lcc15: .asciz "CC15"
.Lcc16: .asciz "CC16"
.Lcc17: .asciz "CC17"
.Lcc18: .asciz "CC18"
.Lcc19: .asciz "CC19"
.Lcc20: .asciz "CC20"
.Lcc21: .asciz "CC21"
.Lcc22: .asciz "CC22"
.Lcc23: .asciz "CC23"
.Lcc24: .asciz "CC24"
.Lcc25: .asciz "CC25"
.Lcc26: .asciz "CC26"
.Lcc27: .asciz "CC27"
.Lcc28: .asciz "CC28"
.Lcc29: .asciz "CC29"
.Lcc30: .asciz "CC30"
.Lcc31: .asciz "CC31"
.Lcc32: .asciz "CC32"
.Lcc33: .asciz "CC33"
.Lcc34: .asciz "CC34"
.Lcc35: .asciz "CC35"
.Lcc36: .asciz "CC36"
.Lcc37: .asciz "CC37"
.Lcc38: .asciz "CC38"
.Lcc39: .asciz "CC39"
.Lcc40: .asciz "CC40"
.Lcc41: .asciz "CC41"
.Lcc42: .asciz "CC42"
.Lcc43: .asciz "CC43"
.Lcc44: .asciz "CC44"
.Lcc45: .asciz "CC45"
.Lcc46: .asciz "CC46"
.Lcc47: .asciz "CC47"
.Lcc48: .asciz "CC48"
.Lcc49: .asciz "CC49"
.Lcc50: .asciz "CC50"
.Lcc51: .asciz "CC51"
.Lcc52: .asciz "CC52"
.Lcc53: .asciz "CC53"
.Lcc54: .asciz "CC54"
.Lcc55: .asciz "CC55"
.Lcc56: .asciz "CC56"
.Lcc57: .asciz "CC57"
.Lcc58: .asciz "CC58"
.Lcc59: .asciz "CC59"
.Lcc60: .asciz "CC60"
.Lcc61: .asciz "CC61"
.Lcc62: .asciz "CC62"
.Lcc63: .asciz "CC63"
.Lcc64: .asciz "CC64 Sustain"
.Lcc65: .asciz "CC65 Porta"
.Lcc66: .asciz "CC66"
.Lcc67: .asciz "CC67"
.Lcc68: .asciz "CC68"
.Lcc69: .asciz "CC69"
.Lcc70: .asciz "CC70"
.Lcc71: .asciz "CC71 Res"
.Lcc72: .asciz "CC72"
.Lcc73: .asciz "CC73"
.Lcc74: .asciz "CC74 Cutoff"
.Lcc75: .asciz "CC75"
.Lcc76: .asciz "CC76"
.Lcc77: .asciz "CC77"
.Lcc78: .asciz "CC78"
.Lcc79: .asciz "CC79"
.Lcc80: .asciz "CC80"
.Lcc81: .asciz "CC81"
.Lcc82: .asciz "CC82"
.Lcc83: .asciz "CC83"
.Lcc84: .asciz "CC84"
.Lcc85: .asciz "CC85"
.Lcc86: .asciz "CC86"
.Lcc87: .asciz "CC87"
.Lcc88: .asciz "CC88"
.Lcc89: .asciz "CC89"
.Lcc90: .asciz "CC90"
.Lcc91: .asciz "CC91 Reverb"
.Lcc92: .asciz "CC92"
.Lcc93: .asciz "CC93 Chorus"
.Lcc94: .asciz "CC94"
.Lcc95: .asciz "CC95"
.Lcc96: .asciz "CC96"
.Lcc97: .asciz "CC97"
.Lcc98: .asciz "CC98"
.Lcc99: .asciz "CC99"
.Lcc100: .asciz "CC100"
.Lcc101: .asciz "CC101"
.Lcc102: .asciz "CC102"
.Lcc103: .asciz "CC103"
.Lcc104: .asciz "CC104"
.Lcc105: .asciz "CC105"
.Lcc106: .asciz "CC106"
.Lcc107: .asciz "CC107"
.Lcc108: .asciz "CC108"
.Lcc109: .asciz "CC109"
.Lcc110: .asciz "CC110"
.Lcc111: .asciz "CC111"
.Lcc112: .asciz "CC112"
.Lcc113: .asciz "CC113"
.Lcc114: .asciz "CC114"
.Lcc115: .asciz "CC115"
.Lcc116: .asciz "CC116"
.Lcc117: .asciz "CC117"
.Lcc118: .asciz "CC118"
.Lcc119: .asciz "CC119"
.Lcc120: .asciz "CC120"
.Lcc121: .asciz "CC121"
.Lcc122: .asciz "CC122"
.Lcc123: .asciz "CC123"
.Lcc124: .asciz "CC124"
.Lcc125: .asciz "CC125"
.Lcc126: .asciz "CC126"
.Lcc127: .asciz "CC127"
.Lcc128: .asciz "OFF"
.Lerr: .asciz "ERR"
