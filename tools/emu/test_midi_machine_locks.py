"""CC machine MIDI : gestes puis vrais locks/save/load/copie du pattern OS.

Seuls observateurs, horloge, UI et pilotes sont instrumentes. Aucun moteur B,
aucun codec de pattern remplace, aucune image de firmware exportee.
"""
import json,pathlib,struct,sys
HERE=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from test_midi_machine_ui import UI,ROOT,SOUND
from test_midi_machine_notes import PROJECT
import gen_sdvintage_7th as g7
RAW=0x92010000;LOAD=0x92020000;SERIAL=0x92030000;STATE=0x92040000

class Locks(UI):
 def __init__(self,stock,data):
  self.record=False;self.step=0
  super().__init__(stock,data)
  self.stub(0x400d0f6c,lambda a:0)
  self.stub(0x4006ba76,lambda a:int(self.record))
  self.bind(RAW)
 def stub(self,at,fn):
  if at==0x4006ba76:fn=lambda a:int(self.record)
  return super().stub(at,fn)
 def bind(self,raw,initialize=True):
  if initialize:self.call(0x400615e8,raw,0)
  obj=PROJECT+5192;self.obj=obj;self.raw=raw;self.plock=obj+640
  self.word(PROJECT+48,0x400fd8c0);self.word(0x40a7887c,raw);self.word(raw+30706,0)
  self.u.mem_write(obj,bytes(732))
  for offset,table in ((0,0x400fda54),(44,0x400fd8c0),(640,0x400fddf4)):self.word(obj+offset,table)
  for lane in range(6):
   track=self.track_obj(lane)
   for off,value in ((0,0x400ff894),(44,self.plock),(56,lane),(60,obj)):self.word(track+off,value)
   queue=PROJECT+83148+40*lane;self.word(queue+24,0x92050000+0x1000*lane);self.word(queue+32,0x92050800+0x1000*lane)
  self.call(0x4000c5d0,obj,raw);self.call(0x4000c9c4,obj+44,64)
  for lane in range(6):self.word(raw+30682+4*lane,0x80000000|(48<<21))
 def track_obj(self,lane):return PROJECT+5192+112+88*lane
 def get(self,lane,step,knob):return self.call(0x4000da2a,self.plock,lane,step,11+knob)
 def turn(self,knob,delta,assign=False):
  self.assign=assign;return self.call(self.s['mm_encoder'],self.event(knob,delta))
 def held(self,*steps):
  bits=sum(1<<s for s in steps);self.u.mem_write(STATE+357,b'\1');self.word(STATE+348,bits>>32);self.word(STATE+352,bits&0xffffffff)

def main():
 stock=g7.cycles_main(str(ROOT/'firmware/model-cycles_OS1.13.syx'))
 data=json.loads((ROOT/'build/midi-machine/controls-ui.json').read_text());r=Locks(stock,data)
 expected={}
 # Douze lanes de locks par piste : valeurs extremes et pages 1/2/3/4.
 for lane in range(6):
  r.track=lane;r.held()
  for knob in range(12):r.turn(knob,knob+1,True)
  base=bytes(r.u.mem_read(SOUND+0x1000*lane+20,66))
  r.output.clear();r.held(2,31,32,63)
  for knob in range(12):
   assert r.turn(knob,knob+1)==1
   for step in (2,31,32,63):
    value=(knob+1)*128+65+knob;assert r.get(lane,step,knob)==value,(lane,step,knob,hex(r.get(lane,step,knob)))
    expected[lane,step,knob]=value
  assert bytes(r.u.mem_read(SOUND+0x1000*lane+20,66))==base
  assert not r.output,'Edition de lock qui envoie un CC live'
  for step in (2,31,32,63):
   assert r.call(0x40015c7c,r.track_obj(lane),step)&255
   assert not r.call(0x40015c20,r.track_obj(lane),step)&255
 print('PASS six pistes x12CC x4pages : vrais locks natifs, bases preservees, lock-only sans note ni CC live')
 # Le lock garde son ancienne destination apres reassignment de la base.
 r.track=0;r.held();r.turn(0,20,True);r.held(2);r.turn(0,1)
 expected[0,2,0]+=1;assert r.get(0,2,0)==expected[0,2,0]
 r.turn(0,-127);expected[0,2,0]=128;assert r.get(0,2,0)==128
 r.turn(0,127);expected[0,2,0]=255;assert r.get(0,2,0)==255
 print('PASS increment depuis chaque lock, changement CC de base sans retargeter les locks, saturation0..127')
 r.held();r.call(0x4005ba0a,SERIAL,RAW,0);r.call(0x4005b894,LOAD,SERIAL,0);r.bind(LOAD,False)
 for (lane,step,knob),value in expected.items():assert r.get(lane,step,knob)==value,(lane,step,knob,r.get(lane,step,knob),value)
 r.call(0x4008f1f0,RAW,LOAD,30710);r.bind(RAW,False)
 for (lane,step,knob),value in expected.items():assert r.get(lane,step,knob)==value
 print('PASS sauvegarde/chargement/copie OS reels : 288locks conservent numero CC et valeur exacte')
 # Le recorder utilise le pas natif, avec le meme setter qu une edition grille.
 r.stub(0x4006a984,lambda a:r.step);r.record=True;r.track=3;r.step=17;r.output.clear();r.turn(4,2)
 assert r.get(3,17,4)==5*128+66
 assert any(message[1]==bytes((0xb0,4,66)) for message in r.output)
 print('PASS enregistrement CC live au pas natif, valeur envoyee et lock sauvegardable')
 print('LIMITES : stockage des reglages de son, worker de lecture des CC et composition finale encore requis')
if __name__=='__main__':main()
