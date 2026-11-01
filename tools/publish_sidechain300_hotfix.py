"""Publication du correctif Sidechain en conservant la version3.00."""
from pathlib import Path
import argparse,json,hashlib,re
R=Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0,str(R/'tools'))
from gen_governor_recovery_test import read
from sparse_loader_relocations import collect
p=argparse.ArgumentParser();p.add_argument('--assets-only',action='store_true');p.add_argument('--asset-commit');a=p.parse_args()
W=R.parent/'sidechain-manual300-hotfix';site=R/'docs/flasher';opt=R/'docs/flasher-optional'
sha=lambda v:hashlib.sha256(v).hexdigest()
def jr(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def put(p,s):p.write_text(s,encoding='utf-8',newline='\n')
def jw(p,d):put(p,json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def jsr(p):s=p.read_text(encoding='utf-8');return json.loads(s[s.index('=')+1:].strip().rstrip(';'))
def jsw(p,n,d):put(p,'window.'+n+'='+json.dumps(d,ensure_ascii=False,separators=(',',':'))+';\n')
main=jr(site/'BUILD.json');optional=jr(opt/'BUILD.json');entries={};metadata={}
for scope,ed in [('main','full'),('main','lite'),('optional','full'),('optional','lite')]:
 d=W/scope/ed;m=jr(d/'BUILD.json');raw=next(d.glob('*.syx')).read_bytes();assert sha(raw)==m['sha256'];assert m['release']==m['title_screen']['version']=='3.00'
 e=dict((main['editions'] if scope=='main' else optional['base_editions'])[ed]);name='Supermodel_'+('Optional_' if scope=='optional' else '')+ed.title()+'_3.00_'+sha(raw)[:12]+'.syx';(site/name).write_bytes(raw)
 e.update(file=name,syxSha256=sha(raw),mainOsSha=m['main_os_sha256'],startup_title=m['title_screen'],sidechain_muted_live=True,sidechain_muted_live_hardware_confirmed=scope=='optional' and ed=='full')
 entries[(scope,ed)]=e;metadata[(scope,ed)]=m
if a.assets_only:
 jw(site/'release300-assets.json',dict(release='3.00',sidechain_muted_live=True,editions={s:{e:entries[(s,e)] for e in ['full','lite']} for s in ['main','optional']}));print('Prepared four version3.00 hotfix assets');sys.exit(0)
assert a.asset_commit and re.fullmatch('[0-9a-f]{40}',a.asset_commit)
oldcommit=main['asset_source_commit'];stamps={main['stamp']:'2026-11-01-main300-sc1',optional['stamp']:'2026-11-01-optional300-sc1','2026-11-01-guide300':'2026-11-01-guide300-sc1'}
for root in (site,opt):
 for f in root.iterdir():
  if f.name=='tweaks.js' or f.suffix not in ('.js','.html','.md'):continue
  before=f.read_text(encoding='utf-8');s=before.replace(oldcommit,a.asset_commit)
  for old,new in stamps.items():s=s.replace(old,new)
  if s!=before:put(f,s)
for m in (main,optional):
 m.update(asset_source_commit=a.asset_commit,delivery_source_commit=a.asset_commit,sidechain_muted_live=True,sidechain_muted_live_hardware_confirmation='User confirmed on Machine Optional Model:Cycles, 2026-11-01',guide_version=stamps['2026-11-01-guide300']);m['stamp']=stamps[m['stamp']]
main['editions']={e:entries[('main',e)] for e in ('full','lite')};optional['base_editions']={e:entries[('optional',e)] for e in ('full','lite')}
f=main['editions']['full'];main.update(fixed_image=f['file'],fixed_image_legacy=f['file'],approved_source=f['file'],fixed_image_sha256=f['syxSha256'],approved_source_sha256=f['syxSha256'],main_os_sha256=f['mainOsSha'])
loader=site/'fixed-main-image.js';s=loader.read_text(encoding='utf-8');start=s.index('const catalogue=')+len('const catalogue=');end=s.index(';',start);put(loader,s[:start]+json.dumps(main['editions'],ensure_ascii=False,indent=2)+s[end:])
jsw(opt/'editions.js','MCOptionalBaseEditions',optional['base_editions'])
recipe=jr(W/'selection/manifest.json');assert recipe['source_release']=='3.00';jsw(opt/'recipe.js','MCOptionalRecipe',recipe);optional['recipe_sha256']=sha((opt/'recipe.js').read_bytes())
md=jsr(opt/'machinedrum-data.js');md.update(source_sha256=entries[('optional','full')]['syxSha256'],title=metadata[('optional','full')]['title_screen'],release='3.00',title_edits=[]);md['base_loader_relocations']=collect(read(site/entries[('optional','full')]['file'])[2],metadata[('optional','full')]);jsw(opt/'machinedrum-data.js','MCOptionalMDData',md)
change={'en':'Sidechain Mute On blocks muted sequencer triggers while manual pad and trig-key hits still drive the complete ducking envelope. Confirmed on Model:Cycles Machine Optional.','fr':'Sidechain Mute On bloque les trigs de sequence mutes ; les pads et touches TRIG joues manuellement declenchent toute l enveloppe. Confirme sur Model:Cycles Machine Optional.'}
for f in (R/'docs/assets/release.js',site/'midi-machine-release.js',opt/'release.js'):
 h=jsr(f);current=next(v for v in h if v['version']=='3.00');current['changes'].insert(0,change);jsw(f,'MC_RELEASES',h)
f=site/'release-notes-3.00.html';s=f.read_text(encoding='utf-8');s=s.replace('<h1>Supermodel3.00</h1>','<h1>Supermodel3.00</h1><p>'+change['en']+'</p><p lang="fr">'+change['fr']+'</p>');put(f,s)
p=R/'docs/index.html';text=p.read_text(encoding='utf-8');text=re.sub(r'((?:flasher/midi-machine-release|assets/site)\.js\?v=)[^\"\s]+',r'\g<1>2026-11-01-main300-sc1',text);put(p,text)
jw(site/'BUILD.json',main);jw(opt/'BUILD.json',optional)
validation=dict(release='3.00',version_unchanged=True,sidechain_muted_live=True,user_hardware_confirmed_optional_full=True,variants=[])
for scope,ed in entries:
 proof=jr(W/scope/ed/'proof.json');validation['variants'].append(dict(scope=scope,edition=ed,sha256=entries[(scope,ed)]['syxSha256'],proof=proof))
jw(site/'sidechain300-validation.json',validation);jw(opt/'sidechain300-validation.json',validation)
print('Prepared metadata, Optional recipes, hashes and caches; all versions3.00')
