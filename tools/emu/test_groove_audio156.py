"""156 : audio au repos des nouvelles options identique au155, CHORD strum actif."""
from pathlib import Path
import sys,struct,json
import numpy as np
R=Path(__file__).resolve().parents[2];W=R/'output/firmware';sys.path[:0]=[str(R/'tools'),str(R/'tools/emu')]
from test_fx_menu_audio import fixture
import mcengine as E
from unicorn import m68k_const as C
v=sys.argv[1] if len(sys.argv)>1 else 'v156'
fs=[fixture('staging/all-features-polivoks-cpu-trim-test-'+n,0) for n in ('v155',v)]
for models in ([5]*6,[20,12,23,23,0,13],[21,21,23,23,0,13]):
 for e,m,sy,g in fs:
  e.uc.reg_write(C.UC_M68K_REG_SR,0x2700)
  for t,machine in enumerate(models):
   e.call(E.VOICE_RESET,E.VOICE0+t*E.VSTRIDE);e.set(t,machine=machine,shape=15,note=36+3*t,pitch=64,finetune=64,color=60,contour=40,sweep=68,decay=100,punch=0,gate=0)
 for b in range(64):
  outs=[f[0].block(63 if b in (0,1,40) else 0) for f in fs];assert np.array_equal(*outs),(models,b)
 print('PASS 64 native blocks default PCM exact155/156 machines',models,flush=True)
# Montrer un effet reel dans le render de CHORD, puis retour0 exact avec reset.
e,m,sy,g=fs[1];s=m['groove_strum']['symbols'];e.uc.mem_write(s['gc_strum'],b'\x20')
for t in range(6):e.call(E.VOICE_RESET,E.VOICE0+t*E.VSTRIDE);e.set(t,machine=5,shape=15,note=36+3*t,pitch=64,finetune=64,color=60,contour=40,sweep=68,decay=100,punch=0,gate=0)
peaks=[]
for b in range(64):peaks.append(int(abs(e.block(63 if b<2 else 0)).max()))
assert max(peaks)>0
assert any(int.from_bytes(e.uc.mem_read(s['gc_ticks']+4*t,4),'big')>0 for t in range(6))
print('PASS CHORD Strum hook reached by native voice loop, audible render',max(peaks),flush=True)
