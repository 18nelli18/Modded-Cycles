#!/usr/bin/env python3
"""Chance B : entrée encodeur réelle, locks multiples et formatter OS."""
import argparse
from unicorn import UC_HOOK_CODE
from test_midi_lane_page import make,key,knob,PAT,EVENT
from test_sdvintage import main_os_from_syx
from test_seq_gen_menu import RAW

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--cycles',required=True);a=ap.parse_args()
 r=make(main_os_from_syx(a.cycles),repeat=True,conditions=True)
 assert r.call('mlp_open')==1
 obj=r.r32(r.s['mlp_obj']);r.w32(r.s['mlp_track'],0);r.w32(r.s['ml_play_pattern'],PAT)
 state=0x930a0000;r.stubs[0x400cf9a8]=lambda args:state
 r.u.hook_add(UC_HOOK_CODE,r.stub,begin=0x400cf9a8,end=0x400cf9a8)
 r.u.mem_write(state+357,b'\x01\x01')
 sound=bytes(r.u.mem_read(RAW,722))
 r.call('ml_repeat_prepare_ui');settings=r.r32(r.s['ml_repeat_edit_settings'])
 assert r.call('mlp_chance_value')==0xffffffff
 # Deux pas maintenus ; aucun défaut de voie ni piste audio touché.
 r.u.mem_write(PAT+8,bytes((72,100,1,1))*2)
 key(r,16);key(r,17);assert r.r32(r.s['mlp_held'])==3
 def chance(delta):
  r.delta=delta;r.w32(EVENT+12,13);r.call('mlp_enc',obj,EVENT)
 chance(1);assert r.r32(r.s['mlp_setup'])==5
 assert bytes(r.u.mem_read(settings+7,1))==b'\0'
 assert r.call('mlp_chance_value')==0
 for code in range(64):
  assert r.call('mlp_chance_value')==code
  assert r.u.mem_read(settings+15,1)[0]==102+code,(code,bytes(r.u.mem_read(settings,32)).hex(),r.r32(r.s['mlp_held']))
  assert r.u.mem_read(settings+23,1)[0]==102+code
  if code<63:knob(r,1)
 knob(r,1);assert r.call('mlp_chance_value')==63
 for _ in range(64):knob(r,-1)
 assert r.call('mlp_chance_value')==0xffffffff,(r.call('mlp_chance_value'),bytes(r.u.mem_read(settings,24)).hex())
 chance(19);assert r.call('mlp_chance_value')==18
 key(r,16,0);key(r,17,0)
 assert bytes(r.u.mem_read(PAT+11,1))==b'\x01'
 assert bytes(r.u.mem_read(PAT+15,1))==b'\x01'
 key(r,12);assert r.r32(r.s['mlp_setup'])==0 and r.r32(r.s['mlp_obj'])==obj
 key(r,15);assert r.r32(r.s['ml_cond_fill'])==1
 key(r,15,0);assert r.r32(r.s['ml_cond_fill'])==0
 # Valeurs/écran réellement dessinés par l'OS avec tous les choix.
 r.call(0x400e7dbc);r.call(0x40070172,0x93006000,128,64,0x93090000,0)
 r.w32(r.s['mlp_setup'],5);r.w32(r.s['mlp_held'],1);r.w32(r.s['mlp_step'],0)
 for code in range(64):
  r.u.mem_write(settings+15,bytes((102+code,)))
  r.call('mlp_render',obj,0x93006000)
 assert bytes(r.u.mem_read(RAW,722))==sound
 print('ok : CHANCE/DATA,64 choix natifs, héritage, locks multiples, release sans suppression, BACK conserve B, FILL appui/release, rendu OS et isolation audio')
if __name__=='__main__':main()
