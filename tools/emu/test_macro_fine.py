"""Vrai lookup/edition/popup MACRO ; accord fin et lo-fi independants."""
import argparse,pathlib,sys,struct
HERE=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from test_midi_entry import boot_case
from lofi_ui import UI,SCRATCH,UI_REC,PITCH,FTUN,want_text
from unicorn import m68k_const as mk
ROOT=HERE.parent.parent
class FineUI(UI):
 def __init__(self,img,payload):
  self.settings=False;self.machine=0
  super().__init__(img,payload,end=0x40000400+len(img))
  self.hooks[0x400cf866]=('root',SCRATCH+0x4000);self.hooks[0x40012412]=('track',0)
 def _hook(self,u,pc,size,data):
  if pc==0x4007faf4:
   sp=u.reg_read(mk.UC_M68K_REG_A7);key=int.from_bytes(u.mem_read(sp+4,4),'big')
   u.reg_write(mk.UC_M68K_REG_D0,int(key==13 and self.settings));u.reg_write(mk.UC_M68K_REG_PC,self.u32(sp));u.reg_write(mk.UC_M68K_REG_A7,sp+4);return
  return super()._hook(u,pc,size,data)
 def call(self,fn,*args,**kwargs):
  if fn==0x4000b7d6 and getattr(self,'normal_edit',False):
   args=list(args);args[4]=0
  return super().call(fn,*args,**kwargs)
 def edit_normal(self,desc,value,delta):
  self.normal_edit=True
  try:return self.edit_func(desc,value,delta)
  finally:self.normal_edit=False
 def lookup(self,machine,knob,func):
  self.machine=machine;return super().lookup(machine,knob,func)
def load(case):
 img,mem,ts=boot_case(case);lo=min(at for at,raw in mem);hi=max(at+len(raw) for at,raw in mem);raw=bytearray(hi-lo)
 for at,data in mem:raw[at-lo:at-lo+len(data)]=data
 r=FineUI(img,(lo,bytes(raw)));return r,ts
