"""143 : PCM exact sous changements live ; charge mixte native avec HALL et delay."""
from pathlib import Path
import sys,json,struct
import numpy as np
R=Path(__file__).resolve().parents[2];W=R/'output/firmware'
sys.path[:0]=[str(R/'tools'),str(R/'tools/emu')]
from test_fx_menu_audio import fixture
from test_fx_combo_cpu import prep
from test_delay_crush_sends import run
import mcengine as E
from unicorn import m68k_const as C
v=sys.argv[1] if len(sys.argv)>1 else 'v144'
old='staging/all-features-polivoks-cpu-trim-test-v143'
new='staging/all-features-polivoks-cpu-trim-test-'+v
fs=[fixture(s,0) for s in (old,new)]
def init(f,models):
 e,m,sy,g=f;e.uc.reg_write(C.UC_M68K_REG_SR,0x2700)
 for t,(machine,model) in enumerate(models):
  e.call(E.VOICE_RESET,E.VOICE0+t*E.VSTRIDE)
  e.set(t,machine=machine,shape=model,note=36+6*t,pitch=64,finetune=64,color=60,contour=40,sweep=68,decay=100,punch=0,gate=0)
  e.uc.mem_write(0x40fe4cdc+2*t,struct.pack('>H',100<<8))
for model in ([] if '--mixed-only' in sys.argv else range(12)):
 for f in fs:init(f,[(23,model)]*6)
 for b in range(12):
  for f in fs:
   for t in range(6):
    # Chaque controle utile change seul, puis reste stable pour exercer le cache.
    changes=[{},dict(color=17+t*17),dict(contour=11+t*19),dict(decay=20+t*20),dict(sweep=25.5+t*15),dict(punch=1),dict(note=43+t*7),dict(gate=1),dict(shape=(model+1)%12),{},dict(finetune=65),{}][b]
    f[0].set(t,**changes)
  out=[f[0].block(63 if b in (0,8) else 0,63 if b==9 else 0) for f in fs]
  assert np.array_equal(*out),(model,b)
 print('PASS delivered firmware PCM exact: live controls, fine ratio, retrigger, model change, gate/release',model,flush=True)

for model in (0,9,11):
 for f in fs:
  init(f,[(23,model)]*6)
  for t in range(6):f[0].set(t,note=[0,24,48,72,100,127][t],decay=[0,1,30,64,100,127][t],color=[0,1,32,64,100,127][t],contour=[0,127,0,127,64,64][t],punch=t%2,gate=t%2)
 for b in range(16):
  out=[f[0].block(63 if b in (0,10) else 0,63 if b==7 else 0) for f in fs]
  assert np.array_equal(*out),('extremes',model,b)
 print('PASS exact extremes: note0..127, Decay0..127, feedback and gate/release',model,flush=True)

rows=[]
for f in fs:f[0].count_instructions()
for macro in (None,0,20):
 models=[(20,0),(23,0),(23,9),(23,11),(13,64),(0,16)]
 if macro is not None:models[4]=(12,macro)
 for f in fs:
  prep(f,11,0,90,64,False);init(f,models)
  d=f[1]['sidechain']['symbols'];f[0].uc.mem_write(d['du_config'],bytes([30,10,0,0,6]+[0,9,0,0,6]*5));f[0].call(d['du_reset'])
 costs=[[],[]]
 for b in range(12):
  outs=[]
  for j,f in enumerate(fs):
   e,m,sy,g=f
   e.instructions=0;voice=e.block(63 if b in (0,8) else 0)
   d=m['sidechain']['symbols'];e.call(d['du_voice_triggers'],1 if b in (0,8) else 0)
   result=run(f,1);costs[j].append(e.instructions);outs.append((voice,result))
  assert np.array_equal(outs[0][0],outs[1][0]),('mixed voice',macro,b)
  for key in ('post','wet','rev_wet','send'):assert outs[0][1][key]==outs[1][1][key],('mixed FX',macro,b,key)
 row=dict(macro_model=macro,before=sum(costs[0]),after=sum(costs[1]),reduction_percent=round(100*(1-sum(costs[1])/sum(costs[0])),2),worst_before=max(costs[0]),worst_after=max(costs[1]),block_counts=costs,delay='native ping pong fixture',reverb='HALL',sidechain=True)
 rows.append(row);print('PASS six-track native voice+mixer PCM exact and instruction cost',row,flush=True)
out=W/'private-v144';out.mkdir(exist_ok=True)
(out/('performance-'+v+'.json')).write_text(json.dumps(dict(rows=rows,hardware_cpu_percent=None,hardware_tested=False),indent=2)+'\n')
