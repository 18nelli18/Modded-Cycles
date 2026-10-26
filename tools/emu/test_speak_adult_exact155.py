"""188 : preuves natives exactes et cout en instructions, pas de CPU physique."""
from pathlib import Path
import json,sys,struct
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R/'tools'),str(R/'tools/emu')]
from test_wizard_playback import fixtures
from unicorn import m68k_const as C
es=fixtures(False,127,0,['staging/all-features-polivoks-cpu-trim-test-'+v for v in ['v154adult','v155adult']],audit_count=False);ms=[json.loads((R/'output/firmware/staging'/('all-features-polivoks-cpu-trim-test-'+v+'.json')).read_text()) for v in ['v154adult','v155adult']];sizes=[]
for e,m in zip(es,ms):
 e.uc.reg_write(C.UC_M68K_REG_SR,0x2700);e.count_instructions();sizes.append(int.from_bytes(e.uc.mem_read(m['speak']['symbols']['speak_state_bytes'],4),'big'))
assert sizes[0]==sizes[1];state=0x40a71000;inp=0x40a72000;out=0x40a73000;rows=[]
words=json.loads((R/'tools/machines/speak/words-adult-private.json').read_text())
for case in range(128):
 costs=[0,0]
 for e in es:e.uc.mem_write(state,bytes(sizes[0]))
 for b in range(32):
  results=[]
  for j,(e,m) in enumerate(zip(es,ms)):
   data=[([0,24,60,96,127][case%5]<<16)+(b%4)*8192,(case*17+b//8)%128,case,[0,64,127][(case+b//8)%3],(case*31+b//8)%128,case%2,int(b==0)]
   e.uc.mem_write(inp,struct.pack('>7i',*data));e.instructions=0;e.call(m['speak']['symbols']['speak_block'],state,inp,out);costs[j]+=e.instructions
   if b==0:e.uc.mem_write(state+12,struct.pack('>I',1+case%len(words[case]['phones'])));e.uc.mem_write(state+16,bytes(8))
   results.append((bytes(e.uc.mem_read(state,sizes[0])),bytes(e.uc.mem_read(out,128))))
  assert results[0]==results[1],('SPEAK PCM/state',case,b)
 rows.append(dict(word=case,instructions=costs))
 if case%16==15:print('PASS SPEAK exact PCM/full State',case+1,'words',flush=True)
(R/'output/firmware/speak155adult-profile.json').write_text(json.dumps(dict(rows=rows,hardware_cpu_percent=None),indent=2))
print('PASS speech native128words,4096blocks; live pitch/voice/speed/articulation, punch, all interpolation phases',flush=True)
