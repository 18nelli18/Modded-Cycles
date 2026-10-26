"""186 : LEGACY exact, Hagedisk original et bornes arithmetiques."""
from pathlib import Path
import sys,json,struct,random
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R/'tools'),str(R/'tools/emu')]
from test_wizard_playback import fixtures
from unicorn import m68k_const as C
es=fixtures(False,127,0,['staging/all-features-polivoks-cpu-trim-test-'+v for v in ['v153','v154']],audit_count=False);ms=[json.loads((R/'output/firmware/staging'/('all-features-polivoks-cpu-trim-test-'+v+'.json')).read_text()) for v in ['v153','v154']];rng=random.Random(154);core=0x40a74000;out=0x40a74200;params=0x40a74300;fb=0x40a74400
for case in range(128):
 state=rng.randbytes(288);pcm=rng.randbytes(128);feedback=rng.randbytes(8);ops=[]
 for k in range(6):
  active=bool(case&(1<<k));level=(rng.randrange(10<<24,17<<24) if active else 0);gain=rng.choice([0,1119,1120,1121,1<<24]) if active else (1119 if case<64 else 0);ops.extend([level,gain,rng.randrange(1<<24),rng.randrange(1<<32)])
 raw=struct.pack('>24I',*ops);outputs=[]
 for e,m in zip(es,ms):
  e.uc.reg_write(C.UC_M68K_REG_SR,0x2700);e.emac.macsr=0x20
  for k in range(4):e.emac.put_physical(k,0 if k==0 else 0x123456789abc+k)
  for a,b in [(core,state),(out,pcm),(params,raw),(fb,feedback)]:e.uc.mem_write(a,b)
  e.call(m['legacy']['symbols']['_ZN6FmCore6renderEPlP10FmOpParamsiS0_i'],core,out,params,11,fb,case%17)
  outputs.append(tuple(bytes(e.uc.mem_read(a,n)) for a,n in [(core,288),(out,128),(params,96),(fb,8)]))
  assert e.emac.macsr==0x20 and all(e.emac.physical(k)==(0 if k==0 else 0x123456789abc+k) for k in range(4))
 assert outputs[0]==outputs[1],case
print('PASS 128 native algorithm12 cases: all64 inactive-operator masks, gain threshold1119/1120/1121, feedback0..16, exact PCM/core/params/feedback/EMAC',flush=True)
