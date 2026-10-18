"""Gestes MIDI seuls, vrai vtable MainScreenView, notifications et redraw OS."""
import json,struct,pathlib,sys
HERE=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from test_midi_machine_ui import UI,ROOT,EVENT,SOUND
import gen_sdvintage_7th as g7
def main():
 r=UI(g7.cycles_main(str(ROOT/'firmware/model-cycles_OS1.13.syx')),json.loads((ROOT/'build/midi-machine/controls-ui.json').read_text()));r.assign=False
 app=0x920d0000;manager=app+64;node=app+512;view=app+768
 r.word(0x40fe4178,app);r.stub(0x400d0974,lambda args:app)
 r.word(manager+24,node);r.word(node+4,manager+20);r.word(node+8,view);r.word(view,0x400ffe20)
 assert r.word(0x400ffe20+16)==0x4001b22a,'vtable native MainScreenView'
 def key(code,flags):
  r.u.mem_write(EVENT,struct.pack('>6I',0,0,0,code,flags,0));return r.call(r.s['mm_ui_key'],EVENT)
 def title():
  r.lines.clear();assert r.call(r.s['mm_draw'],view,0x920c0000)==1;return r.lines[0]
 for lane in range(6):
  r.track=lane;params=SOUND+0x1000*lane+20
  assert key(13,1)==1 and key(13,0)==1
  assert title()==f'T{lane+1} MIDI SETUP'
  before=bytes(r.u.mem_read(params,66));r.call(r.s['mm_encoder'],r.event(-1,1));assert bytes(r.u.mem_read(params,66))==before
  assert key(32,16)==1;r.call(r.s['mm_encoder'],r.event(-1,1));assert r.call(r.s['mm_route_read'],params,1)==1
  r.call(r.s['mm_encoder'],r.event(0,-13));assert r.call(r.s['mm_route_read'],params,0)==3
  r.call(r.s['mm_encoder'],r.event(1,3));assert r.call(r.s['mm_route_read'],params,1)==4
  assert key(12,1)==1 and title()==f'T{lane+1} MIDI OUT'
  for lfo,cc in ((0,74),(1,71)):
   assert key(8,1)==1 and key(8,0)==1;assert title()==f'T{lane+1} MIDI LFO {lfo+1}'
   r.call(r.s['mm_encoder'],r.event(3,cc-128));assert r.call(r.s['mm_lfo_read'],params,lfo,3)==cc
  key(12,1);assert title()==f'T{lane+1} MIDI OUT'
  assert key(13,1)==1;r.assign=True;r.output.clear();r.call(r.s['mm_encoder'],r.event(0,75));assert not r.output;r.assign=False
  assert key(13,0)==1 and title()==f'T{lane+1} MIDI OUT'
  assert r.u.mem_read(manager+32,1)==b'\1','redraw natif absent'
 print('PASS six pistes : SETTINGS/CC sans CONFIG, canal/port, DATA clic avant edition, deux menus LFO, BACK, redraw natif')
 r.word(view,0x40117920);assert r.call(r.s['mm_encoder'],r.event(-1,1))==0
 print('PASS DATA delegue quand une fenetre native couvre le panneau MIDI ; aucun reglage audio cache dans les panneaux MIDI')
if __name__=='__main__':main()
