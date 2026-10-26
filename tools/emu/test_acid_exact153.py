"""185 : calculs LEGACY/ACID exacts et cout en instructions, sans mesure appareil."""
from pathlib import Path
import sys,json,struct
import numpy as np
R=Path(__file__).resolve().parents[2];W=R/'output/firmware';sys.path[:0]=[str(R/'tools'),str(R/'tools/emu')]
from test_wizard_playback import fixtures
import mcengine as E
from unicorn import m68k_const as C
versions=['v152','v153'];es=fixtures(False,127,0,['staging/all-features-polivoks-cpu-trim-test-'+v for v in versions],audit_count=False);ms=[json.loads((R/'output/firmware/staging'/('all-features-polivoks-cpu-trim-test-'+v+'.json')).read_text()) for v in versions]
for e in es:e.count_instructions();e.uc.reg_write(C.UC_M68K_REG_SR,0x2700)
rows=[]
for case in range(2 if '--quick' in sys.argv else 8):
 for e in es:
  for t in range(6):
   e.call(E.VOICE_RESET,E.VOICE0+t*E.VSTRIDE);e.set(t,machine=13,note=[0,24,48,72,100,127][t],pitch=64,finetune=64,color=[0,64,127][(case+t)%3],shape=[0,64,127][case%3],sweep=[0,64,127][t%3],contour=[0,64,127][case%3],decay=[0,64,127][(case+t)%3],punch=case%2,gate=1);e.uc.mem_write(0x40fe4cdc+2*t,struct.pack('>H',[1,64,97,100,127,127][t]<<8))
 cost=[0,0]
 for b in range(20):
  outs=[];states=[]
  for j,(e,m) in enumerate(zip(es,ms)):
   if b in [3,7,10,16]:
    for t in range(6):e.set(t,**[dict(color=(b*7+t*11)%128),dict(shape=(b*5+t*13)%128),dict(note=(b*3+t*17)%128,finetune=40 if b<12 else 90),dict(contour=(b*9+t*7)%128,sweep=(b*3+t*17)%128)][b%4])
   e.instructions=0;outs.append(e.block(63 if b in [0,8,16] else 0,63 if b==12 else 0));cost[j]+=e.instructions;s=m['fundamentals'];states.append(bytes(e.uc.mem_read(s['bss'],s['end']-s['bss'])))
  assert np.array_equal(*outs),('ACID PCM',case,b,np.max(abs(outs[0]-outs[1])))
  assert states[0]==states[1],('ACID state',case,b)
 row=dict(case=case,instructions=cost,reduction=round(100*(1-cost[1]/cost[0]),3));rows.append(row);print('PASS six ACID tracks exact PCM/state, wave/drive/resonance/live controls/retrigger/release',row,flush=True)
(W/'acid153-profile.json').write_text(json.dumps(dict(rows=rows,hardware_tested=False),indent=2)+'\n')
