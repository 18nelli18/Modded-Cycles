"""Rendu menu MIDI avec les vraies polices, Bitmap et MenuView OS, sans imitation."""
import json,struct,pathlib,sys
HERE=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from test_midi_machine_ui import UI,ROOT,EVENT
from render_midi_bank import png
import gen_sdvintage_7th as g7
class Drawing(UI):
 def stub(self,at,fn):
  if at in (0x40071a04,0x40070dea):return
  return super().stub(at,fn)
def main():
 r=Drawing(g7.cycles_main(str(ROOT/'firmware/model-cycles_OS1.13.syx')),json.loads((ROOT/'build/midi-machine/controls-ui.json').read_text()));heap=[0x92180000]
 def new(a):
  at=heap[0];heap[0]+=(a[0]+15)&~15;r.u.mem_write(at,bytes(a[0]));return at
 for at,fn in ((0x400802e0,new),(0x400802ec,lambda a:0),(0x400cf044,lambda a:0),(0x400f4dc6,lambda a:1),(0x400f4e22,lambda a:0)):
  r.stub(at,fn)
 r.call(0x400e7dbc)
 def key(code,flags):r.u.mem_write(EVENT,struct.pack('>6I',0,0,0,code,flags,0));return r.call(r.s['mm_ui_key'],EVENT)
 key(1,1);key(2,3);key(2,2);key(1,0)
 canvas,fb=0x920c0000,0x920c1000;r.call(0x40070172,canvas,128,64,fb,0)
 for name,edit in (('browse',False),('edit',True)):
  if edit:key(32,16)
  r.u.mem_write(fb,bytes(1024));assert r.call(r.s['mm_draw'],0,canvas)==1
  raw=bytes(r.u.mem_read(fb,1024));assert any(raw)
  pixels=[0 if struct.unpack_from('>I',raw,(x*2+(63-y)//32)*4)[0]&(1<<(31-(63-y)%32)) else 255 for y in range(64) for x in range(128)]
  png(ROOT/f'build/midi-machine/menu-{name}.png',pixels)
  if not edit:before=raw
  else:assert before!=raw,'surbrillance edition identique a navigation'
 print('PASS vrai MenuView OS, polices et Bitmap natifs ; captures navigation/edition distinctes')
if __name__=='__main__':main()
