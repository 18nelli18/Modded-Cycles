"""Isolement v55 face a v54 : runtime, objets DSP et sections de recuperation."""
import sys,json,hashlib
from test_junior_integration import parts,ROOT
from gen_governor_recovery_test import TAIL,BASE
from test_private_container_loader import check
for stem in sys.argv[1:]:
 oldstem=stem.replace('v55','v54');a,b=parts(oldstem),parts(stem);m=json.loads((ROOT/'output/firmware'/(stem+'.json')).read_text());old=json.loads((ROOT/'output/firmware'/(oldstem+'.json')).read_text())
 assert a[2]==b[2],'voice/filter/runtime changed'
 for sec in a[0]['sections']:
  if sec['id']==3:continue
  other=next(x for x in b[0]['sections'] if x['id']==sec['id']);assert a[0]['blob'][sec['off']:sec['off']+sec['size']]==b[0]['blob'][other['off']:other['off']+other['size']]
 build=ROOT/('output/firmware/governor-recovery-'+stem.rsplit('-',1)[-1]);prior=ROOT/('output/firmware/governor-recovery-'+oldstem.rsplit('-',1)[-1])
 for name in ('module.bin','feral-code.bin','junior.bin','chorus.bin','crush.bin'):
  assert (build/name).read_bytes()==(prior/name).read_bytes(),name
 allowed=set();f=m['fx_menu']['symbols']
 for at,n in [(old['repeat_latch']['code'],old['repeat_latch']['end']-old['repeat_latch']['code']), (m['recovery_symbols']['gr_beat_key'],8),(m['beat_repeat_symbols']['br_key_hook'],8),(m['beat_repeat_symbols']['br_key'],8),(m['beat_repeat_symbols']['br_old_track_keys'],4)]:allowed.update(range(at-TAIL,at-TAIL+n))
 # Relais draw unique passe de cr_draw a fx_draw.
 for p in m['recovery_patches']:
  if p['storage']=='tail' and p['new']=='4ef9'+f['fx_draw'].to_bytes(4,'big').hex():allowed.update(range(int(p['at'],16)-TAIL,int(p['at'],16)-TAIL+6))
 assert {i for i,(x,y) in enumerate(zip(a[3],b[3])) if x!=y}<=allowed,'unexpected existing payload writes'
 assert m['fx_menu']['code']==0x46800000 and m['fx_menu']['end']<0x46810000
 result=check(stem);print('PASS v54 DSP objects/voice runtime exact; existing payload changes limited to declared UI hooks; bootloader/updater exact',stem,flush=True)
