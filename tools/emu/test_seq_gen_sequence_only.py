#!/usr/bin/env python3
"""Générateur étendu sans routines de son ; menu, cartouche et setters OS réels."""
import argparse,json
from test_seq_gen_dynamics import fixture
from test_seq_gen_menu import ROOT
from test_seq_gen_advanced import sequence,pads,timer
from test_sdvintage import main_os_from_syx

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cycles',required=True);a=ap.parse_args()
    stock=main_os_from_syx(a.cycles)
    for dep,suffix in [('model-tg',''),('model-tg-st','-st')]:
        base=json.loads((ROOT/f'tweaks/model-cycles_OS1.13/30-{dep}.json').read_text())
        tweak=json.loads((ROOT/f'tweaks/model-cycles_OS1.13/experimental/sequence-only/49-scale-gen{suffix}.json').read_text())
        r=fixture(stock,base,tweak)
        for symbol in ('sg_sound_generate','sg_sound_current','sg_sound_apply','sg_sound_undo','sg_sound_valid','sg_sound_key'):
            assert symbol not in r.s,symbol
        sequence(r);pads(r);timer(r)
        r.w32(r.s['sg_intro'],1);r.rects.clear()
        r.call('sg_render',r.obj,0x93006000)
        assert r.rects[1][1:]==(8,4,119,5,0xffffffff)
        assert len(r.rects)>100
        assert all(0<=q[1]<=q[3]<=127 and 0<=q[2]<=q[4]<=63 for q in r.rects)
        r.w32(r.s['sg_intro'],0)
        for row in range(21):
            r.w32(r.s['sg_row'],row);r.texts.clear()
            r.call('sg_render',r.obj,0x93006000)
            labels=[t[2] for t in r.texts if t[0]==2]
            assert len(labels)==4 and not any('sound' in x.lower() for x in labels),labels
        assert labels==['Euclid hits','Rotation','Generate','Undo'],labels
        r.w32(r.s['sg_row'],19);r.w32(r.s['sg_edit'],0)
        r.knob(1);r.knob(1);assert r.r32(r.s['sg_row'])==20
        r.click();assert r.r32(r.s['sg_undo_valid'])==0
        r.knob(-1);r.click();assert r.r32(r.s['sg_undo_valid'])==1
        r.call('sg_dtor0',r.obj)
        r.call(0x4007240c,r.event(13,1,100))
        r.call(0x4007240c,r.event(2,1,101))
        assert r.r32(r.s['sg_obj'])==0
        r.call(0x4007240c,r.event(2,16,102))
        r.call(0x4007240c,r.event(13,16,103))
        r.call(0x4007240c,r.event(13,1,104))
        r.call(0x4007240c,r.event(15,1,105))
        assert r.r32(r.s['sg_obj']) and r.r32(r.s['sg_row'])==0
        print('ok :',dep,'21 lignes sans son, aucun runtime son, actions Generate/Undo, cartouche arrondi 120×56')
if __name__=='__main__':main()
