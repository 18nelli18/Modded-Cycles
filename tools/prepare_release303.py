"""Assets3.03 epingles, recettes Optional rebasees et historique conserve."""
from pathlib import Path
import argparse
import hashlib
import json
import re

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--repo',type=Path,required=True)
p.add_argument('--asset-commit')
a=p.parse_args()
ROOT=a.repo;WORK=Path(__file__).resolve().parents[2]/'release303'
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
    assert sha(raw)==meta['sha256'] and meta['release']==meta['title_screen']['version']=='3.03'
    entry=dict((main['editions'] if scope=='main' else optional['base_editions'])[edition])
    name='Supermodel_'+('Optional_' if scope=='optional' else '')+edition.title()+'_3.03_'+sha(raw)[:12]+'.syx'
    (SITE/name).write_bytes(raw)
    entry.update(file=name,release='3.03',syxSha256=sha(raw),mainOsSha=meta['main_os_sha256'],
                 startup_title=meta['title_screen'],dummy_available=False,master_retrig_optimized=True,
                 song_starts_at_highlighted_row=True,slice_editor_physical_FUNC=True,
                 voice_stealing_resolved=False,LOW_sample_rate=48000)
    entries[(scope,edition)]=entry
write(SITE/'release303-assets.json',dict(release='3.03',editions={scope:{edition:entries[(scope,edition)] for edition in ['full','lite']} for scope in ['main','optional']}))
if not a.asset_commit:
    print('Prepared four pinned3.03 assets');raise SystemExit
assert re.fullmatch('[0-9a-f]{40}',a.asset_commit)
replacements={main['asset_source_commit']:a.asset_commit,main['stamp']:'2026-11-03-main303',
              optional['stamp']:'2026-11-03-optional303',main['guide_version']:'2026-11-03-guide303',
              '2026-11-03-md302':'2026-11-03-md303','release-notes-3.02.html':'release-notes-3.03.html'}
for root in [SITE,OPT,ROOT/'docs/assets']:
    for file in root.iterdir():
        if file.suffix not in ('.js','.html','.md') or file.name=='tweaks.js':continue
        before=file.read_text(encoding='utf-8');value=before
        for old,new in replacements.items():value=value.replace(old,new)
        if value!=before:put(file,value)
for meta,stamp in [(main,'2026-11-03-main303'),(optional,'2026-11-03-optional303')]:
    meta.update(release='3.03',startup_release_version='3.03',stamp=stamp,
                asset_source_commit=a.asset_commit,delivery_source_commit=a.asset_commit,
                guide_version='2026-11-03-guide303',dummy_available=False)
