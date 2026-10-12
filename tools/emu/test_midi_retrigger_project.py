#!/usr/bin/env python3
"""Load natif : annulation repeat et retrait des extensions à IPL0."""
import argparse,struct
from unicorn import UC_HOOK_CODE
from test_midi_lane_page import make,PAT
from test_sdvintage import main_os_from_syx

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--cycles',required=True);a=ap.parse_args()
 r=make(main_os_from_syx(a.cycles),repeat=True)
 r.w32(r.s['ml_play_pattern'],PAT)
 r.call('ml_repeat_prepare_ui')
 settings=r.r32(r.s['ml_repeat_edit_settings']);assert settings
 assert r.call('ml_repeat_pattern_lookup',PAT)==settings
 at=0x4006a660
 assert bytes(r.u.mem_read(at,8)).hex()=='4cd7040c4fef0020'
 r.u.mem_write(at,b'\x4e\xf9'+struct.pack('>I',r.s['ml_repeat_project_hook'])+b'\x4e\x71')
 status=[0]
 for address,fn in ((0x4006a3ac,lambda args:0x41400000),
                    (0x4005d3dc,lambda args:status[0]),
                    (0x400d0aae,lambda args:0),(0x400cf044,lambda args:0)):
  r.stubs[address]=fn;r.u.hook_add(UC_HOOK_CODE,r.stub,begin=address,end=address)
 def load(slot):return r.call(0x4006a5a0,0x93010000,slot,0x93011000,0x93012000)
 assert load(3)==0 and r.r32(r.s['ml_repeat_reset_pending'])==0
 assert r.call('ml_repeat_pattern_lookup',PAT)==settings
 for slot in (0,95,96):
  state=r.s['ml_repeat_states'];runtime=r.r32(r.s['ml_runtime'])
  assert r.call('ml_repeat_arm',runtime,state,0,100,0x96486404,8,0xffffffff)==1
  assert r.call('ml_take',runtime)==0x96486404
  status[0]=1;assert load(slot)==1
  assert r.r32(r.s['ml_repeat_reset_pending'])==1
  assert r.r32(state)==0 and r.call('ml_take',runtime)==0x86480004
  assert r.r32(r.s['ml_repeat_play_settings'])==0
  assert r.r32(r.s['ml_repeat_edit_settings'])==0
  assert r.call('ml_repeat_pattern_lookup',PAT)==0
  freed=len(r.free);r.call('ml_repeat_prepare_ui')
  assert len(r.free)==freed+1 and r.free[-1]==settings
  assert r.r32(r.s['ml_repeat_reset_pending'])==0
  settings=r.r32(r.s['ml_repeat_edit_settings']);assert settings
  assert bytes(r.u.mem_read(settings,8))==bytes((0,8,0,0,5,1,0,0))
 print('ok : vrai ProjectCache Load succès/échec/working96, Off avant retrait, lookup bloqué, free UI et nouveaux défauts')
 print('Limite : cache/convertisseur simulés ; ne constitue pas une preuve de sauvegarde')
if __name__=='__main__':main()
