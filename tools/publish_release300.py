"""Publication3.00 : pins Full/Lite/Optional, recettes et cache coherent."""
from pathlib import Path
import argparse,json,hashlib,re,shutil,sys
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from gen_governor_recovery_test import read
from sparse_loader_relocations import collect
p=argparse.ArgumentParser();p.add_argument('--assets-only',action='store_true');p.add_argument('--asset-commit');p.add_argument('--preview-root',type=Path);a=p.parse_args()
sha=lambda b:hashlib.sha256(b).hexdigest()
def jread(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,s):p.write_text(s,encoding='utf-8',newline='\n')
def jwrite(p,o):write(p,json.dumps(o,ensure_ascii=False,indent=2)+'\n')
def jsread(p):s=p.read_text(encoding='utf-8');return json.loads(s[s.index('=')+1:].strip().rstrip(';'))
def jswrite(p,name,o):write(p,'window.'+name+'='+json.dumps(o,ensure_ascii=False,separators=(',',':'))+';\n')
docroot=R/'docs'
if a.preview_root:
 docroot=a.preview_root.resolve()
 assert docroot!=R/'docs' and R not in docroot.parents
 for folder in ['flasher','flasher-optional','assets','guide','bugs']:shutil.copytree(R/'docs'/folder,docroot/folder,dirs_exist_ok=True)
 shutil.copyfile(R/'docs/index.html',docroot/'index.html')
site=docroot/'flasher';opt=docroot/'flasher-optional';main=jread(site/'BUILD.json');optional=jread(opt/'BUILD.json');entries={};metadata={}
for scope,ed in [('main','full'),('main','lite'),('optional','full'),('optional','lite')]:
 folder=R.parent/('release300/final/'+scope+'/'+ed)
 raw=next(folder.glob('*.syx')).read_bytes();m=jread(folder/'BUILD.json');assert sha(raw)==m['sha256']

 e=dict((main['editions'] if scope=='main' else optional['base_editions'])[ed]);name='Supermodel_'+('Optional_' if scope=='optional' else '')+ed.title()+'_3.00_'+sha(raw)[:12]+'.syx'
 (site/name).write_bytes(raw)
 e.update(dummy_available=scope=='optional' and ed=='full',chordkeys_pattern_storage=scope=='optional',recent_cuts_page=True,wizard_sustained_plocks=True,filter_pattern_storage=True,smp_export_unclipped=True)
 e.update(release='3.00',file=name,syxSha256=sha(raw),mainOsSha=m['main_os_sha256'],startup_title=m['title_screen'],control_all_latch=True,stock_machine_punch=True,activity_masks=True,wizard_usb_main_independent=True,machine_confirmation=True,hardware_verified=False,live_cpu_monitor=True,dx_monitor_global_gate=True,ctrl_all_native_back_undo=True,voice_stealing_resolved=False,machine_selection_default='Stk',valid_21bit_sysex=True)
 entries[(scope,ed)]=e;metadata[(scope,ed)]=m
if a.assets_only:
 jwrite(site/'release300-assets.json',{'release':'3.00','editions':{scope:{ed:entries[(scope,ed)] for ed in ['full','lite']} for scope in ['main','optional']}});print('Prepared four pinned image assets');sys.exit(0)
assert a.preview_root or (a.asset_commit and re.fullmatch('[0-9a-f]{40}',a.asset_commit) and int(a.asset_commit,16)!=0)
# Les pages reutilisent le chargement verifie et les deux catalogues existants.
oldmain=main['stamp'];oldopt=optional['stamp'];stamp='2026-11-01-main300';ostamp='2026-11-01-optional300';guide='2026-11-01-guide300'
for root,old,new in [(site,oldmain,stamp),(opt,oldopt,ostamp)]:
 for f in root.iterdir():
  if f.name=='tweaks.js':continue
  if f.is_file() and f.suffix in ['.html','.js','.md']:
   s=f.read_text(encoding='utf-8');s=s.replace(old,new).replace('release-notes-2.99.html','release-notes-3.00.html').replace('2026-10-30-guide264',guide).replace('2026-10-29-md262','2026-11-01-md300').replace('8a10633b3ab20937a363ece8c9e36683d1e5efe3',a.asset_commit or '8a10633b3ab20937a363ece8c9e36683d1e5efe3')
   s=s.replace('2026-10-31-guide275',guide).replace('2026-10-31-main275',stamp).replace('2026-10-31-optional275',ostamp)
   s=re.sub(r'(raw.githubusercontent.com/AveyCole/Supermodel/)[0-9a-f]{40}(/docs/flasher/)',lambda m:m[1]+(a.asset_commit or '98c7ec9f1cf4754ec936a26c962c59fbf0333d90')+m[2],s)
   if f.suffix=='.html':s=s.replace('release-notes-2.75.html','release-notes-3.00.html')
   if f.suffix=='.html':s=s.replace('release-notes-2.64.html','release-notes-3.00.html')
   write(f,s)
