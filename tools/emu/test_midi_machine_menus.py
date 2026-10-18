"""Gestes MIDI : vrais getters/setters KbT/Pad et notifications, appui SETTINGS brut."""
import json,struct,pathlib,sys
HERE=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from test_midi_machine_ui import UI,ROOT,EVENT,SOUND
from test_midi_machine_notes import TRACK,TRACK_DATA,VT
import gen_sdvintage_7th as g7

def main():
 r=UI(g7.cycles_main(str(ROOT/'firmware/model-cycles_OS1.13.syx')),json.loads((ROOT/'build/midi-machine/controls-ui.json').read_text()));r.assign=False
 app=0x920d0000;manager=app+64;node=app+512;view=app+768
 r.word(0x40fe4178,app);r.stub(0x400d0974,lambda args:app)
 r.word(manager+24,node);r.word(node+4,manager+20);r.word(node+8,view);r.word(view,0x400ffe20)
 r.stub(0x92060320,lambda a:TRACK_DATA+0x1000*((a[0]-TRACK)//88));r.word(VT+256+40,0x92060320);r.word(VT+256+16,0x92060400)
 held=app+1024;used=held+4;r.word(r.s['mm_ui_api'],held);r.word(r.s['mm_ui_api']+4,used)
 def key(code,flags):
  r.u.mem_write(EVENT,struct.pack('>6I',0,0,0,code,flags,0));return r.call(r.s['mm_ui_key'],EVENT)
 def title():
  r.lines.clear();active=r.call(r.s['mm_draw'],view,0x920c0000);return r.lines[0] if active else 'TRACK'
 for lane in range(6):
  r.track=lane;params=SOUND+0x1000*lane+20
  assert key(13,1)==0 and r.word(held)==1
  r.output.clear();r.call(r.s['mm_encoder'],r.event(0,75));assert not r.output and r.word(used)==1
  assert key(13,0)==1 and r.word(held)==0 and title()=='TRACK'
  # FUNC+TRACK, meme geste que B, sans simuler le getter FUNC natif.
  mute=app+2048;mute_node=app+2304
  r.word(manager+24,mute_node);r.word(mute_node+4,node);r.word(mute_node+8,mute);r.word(mute,0x40100c3c);r.u.mem_write(mute+48,b'\0')
  r.word(0x40100c44,0x40148744);r.u.mem_write(0x401487ec,b'\1\1')
  assert key(1,1)==0 and key(2,3)==1 and key(2,2)==1 and key(1,0)==0
  assert r.u.mem_read(mute+48,1)==b'\1' and r.u.mem_read(0x401487ec,2)==bytes(2)
  r.word(manager+24,node)
  assert title()==f'T{lane+1} MIDI SETUP'
  assert all(any(name in line for line in r.lines) for name in ('Channel','Output','KbT','Pad Note'))
  before=bytes(r.u.mem_read(params,66));r.call(r.s['mm_encoder'],r.event(-1,1));assert bytes(r.u.mem_read(params,66))==before
  assert key(32,16)==1;r.call(r.s['mm_encoder'],r.event(-1,4));assert r.call(r.s['mm_route_read'],params,1)==4
  key(32,16);r.call(r.s['mm_encoder'],r.event(-1,-1));key(32,16);r.call(r.s['mm_encoder'],r.event(-1,-13));assert r.call(r.s['mm_route_read'],params,0)==3
  key(32,16);r.call(r.s['mm_encoder'],r.event(-1,2));key(32,16)
  r.call(r.s['mm_encoder'],r.event(-1,200));assert r.call(r.s['mm_track_read'],lane,0)==60
  r.call(r.s['mm_encoder'],r.event(-1,-200));assert r.call(r.s['mm_track_read'],lane,0)==0xffffffc4
  key(32,16);r.call(r.s['mm_encoder'],r.event(-1,1));key(32,16)
  r.call(r.s['mm_encoder'],r.event(-1,-127));r.call(r.s['mm_encoder'],r.event(-1,72));assert r.call(r.s['mm_track_read'],lane,1)==72,(lane,r.call(r.s['mm_track_read'],lane,1),r.lines)
  title();assert any('Pad Note C5' in line for line in r.lines),r.lines
  assert key(12,1)==1 and title()=='TRACK'
  for lfo,cc in ((0,74),(1,71)):
   assert key(8,1)==1 and key(8,0)==1;assert title()==f'T{lane+1} MIDI LFO {lfo+1}'
   r.call(r.s['mm_encoder'],r.event(3,cc-128));assert r.call(r.s['mm_lfo_read'],params,lfo,3)==cc
  key(12,1);assert title()=='TRACK'
  assert r.u.mem_read(manager+32,1)==b'\1'
  assert key(15,3)==0 and title()=='TRACK'
  assert r.call(r.s['mm_encoder'],r.event(-1,1))==0
 print('PASS six pistes : SETTINGS brut/CC/release, FUNC+TRACK Channel/Output/KbT/Pad via setters natifs, DATA clic avant edition, LFO et BACK')
 r.word(view,0x40117920);assert r.call(r.s['mm_encoder'],r.event(-1,1))==0
 print('PASS FUNC+PAGE/DATA et autres fenetres delegues ; aucune vue audio remplacee par defaut')
if __name__=='__main__':main()
