"""186 : LEGACY exact, Hagedisk original et bornes arithmetiques."""
from pathlib import Path
import sys,json,struct
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R/'tools')];from gen_governor_recovery_test import read
D=R/'output/firmware';a=D/'governor-recovery-v153';b=D/'governor-recovery-v154';old=json.loads((D/'staging/all-features-polivoks-cpu-trim-test-v153.json').read_text());new=json.loads((D/'staging/all-features-polivoks-cpu-trim-test-v154.json').read_text());mapping={}
def collect(x,y):
 if isinstance(x,dict) and isinstance(y,dict):
  for k in x.keys()&y.keys():collect(x[k],y[k])
 elif isinstance(x,list) and isinstance(y,list):
  for xx,yy in zip(x,y):collect(xx,yy)
 elif isinstance(x,int) and isinstance(y,int) and 0x40000400<=x<0x46a00000 and x!=y:mapping.setdefault(x,set()).add(y)
collect(old,new)
import re
for x,y in zip(re.findall(r'jmp (0x[0-9a-f]+)',(a/'mod-overlay-tramp.S').read_text()),re.findall(r'jmp (0x[0-9a-f]+)',(b/'mod-overlay-tramp.S').read_text())):
 if x!=y:mapping.setdefault(int(x,16),set()).add(int(y,16))
def relocate(raw):
 out=bytearray(raw)
 for x,values in mapping.items():
  if len(values)!=1:continue
  needle=struct.pack('>I',x);dest=struct.pack('>I',next(iter(values)));pos=raw.find(needle)
  while pos>=0:out[pos:pos+4]=dest;pos=raw.find(needle,pos+4)
 return bytes(out)
objects=[p.name for p in a.glob('*.o') if (b/p.name).exists() and p.read_bytes()!=(b/p.name).read_bytes()];allowed={'dx7_fm_core.cc.o','dx7_port.cc.o'};assert set(objects)==allowed,objects
assert (a/'mod-overlay-tramp.S.o').read_bytes()==(b/'mod-overlay-tramp.S.o').read_bytes()
for p in a.glob('*.bin'):
 if not (b/p.name).exists() or p.name in ['dx7.bin','fundamentals.bin']:continue
 raw=p.read_bytes();after=(b/p.name).read_bytes();assert (raw==after or relocate(raw)==after),p.name
print('PASS changes restricted to LEGACY routing and pitch; all other compiled audio exact')
assert (a/'dx7_kernels152.S.o').read_bytes()==(b/'dx7_kernels152.S.o').read_bytes()
assert new['legacy']['symbols']['dx7_code_end']<new['wave_starter']['data'] and new['fundamentals']['symbols']['fund_code_end']<new['fundamentals']['bss'];assert new['bank_queue']==old['bank_queue'];assert not new.get('mixer_headroom') and not new.get('macro_cache')
for suffix in ['', 'adult']:
 _,pkg,_,_=read(D/'staging'/('all-features-polivoks-cpu-trim-test-v154'+suffix+'.syx'));_,base,_,_=read(R/'firmware/model-cycles_OS1.13.syx')
 for sec in base['sections']:
  if sec['id']==3:continue
  s=next(s for s in pkg['sections'] if s['id']==sec['id']);assert pkg['blob'][s['off']:s['off']+s['size']]==base['blob'][sec['off']:sec['off']+sec['size']]
 print('PASS bootloader/updater/protected sections exact','v154'+suffix)
for name in ['dx7.bin','fundamentals.bin','fx.bin','punch.bin','du.bin','hall-hot145.bin']:assert (b/name).read_bytes()==(D/'governor-recovery-v154adult'/name).read_bytes(),name
print('PASS memory bounds, confirmed151 bank queue retained, standard/adult DSP exact')
