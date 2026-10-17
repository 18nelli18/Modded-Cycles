"""Note113 : prouver la sortie du latch apres save et les autres accords inchanges."""
import argparse,json,pathlib,sys
from unicorn import UC_HOOK_CODE,m68k_const as mk
HERE=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from test_midi_current_audio import boot
from test_seq_gen_menu import Rig,EVENT

def main():
 p=argparse.ArgumentParser();p.add_argument('--case',required=True);a=p.parse_args();root=HERE.parents[1];d=json.loads((root/'docs/flasher-quick-save-test/quick-save-latch-data.js').read_text().split('=',1)[1].strip().rstrip(';'));img,rt,ts=boot(a.case);origin=int(next(t['symbols']['qs_latch'] for t in ts if 'qs_latch' in t.get('symbols',{})),16);d['origin']=origin;d['jump']='4ef9'+origin.to_bytes(4,'big').hex()+'4e71'*22;ws={k:int(v,16) for k,v in next(t['symbols'] for t in ts if t['id']=='sample-wizard').items()};fixtures=[]
 for reference in (True,False):
  r=Rig(img,{'writes':[]},{'writes':[],'symbols':{}});u=r.u;u.mem_map(0x46700000,0x400000);u.mem_map(0x80000000,0x200000);u.mem_write(0x46700000,rt)
  for t in ts:
   for part in t.get('append',{}).get('parts',[]):
    if 'hex' in part:u.mem_write(int(part['dest'],16),bytes.fromhex(part['hex']))
  assert bytes(u.mem_read(d['at'],50)).hex()==d['jump'];assert bytes(u.mem_read(d['origin'],len(d['hex'])//2)).hex()==d['hex']
  if reference:u.mem_write(d['at'],bytes.fromhex(d['old']))
  fixtures.append(r)
 regs=[getattr(mk,'UC_M68K_REG_D'+str(i)) for i in range(2,8)]+[getattr(mk,'UC_M68K_REG_A'+str(i)) for i in range(2,6)]
 for flags in range(128):
  for held in (0,1):
   for used in (0,1):
    rows=[]
    for r in fixtures:
     r.w32(ws['set_held'],held);r.w32(ws['mod_used'],used);r.u.mem_write(0x401487ec,b'\x01\x01');r.event(13,flags,1234);event=bytes(r.u.mem_read(EVENT,24));r.u.reg_write(mk.UC_M68K_REG_A0,EVENT);r.u.reg_write(mk.UC_M68K_REG_D0,13)
     for i,reg in enumerate(regs):r.u.reg_write(reg,0x12340000+i)
     value=r.call(ws['kh_mod']);assert event==bytes(r.u.mem_read(EVENT,24));assert [r.u.reg_read(reg) for reg in regs]==[0x12340000+i for i in range(len(regs))]
     rows.append((value,r.r32(ws['set_held']),r.r32(ws['mod_used']),bytes(r.u.mem_read(0x401487ec,2))))
    assert rows[0][:3]==rows[1][:3],(flags,held,used,rows)
    assert rows[0][3]==b'\x01\x01';assert rows[1][3]==(b'\0\0' if flags&32 and flags&2 and not used else b'\x01\x01'),(flags,held,used,rows)
 print('PASS 512 cas : save/accords/ABI identiques ; seul long FUNC inutilise libere latch',flush=True)
 for reference,r in zip((True,False),fixtures):
  u=r.u;held={1};r.stubs[0x4007faf4]=lambda a:int(a[0] in held);u.hook_add(UC_HOOK_CODE,r.stub,begin=0x4007faf4,end=0x4007faf4)
  r.stubs[0x4007240c]=lambda a:13;r.stubs[0x40148662]=lambda a:0
  for at in (0x4007240c,0x40148662):u.hook_add(UC_HOOK_CODE,r.stub,begin=at,end=at)
  u.mem_write(0x401487ec,b'\0\1');r.event(13,3,0);r.call(0x40148744,0,EVENT);assert bytes(u.mem_read(0x401487ec,2))==b'\1\1'
  r.w32(ws['set_held'],1);r.w32(ws['mod_used'],0);r.event(13,34,1000);u.reg_write(mk.UC_M68K_REG_A0,EVENT);u.reg_write(mk.UC_M68K_REG_D0,13);assert r.call(ws['kh_mod'])==13
  held.clear();assert r.call(0x401486fc)==int(reference)
 print('PASS garde mute natif : ancien reste ouvert, candidat ferme apres relachement',flush=True)
 print('LIMITES : cycle modal et LEDs physiques a verifier sur appareil')
if __name__=='__main__':main()
