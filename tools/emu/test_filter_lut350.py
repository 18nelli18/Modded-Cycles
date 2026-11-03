"""Coefficients302 vs LUT : balayage exhaustif cutoff, quatre modes, ABI et cout."""
from pathlib import Path
import argparse,json,struct,sys,random,subprocess,re
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tools/emu')]
from test_seq_gen_menu import Rig
from unicorn import UC_HOOK_CODE,m68k_const as C
from filter_lut350 import apply
p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);p.add_argument('--capture',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.parent.mkdir(parents=True,exist_ok=True)
m=json.loads((a.build/'BUILD.json').read_text());native=(a.capture/'native.bin').read_bytes();old=(a.capture/'runtime.bin').read_bytes();new=bytearray(old);d=apply(m,bytearray(native),new,a.output.parent/'module');base=0x46700000
rigs=[]
for blob in [old,new]:
 r=Rig(native,{'writes':[]},{'writes':[],'symbols':{}});r.u.mem_map(base,0x300000);r.u.mem_write(base,bytes(blob));rigs.append(r)
cases=[]
for name in ['fast_pf_coeff','fast_fc_coeff']:
 cases.extend((name,f%6,f,0,f%4) for f in range(4096))
rng=random.Random(350)
cases.extend(('fast_fc_coeff',i%6,rng.randrange(65536),rng.choice([1,10,43,44,7499,15000,65535]),i%4) for i in range(512))
rows=[];regs=[getattr(C,'UC_M68K_REG_'+name) for name in ['D2','D3','D4','D5','D6','D7','A2','A3','A4','A5','A6']]
for index,(name,lane,f,q,mode) in enumerate(cases):
 values=[];counts=[];seed=[rng.getrandbits(32) for _ in regs]
 for k,r in enumerate(rigs):
  r.w32(0x401bbd60+4*lane,f);r.w32(0x401bbd7c+4*lane,q);r.w32(m['filter_modes']['symbols']['fc_type']+4*lane,mode)
  for reg,v in zip(regs,seed):r.u.reg_write(reg,v)
  count=[0];h=r.u.hook_add(UC_HOOK_CODE,lambda *unused:count.__setitem__(0,count[0]+1)) if index%64==0 else None
  ptr=r.call((m['filter_single_div'] if k==0 else d)['symbols'][name],lane)
  if h:r.u.hook_del(h)
  values.append(bytes(r.u.mem_read(ptr,20 if name=='fast_pf_coeff' else 24)));counts.append(count[0])
  assert [r.u.reg_read(reg) for reg in regs]==seed
 assert values[0]==values[1],(index,name,lane,f,q,mode,[x.hex() for x in values])
 if index%64==0:rows.append(dict(name=name,q=q,f=f,mode=mode,before=counts[0],after=counts[1],saved=counts[0]-counts[1]))
assert max(x['saved'] for x in rows if x['q']==0)>0
a.output.write_text(json.dumps(dict(cases=len(cases),coefficients_bit_exact=True,all_cutoff_values=True,all_filter_modes=True,register_ABI_preserved=True,instruction_samples=rows,hardware_cycles=False),indent=2)+'\n')
print('PASS',len(cases),'exact coefficients and ABI; sample instruction savings',max(x['saved'] for x in rows),flush=True)