main.update(stamp=stamp,release='3.00',editions={ed:entries[('main',ed)] for ed in ['full','lite']},fixed_image=entries[('main','full')]['file'],approved_source=entries[('main','full')]['file'],fixed_image_sha256=entries[('main','full')]['syxSha256'],main_os_sha256=entries[('main','full')]['mainOsSha'],startup_release_version='3.00',optional_release='3.00',release_notes='release-notes-3.00.html',guide_version=guide,asset_source_commit=a.asset_commit,delivery_source_commit=a.asset_commit,control_all_latch=True,stock_machine_punch=True,activity_masks=True,wizard_usb_main_independent=True,machine_confirmation=True)
main.update(diagnostics='Live CPU monitor: Global DX On, SETTINGS + BACK',live_cpu_monitor=True,voice_stealing_resolved=False,ctrl_all_native_back_undo=True,machine_selection_default='Stk',valid_21bit_sysex=True)
optional.update(live_cpu_monitor=True,voice_stealing_resolved=False,ctrl_all_native_back_undo=True,machine_selection_default='Stk',valid_21bit_sysex=True)
main['approved_source_sha256']=entries[('main','full')]['syxSha256']
main['fixed_image_legacy']=main['fixed_image']
optional.update(stamp=ostamp,release='3.00',base_editions={ed:entries[('optional',ed)] for ed in ['full','lite']},asset_source_commit=a.asset_commit,guide_version=guide,control_all_latch=True,stock_machine_punch=True,activity_masks=True,wizard_usb_main_independent=True,machine_confirmation=True)
loader=site/'fixed-main-image.js';s=loader.read_text(encoding='utf-8');start=s.index('const catalogue=')+len('const catalogue=');end=s.index(';',start);s=s[:start]+json.dumps(main['editions'],ensure_ascii=False,indent=2)+s[end:];write(loader,s)
jswrite(opt/'editions.js','MCOptionalBaseEditions',optional['base_editions'])
recipe=jread(R.parent/'release300/selection/manifest.json');recipe['source_release']='3.00';jswrite(opt/'recipe.js','MCOptionalRecipe',recipe);optional['recipe_sha256']=sha((opt/'recipe.js').read_bytes())
md=jsread(opt/'machinedrum-data.js');md.update(source_sha256=entries[('optional','full')]['syxSha256'],release='3.00',title=entries[('optional','full')]['startup_title'],title_edits=[])
source=read(site/entries[('optional','full')]['file'])[2];md['base_loader_relocations']=collect(source,metadata[('optional','full')]);jswrite(opt/'machinedrum-data.js','MCOptionalMDData',md)
changes=[
 {'en':'Track filter modes save with each pattern; resonance uses its complete range. Sample Wizard p-locks retain priority during sustained loops, and silent machine browsing discards stale candidates.','fr':'Les modes du filtre sont sauvegardes par pattern ; la resonance utilise toute sa plage. Les p-locks Sample Wizard restent prioritaires pendant les boucles longues ; le parcours silencieux ignore les anciens candidats.'},
 {'en':'SMP exports saved resampled recordings as 48 kHz WAV, with stereo decoding and peak-safe gain. Transfer cancellation and repeated reads retain native file ownership. Stored recordings are unchanged.','fr':'SMP exporte les prises sauvegardees en WAV 48 kHz, avec decodage stereo et gain sans ecretage ajoute. Annulation et lectures repetees conservent la gestion native du fichier. Les prises stockees restent intactes.'},
 {'en':'Dummy is a selectable silent machine in Machine Optional only. Main excludes Dummy; Lite contains only the six stock machines. Optional ChordKeys settings save with patterns/projects. Native save/reload tests pass; hardware power-cycle confirmation is pending.','fr':'Dummy est une machine silencieuse selectable dans Machine Optional uniquement. Absente de Main ; Lite conserve les six machines stock. Les reglages ChordKeys Optional sont sauvegardes dans les patterns/projets. Tests natifs reussis ; confirmation apres extinction materielle attendue.'},
 {'en':'DX includes CPU Load, Recent Cuts across all tracks, and Track Totals. Global DX On, then SETTINGS + BACK; PAGE switches pages, DATA clears counters, double-BACK exits. Stock-pattern long-note cuts remain unresolved.','fr':'DX propose charge CPU, coupures recentes de toutes les pistes et totaux par piste. Global DX On puis SETTINGS + BACK ; PAGE change de page, DATA efface, double BACK quitte. Les coupures de longues notes sur patterns stock restent non resolues.'},

]

