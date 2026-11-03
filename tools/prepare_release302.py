"""Prepare les assets, recettes gardees et notes3.02 dans un checkout propre."""
from pathlib import Path
import argparse,hashlib,json,re
p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);p.add_argument('--asset-commit');a=p.parse_args()
R=a.repo;W=Path(__file__).resolve().parents[2]/'release302';site=R/'docs/flasher';opt=R/'docs/flasher-optional'
def jr(p):return json.loads(p.read_text(encoding='utf-8'))
def put(p,s):p.write_text(s,encoding='utf-8',newline='\n')
def jw(p,d):put(p,json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def jsr(p):return json.loads(p.read_text(encoding='utf-8').split('=',1)[1].strip().rstrip(';'))
def jsw(p,n,d):put(p,'window.'+n+'='+json.dumps(d,ensure_ascii=False,separators=(',',':'))+';\n')
sha=lambda b:hashlib.sha256(b).hexdigest()
main=jr(site/'BUILD.json');optional=jr(opt/'BUILD.json');entries={}
for scope,ed in [('main','full'),('main','lite'),('optional','full'),('optional','lite')]:
 folder=W/'final'/scope/ed;m=jr(folder/'BUILD.json');raw=next(folder.glob('*.syx')).read_bytes()
 assert sha(raw)==m['sha256'] and m['release']==m['title_screen']['version']=='3.02'
 e=dict((main['editions'] if scope=='main' else optional['base_editions'])[ed]);name='Supermodel_'+('Optional_' if scope=='optional' else '')+ed.title()+'_3.02_'+sha(raw)[:12]+'.syx';(site/name).write_bytes(raw)
 e.update(file=name,release='3.02',syxSha256=sha(raw),mainOsSha=m['main_os_sha256'],startup_title=m['title_screen'],dummy_available=False,granular_mode_labels=True,genie_stopped_intro=True,silent_commit_guard=True,deep_stop_idle=True,LOW_sample_rate=48000,voice_stealing_resolved=False)
 entries[(scope,ed)]=e
jw(site/'release302-assets.json',dict(release='3.02',editions={s:{e:entries[(s,e)] for e in ['full','lite']} for s in ['main','optional']}))
if not a.asset_commit:print('Prepared four pinned3.02 assets');raise SystemExit
assert re.fullmatch('[0-9a-f]{40}',a.asset_commit)
oldcommit=main['asset_source_commit'];replacements={oldcommit:a.asset_commit,main['stamp']:'2026-11-03-main302',optional['stamp']:'2026-11-03-optional302',main['guide_version']:'2026-11-03-guide302','2026-11-01-md301':'2026-11-03-md302','release-notes-3.01.html':'release-notes-3.02.html'}
for root in [site,opt,R/'docs/assets']:
 for f in root.iterdir():
  if f.name=='tweaks.js' or f.suffix not in ['.js','.html','.md']:continue
  before=f.read_text(encoding='utf-8');s=before
  for old,new in replacements.items():s=s.replace(old,new)
  if s!=before:put(f,s)
for m,stamp in [(main,'2026-11-03-main302'),(optional,'2026-11-03-optional302')]:m.update(release='3.02',startup_release_version='3.02',stamp=stamp,asset_source_commit=a.asset_commit,delivery_source_commit=a.asset_commit,guide_version='2026-11-03-guide302',dummy_available=False)
main['editions']={e:entries[('main',e)] for e in ['full','lite']};optional['base_editions']={e:entries[('optional',e)] for e in ['full','lite']}
f=main['editions']['full'];main.update(fixed_image=f['file'],fixed_image_legacy=f['file'],approved_source=f['file'],fixed_image_sha256=f['syxSha256'],approved_source_sha256=f['syxSha256'],main_os_sha256=f['mainOsSha'],optional_release='3.02',release_notes='release-notes-3.02.html')
loader=site/'fixed-main-image.js';s=loader.read_text(encoding='utf-8');start=s.index('const catalogue=')+len('const catalogue=');end=s.index(';',start);put(loader,s[:start]+json.dumps(main['editions'],ensure_ascii=False,indent=2)+s[end:]);jsw(opt/'editions.js','MCOptionalBaseEditions',optional['base_editions'])
# Rebases des seules gardes : chaque nouvel octet reste celui de la recette validee.
cold=W/'cold/optional/full';banks=[(0x40000400,(cold/'native.bin').read_bytes()),(0x46700000,(cold/'runtime.bin').read_bytes()),(0x80000000,(cold/'sram.bin').read_bytes())]
def rebase(patches):
 for p in patches:
  n=len(bytes.fromhex(p['old']));raw=next(b[p['at']-at:p['at']-at+n] for at,b in banks if at<=p['at'] and p['at']+n<=at+len(b));assert len(raw)==n;p['old']=raw.hex()
recipe=jsr(opt/'recipe.js');recipe.update(source_sha256=entries[('optional','full')]['syxSha256'],lite_sha256=entries[('optional','lite')]['syxSha256'],release='3.02',dummy_available=False);rebase(recipe['patches']);jsw(opt/'recipe.js','MCOptionalRecipe',recipe);optional['recipe_sha256']=sha((opt/'recipe.js').read_bytes())
md=jsr(opt/'machinedrum-data.js');md.update(source_sha256=recipe['source_sha256'],release='3.02',source_release='3.02',title=entries[('optional','full')]['startup_title'],full_mask=0x3fffff,dummy_available=False);rebase(md['clean_patches']);jsw(opt/'machinedrum-data.js','MCOptionalMDData',md)
for file in [opt/'optional-builder.js',opt/'machinedrum-builder.js']:
 s=file.read_text(encoding='utf-8').replace('0x47ffff','0x7ffff').replace('mask>0x7fffff','mask>0x3fffff').replace('ALL:0x7fffff','ALL:0x3fffff');put(file,s)
file=opt/'optional-ui.js';s=file.read_text(encoding='utf-8').replace(",[28,'Dummy']",'');s=re.sub(r'28:\{en:.*?\},25:', '25:',s,count=1);put(file,s)
changes=[
 {'en':'Sample Wizard knob popups and LFO destination names follow the selected playback mode. Granular shows Position, Grain Size, Density and Spray. Sequence Genie opens after double-STOP instead of remaining on its title screen.','fr':'Les popups et noms de destinations LFO Sample Wizard suivent le mode choisi. Granular affiche Position, Grain Size, Density et Spray. Sequence Genie quitte son ecran titre meme apres double-STOP.'},
 {'en':'SIL machine browsing protects an active confirmation from re-entrant redraws. Dummy is removed from Machine Optional; the other machine choices remain. The external-sequencing exception hotfix is retained.','fr':'Le parcours SIL protege la confirmation pendant les redessins imbriques. Dummy est retire de Machine Optional ; les autres machines restent disponibles. Le correctif de crash du sequencage externe est conserve.'},
 {'en':'Double-STOP clears lingering processing and allows low-load stopped sleep, with playback wake-up retained. FX, filter and CHORD paths reduce repeated work; hot CHORD, filter, delay and post-processing kernels run from SRAM. LOW remains 12 dB/octave at 48 kHz.','fr':'Double-STOP libere les traitements persistants et permet une veille a faible charge, avec reveil en lecture. FX, filtre et CHORD evitent les calculs repetes ; leurs noyaux critiques utilisent la SRAM. LOW reste a 12 dB/octave et 48 kHz.'},
 {'en':'Performance tradeoffs: HALL uses a 3 kHz internal network; stock reverb uses fewer allpass stages; CHORD omits wavetable interpolation. Six-track FX clicking, voice stealing, and the reported filter-mode change on sequence clear remain under investigation.','fr':'Compromis : reseau interne HALL a 3 kHz, moins d etages allpass dans la reverb stock, CHORD sans interpolation de table. Craquements avec FX sur six pistes, vols de voix et changement de filtre au clear restent a l etude.'}]
for file in [R/'docs/assets/release.js',site/'midi-machine-release.js',opt/'release.js']:
 history=jsr(file);history=[x for x in history if x['version']!='3.02'];history.insert(0,dict(version='3.02',date='2026-11-03',changes=changes));jsw(file,'MC_RELEASES',history)
html='<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Supermodel 3.02</title><style>body{max-width:760px;margin:3rem auto;padding:0 1rem;font:18px/1.6 system-ui}h1{line-height:1.2}</style><a href="./">Flasher</a><h1>Supermodel 3.02</h1>'
for c in changes:html+='<p>'+c['en']+'</p><p lang="fr">'+c['fr']+'</p>'
for root in [site,opt]:put(root/'release-notes-3.02.html',html+'<p><a href="shortcut-guide.html">Feature and shortcut guide / Guide des fonctions et raccourcis</a></p></html>')
for file in [R/'docs/index.html',R/'README.md',opt/'README.md']:
 s=file.read_text(encoding='utf-8').replace('3.01','3.02')
 for old,new in replacements.items():s=s.replace(old,new)
 put(file,s)
for root in [site,opt]:
 for name in ['guide.html','shortcut-guide.html']:
  file=root/name
  if not file.exists():continue
  s=file.read_text(encoding='utf-8');s=re.sub(r'<tr><td>Dummy</td>.*?</tr>','',s,flags=re.S)
  s=s.replace('3.01','3.02');put(file,s)
jw(site/'BUILD.json',main);jw(opt/'BUILD.json',optional)
print('Prepared3.02 catalogues, recipes, notes, stamps and Dummy removal')
