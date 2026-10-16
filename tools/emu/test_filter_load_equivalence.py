"""Note 105 : deux vrais corps ColdFire, samples/etats identiques et instructions.
Le compteur n'est pas une mesure de cycles ou de charge materielle.
"""
import argparse,json,pathlib,random,struct,sys
from unicorn import UC_HOOK_CODE
HERE=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from test_seq_gen_menu import Rig
from test_sdvintage import main_os_from_syx
import emac
ROOT=HERE.parents[1]
def data(path):return json.loads(pathlib.Path(path).read_text().split('=',1)[1].strip().rstrip(';'))
def main():
 p=argparse.ArgumentParser();p.add_argument('--cases',type=int,default=256);a=p.parse_args();stock=main_os_from_syx('firmware/model-cycles_OS1.13.syx');base=data('docs/flasher/filter-precision-data.js');new=data('build/filter-load-data.js');ws=json.loads((ROOT/'firmware/wizard-catalogue.json').read_text())['variants']['0']['wizard']['symbols'];ws={k:int(v,16) for k,v in ws.items()};rigs=[]
 for n,d in enumerate([base,new]):
  r=Rig(stock,{'writes':[]},{'writes':[],'symbols':{}});r.u.mem_write(d['at'],bytes.fromhex(d['hex']));path=ROOT/f'build/filter-load-{n}.bin';path.write_bytes(bytes.fromhex(d['hex']));r.emac=emac.EMAC(r.u);r.emac.install(emac.disasm(str(path),d['at'],d['at'],d['at']+d['code_size']));r.instructions=0
  def count(u,pc,size,user,r=r):r.instructions+=1
  r.u.hook_add(UC_HOOK_CODE,count,begin=d['at'],end=d['at']+d['code_size']);rigs.append(r)
 rng=random.Random(105);totals={0:[0,0],1:[0,0]};buf=0x93070000;limit=1<<27
 for case in range(a.cases):
  q=0 if case%2==0 else rng.randrange(1,8192);f=[1,4095,2048,rng.randrange(1,4096)][case%4];mk=rng.randrange(4096,8192);lane=case%6
  state=[rng.choice([-limit,limit,rng.randrange(-limit,limit+1)]) for _ in range(4)]
  samples=[rng.choice([-0x80000000,0x7fffffff,0,rng.randrange(-0x80000000,0x80000000)]) for _ in range(32)]
  outputs=[]
  for index,r in enumerate(rigs):
   r.emac.macsr=0xa0;r.emac.acc[:]=[0,111,222,333]
   for name,v in [('gflt_f',f),('gflt_q',q),('gflt_mk',mk)]:r.w32(ws[name]+4*lane,v)
   for pole,v in enumerate(state):r.w32(ws['gflt_y1']+28*pole+4*lane,v)
   r.u.mem_write(buf,struct.pack('>32i',*samples));r.instructions=0;r.call(base['at'],buf,lane);totals[bool(q)][index]+=r.instructions
   outputs.append((bytes(r.u.mem_read(buf,128)),tuple(r.r32(ws['gflt_y1']+28*pole+4*lane) for pole in range(4))))
   assert r.emac.macsr==0xa0 and r.emac.acc==[0,111,222,333]
  assert outputs[0]==outputs[1],(case,f,q,mk,lane)
 print('PASS',a.cases,'blocs de 32 samples : entiers extremes/aleatoires, six pistes, resonance et etats limites ; samples/etats bit exacts')
 for q,counts in totals.items():
  saving=100*(counts[0]-counts[1])/counts[0];assert saving>10;print('MESURE instructions resonance',q,counts,'reduction',round(saving,1),'%')
if __name__=='__main__':main()
