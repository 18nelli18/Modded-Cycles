from pathlib import Path
import sys,json,struct
R=Path(__file__).resolve().parents[2];W=R/'output/firmware';sys.path[:0]=[str(R/'tools'),str(R/'tools/emu')]
from test_wizard_playback import fixtures
import emac
from unicorn import m68k_const as C
versions=['v151','v152'];es=fixtures(False,127,0,['staging/all-features-polivoks-cpu-trim-test-'+v for v in versions],audit_count=False);ms=[]
for v,e in zip(versions,es):
 m=json.loads((R/'output/firmware/staging'/('all-features-polivoks-cpu-trim-test-'+v+'.json')).read_text());ms.append(m);d=m['legacy'];f=R/('output/firmware/governor-recovery-'+v+'/dx7.bin');e.emac.install(emac.disasm(str(f),d['code'],d['code'],d['code']+d['code_bytes']));e.count_instructions();e.emac.macsr=0xa0
 for i in range(4):e.emac.put_physical(i,0x123456789abc+i)
 e.uc.reg_write(C.UC_M68K_REG_SR,0x2700)

import random
rng=random.Random(152);names=['_ZN10FmOpKernel7computeEPlPKlllllb','_ZN10FmOpKernel12compute_pureEPlllllb','_ZN10FmOpKernel10compute_fbEPlllllS0_ib'];cost=[0,0]
regs=[getattr(C,'UC_M68K_REG_'+n) for n in ['D2','D3','D4','D5','D6','D7','A2','A3','A4','A5','A6']]
for kind,name in enumerate(names):
 for add in [0,1]:
  for case in range(32):
   phase=rng.getrandbits(32);freq=rng.getrandbits(32);g1=rng.randrange(1<<27);g2=rng.randrange(1<<27);inp=[rng.randrange(-(1<<30),1<<30) for i in range(32)];out=[rng.randrange(-(1<<29),1<<29) for i in range(32)];fb=[rng.randrange(-(1<<27),1<<27) for i in range(2)];shift=case%15+1;results=[]
   for j,(e,m) in enumerate(zip(es,ms)):
    e.uc.mem_write(0x40a70000,b'GUAR'+struct.pack('>32i',*out)+b'GUAR');e.uc.mem_write(0x40a70100,struct.pack('>32i',*inp));e.uc.mem_write(0x40a70200,struct.pack('>2i',*fb));e.emac.macsr=0x20
    for k in range(4):e.emac.put_physical(k,0 if k==0 else 0x123456789abc+k)
    for k,reg in enumerate(regs):e.uc.reg_write(reg,0x12700000+k)
    args=([0x40a70004,0x40a70100,phase,freq,g1,g2,add] if kind==0 else [0x40a70004,phase,freq,g1,g2,add] if kind==1 else [0x40a70004,phase,freq,g1,g2,0x40a70200,shift,add]);e.instructions=0;e.call(m['legacy']['symbols'][name],*args);cost[j]+=e.instructions
    results.append((bytes(e.uc.mem_read(0x40a70000,136)),bytes(e.uc.mem_read(0x40a70200,8))))
    assert results[-1][0][:4]==results[-1][0][-4:]==b'GUAR'
    assert all(e.uc.reg_read(reg)==0x12700000+k for k,reg in enumerate(regs))
    assert e.emac.macsr==0x20 and e.emac.physical(0)==0 and all(e.emac.physical(k)==0x123456789abc+k for k in range(1,4))
   assert results[0]==results[1],(kind,add,case)
  print('PASS native LEGACY kernel exact random PCM/feedback/canaries/ABI/EMAC',kind,add,flush=True)
print('PASS192 native operator cases; instructions',cost,'reduction',100*(1-cost[1]/cost[0]),flush=True)
