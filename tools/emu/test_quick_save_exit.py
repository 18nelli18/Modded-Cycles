"""Note113 : close natif de la vue mute, resultat clavier et autres accords preserves."""
import argparse,json,pathlib,sys
from unicorn import UC_HOOK_CODE,m68k_const as mk
HERE=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from test_midi_entry import boot_case
from test_seq_gen_menu import Rig,EVENT,OBJ

def main():
 p=argparse.ArgumentParser();p.add_argument('--case',required=True);a=p.parse_args();img,memories,ts=boot_case(a.case);ws={k:int(v,16) for k,v in next(t['symbols'] for t in ts if t['id']=='sample-wizard').items()};entry=int(next(t['symbols']['qs_exit'] for t in ts if 'qs_exit'in t.get('symbols',{})),16)
 for reference in (True,False):
  r=Rig(img,{'writes':[]},{'writes':[],'symbols':{}});u=r.u
  for at,size in ((0x43000000,0x800000),(0x46700000,0x400000),(0x80000000,0x200000)):u.mem_map(at,size)
  for at,raw in memories:u.mem_write(at,raw)
  assert r.r32(0x40100c44)==entry,'vtable non raccordee'
  r.stubs[0x40148662]=lambda a:37;u.hook_add(UC_HOOK_CODE,r.stub,begin=0x40148662,end=0x40148662)
  # Corps key natif execute ; delegateur UI exterieur seul est simule.
  u.mem_write(OBJ,bytes(128));r.w32(OBJ,0x40100c3c);cases=0
  regs=[getattr(mk,'UC_M68K_REG_D'+str(i)) for i in range(2,8)]+[getattr(mk,'UC_M68K_REG_A'+str(i)) for i in range(2,6)]
  closes=[];u.hook_add(UC_HOOK_CODE,lambda u,pc,size,data:closes.append(1),begin=0x40076126,end=0x40076126)
  for flags in range(128):
   for used in (0,1):
    for held in (0,1):
     r.w32(ws['set_held'],held);r.w32(ws['mod_used'],used);u.mem_write(0x401487ec,b'\1\1');u.mem_write(OBJ+48,b'\0');r.event(13,flags,1234);event=bytes(u.mem_read(EVENT,24));closes.clear()
     for i,reg in enumerate(regs):u.reg_write(reg,0x12340000+i)
     value=r.call(0x40148744 if reference else entry,OBJ,EVENT)
     assert value==37 and event==bytes(u.mem_read(EVENT,24));assert [u.reg_read(reg) for reg in regs]==[0x12340000+i for i in range(len(regs))]
     # Une liberation/settings frais modifie mod_used selon les regles existantes.
     passed=(flags&34)==34 and not used
     assert bytes(u.mem_read(OBJ+48,1))==(b'\1' if not reference and passed else b'\0'),(reference,flags,used,held)
     assert len(closes)==int(not reference and passed),(reference,flags,used,held,closes)
     cases+=1
  print('PASS',cases,'cas', 'ancien laisse vue ouverte' if reference else 'candidat appelle close natif et marque la vue fermee uniquement pour save long FUNC',flush=True)
 print('PASS resultat clavier,evenement,ABI preserves ; view-close natif execute sans destruction immediate')
 print('LIMITES : retrait de la pile de vues, menu save complet et LED FUNCTION a verifier sur appareil')
if __name__=='__main__':main()