for f in [docroot/'assets/release.js',site/'midi-machine-release.js',opt/'release.js']:
 history=jsread(f);history=[x for x in history if x['version']!='3.00'];history.insert(0,dict(version='3.00',date='2026-11-01',changes=changes));jswrite(f,'MC_RELEASES',history)
jwrite(site/'BUILD.json',main);jwrite(opt/'BUILD.json',optional)
html='<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Supermodel3.00</title><style>body{max-width:760px;margin:3rem auto;padding:0 1rem;font:18px/1.6 system-ui}h1{line-height:1.2}</style><a href="./">Flasher</a><h1>Supermodel3.00</h1>'
for c in changes:html+='<p>'+c['en']+'</p><p lang="fr">'+c['fr']+'</p>'
html+='<p>Optional keeps its extra machine choices. Hardware coverage varies by combination.</p><p><a href="shortcut-guide.html">Feature and shortcut guide</a></p></html>'
write(site/'release-notes-3.00.html',html)
for f in [docroot/'index.html',opt/'README.md']+([] if a.preview_root else [R/'README.md']):
 s=f.read_text(encoding='utf-8').replace('2.64','3.00').replace('2.75','3.00').replace('2.99','3.00').replace('2026-10-30-main264','2026-11-01-main300').replace('2026-10-30-guide264',guide);write(f,s)
print('Prepared local preview3.00' if a.preview_root else 'Published metadata, exact assets, recipes, releases and stamps3.00')

# Note visible hors du descriptif protege ; son bloc h3/ul reste byte-identique.
for page in (site/'index.html',opt/'index.html'):
 text=page.read_text(encoding='utf-8')
 text=re.sub(r'<aside class="release(?:299|300)-note">.*?</aside>','',text,flags=re.S)
 protected=re.search(r'<h3><span data-l="en">Supermodel edition.*?</ul>',text,re.S)
 kept=protected[0] if protected else None
 text=text.replace('TRACK once or BACK exits. Track and trig selection remain momentary.','TRACK once or quick double-BACK exits. Single BACK keeps native parameter undo. Track and trig selection remain momentary.').replace('TRACK ou BACK quitte. Selection des pistes et trigs momentanee.','TRACK ou double BACK rapide quitte. BACK simple conserve l annulation native. Selection des pistes et trigs momentanee.')
 text=text.replace('Each sound machine has its own Punch attack.','Stock machines retain their native PUNCH; added machines keep their own Punch attacks.').replace('Chaque machine sonore possède sa propre attaque Punch.','Les machines stock conservent leur PUNCH natif ; les machines ajoutees gardent leur attaque Punch.')
 note='<aside class="release300-note"><p><span data-l="en"><b>DX CPU monitor:</b> Global DX On, then SETTINGS + BACK. PAGE switches pages; press DATA to clear; double-BACK exits. All knob turns and transport work normally without covering the monitor.</span><span data-l="fr"><b>Moniteur CPU DX :</b> Global DX On, puis SETTINGS + BACK. PAGE change de page ; clic DATA efface ; double BACK quitte. Potards et transport restent actifs sans masquer le moniteur.</span></p><p><span data-l="en"><b>Known issue:</b> voice stealing / long-note cuts on some stock patterns remain unresolved.</span><span data-l="fr"><b>Probleme connu :</b> vol de voix / longues notes coupees sur certains patterns stock toujours non resolus.</span></p></aside>'
 text=text.replace('<div class="fixed-features"',note+'<div class="fixed-features"',1)
 if kept:assert re.search(r'<h3><span data-l="en">Supermodel edition.*?</ul>',text,re.S)[0]==kept
 write(page,text)
