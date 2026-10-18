"""MIDI : deux LFO, canal/port et12CC conserves dans le vrai record son OS.

Configuration seule, sans horloge LFO raccordee ; ne prouve pas l'interface.
"""
import pathlib,json,sys,struct
HERE=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from test_midi_machine_storage import UI,ROOT,SOUND,RECORD,HOOKS
import gen_sdvintage_7th as g7

def main():
 r=UI(g7.cycles_main(str(ROOT/'firmware/model-cycles_OS1.13.syx')),json.loads((ROOT/'build/midi-machine/controls-ui.json').read_text()))
 for at,name in HOOKS:r.u.mem_write(at,b'\x4e\xf9'+struct.pack('>I',r.s[name])+b'\x4e\x71')
 call=lambda name,*args:r.call(r.s['mm_'+name],*args)
 bounds=[32767,23,32767,128,6,32767,4,32767]
 for lane in range(6):
  r.track=lane;raw=SOUND+0x1000*lane;params=raw+20
  for knob in range(12):r.assign=True;r.call(r.s['mm_encoder'],r.event(knob,75+knob))
  cc=bytes(r.u.mem_read(params+22,24));call('setup',params)
  assert bytes(r.u.mem_read(params+22,24))==cc
  for lfo in range(2):
   for field,maximum in enumerate(bounds):
    assert call('lfo_edit',params,lfo,field,32767)==maximum
    assert call('lfo_read',params,lfo,field)==maximum
  assert call('route_edit',params,0,-127)==0
  assert call('route_edit',params,1,127)==4
  original=bytes(r.u.mem_read(params,66))
  assert r.call(0x4005afa0,RECORD,raw)==1
  r.u.mem_write(raw,bytes(100));assert r.call(0x4005aecc,raw,RECORD)==1
  assert bytes(r.u.mem_read(params,66))==original
  for lfo in range(2):
   for field in range(8):assert call('lfo_edit',params,lfo,field,-32767)==0
  assert call('route_edit',params,0,127)==16 and call('route_edit',params,1,-127)==0
  original=bytes(r.u.mem_read(params,66));r.call(0x4005afa0,RECORD,raw);r.u.mem_write(raw,bytes(100));r.call(0x4005aecc,raw,RECORD)
  assert bytes(r.u.mem_read(params,66))==original
 print('PASS six sons :12CC,16champs LFO aux extremes, canal/port,33mots exacts apres vrai save/load OS')
 assert call('lfo_edit',SOUND+20,2,0,1)==0xffffffff
 assert call('lfo_edit',SOUND+20,0,8,1)==0xffffffff
 assert call('route_edit',SOUND+20,2,1)==0xffffffff
 print('PASS bornes/OFF129choix CC pour chaque LFO, aucune allocation ou transmission pendant configuration')
 print('LIMITES : ce test isole le format ; horloge et menus couverts par les preuves LFO/menus separees')
if __name__=='__main__':main()
