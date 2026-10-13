#!/usr/bin/env python3
"""Page LFO MIDI dérivée du rendu LFO2 stock du fork.

Garde la banque B sous la page,
LFO bascule1/2, destination CC0–127/OFF indépendante des paramètres audio.
"""
import pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]


def sources():
 page=(ROOT/'tools/machines/lfo_secondary/page.s').read_text()
 layout=(ROOT/'tools/machines/lfo_secondary/layout.s').read_text()
 def rename(s):return s.replace('lf2p','mlccp').replace('lf2l','mlccl').replace('lf2_context','mlcc_settings')
 # Le quick assign audio LFO2 ne s'applique pas au menu CC dérivé.
 if '    .section .text.lf2p_enc_quick,' in page:
  a=page.index('    .section .text.lf2p_enc_quick,');b=page.index('    .section .text.lf2p_enc_value,',a)
  page=page[:a]+page[b:]
  page=page.replace('    bne .Lpe_quick','    bne .Lpe_b_knob')
  page=page.replace('    tstl lf2p_assigned\n    beq .Lpk_close\n    clrl lf2p_assigned\n    bra .Lpk_used', '    bra .Lpk_close')
 # B consomme les potards audio même si A les laisse passer.
 page=page.replace('    bne .Lpe_quick','    bne .Lpe_out')
 # La page A laisse le clavier au gestionnaire natif ; B doit le router privé.
 a=page.index('    | Le clavier natif sous la fenêtre')
 b=page.index('    cmpil #10,%d0',a)
 page=page[:a]+page[b:]
 a=page.index('lf2p_pad:');b=page.index('    .section .text.lf2p_enc_navigation',a)
 page=page[:a]+'''lf2p_pad:
    movel %sp@(8),%sp@-
    moveal mlp_obj,%a0
    lea %a0@(16),%a0
    movel %a0,%sp@-
    jsr mlp_pad
    addql #8,%sp
    movel mlp_track,%d0
    movel %d0,lf2p_track
    moveal %sp@(4),%a0
    lea %a0@(-16),%a0
    movel %a0,%sp@-
    jsr 0x40076082
    addql #4,%sp
    moveq #1,%d0
    rts

'''+page[b:]
 page=page.replace('    | Sans LFO maintenu, laisser le gestionnaire natif éditer le synthé A.\n    moveq #0,%d0','    | Les autres potards restent consommés côté B.\n    moveq #1,%d0')
 page+='''
    .text
.Lpe_b_knob:
    subql #2,%d0
    cmpil #11,%d0
    bhi .Lpe_out
    movel %d0,%d4
    bra .Lpe_pass
'''
 page=rename(page);layout=rename(layout)
 a=page.index('    | Même sélection de piste');b=page.index('    lea.l   0x400802e0',a)
 page=page[:a]+'''    movel mlp_track,%d0
    movel %d0,mlccp_track
'''+page[b:]
 page=page.replace('    tstl mlcc_settings\n    beqw mlccp_o_done','    tstl mlcc_settings\n    beqw mlccp_o_done\n    tstl mlp_obj\n    beqw mlccp_o_done')
 page=page.replace('jsr     0x4007700e            | présenter','jsr     mlccp_present        | garder la banque B')
 page=page.replace('    bra .Lpk_close\n.Lpk_close_down:', '    moveq #1,%d0\n    eorl %d0,mlccp_index\n    bra .Lpk_redraw\n.Lpk_close_down:')
 a=page.index('    cmpil #33,%d4');b=page.index('    cmpil #32767,%d4',a);page=page[:a]+page[b:]
 a=page.index('.Lpe_high_ok:');b=page.index('.Lpe_set:',a);page=page[:a]+'.Lpe_high_ok:\n'+page[b:]
 page=page.replace('    movel mlccp_track,%sp@-\n    movel mlcc_settings,%sp@-\n    jsr lf2_edit\n    lea %sp@(16),%sp','    movel mlccp_index,%sp@-\n    movel mlccp_track,%sp@-\n    movel mlcc_settings,%sp@-\n    jsr mlcc_cfg_edit\n    lea %sp@(20),%sp')
 page=page.replace('    movel mlccp_track,%sp@-\n    movel mlcc_settings,%sp@-\n    jsr lf2_edit\n    lea.l %sp@(16),%sp','    movel mlccp_index,%sp@-\n    movel mlccp_track,%sp@-\n    movel mlcc_settings,%sp@-\n    jsr mlcc_cfg_edit\n    lea.l %sp@(20),%sp')
 a=page.index('mlccp_raw_value:');b=page.index('    .section .text.mlccp_value',a)
 page=page[:a]+'''mlccp_raw_value:
    movel %d2,%d0
    subql #1,%d0
    movel %d0,%sp@-
    movel mlccp_index,%sp@-
    movel mlccp_track,%sp@-
    movel mlcc_settings,%sp@-
    jsr mlcc_cfg_get
    lea.l %sp@(16),%sp
    rts

'''+page[b:]
 a=page.index('.Lpr_dest:');b=page.index('    .section .text.mlccp_render_tail',a)
 page=page[:a]+'''.Lpr_dest:
    cmpil #4,%d2
    beq mlccp_dest_name
    bra .Lpr_not_dest
'''+page[b:]
 a=page.index('mlccp_destination_name:');b=page.index('    .section .data.mlccp_state',a)
 page=page[:a]+'mlccp_destination_name:\n    jmp mlcc_name\n\n'+page[b:]
 page=page.replace('.word 32767,23,32767,33,6,32767,4,32767','.word 32767,23,32767,128,6,32767,4,32767')
 page=page.replace('    movel %d0,mlccp_track\n    moveal %sp@(4)', '    movel %d0,mlccp_track\n    movel %d0,mlp_track\n    moveal %sp@(4)')
 page=page.replace('    lea.l   mlccp_obj,%a0\n    clrl    %a0@', '    jsr mlp_keyboard_cancel\n    lea.l   mlccp_obj,%a0\n    clrl    %a0@')
 # Les touches clavier gardent le routage MIDI B, même sous la page LFO.
 page=page.replace('    cmpil #10,%d0\n    beq .Lpk_transport', """    cmpil #16,%d0
    bcs .Lcc_not_trig
    cmpil #31,%d0
    bhi .Lcc_not_trig
    movel %d2,%sp@-
    movel %d0,%sp@-
    jsr mlp_keyboard
    addql #8,%sp
    bra .Lpk_used
.Lcc_not_trig:
    cmpil #10,%d0
    beq .Lpk_transport""")
 page=page.replace('    movel %d0,%sp@-\n    pea mlccp_fmt_s\n    jmp .Lpr_value', '    movel %d0,%sp@-\n    jsr mlccp_window\n    addql #4,%sp\n    movel %d0,%sp@-\n    pea mlccp_fmt_s\n    jmp .Lpr_value')
 # Le titre change dans le descripteur privé avant chaque rendu natif.
 layout=layout.replace('    lea.l %a2@(0x500),%a2\n    movel mlccp_row', '''    lea.l %a2@(0x500),%a2
    lea mlccl_title,%a0
    tstl mlccp_index
    beq .Lcc_title_ready
    lea mlccl_title2,%a0
.Lcc_title_ready:
    movel %a0,%a2@(148)
    movel mlccp_row''')
 layout=layout.replace('.long 5,5,-1\nmlccl_title: .asciz "LFO 2"','.long 7,7,-1\nmlccl_title: .asciz "M LFO 1"\n    .balign 4\n    .long 7,7,-1\nmlccl_title2: .asciz "M LFO 2"')
 extra='''
    .data
    .balign 4
    .globl mlcc_settings,mlccp_index
mlcc_settings: .long 0
mlccp_index: .long 0
    .text
    .globl mlccp_present
mlccp_present:
    lea %sp@(-8),%sp
    moveml %d2/%a2,%sp@
    moveal %sp@(16),%a0
    moveal %a0@,%a2
    movel %a2@(32),%d2
    movel %a2@(28),%d0
    movel %d0,%a2@(32)
    movel %sp@(20),%sp@-
    movel %sp@(20),%sp@-
    movel %sp@(20),%sp@-
    jsr 0x4007700e
    lea %sp@(12),%sp
    movel %d2,%a2@(32)
    moveml %sp@,%d2/%a2
    lea %sp@(8),%sp
    rts
'''
 return {'page':page,'layout':layout,'support':extra,'scroll':(ROOT/'tools/machines/midi_lanes/lfo_cc_scroll.s').read_text()}
