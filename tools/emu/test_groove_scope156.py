"""156/157 : portee, absence de recouvrement, audio et sections protegees."""
from pathlib import Path
import sys,json
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R/'tools')];from gen_governor_recovery_test import read
D=R/'output/firmware';old=D/'governor-recovery-v155';base=json.loads((D/'staging/all-features-polivoks-cpu-trim-test-v155.json').read_text())
_,stock,_,_=read(R/'firmware/model-cycles_OS1.13.syx')
for v in ('v156','v156adult','v157','v157adult'):
 new=D/('governor-recovery-'+v);meta=json.loads((D/('staging/all-features-polivoks-cpu-trim-test-'+v+'.json')).read_text());s=meta['groove_strum']['symbols'];baseline=D/('governor-recovery-v155adult' if v.endswith('adult') else 'governor-recovery-v155')
 changes=[p.name for p in baseline.glob('*.o') if (new/p.name).exists() and p.read_bytes()!=(new/p.name).read_bytes()];assert changes==[],(v,changes)
 for p in baseline.glob('*.bin'):
  if (new/p.name).exists():assert p.read_bytes()==(new/p.name).read_bytes(),(v,p.name)
 assert meta['bank_queue']==base['bank_queue']
 assert meta['private_retrosyn']['symbols']['retrosyn_code_end']<=0x468b2000<s['gc_code_end']<0x468ba000<=s['gc_amounts']<s['gc_end']<0x468bb000
 assert not meta['groove_strum']['pattern_header_bytes']
 _,pkg,_,_=read(D/('staging/all-features-polivoks-cpu-trim-test-'+v+'.syx'))
 for sec in stock['sections']:
  if sec['id']==3:continue
  x=next(x for x in pkg['sections'] if x['id']==sec['id']);assert pkg['blob'][x['off']:x['off']+x['size']]==stock['blob'][sec['off']:sec['off']+sec['size']]
 print('PASS',v,'all existing compiled audio/objects exact155, protected sections, bounds, bank151 and Chord Keys header retained',flush=True)
