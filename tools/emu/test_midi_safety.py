"""Regression native du bridge LFO2 et des producteurs MIDI live : avant/apres."""
import pathlib,sys,struct,os
HERE=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from test_midi_entry import boot_case
from test_midi_machine_worker import Worker
from test_midi_machine_ui import SOUND,EVENT
from test_midi_machine_notes import OBJECT,STACK
from unicorn import m68k_const as mk

def load(case):
 img,mem,ts=boot_case(case);e=next(t for t in ts if t.get('machine_selection')==1023);pay=int(e['append']['dest'],16);blob=next(b for a,b in mem if a==pay)
 r=Worker(img,dict(hex=blob.hex(),symbols=e['symbols'],machine=17),pay)
 for a,b in mem:r.u.mem_write(a,b)
 return r,ts

def producer(r,at,end,lane,note):
 r.u.mem_write(STACK,bytes(128));r.u.mem_write(STACK+512,bytes(100));r.u.mem_write(STACK+512+19,b'\x63')
 for reg,value in [('A7',STACK),('A6',STACK+512),('D2',lane),('D3',note)]:r.u.reg_write(getattr(mk,'UC_M68K_REG_'+reg),value)
 r.u.emu_start(at,end,count=100000)
 assert r.u.reg_read(mk.UC_M68K_REG_PC)==end
 assert r.u.reg_read(mk.UC_M68K_REG_A7)==STACK

def main():
 for case,fixed in [('build/cut-endpoint/usb',False),(os.environ.get('MIDI_SAFETY_CASE','build/midi-safety/usb'),True)]:
  r,ts=load(case);secondary=next(t for t in ts if t['id']=='lfo-secondary');bridge=int(secondary['symbols']['lf2n_write'],16)
  context=0x920e0000;r.word(context,0x400fd134);r.word(context+4,OBJECT);r.stub(0x400097f0,lambda a:context)
  p=SOUND+20;r.call(r.s['mm_setup'],p);r.call(r.s['mm_route_edit'],p,0,-11);r.call(r.s['mm_route_edit'],p,1,4)
  initial=bytes(r.u.mem_read(p,66));bad=[]
  for lane in range(6):
   r.track=lane;r.word(context+4,OBJECT+lane*0x1000);p=SOUND+lane*0x1000+20
   for field,value in enumerate((17000,2560,12000,74<<8,3<<8,8000,2<<8,20000)):
    r.u.mem_write(p,initial);r.call(bridge,lane,field,value)
    words=struct.unpack('>33H',r.u.mem_read(p,66))
    if words[31:]!=struct.unpack('>33H',initial)[31:]:bad.append((lane,field))
    if fixed:
     expected=value if field!=3 else value
     assert words[23+field]==expected,(lane,field,words[23:])
  assert bool(bad)==(not fixed),bad
  print('PASS',case,'LFO2 :',('canal/port/marqueur preserves pour48editions' if fixed else 'collision native reproduite '+str(bad)),flush=True)
  from test_midi_machine_sequence import Sequence,RAW
  e=next(t for t in ts if t.get('machine_selection')==1023)
  img,mem,_=boot_case(case);pay=int(e['append']['dest'],16);blob=next(b for a,b in mem if a==pay)
  sq=Sequence(img,dict(hex=blob.hex(),symbols=e['symbols'],machine=17),pay,prepared=True)
  for a,b in mem:sq.uc.mem_write(a,b)
  # Evenement live identique a4005894a : source2, flags30001, duree0.
  locks=sq.e.call(0x40091e66);sq.uc.mem_write(RAW,b'\xff'*68);sq.e.call(0x4005487c,locks,RAW,0,0)
  ev=sq.e.call(0x40091eb6)
  for off,val in ((4,1),(8,0),(12,2),(28,60),(40,0x30001),(52,0),(60,127),(72,locks)):sq.w32(ev+off,val)
  sq.uc.mem_write(ev+22,b'\x63\0');sq.e.call(0x40092116,ev);sq.run()
  notes=[bytes(sq.uc.mem_read(at,16)) for at in sq.queue if at!=sq.s['mm_wakeup']]
  assert not notes,(case,notes)
  print('PASS',case,'evenement audio live source2 ne regenere aucune attaque MIDI',flush=True)
  # Les producteurs natifs ne doivent pas doubler le relais direct MIDI.
  for machine in (17,0):
   r.u.mem_write(SOUND+38,bytes((machine,0)));r.queue.clear();r.output.clear()
   producer(r,0x400817aa,0x400817d8,0,60);producer(r,0x40081552,0x40081576,0,60)
   assert len(r.queue)==(0 if fixed and machine==17 else 2),(case,machine,r.queue)
  print('PASS',case,'producteurs natifs live : duplication reproduite/supprimee, deux messages audio conserves',flush=True)
  if fixed:
   text_at=0x920ef000;r.u.mem_write(text_at,b'ERR\0'+bytes(60));r.stub(0x4000b208,lambda a:text_at)
   before=bytes(r.u.mem_read(SOUND+20,66));assert r.string(r.call(r.s['mm_primary_name'],0,0,0,7))=='OFF'
   for dest,name in ((23,'ATK'),(24,'FLT'),(25,'RES')):assert r.string(r.call(r.s['mm_primary_name'],0,0,0,dest))==name
   assert bytes(r.u.mem_read(SOUND+20,66))==before
   print('PASS noms LFO : destination indisponible OFF, ATK/FLT/RES conserves, aucun parametre ecrit depuis le dessin',flush=True)
   r.assign=False
   for lane in range(6):
    r.track=lane;p=SOUND+lane*0x1000+20;r.u.mem_write(p,initial)
    for page in range(2):r.u.mem_write(EVENT,struct.pack('>6I',0,0,0,8,1,0));r.call(r.s['mm_ui_key'],EVENT)
    for k in range(8):r.call(0x40006158,0,r.event(k,1))
    assert bytes(r.u.mem_read(p+62,4))==initial[62:]
    r.call(r.s['mm_live_on'],lane,64,99);r.call(r.s['mm_route_edit'],p,0,1);r.call(r.s['mm_live_off'],lane,64)
   assert sum(1 for dest,msg in r.output if dest=='DIN' and msg[0]==0x85 and msg[1]==64)==6,r.output
   print('PASS six pistes : vraie entree encodeur LFO1/2 ne change pas le routage ; note-off sur ancien canal apres edition explicite',flush=True)
 print('LIMITES : drivers physiques et charge temps reel a verifier sur appareil')
if __name__=='__main__':main()