main['editions']={edition:entries[('main',edition)] for edition in ['full','lite']}
optional['base_editions']={edition:entries[('optional',edition)] for edition in ['full','lite']}
f=main['editions']['full'];main.update(fixed_image=f['file'],fixed_image_legacy=f['file'],approved_source=f['file'],
    fixed_image_sha256=f['syxSha256'],approved_source_sha256=f['syxSha256'],main_os_sha256=f['mainOsSha'],
    optional_release='3.03',release_notes='release-notes-3.03.html')
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
recipe=jsread(OPT/'recipe.js');recipe.update(source_sha256=entries[('optional','full')]['syxSha256'],lite_sha256=entries[('optional','lite')]['syxSha256'],release='3.03',dummy_available=False)
rebase(recipe['patches']);jswrite(OPT/'recipe.js','MCOptionalRecipe',recipe);optional['recipe_sha256']=sha((OPT/'recipe.js').read_bytes())
md=jsread(OPT/'machinedrum-data.js');md.update(source_sha256=recipe['source_sha256'],release='3.03',source_release='3.03',title=entries[('optional','full')]['startup_title'],full_mask=0x3fffff,dummy_available=False)
rebase(md['clean_patches']);jswrite(OPT/'machinedrum-data.js','MCOptionalMDData',md)
changes=[
 dict(en='Master retrig uses a cheaper steady-repeat loop while retaining its sample output, history ordering, fades and track exclusions. Shared voice, filter and routing paths avoid repeated work; double-STOP idle savings remain.',
      fr='Le retrig master utilise une boucle de repetition moins couteuse, avec sortie audio, ordre de capture, fondus et exclusions conserves. Voix, filtres et routage evitent des calculs repetes ; la faible charge apres double-STOP reste disponible.'),
 dict(en='Song: PLAY while stopped starts at the highlighted row, including after a single STOP. STOP mode plays to the end; LOOP wraps through the whole arrangement.',
      fr='Song : PLAY a l arret demarre sur la ligne selectionnee, meme apres un seul STOP. STOP joue jusqu a la fin ; LOOP parcourt tout l arrangement en boucle.'),
 dict(en='Sample Wizard Slice Editor reads the physical FUNC state for upper slices 17–32, including when FUNC was already held before opening the editor. For Step Recorder octaves, use FUNC + TRACK > KBT; 12 semitones equals one octave.',
      fr='L editeur de slices Sample Wizard lit l etat physique de FUNC pour les slices17–32, meme si FUNC etait deja tenu a l ouverture. Pour les octaves du Step Recorder : FUNC + TRACK > KBT ;12 demi-tons font une octave.'),
 dict(en='Delay and Ping Pong use a 12 kHz, 16-bit internal echo loop to recover CPU headroom; their echoes can sound darker. HALL and the 48 kHz LOW filter retain their previous sound. Full and Lite share the non-machine controls; Optional retains its extra choices. Dummy remains excluded.',
      fr='Delay et Ping Pong utilisent une boucle interne12 kHz/16 bits pour alleger la charge ; les echos peuvent etre plus sombres. HALL et le filtre LOW48 kHz gardent leur son precedent. Full et Lite partagent les commandes hors machines ; Optional garde ses choix supplementaires. Dummy reste exclu.'),
 dict(en='Voice stealing and six-track FX clicks remain unresolved. Matched private tests peaked at105 on Main Full and107 on Optional, with1% stopped idle; these are individual test results, not limits for every pattern. Lite hardware load has not been measured.',
      fr='Vols de voix et craquements FX sur six pistes restent a resoudre. Des essais prives comparables ont atteint105 sur Main Full et107 sur Optional, avec1% a l arret ; ces resultats ne garantissent pas un plafond pour tous les patterns. La charge materielle de Lite n a pas ete mesuree.')]
for file in [ROOT/'docs/assets/release.js',SITE/'midi-machine-release.js',OPT/'release.js']:
    history=[row for row in jsread(file) if row['version']!='3.03']
    history.insert(0,dict(version='3.03',date='2026-11-03',changes=changes));jswrite(file,'MC_RELEASES',history)
from html import escape
html='<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Supermodel 3.03 — What changed</title><style>body{max-width:780px;margin:3rem auto;padding:0 1rem;font:18px/1.6 system-ui}h1{line-height:1.2}li{margin-bottom:1rem}</style><a href="./">Flasher</a><h1>Supermodel 3.03</h1><h2>What changed in this version…</h2><ul>'
html+=''.join('<li>'+escape(c['en'])+'</li>' for c in changes)+'</ul><h2 lang="fr">Changements de cette version…</h2><ul>'
html+=''.join('<li lang="fr">'+escape(c['fr'])+'</li>' for c in changes)+'</ul><p><a href="../version-history.html">Version history / Historique des versions</a></p></html>'
for root in [SITE,OPT]:put(root/'release-notes-3.03.html',html)
for file in [ROOT/'docs/index.html',ROOT/'README.md',OPT/'README.md']:
    value=file.read_text(encoding='utf-8').replace('3.02','3.03')
    for old,new in replacements.items():value=value.replace(old,new)
    put(file,value)
write(SITE/'BUILD.json',main);write(OPT/'BUILD.json',optional)
print('Prepared3.03 catalogues, guarded recipes and preserved release history')
