"""Prototype Harmonics : cache des12cibles, synthese/arrondis inchanges."""
from pathlib import Path
import sys,json,struct,subprocess,os
import numpy as np
R=Path(__file__).resolve().parents[2];W=R/'output/firmware';sys.path[:0]=[str(R/'tools'),str(R/'tools/emu')]
from test_wizard_playback import fixtures
from unicorn import m68k_const as C
from capstone import Cs,CS_ARCH_M68K,CS_MODE_BIG_ENDIAN,CS_MODE_M68K_040
import mcengine as E
build=W/'private-v149';build.mkdir(exist_ok=True)
meta=json.loads((R/'output/firmware/staging/all-features-polivoks-cpu-trim-test-v149.json').read_text())['macro_cache'];guard=[meta['old_prologue']];sy={'cache_code_end':meta['code_end'],'cache_end':meta['end']}
es=fixtures(False,127,0,['staging/all-features-polivoks-cpu-trim-test-v148'],audit_count=False)+fixtures(False,127,0,['staging/all-features-polivoks-cpu-trim-test-v149'],audit_count=False)
for e in es:e.count_instructions();e.uc.reg_write(C.UC_M68K_REG_SR,0x2700)
rows=[]
for case in range(4):
 for e in es:
  for t in range(6):
   e.call(E.VOICE_RESET,E.VOICE0+t*E.VSTRIDE);e.set(t,machine=12,note=[0,24,48,72,100,127][t],pitch=64,finetune=64,shape=24,color=20+t*20,contour=case*35,sweep=20+t*20,decay=100,punch=t%2,gate=t%2);e.uc.mem_write(0x40fe4cdc+2*t,struct.pack('>H',100<<8))
 costs=[0,0]
 for b in range(24):
  out=[]
  for j,e in enumerate(es):
   if case and b in [3,8,12,18]:
    for t in range(6):e.set(t,**[dict(color=(b*7+t*11)%128),dict(sweep=(b*5+t*13)%128),dict(note=(b*3+t*17)%128)][(b//3)%3])
   if b==16:e.set(2,shape=0)
   if b==20:e.set(2,shape=24)
   e.instructions=0;out.append(e.block(63 if b in [0,12,20] else 0,42 if b==15 else 0));costs[j]+=e.instructions
  assert np.array_equal(*out),(case,b,np.max(abs(out[0]-out[1])))
 row=dict(case=case,instructions=costs,reduction=100*(1-costs[1]/costs[0]));rows.append(row);print('PASS exact six-MACRO Harmonics PCM',row,flush=True)
(build/'profile.json').write_text(json.dumps(dict(rows=rows,guard=guard,code_end=sy['cache_code_end'],bss_end=sy['cache_end']),indent=2)+'\n')
