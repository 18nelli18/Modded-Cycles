#!/usr/bin/env python3
"""Intégration menu retrigger B : raccourci, réglages/locks, rendu OS réel."""
import argparse
from unicorn import UC_HOOK_CODE
from test_midi_lane_page import make,key,knob,PAT
from test_sdvintage import main_os_from_syx
from test_seq_gen_menu import RAW

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--cycles',required=True);a=ap.parse_args()
 r=make(main_os_from_syx(a.cycles),repeat=True);assert r.call('mlp_open')==1
 obj=r.r32(r.s['mlp_obj']);r.w32(r.s['mlp_track'],0);r.w32(r.s['ml_play_pattern'],PAT)
 r.call(0x400e7dbc);r.call(0x40070172,0x93006000,128,64,0x93090000,0)
 sound=bytes(r.u.mem_read(RAW,722));notes=bytes(r.u.mem_read(PAT,1584))
 assert key(r,1)==1 and key(r,4)==1
 assert r.r32(r.s['mlp_setup'])==4
 key(r,4,0);key(r,1,0)
 settings=r.r32(r.s['ml_repeat_edit_settings']);assert settings
 assert r.r32(r.s['ml_repeat_play_settings'])==settings
 assert [r.call('mlp_retrigger_value',i) for i in range(6)]==[8,0,0,0,5,1]
 r.texts.clear();r.call('mlp_render',obj,0x93006000)
 assert any(t[2]=='1/12' for t in r.texts),r.texts
 assert key(r,32,16)==1
 for _ in range(20):knob(r,1)
 assert r.call('mlp_retrigger_value',0)==16
 key(r,32,16);knob(r,1);key(r,32,16)
 for _ in range(150):knob(r,1)
 assert r.call('mlp_retrigger_value',1)==127
 key(r,32,16);knob(r,1);key(r,32,16);knob(r,-1)
 assert r.call('mlp_retrigger_value',2)==0
 # Un trig maintenu écrit un lock privé ; les défauts restent inchangés.
 r.w32(r.s['mlp_held'],1);r.w32(r.s['mlp_step'],0)
 r.w32(r.s['mlp_row'],3);r.w32(r.s['mlp_edit'],1);knob(r,1)
 assert r.call('mlp_retrigger_value',3)==1
 assert bytes(r.u.mem_read(settings,1))==b'\0'
 assert bytes(r.u.mem_read(settings+8,8))==bytes((1,0,0,0,0,1,1,0)),bytes(r.u.mem_read(settings+8,8)).hex()
 r.w32(r.s['mlp_held'],0)
 assert r.call('mlp_retrigger_value',3)==0
 # Le clavier continue à jouer derrière ce menu, même REC actif.
 state=0x930a0000;r.stubs[0x400cf9a8]=lambda args:state
 r.u.hook_add(UC_HOOK_CODE,r.stub,begin=0x400cf9a8,end=0x400cf9a8)
 r.u.mem_write(state+357,b'\x01\x01')
 live=r.s['ml_live_runtime'];r.u.mem_write(live,bytes(320))
 assert key(r,19)==1 and r.call('ml_take',live)==0x96376404
 assert key(r,19,0)==1 and r.call('ml_take',live)==0x86370004
 assert r.call('ml_take',live)==0 and r.r32(r.s['mlp_setup'])==4
 assert bytes(r.u.mem_read(RAW,722))==sound and bytes(r.u.mem_read(PAT,1584))==notes
 assert key(r,12)==1 and r.r32(r.s['mlp_setup'])==0 and r.r32(r.s['mlp_obj'])==obj
 # Vrai hold avant FUNC+RETRIG : le lock édité survit au release du trig.
 r.u.mem_write(PAT+8,bytes((72,100,1,1)))
 r.w32(r.s['mlp_step'],0)
 assert key(r,16)==1 and r.r32(r.s['mlp_held'])==1
 assert key(r,1)==1 and key(r,4)==1
 key(r,4,0);key(r,1,0)
 r.w32(r.s['mlp_row'],3);r.w32(r.s['mlp_edit'],1);knob(r,1)
 assert key(r,16,0)==1
 assert bytes(r.u.mem_read(PAT+11,1))==b'\x01'
 assert bytes(r.u.mem_read(settings+8,8))==bytes((1,0,0,0,0,1,1,0))
 assert key(r,12)==1 and r.r32(r.s['mlp_setup'])==0
 # Supprimer ensuite ce trig retire son lock sans modifier les défauts.
 assert key(r,16)==1 and key(r,16,0)==1
 assert bytes(r.u.mem_read(settings+8,8))==bytes((0,0,0,0,0,1,0,0))
 assert bytes(r.u.mem_read(settings,8))==bytes((0,16,127,0,5,1,6,0))
 print('ok : FUNC+RETRIG ouvre le menu natif B, six lignes/limites/INF, lock de pas privé, BACK conserve B, A intact')
if __name__=='__main__':main()
