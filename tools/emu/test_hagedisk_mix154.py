"""186 : LEGACY exact, Hagedisk original et bornes arithmetiques."""
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
v=sys.argv[1] if len(sys.argv)>1 else 'v154'
old='staging/all-features-polivoks-cpu-trim-test-v153'
new='staging/all-features-polivoks-cpu-trim-test-'+v
fs=[fixture(s,0) for s in (old,new)]
import emac
for f,stem in zip(fs,(old,new)):
 m=f[1];d=m['legacy'];raw=R/('output/firmware/governor-recovery-'+stem.rsplit('-test-',1)[-1]+'/dx7.bin');f[0].emac.install(emac.disasm(str(raw),d['code'],d['code'],d['code']+d['code_bytes']))
def init(f,models):
 e,m,sy,g=f;e.uc.reg_write(C.UC_M68K_REG_SR,0x2700)
 for t,(machine,model) in enumerate(models):
  e.call(E.VOICE_RESET,E.VOICE0+t*E.VSTRIDE)
  e.set(t,machine=machine,shape=model,note=36+6*t,pitch=64,finetune=64,color=60,contour=40,sweep=68,decay=100,punch=0,gate=0)
  e.uc.mem_write(0x40fe4cdc+2*t,struct.pack('>H',100<<8))
rows=[]
for f in fs:f[0].count_instructions()
for macro in (None,8):
 models=[(20,0),(12,36),(23,0),(23,9),(0,16),(13,64)]
 if macro is not None:models[1]=(21,8);models[0]=(17,0)
 for f in fs:
  prep(f,11,0,90,64,False);init(f,models)
  from dx7_assets import unpack
  original=Path('C:/Users/austi/OneDrive/Desktop/Muzak/Legowelt magic DX7 cart.syx').read_bytes();ls=f[1]['legacy']['symbols'];voices=b''.join(bytes(unpack(original[6+128*k:6+128*(k+1)])) for k in range(32));f[0].uc.mem_write(ls['banks'],voices);f[0].uc.mem_write(ls['bank_ready'],bytes([1]));f[0].uc.mem_write(ls['bank_active'],bytes([0]));f[0].set(1,machine=21,shape=8)
  for _ in range(2):f[0].block(0)
  d=f[1]['sidechain']['symbols'];f[0].uc.mem_write(d['du_config'],bytes([30,10,0,0,6]+[0,9,0,0,6]*5));f[0].call(d['du_reset'])
 costs=[[],[]]
 for b in range(32):
  outs=[]
  for j,f in enumerate(fs):
   e,m,sy,g=f
   e.instructions=0;voice=e.block((62 if macro is not None else 63) if b%8==0 else 0)
   d=m['sidechain']['symbols'];e.call(d['du_voice_triggers'],1 if b%8==0 else 0)
   result=run(f,1);costs[j].append(e.instructions);outs.append((voice,result))
  assert np.array_equal(outs[0][0],outs[1][0]),('mixed voice',macro,b)
  for key in ('post','wet','rev_wet','send'):assert outs[0][1][key]==outs[1][1][key],('mixed FX',macro,b,key)
 row=dict(macro_model=macro,before=sum(costs[0]),after=sum(costs[1]),reduction_percent=round(100*(1-sum(costs[1])/sum(costs[0])),2),worst_before=max(costs[0]),worst_after=max(costs[1]),block_counts=costs,delay='native ping pong fixture',reverb='HALL',sidechain=True)
 rows.append(row);print('PASS six-track native voice+mixer PCM exact and instruction cost',row,flush=True)
out=W/'private-v154';out.mkdir(exist_ok=True)
(out/('performance-'+v+'.json')).write_text(json.dumps(dict(rows=rows,hardware_cpu_percent=None,hardware_tested=False),indent=2)+'\n')
