"""Note 104 : vrai boot, copie Wizard avant init, cache et ABI du stage."""
import argparse,json,pathlib,struct,sys
from unicorn import UC_HOOK_CODE,m68k_const as mk
HERE=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from test_seq_gen_menu import Rig,STACK,STOP
from test_sdvintage import main_os_from_syx
import build
def main():
 p=argparse.ArgumentParser();p.add_argument('--case',required=True);a=p.parse_args();prefix=pathlib.Path(a.case);cat=json.loads(prefix.with_suffix('.json').read_text())['tweaks'];engine=next(t for t in cat if t.get('symbols',{}).get('no_midi_capacity_stage'));wizard=next(t for t in cat if t['id']=='sample-wizard');assert not any(t['id']=='midi-out-bank' for t in cat)
 stage=int(engine['symbols']['no_midi_capacity_stage'],16);copy=int(engine['symbols']['no_midi_capacity_wizard'],16);parts=engine['append']['parts'];expected=bytes.fromhex(next(p['hex'] for p in parts if int(p['dest'],16)==copy));stageBytes=bytes.fromhex(next(p['hex'] for p in parts if int(p['dest'],16)==stage));data=json.loads(pathlib.Path('build/no-midi-capacity-data.js').read_text().split('=',1)[1].strip().rstrip(';'));sy=data['symbols'];init=int.from_bytes(stageBytes[sy['capacity_init']+2:sy['capacity_init']+6],'big');dest=int.from_bytes(stageBytes[sy['capacity_dest']:sy['capacity_dest']+4],'big');assert dest==0x401aa140
 img=main_os_from_syx(str(prefix.with_suffix('.syx')));r=Rig(img,{'writes':[]},{'writes':[],'symbols':{}});u=r.u
 for at,n in [(0x43000000,0x800000),(0x46700000,0x400000),(0x80000000,0x200000),(0x90000000,0x20000)]:u.mem_map(at,n)
 def cache(u,pc,size,data):u.reg_write(mk.UC_M68K_REG_PC,pc+4)
 sites=set()
 for at,raw in [(build.BASE,img)]+[(int(p['dest'],16),bytes.fromhex(p['hex'])) for t in cat if t.get('append') for p in t['append']['parts'] if 'hex' in p]:sites.update(at+i for i in range(0,len(raw)-3,2) if raw[i:i+2]==b'\x4e\x7b')
 for at in sites:u.hook_add(UC_HOOK_CODE,cache,begin=at,end=at)
 calls=[]
 def before_init(u,pc,size,data):assert bytes(u.mem_read(dest,len(expected)))==expected,'Wizard avant init incorrect';calls.append(pc)
 handle=u.hook_add(UC_HOOK_CODE,before_init,begin=init,end=init)
 u.reg_write(mk.UC_M68K_REG_A7,STACK);u.mem_write(STACK,struct.pack('>I',STOP));u.emu_start(0x40000530,0x4000053a,count=200_000_000);assert u.reg_read(mk.UC_M68K_REG_PC)==0x4000053a;assert calls==[init];u.hook_del(handle)
 assert bytes(u.mem_read(dest,len(expected)))==expected;assert bytes(u.mem_read(copy,len(expected)))==expected;assert bytes(u.mem_read(stage,len(stageBytes)))==stageBytes
 r.call(0x4007929c);assert bytes(u.mem_read(dest,len(expected)))==expected;assert bytes(u.mem_read(stage,len(stageBytes)))==stageBytes
 print('PASS vrai boot sans Banque, init moteurs unique ; Wizard exact avant/apres init et constructeur cache',flush=True)
 # Rappeler seulement le stage, avec init originale simulee pour observer l'ABI.
 regs=[getattr(mk,'UC_M68K_REG_D'+str(i)) for i in range(8)]+[getattr(mk,'UC_M68K_REG_A'+str(i)) for i in range(7)];values={reg:0x12340000+4*i for i,reg in enumerate(regs)}
 def abi(args):
  assert all(u.reg_read(reg)==value for reg,value in values.items());assert u.reg_read(mk.UC_M68K_REG_A7)==STACK;return 0
 r.stubs[init]=abi;u.hook_add(UC_HOOK_CODE,r.stub,begin=init,end=init)
 for reg,value in values.items():u.reg_write(reg,value)
 r.call(stage);assert bytes(u.mem_read(dest,len(expected)))==expected
 print('PASS stage : D0-D7/A0-A6 et pile preserves a l entree init originale ; copie exacte',flush=True)
if __name__=='__main__':main()
