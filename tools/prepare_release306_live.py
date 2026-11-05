"""Publication du correctif live, version3.06 conservee et assets immuables."""
from pathlib import Path
import argparse,json,hashlib,re
from html import escape
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--repo',type=Path,required=True);p.add_argument('--work',type=Path,required=True);p.add_argument('--asset-commit')
a=p.parse_args();R=a.repo;W=a.work;SITE=R/'docs/flasher';OPT=R/'docs/flasher-optional'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def put(p,s):p.write_text(s,encoding='utf-8',newline='\n')
def write(p,v):put(p,json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def jsread(p):return json.loads(p.read_text(encoding='utf-8').split('=',1)[1].strip().rstrip(';'))
def jswrite(p,name,v):put(p,'window.'+name+'='+json.dumps(v,ensure_ascii=False,separators=(',',':'))+';\n')
sha=lambda b:hashlib.sha256(b).hexdigest()
main=read(SITE/'BUILD.json');opt=read(OPT/'BUILD.json');entries={}
for scope in ('main','optional'):
    for edition in ('full','lite'):
        folder=W/'final'/scope/edition;m=read(folder/'BUILD.json');raw=next(folder.glob('*.syx')).read_bytes()
        assert m['release']==m['title_screen']['version']=='3.06' and sha(raw)==m['sha256'] and m.get('fx_live383')
        e=dict((main['editions'] if scope=='main' else opt['base_editions'])[edition])
        name='Supermodel_'+('Optional_' if scope=='optional' else '')+edition.title()+'_3.06_'+sha(raw)[:12]+'.syx'
        (SITE/name).write_bytes(raw);e.update(file=name,release='3.06',syxSha256=sha(raw),mainOsSha=m['main_os_sha256'],startup_title=m['title_screen'],fx_live_pattern_switch_fixed=True,build_revision='fx-live383')
        entries[(scope,edition)]=e
write(SITE/'release306-assets.json',dict(release='3.06',build_revision='fx-live383',editions={scope:{edition:entries[(scope,edition)] for edition in ('full','lite')} for scope in ('main','optional')}))
if not a.asset_commit:
    print('Prepared same-version3.06 live-fix assets');raise SystemExit
assert re.fullmatch('[0-9a-f]{40}',a.asset_commit)
stamps={'main':'2026-11-05-main306-fx-live1','optional':'2026-11-05-optional306-fx-live1'}
replacements={main['asset_source_commit']:a.asset_commit,main['stamp']:stamps['main'],opt['stamp']:stamps['optional']}
for folder in (SITE,OPT,R/'docs/assets'):
    for path in folder.iterdir():
        if path.suffix not in ('.js','.html','.md'):continue
        try:s=path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            assert path.name.startswith('release-notes-'),path
            continue
        new=s
        for old,value in replacements.items():new=new.replace(value,old).replace(old,value)
        if new!=s:put(path,new)
for path in (R/'docs/index.html',R/'docs/version-history.html'):
    s=path.read_text(encoding='utf-8')
    for old,new in replacements.items():s=s.replace(new,old).replace(old,new)
    put(path,s)
for scope,m in (('main',main),('optional',opt)):
    m.update(release='3.06',startup_release_version='3.06',stamp=stamps[scope],asset_source_commit=a.asset_commit,delivery_source_commit=a.asset_commit,fx_live_pattern_switch_fixed=True,build_revision='fx-live383')
main['editions']={e:entries[('main',e)] for e in ('full','lite')};opt['base_editions']={e:entries[('optional',e)] for e in ('full','lite')}
e=main['editions']['full'];main.update(fixed_image=e['file'],fixed_image_legacy=e['file'],approved_source=e['file'],fixed_image_sha256=e['syxSha256'],approved_source_sha256=e['syxSha256'],main_os_sha256=e['mainOsSha'])
path=SITE/'fixed-main-image.js';s=path.read_text(encoding='utf-8');start=s.index('const catalogue=')+len('const catalogue=');end=s.index(';',start);put(path,s[:start]+json.dumps(main['editions'],ensure_ascii=False,indent=2)+s[end:])
jswrite(OPT/'editions.js','MCOptionalBaseEditions',opt['base_editions'])
cold=W/'cold/optional/full';banks=[(0x40000400,(cold/'native.bin').read_bytes()),(0x46700000,(cold/'runtime.bin').read_bytes()),(0x80000000,(cold/'sram.bin').read_bytes())]
def rebase(patches):
    for patch in patches:
        n=len(bytes.fromhex(patch['old']));raw=next(data[patch['at']-base:patch['at']-base+n] for base,data in banks if base<=patch['at'] and patch['at']+n<=base+len(data));assert len(raw)==n;patch['old']=raw.hex()
recipe=jsread(OPT/'recipe.js');recipe.update(source_sha256=entries[('optional','full')]['syxSha256'],lite_sha256=entries[('optional','lite')]['syxSha256'],release='3.06',fx_live_pattern_switch_fixed=True);rebase(recipe['patches']);jswrite(OPT/'recipe.js','MCOptionalRecipe',recipe);opt['recipe_sha256']=sha((OPT/'recipe.js').read_bytes())
md=jsread(OPT/'machinedrum-data.js');md.update(source_sha256=recipe['source_sha256'],title=entries[('optional','full')]['startup_title'],release='3.06',source_release='3.06',fx_live_pattern_switch_fixed=True);rebase(md['clean_patches']);jswrite(OPT/'machinedrum-data.js','MCOptionalMDData',md)
change=dict(en='FX playback-switching fix: changing patterns while playing now restores the saved FX at the live pattern boundary without copying another pattern\'s settings into the outgoing pattern. This update stays on 3.06. If incorrect choices were already saved, reselect the intended FX and Save Project once.',fr='Correctif FX pendant lecture : le changement de pattern restaure les FX sauvegardes a la frontiere reelle, sans recopier les reglages d un autre pattern dans le pattern precedent. La version reste3.06. Si des choix incorrects etaient deja sauvegardes, rechoisissez les FX voulus puis sauvegardez le projet une fois.')
for path in (R/'docs/assets/release.js',SITE/'midi-machine-release.js',OPT/'release.js'):
    history=jsread(path);assert history[0]['version']=='3.06';history[0]['changes']=[change]+[v for v in history[0]['changes'] if not v['en'].startswith('FX playback-switching fix:')];jswrite(path,'MC_RELEASES',history)
changes=jsread(R/'docs/assets/release.js')[0]['changes']
html='<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Supermodel 3.06 — What changed</title><style>body{max-width:780px;margin:3rem auto;padding:0 1rem;font:18px/1.6 system-ui}li{margin-bottom:1rem}</style><a href="./">Flasher</a><h1>Supermodel 3.06</h1><h2>What changed in this version…</h2><ul>'+''.join('<li>'+escape(c['en'])+'</li>' for c in changes)+'</ul><h2 lang="fr">Changements de cette version…</h2><ul>'+''.join('<li lang="fr">'+escape(c['fr'])+'</li>' for c in changes)+'</ul><p><a href="../version-history.html">Version history / Historique des versions</a></p></html>'
for folder in (SITE,OPT):put(folder/'release-notes-3.06.html',html)
write(SITE/'BUILD.json',main);write(OPT/'BUILD.json',opt)
print('Prepared3.06 live fix: new SHA pins, recipe guards, cache stamps and bilingual notes; no version bump')
