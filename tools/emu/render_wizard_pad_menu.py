"""Test130 : dessin reel du menu Pad Setup avec Bitmap/polices/MenuView natifs."""
import pathlib,sys,struct
HERE=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from test_midi_entry import boot_case
from test_midi_machine_menu_render import Drawing
from test_midi_machine_ui import EVENT
from test_midi_machine_notes import PROJECT
from render_midi_bank import png
ROOT=HERE.parent.parent
def main():
 img,mem,ts=boot_case('build/wizard-control/usb-after');engine=next(t for t in ts if t.get('machine_selection')==1023);pay=int(engine['append']['dest'],16);blob=next(raw for at,raw in mem if at==pay)
 sy={k:v for t in ts for k,v in t.get('symbols',{}).items()};r=Drawing(img,dict(hex=blob.hex(),symbols=sy,machine=17),pay)
 for at,raw in mem:r.u.mem_write(at,raw)
 heap=[0x92400000]
 def new(a):
  at=heap[0];heap[0]+=(a[0]+15)&~15;r.u.mem_write(at,bytes(a[0]));return at
 for at,fn in ((0x400802e0,new),(0x400802ec,lambda a:0),(0x400cf044,lambda a:0),(0x400f4dc6,lambda a:1),(0x400f4e22,lambda a:0)):
  r.stub(at,fn)
 r.word(PROJECT,0x92070010);r.word(0x92070004,0);r.call(0x4005a274);r.call(0x400e7dbc);r.call(0x40070172,0x40fe3310,48,22,0x4016bd98,r.word(0x400b12fe));r.word(0x40fe4178,0)
 def key(code,flags):r.u.mem_write(EVENT,struct.pack('>6I',0,0,0,code,flags,0));return r.call(r.s['wf_key'],EVENT)
 key(13,1);key(2,1);key(2,0);key(13,0)
 canvas,fb=0x920c0000,0x920c1000;r.call(0x40070172,canvas,128,64,fb,0)
 frames=[]
 for name,mode,edit in (('silent',0,False),('stock',1,True)):
  r.word(r.s['wf_stock'],mode)
  if edit:key(32,16)
  r.u.mem_write(fb,bytes(1024))
  assert r.call(r.s['wf_draw'],0,canvas)==1
  raw=bytes(r.u.mem_read(fb,1024));assert any(raw);frames.append(raw)
  pixels=[0 if struct.unpack_from('>I',raw,(x*2+(63-y)//32)*4)[0]&(1<<(31-(63-y)%32)) else 255 for y in range(64) for x in range(128)]
  png(ROOT/f'build/wizard-control/menu-{name}.png',pixels)
 assert frames[0]!=frames[1]
 print('PASS vrai MenuView/Bitmap/polices : Pad Setup Silent et Stock, navigation/edition distinctes')
if __name__=='__main__':main()
