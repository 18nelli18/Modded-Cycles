"""Catalogue MIDI complet : vrais constructeurs/accesseurs natifs au-dela127.

Verifie menus et descripteurs, pas encore une integration MIDI publiable.
"""
import argparse,json,pathlib,sys,struct
HERE=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
import build,syntakt,gen_sdvintage_7th as g7,test_sdvintage_7th as T
ROOT=HERE.parent.parent

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--controls',action='store_true');a=parser.parse_args()
 stock=g7.cycles_main(str(ROOT/'firmware/model-cycles_OS1.13.syx'));st=syntakt.dsp_image(str(ROOT/'firmware/Syntakt_OS1.42.syx'))
 entry=json.loads((ROOT/f'build/midi-machine/catalogue-1023-1{"-controls" if a.controls else ""}.json').read_text());t=entry['engine'];pay=int(t['append']['dest'],16)
 recipes=[entry['wizard'],t];img,_=build.apply_writes(stock,recipes);rt=build.payload_runtime(t,stock,st)
 class UI(T.UI):
  def __init__(self):
   super().__init__(bytes(img));self.uc.mem_map(pay,0x100000);self.uc.mem_write(pay,rt)
   for p in entry['wizard']['append']['parts']:
    if 'hex'in p:self.uc.mem_write(int(p['dest'],16),bytes.fromhex(p['hex']))
 u=UI();u.call(0x4005a274);names=t['machine_names'];assert u.u32(T.ROW_COUNT)==18
 table=int(t['machine_tables'],16)
 for machine,name in enumerate(names):
  ptr=u.u32(table+4*machine);actual=bytes(u.uc.mem_read(ptr,32)).split(b'\0')[0].decode()
  if machine!=6:assert actual==name,(machine,name,actual)
  if machine>=7:
   first=76+5*(machine-7)
   for slot in range(4):
    idx=first+slot;assert u.call(0x4005a692,11+slot,machine)==idx,(machine,slot)
    assert u.call(0x4005a4e8,idx)==11+slot,(machine,idx)
   assert u.call(0x4005a4e8,first+4)==18
 print('PASS all18 native machines, own parameter descriptors, MIDI Out appended',flush=True)
 for i,label in enumerate(('CC 1','CC 2','CC 3','CC 4')):
  idx=126+i;ptr=u.call(0x4000b22a,0,idx);assert bytes(u.uc.mem_read(ptr,16)).split(b'\0')[0].decode()==label
  u.call(0x4005a65a,idx);assert struct.unpack('>3i',u.uc.mem_read(T.SCRATCH,12))==(0,127<<8,64<<8)
 reference=T.UI(stock);invalid=reference.call(0x4005a4e8,76)
 for idx in (131,132,255,256,0x7fffffff,0xffffffff):assert u.call(0x4005a4e8,idx)==invalid,(idx,'out-of-range accepted')
 assert not u.bad
 print('PASS MIDI descriptors126..130 accessible, indices131..UINT_MAX safely rejected',flush=True)
 if a.controls:
  from test_midi_machine_ui import UI as MidiUI,SOUND
  r=MidiUI(bytes(img),dict(hex=rt.hex(),symbols=t['symbols'],machine=17),pay)
  for part in entry['wizard']['append']['parts']:
   if 'hex' in part:r.u.mem_write(int(part['dest'],16),bytes.fromhex(part['hex']))
  for lane in range(6):
   r.track=lane;r.assign=True;r.output.clear();r.call(0x40006158,0,r.event(0,75))
   assert not r.output and r.popups[-1]=='CC01 ASSIGN 074'
   r.assign=False;r.call(0x40006158,0,r.event(0,1));assert ('DIN',bytes((0xb0,74,65))) in r.output
   r.lines.clear();assert r.call(r.s['mm_draw'],0,0x920c0000)==0 and not r.lines
   r.call(0x4005afa0,0x920a0000,SOUND+0x1000*lane)
   r.u.mem_write(SOUND+0x1000*lane,bytes(100));r.call(0x4005aecc,SOUND+0x1000*lane,0x920a0000)
   assert r.call(r.s['mm_cc_read'],SOUND+0x1000*lane+20,0)==75*128+65
  print('PASS catalogue18 : vrais dispatchs CC/UI et save/load des six sons MIDI, autres moteurs conserves')
 print('LIMITES : autres options, menus MIDI/LFO et verification physique encore requis' if a.controls else 'LIMITES : seuls menus/accesseurs verifies, CC/output/persistence integration pending')
if __name__=='__main__':main()
