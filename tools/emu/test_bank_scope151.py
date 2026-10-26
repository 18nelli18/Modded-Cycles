from pathlib import Path
import sys,json
R=Path(__file__).resolve().parents[2];W=R/'output/firmware';sys.path[:0]=[str(R/'tools')]
from gen_governor_recovery_test import read
D=R/'output/firmware';base=D/'governor-recovery-v148'
for v in ['v151']:
 b=D/('governor-recovery-'+v);m=json.loads((D/'staging'/('all-features-polivoks-cpu-trim-test-'+v+'.json')).read_text())
 changed=[]
 for f in base.glob('*.bin'):
  if (b/f.name).read_bytes()!=f.read_bytes():changed.append(f.name)
 print(v,'changed compiled modules',changed)
 assert set(changed)<=({'mod-overlay.bin'} if v=='v149' else {'fx.bin','dx7.bin','fundamentals.bin'}),changed
 if v=='v151':
  import struct
  oldmeta=json.loads((D/'staging/all-features-polivoks-cpu-trim-test-v148.json').read_text())
  so=oldmeta['legacy']['symbols'];sn=m['legacy']['symbols']
  for name in ['fx.bin','fundamentals.bin']:
   raw=(base/name).read_bytes();expected=bytearray(raw)
   for key,at in so.items():
    if key not in sn or sn[key]==at:continue
    needle=struct.pack('>I',at);pos=raw.find(needle)
    while pos>=0:
     expected[pos:pos+4]=struct.pack('>I',sn[key]);pos=raw.find(needle,pos+4)
   assert bytes(expected)==(b/name).read_bytes(),name
  objects=[p.name for p in base.glob('*.o') if (b/p.name).exists() and p.read_bytes()!=(b/p.name).read_bytes()]
  assert set(objects)=={'dx7_bank.c.o','dx7_library.c.o'},objects
 assert not m.get('mixer_headroom') and m['fx_menu']['dub_stereo']
 if v=='v151':
  s=m['legacy']['symbols'];assert s['dx7_code_end']<m['wave_starter']['data']<m['wave_starter']['end']<0x46888000<0x46890000<s['dx7_end']<m['mod_overlay']['code'];assert m['audio_headroom']['hall']['end']<0x468a8000<s['dx7_chunks_end']<0x468ae000
 else:assert m['macro_cache']['cache_bytes']==408
 for adult in ['', 'adult']:
  f=D/'staging'/('all-features-polivoks-cpu-trim-test-'+v+adult+'.syx');_,p,_,_=read(f)
  _,orig,_,_=read(R/'firmware/model-cycles_OS1.13.syx')
  for sec in orig['sections']:
   if sec['id']==3:continue
   x=next(z for z in p['sections'] if z['id']==sec['id']);assert p['blob'][x['off']:x['off']+x['size']]==orig['blob'][sec['off']:sec['off']+sec['size']]
  print('PASS protected native sections unchanged',v+adult)
print('PASS v151 bank-only source changes, relocated callback addresses only, protected sections and global memory bounds')