def main():
 p=argparse.ArgumentParser();p.add_argument('--profile',default='all');a=p.parse_args();prefix='build/macro-fine/'+a.profile
 before,bt=load(prefix+'-before');after,ts=load(prefix+'-after');q=next(t for t in ts if t['id'] in ('macro-fine-test','macro-fine'));machine=int(q['symbols']['macro_fine_index'],16)
 assert before.lookup(machine,2,True)==FTUN and after.lookup(machine,2,True)==FTUN
 assert [after.text(FTUN,n<<8) for n in range(128)]==[want_text(n) for n in range(128)]
 assert after.lookup(machine,2,False)==PITCH
 bounds=SCRATCH+0x5500;after.uc.reg_write(mk.UC_M68K_REG_A0,bounds);after.call(0x4005a65a,PITCH);lo,hi,_=struct.unpack('>3i',after.uc.mem_read(bounds,12))
 after.settings=True
 sy={k:int(v,16) for k,v in q['symbols'].items() if k.startswith('mf_')}
 held=after.u32(sy['mf_api']+16)
 if held:after.uc.mem_write(held,struct.pack('>I',1))
 for value in (0,2,256,0x3ffe,0x4000,0x4002,0x40fe,0x7efe,0x7f00):
  for delta in (1,256,512,768,-1,-256,-512,-768):
   turns=(abs(delta)+255)//256*(1 if delta>=0 else -1);expected=max(lo,min(hi,value+2*turns))
   assert after.edit_func(PITCH,value,delta)==expected,(value,delta,after.edit_func(PITCH,value,delta),expected)
 assert after.text(PITCH,0x4002)=='+0.008' and after.text(PITCH,0x3ffe)=='-0.008'
 assert after.popup(PITCH,0x4002)==after.popup(PITCH,0x4002,text_path=True)
 print('PASS SETTINGS + PITCH : vrai setter natif,72editions fines, bornes et popup decimal ;128valeurs lo-fi intactes')
 after.settings=False
 if held:after.uc.mem_write(held,bytes(4))
 assert after.edit_func(PITCH,0x4002,256)==0x4102
 for other in range(machine):
  assert after.lookup(other,2,False)==before.lookup(other,2,False)
  for cur in (0x4000,0x4002,0x40fe):
   assert after.edit_func(PITCH,cur,256)==before.edit_func(PITCH,cur,256)
   assert after.text(PITCH,cur)==before.text(PITCH,cur)
   for delta in (32,-32,256):assert after.edit_normal(PITCH,cur,delta)==before.edit_normal(PITCH,cur,delta)
 print('PASS PITCH normal garde la fraction MACRO ; autres machines gardent edition/texte natifs')
 after.lookup(machine,2,False);after.settings=True
 if held:after.uc.mem_write(held,struct.pack('>I',1))
 after.edit_func(PITCH,0x4000,256)
 event=SCRATCH+0x5000;after.uc.mem_write(event,struct.pack('>6I',0,0,0,13,0,0))
 sy={k:int(v,16) for k,v in q['symbols'].items() if k.startswith('mf_')}
 # Sans support commun, le hook consomme la release ; avec support, mod_used la consomme.
 api=sy['mf_api'];used=after.u32(api+4)
 assert after.call(sy['mf_key'],event)==(0 if used else 1)
 if used:assert after.u32(used)==1
 # Vrai hook clavier physique, getter/flag commun a zero : aucune injection held.
 after.settings=False
 if held:after.uc.mem_write(held,bytes(4))
 mm=next((t for t in ts if t.get('symbols',{}).get('mm_ui_api')),None)
 if mm:
  delegate=SCRATCH+0x7000
  after.uc.mem_write(int(mm['symbols']['mm_ui_api'],16)+16,struct.pack('>I',delegate))
  after.hooks[delegate]=('native-key-dispatch',0)
 after.lookup(machine,2,False)
 after.uc.mem_write(event,struct.pack('>6I',0,0,0,13,1,0))
 after.call(0x40077720,0,event)
 assert after.edit_func(PITCH,0x4000,256)==0x4002
 assert after.edit_normal(PITCH,0x4000,32)==0x4002
 assert after.edit_normal(PITCH,0x4000,-32)==0x3ffe
 after.uc.mem_write(event,struct.pack('>6I',0,0,0,13,0,0));after.call(0x40077720,0,event)
 assert after.edit_func(PITCH,0x4000,256)==0x4100
 before.lookup(machine,2,False)
 for delta in (1,32,64,256,-1,-32,-256):
  assert after.edit_normal(PITCH,0x4000,delta)==before.edit_normal(PITCH,0x4000,delta),delta
 print('PASS chemin potard ordinaire vt[20] : SETTINGS donne2unites, sinon comportement stock intact')
 print('PASS vrai hook SETTINGS down/release -> PITCH : deux unites fines tenu,256unites normales relache, flag commun nul')
 # Les fractions doivent survivre au vrai codec son, pas seulement a l'UI.
 raw,record,loaded=SCRATCH+0x6000,SCRATCH+0x6100,SCRATCH+0x6200
 for fraction in (2,126,128,254):
  sound=bytearray(100);sound[38]=machine;struct.pack_into('>H',sound,40,0x4000+fraction);struct.pack_into('>H',sound,54,64<<8)
  after.uc.mem_write(raw,bytes(sound));assert after.call(0x4005afa0,record,raw)==1
  after.uc.mem_write(loaded,bytes(100));assert after.call(0x4005aecc,loaded,record)==1
  got=int.from_bytes(after.uc.mem_read(loaded+40,2),'big');assert got==0x4000+fraction,(fraction,hex(got))
 print('PASS sauvegarde/rechargement son natif conserve les fractions ; release SETTINGS ne declenche pas CONFIG')
if __name__=='__main__':main()
