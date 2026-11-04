"""Assets3.05 epingles, recettes Optional rebasees et historique conserve."""
from pathlib import Path
import argparse
import hashlib
import json
import re

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--repo',type=Path,required=True)
p.add_argument('--asset-commit')
a=p.parse_args()
ROOT=a.repo;WORK=Path(__file__).resolve().parents[2]/'release305'
SITE=ROOT/'docs/flasher';OPT=ROOT/'docs/flasher-optional'
def read(path):return json.loads(path.read_text(encoding='utf-8'))
def put(path,value):path.write_text(value,encoding='utf-8',newline='\n')
def write(path,value):put(path,json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def jsread(path):return json.loads(path.read_text(encoding='utf-8').split('=',1)[1].strip().rstrip(';'))
def jswrite(path,name,value):put(path,'window.'+name+'='+json.dumps(value,ensure_ascii=False,separators=(',',':'))+';\n')
sha=lambda value:hashlib.sha256(value).hexdigest()
main=read(SITE/'BUILD.json');optional=read(OPT/'BUILD.json');entries={}
for scope,edition in [('main','full'),('main','lite'),('optional','full'),('optional','lite')]:
    folder=WORK/'final'/scope/edition;meta=read(folder/'BUILD.json');raw=next(folder.glob('*.syx')).read_bytes()
    assert sha(raw)==meta['sha256'] and meta['release']==meta['title_screen']['version']=='3.05'
    entry=dict((main['editions'] if scope=='main' else optional['base_editions'])[edition])
    name='Supermodel_'+('Optional_' if scope=='optional' else '')+edition.title()+'_3.05_'+sha(raw)[:12]+'.syx'
    (SITE/name).write_bytes(raw)
    entry.update(file=name,release='3.05',syxSha256=sha(raw),mainOsSha=meta['main_os_sha256'],
                 startup_title=meta['title_screen'],dummy_available=False,master_retrig_optimized=True,
                 song_starts_at_highlighted_row=True,slice_editor_physical_FUNC=True,
                 voice_stealing_resolved=False,LOW_sample_rate=48000,pattern_selection_latch=True,governor_choice=True,governor_default='Lod',wizard_upper_slice_keyboard=edition=='full',wizard_pan_display=edition=='full',silent_commit_fixed=True,control_all_notice_restored=True,track_swap=True,track_swap_stopped_only=True)
    entries[(scope,edition)]=entry
write(SITE/'release305-assets.json',dict(release='3.05',editions={scope:{edition:entries[(scope,edition)] for edition in ['full','lite']} for scope in ['main','optional']}))
if not a.asset_commit:
    print('Prepared four pinned3.05 assets');raise SystemExit
assert re.fullmatch('[0-9a-f]{40}',a.asset_commit)
replacements={main['asset_source_commit']:a.asset_commit,main['stamp']:'2026-11-04-main305',
              optional['stamp']:'2026-11-04-optional305',main['guide_version']:'2026-11-04-guide305',
              '2026-11-04-md302':'2026-11-04-md305','release-notes-3.04.html':'release-notes-3.05.html'}
for root in [SITE,OPT,ROOT/'docs/assets']:
    for file in root.iterdir():
        if file.suffix not in ('.js','.html','.md') or file.name in ('tweaks.js','release-notes-3.03.html','release-notes-3.04.html'):continue
        before=file.read_text(encoding='utf-8');value=before
        for old,new in replacements.items():value=value.replace(old,new)
        if value!=before:put(file,value)
for meta,stamp in [(main,'2026-11-04-main305'),(optional,'2026-11-04-optional305')]:
    meta.update(release='3.05',startup_release_version='3.05',stamp=stamp,
                asset_source_commit=a.asset_commit,delivery_source_commit=a.asset_commit,
                guide_version='2026-11-04-guide305',dummy_available=False)
main['editions']={edition:entries[('main',edition)] for edition in ['full','lite']}
optional['base_editions']={edition:entries[('optional',edition)] for edition in ['full','lite']}
f=main['editions']['full'];main.update(fixed_image=f['file'],fixed_image_legacy=f['file'],approved_source=f['file'],
    fixed_image_sha256=f['syxSha256'],approved_source_sha256=f['syxSha256'],main_os_sha256=f['mainOsSha'],
    optional_release='3.05',release_notes='release-notes-3.05.html')
file=SITE/'fixed-main-image.js';value=file.read_text(encoding='utf-8');start=value.index('const catalogue=')+len('const catalogue=');end=value.index(';',start)
put(file,value[:start]+json.dumps(main['editions'],ensure_ascii=False,indent=2)+value[end:])
jswrite(OPT/'editions.js','MCOptionalBaseEditions',optional['base_editions'])
cold=WORK/'cold/optional/full'
banks=[(0x40000400,(cold/'native.bin').read_bytes()),(0x46700000,(cold/'runtime.bin').read_bytes()),(0x80000000,(cold/'sram.bin').read_bytes())]
def rebase(patches):
    for patch in patches:
        n=len(bytes.fromhex(patch['old']))
        raw=next(blob[patch['at']-base:patch['at']-base+n] for base,blob in banks if base<=patch['at'] and patch['at']+n<=base+len(blob))
        assert len(raw)==n;patch['old']=raw.hex()
recipe=jsread(OPT/'recipe.js');recipe.update(source_sha256=entries[('optional','full')]['syxSha256'],lite_sha256=entries[('optional','lite')]['syxSha256'],release='3.05',dummy_available=False)
pan=read(WORK/'final/optional/full/BUILD.json')['wizard_pan371']
for patch in recipe['patches']:
    if patch['at']==pan['native_input']:
        assert patch['new']=='4ef9468d0da4'
        patch['at']=pan['symbols']['ws_previous_model_key']
rebase(recipe['patches']);jswrite(OPT/'recipe.js','MCOptionalRecipe',recipe);optional['recipe_sha256']=sha((OPT/'recipe.js').read_bytes())
md=jsread(OPT/'machinedrum-data.js');md.update(source_sha256=recipe['source_sha256'],release='3.05',source_release='3.05',title=entries[('optional','full')]['startup_title'],full_mask=0x3fffff,dummy_available=False)
# Le selecteur MD doit rester derriere le guard de commit SIL369.
guard=read(WORK/'final/optional/full/BUILD.json')['silent_select369']
pan=read(WORK/'final/optional/full/BUILD.json')['wizard_pan371']
for patch in md['clean_patches']:
    if patch['at']==0x400148ad:
        assert patch['new']==int(guard['prior_selector']).to_bytes(4,'big')[1:].hex()
        patch['at']=guard['code']+25
    if patch['at']==pan['native_input']:
        assert patch['new']=='4ef9468d0da4'
        patch['at']=pan['symbols']['ws_previous_model_key']
rebase(md['clean_patches']);jswrite(OPT/'machinedrum-data.js','MCOptionalMDData',md)
changes=[
 dict(en='Track Swap: open Mod Setup > Track > Swap while stopped. Select From and To with DATA, then select Swap and press DATA. Sounds, sequences, p-locks, volume, filters, LFO settings and per-track FX move together; sidechain connections and Song mute references follow the swapped contents. Swapping the same pair again reverses the operation. Save Project to keep edits.',fr='Track Swap : ouvrez Mod Setup > Track > Swap a l arret. Choisissez From et To avec DATA, puis Swap et appuyez sur DATA. Sons, sequences, p-locks, volume, filtres, LFO et FX par piste sont echanges ; sidechain et mutes Song suivent le contenu. Refaire le meme echange annule l operation. Sauvegardez le projet pour conserver les changements.'),
 dict(en='Available in Full, Lite and Optional. Optional also moves its ChordKeys settings without changing Page Length. Lite keeps its stock-only machine roster. Existing DSP, SRAM audio code and governor thresholds are unchanged from 3.04; no new audio-interrupt work is added.',fr='Disponible dans Full, Lite et Optional. Optional deplace aussi ChordKeys sans modifier Page Length. Lite garde les machines stock. Le DSP, le code audio SRAM et les seuils du regulateur restent ceux de3.04 ; aucun travail audio supplementaire.'),
 dict(en='Guides, manuals, startup screens and flashers updated to 3.05. FX clicks and voice stealing remain under investigation.',fr='Guides, manuels, ecrans de demarrage et flasheurs passes en3.05. Les craquements FX et vols de voix restent a l etude.')]

for file in [ROOT/'docs/assets/release.js',SITE/'midi-machine-release.js',OPT/'release.js']:
    history=[row for row in jsread(file) if row['version']!='3.05']
    history.insert(0,dict(version='3.05',date='2026-11-04',changes=changes));jswrite(file,'MC_RELEASES',history)
from html import escape
html='<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Supermodel 3.05 — What changed</title><style>body{max-width:780px;margin:3rem auto;padding:0 1rem;font:18px/1.6 system-ui}h1{line-height:1.2}li{margin-bottom:1rem}</style><a href="./">Flasher</a><h1>Supermodel 3.05</h1><h2>What changed in this version…</h2><ul>'
html+=''.join('<li>'+escape(c['en'])+'</li>' for c in changes)+'</ul><h2 lang="fr">Changements de cette version…</h2><ul>'
html+=''.join('<li lang="fr">'+escape(c['fr'])+'</li>' for c in changes)+'</ul><p><a href="../version-history.html">Version history / Historique des versions</a></p></html>'
for root in [SITE,OPT]:put(root/'release-notes-3.05.html',html)
for file in [ROOT/'docs/index.html',ROOT/'README.md',OPT/'README.md']:
    value=file.read_text(encoding='utf-8').replace('3.04','3.05')
    for old,new in replacements.items():value=value.replace(old,new)
    put(file,value)
write(SITE/'BUILD.json',main);write(OPT/'BUILD.json',optional)
print('Prepared3.05 catalogues, guarded recipes and preserved release history')
