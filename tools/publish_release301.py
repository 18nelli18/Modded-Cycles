"""Publie les quatre images lean validees, puis leurs catalogues epingles."""
from pathlib import Path
import argparse, hashlib, json, re

R=Path(__file__).resolve().parents[1]
W=R.parent/'release301'
p=argparse.ArgumentParser();p.add_argument('--assets-only',action='store_true');p.add_argument('--asset-commit');a=p.parse_args()
sha=lambda b:hashlib.sha256(b).hexdigest()
def jr(p):return json.loads(p.read_text(encoding='utf-8'))
def put(p,s):p.write_text(s,encoding='utf-8',newline='\n')
def jw(p,d):put(p,json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def jsr(p):return json.loads(p.read_text(encoding='utf-8').split('=',1)[1].strip().rstrip(';'))
def jsw(p,n,d):put(p,'window.'+n+'='+json.dumps(d,ensure_ascii=False,separators=(',',':'))+';\n')
site=R/'docs/flasher';opt=R/'docs/flasher-optional'
main=jr(site/'BUILD.json');optional=jr(opt/'BUILD.json');entries={}
for scope,ed in [('main','full'),('main','lite'),('optional','full'),('optional','lite')]:
 folder=W/'final'/scope/ed;m=jr(folder/'BUILD.json');raw=next(folder.glob('*.syx')).read_bytes()
 assert sha(raw)==m['sha256'] and m['release']==m['title_screen']['version']=='3.01'
 e=dict((main['editions'] if scope=='main' else optional['base_editions'])[ed])
 name='Supermodel_'+('Optional_' if scope=='optional' else '')+ed.title()+'_3.01_'+sha(raw)[:12]+'.syx'
 (site/name).write_bytes(raw)
 e.update(file=name,release='3.01',syxSha256=sha(raw),mainOsSha=m['main_os_sha256'],startup_title=m['title_screen'],lean_layout=True,wizard_explicit_lock_scope=True,wizard_sample_parameter_inheritance=True,source_rebuild_complete=False,voice_stealing_resolved=False)
 entries[(scope,ed)]=e
assets=dict(release='3.01',editions={s:{e:entries[(s,e)] for e in ['full','lite']} for s in ['main','optional']})
jw(site/'release301-assets.json',assets)
if a.assets_only:print('Prepared four pinned 3.01 assets');raise SystemExit
assert a.asset_commit and re.fullmatch('[0-9a-f]{40}',a.asset_commit)
oldcommit=main['asset_source_commit'];stamps={main['stamp']:'2026-11-01-main301',optional['stamp']:'2026-11-01-optional301',main['guide_version']:'2026-11-01-guide301','2026-10-31-md275':'2026-11-01-md301'}
for root in [site,opt]:
 for f in root.iterdir():
  if f.name=='tweaks.js' or f.suffix not in ['.js','.html','.md']:continue
  before=f.read_text(encoding='utf-8');s=before.replace(oldcommit,a.asset_commit)
  for old,new in stamps.items():s=s.replace(old,new)
  s=s.replace('release-notes-3.00.html','release-notes-3.01.html')
  if s!=before:put(f,s)
for m,stamp in [(main,'2026-11-01-main301'),(optional,'2026-11-01-optional301')]:
 m.update(release='3.01',startup_release_version='3.01',stamp=stamp,asset_source_commit=a.asset_commit,delivery_source_commit=a.asset_commit,guide_version='2026-11-01-guide301',lean_layout=True,source_rebuild_complete=False)
main['editions']={e:entries[('main',e)] for e in ['full','lite']};optional['base_editions']={e:entries[('optional',e)] for e in ['full','lite']}
f=main['editions']['full'];main.update(fixed_image=f['file'],fixed_image_legacy=f['file'],approved_source=f['file'],fixed_image_sha256=f['syxSha256'],approved_source_sha256=f['syxSha256'],main_os_sha256=f['mainOsSha'],optional_release='3.01',release_notes='release-notes-3.01.html')
loader=site/'fixed-main-image.js';s=loader.read_text(encoding='utf-8');start=s.index('const catalogue=')+len('const catalogue=');end=s.index(';',start);put(loader,s[:start]+json.dumps(main['editions'],ensure_ascii=False,indent=2)+s[end:])
jsw(opt/'editions.js','MCOptionalBaseEditions',optional['base_editions'])
jsw(opt/'recipe.js','MCOptionalRecipe',jr(W/'selection/recipe.json'));optional['recipe_sha256']=sha((opt/'recipe.js').read_bytes())
jsw(opt/'machinedrum-data.js','MCOptionalMDData',jr(W/'selection/machinedrum.json'))
page=opt/'index.html';s=page.read_text(encoding='utf-8');needle='<script src="../flasher-optional/optional-builder.js';assert needle in s
if 'clean-layout.js' not in s:s=s.replace(needle,'<script src="../flasher-optional/clean-layout.js?v=2026-11-01-optional301"></script>'+needle)
put(page,s)
changes=[
 {'en':'Leaner Full, Lite and Machine Optional firmware retains the current feature choices and removes retired code and boot staging. Startup and flashers show 3.01.','fr':'Les firmwares Full, Lite et Machine Optional conservent leurs fonctions avec moins de code retire et de donnees de demarrage. Ecran initial et flashers : 3.01.'},
 {'en':'Sample Wizard sample locks retain the chosen sample while unlocked parameters follow track edits. Only explicitly locked parameters resist CTRL-ALL, including during long loops.','fr':'Les locks de sample Sample Wizard conservent le sample choisi ; les parametres non verrouilles suivent la piste. Seuls les parametres explicitement verrouilles resistent a CTRL-ALL, meme pendant les longues boucles.'},
 {'en':'Shared filter and PUNCH paths avoid redundant work. Stock machines retain native PUNCH. Some six-track setups still click with effects; hardware investigation continues.','fr':'Les chemins filtre et PUNCH evitent du travail redondant. Les machines stock gardent leur PUNCH natif. Des configurations six pistes craquent encore avec effets ; investigation materielle en cours.'}]
for file in [R/'docs/assets/release.js',site/'midi-machine-release.js',opt/'release.js']:
 history=jsr(file);history=[x for x in history if x['version']!='3.01'];history.insert(0,dict(version='3.01',date='2026-11-01',changes=changes));jsw(file,'MC_RELEASES',history)
html='<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Supermodel 3.01</title><style>body{max-width:760px;margin:3rem auto;padding:0 1rem;font:18px/1.6 system-ui}h1{line-height:1.2}</style><a href="./">Flasher</a><h1>Supermodel 3.01</h1>'
for c in changes:html+='<p>'+c['en']+'</p><p lang="fr">'+c['fr']+'</p>'
put(site/'release-notes-3.01.html',html+'<p><a href="shortcut-guide.html">Feature and shortcut guide / Guide des fonctions et raccourcis</a></p></html>')
for f in [R/'docs/index.html',R/'README.md',opt/'README.md']:
 s=f.read_text(encoding='utf-8').replace('3.00','3.01').replace('2026-11-01-main300-sc1','2026-11-01-main301').replace('2026-11-01-guide300-sc1','2026-11-01-guide301');put(f,s)
jw(site/'BUILD.json',main);jw(opt/'BUILD.json',optional)
print('Prepared 3.01 catalogues, recipes, release notes and cache stamps')
