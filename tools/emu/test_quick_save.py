"""Note113 : FUNC+SETTINGS long rejoint le natif ; autres evenements inchanges.
Vrai boot et getters. La persistance disque doit etre confirmee sur appareil.
"""
import argparse,json,pathlib,struct,sys
from unicorn import m68k_const as mk
HERE=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from test_midi_current_audio import boot
from test_seq_gen_menu import Rig,EVENT

def main():
 p=argparse.ArgumentParser();p.add_argument('--case',required=True);p.add_argument('--data',default='build/quicksave/data.json');a=p.parse_args();d=json.loads(pathlib.Path(a.data).read_text(encoding='utf-8'));img,rt,ts=boot(a.case);ws={k:int(v,16) for k,v in next(t['symbols'] for t in ts if t['id']=='sample-wizard').items()};fixtures=[]
 for reference in (True,False):
  r=Rig(img,{'writes':[]},{'writes':[],'symbols':{}});r.u.mem_map(0x46700000,0x400000);r.u.mem_map(0x80000000,0x200000);r.u.mem_write(0x46700000,rt)
  for t in ts:
   for part in t.get('append',{}).get('parts',[]):
    if 'hex' in part:r.u.mem_write(int(part['dest'],16),bytes.fromhex(part['hex']))
  assert bytes(r.u.mem_read(d['at'],d['size'])).hex()==d['hex'],'patched handler absent after boot'
  if reference:r.u.mem_write(d['at'],bytes.fromhex(d['old']))
  fixtures.append(r)
 regs=[getattr(mk,'UC_M68K_REG_D'+str(i)) for i in range(2,8)]+[getattr(mk,'UC_M68K_REG_A'+str(i)) for i in range(2,6)]
 for flags in range(128):
  for held in (0,1):
   for used in (0,1):
    rows=[]
    for r in fixtures:
     r.w32(ws['set_held'],held);r.w32(ws['mod_used'],used);r.event(13,flags,1234);before=bytes(r.u.mem_read(EVENT,24));r.u.reg_write(mk.UC_M68K_REG_A0,EVENT);r.u.reg_write(mk.UC_M68K_REG_D0,13)
     for i,reg in enumerate(regs):r.u.reg_write(reg,0x12340000+i)
     result=r.call(ws['kh_mod']);assert bytes(r.u.mem_read(EVENT,24))==before,'event flags/code altered'
     assert [r.u.reg_read(reg) for reg in regs]==[0x12340000+i for i in range(len(regs))]
     rows.append((result,r.r32(ws['set_held']),r.r32(ws['mod_used'])))
    if flags&32 and flags&2 and not used:assert rows[0][0]==0 and rows[1][0]==13 and rows[0][1:]==rows[1][1:],(flags,held,used,rows)
    else:assert rows[0]==rows[1],(flags,held,used,rows)
 print('PASS 512 cas : seul long FUNC inutilise restaure, autres flags/etats/ABI identiques',flush=True)
 r=fixtures[1];getter=int(next(t['symbols']['br_key_hook'] for t in ts if t['id']=='control-all-beat-repeat'),16)
 for k in ('sle_on','sle_run','set_held','mod_used'):r.w32(ws[k],0)
 def key(code,flags=1,time=42):r.event(code,flags,time);return r.call(getter,EVENT)
 for settings_first in (False,True):
  r.w32(ws['set_held'],0);r.w32(ws['mod_used'],0)
  if settings_first:assert key(13)==13;assert key(1)==1
  else:assert key(1)==1;assert key(13,3)==13
  assert r.r32(ws['set_held'])==1
  assert key(13,34)==13,'native save code swallowed by full chain'
  assert r.call(0x40072444,EVENT)==1 and r.call(0x40072490,EVENT)==1,'stock long/FUNC predicates changed'
  assert key(13,2)==13;assert r.r32(ws['set_held'])==0;assert key(1,0)==1
 r.w32(ws['set_held'],1);r.w32(ws['mod_used'],1);assert key(13,34)==0;assert key(13,2)==0;assert r.r32(ws['set_held'])==0
 print('PASS chaine getter reelle avec/sans ordre inverse, predicates stock long/FUNC, accord consomme bloque',flush=True)
 print('LIMITES : routage sauvegarde stock restaure ; ecriture/permanence a verifier sur hardware')
if __name__=='__main__':main()
