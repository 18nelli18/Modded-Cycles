"""Candidat isolé, recettes MIT et fichiers OS fournis localement par l’utilisateur."""
import argparse,copy,hashlib,json,pathlib,shutil,sys,tempfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
import os
os.chdir(ROOT)
sys.path.insert(0,'tools');sys.path.insert(0,'tools/emu')
import build,ref_mainos
from chord_keys_pr87 import load_stock as main_os_from_syx
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--base-dir',default='docs/flasher');p.add_argument('--source-dir',default='docs/flasher-integration-test/source');p.add_argument('--output',default='docs/flasher-integration-test');p.add_argument('--cycles',required=True);p.add_argument('--check',action='store_true');a=p.parse_args()
BASE=pathlib.Path(a.base_dir);SOURCE=pathlib.Path(a.source_dir);TARGET=pathlib.Path(a.output)
tmp=tempfile.TemporaryDirectory() if a.check else None
OUT=pathlib.Path(tmp.name)/'flasher' if tmp else TARGET
STAMP='2026-10-13-chordkeys-rotero-tg'
input_map={'model-tg-rotero.json':'integration-model-tg.json','model-tg-rotero-st.json':'integration-model-tg-st.json','midi-bank-reclaimed-rebased.json':'integration-midi-bank.json','midi-bank-chord-rebased.json':'integration-midi-bank-chord.json','chord-keys-supermodel.json':'integration-chord-keys.json','chord-supermodel-safe-layout.json':'integration-placement.json','chord-engine-compression.json':'integration-engine-compression.json'}
inputs={old:json.loads((SOURCE/new).read_text()) for old,new in input_map.items()}
ref_text=(SOURCE/'integration-reference-check.json').read_text() if (SOURCE/'integration-reference-check.json').exists() else None
whole_refs=json.loads(ref_text)['refs'] if ref_text else {}
shutil.copytree(BASE,OUT,dirs_exist_ok=True)
for old_source in (OUT/'source').glob('*'):
 if old_source.is_file():old_source.unlink()
stock=main_os_from_syx(a.cycles)
load=lambda p:copy.deepcopy(inputs[pathlib.Path(p).name])
tg=[load('work/model-tg-rotero.json'),load('work/model-tg-rotero-st.json')]
bank=load('work/midi-bank-reclaimed-rebased.json');chordbank=load('work/midi-bank-chord-rebased.json');chord=load('work/chord-keys-supermodel.json');engine_compress=load('work/chord-engine-compression.json')
refs={}
for t in tg+[bank,chordbank,chord]:
 ref=dict(w=hashlib.sha256(ref_mainos.writes_bytes(t)).hexdigest())
 if t.get('append'):ref['p']=hashlib.sha256(build.payload_image(t,build.payload_runtime(t,stock,None))).hexdigest()
 refs[t['id']+('-chord' if t is chordbank else '')]=ref
texts={
 'en':dict(label='ChordKeys — Model-TG integration',short='COLOR, voicings, HARMONY locks and MIDI chords with Model-TG.',desc='The current ChordKeys revision by Nico Heuser, integrated with Model-TG and the Supermodel mods. This experimental placement uses the MIDI Bank bundle; selecting it selects the compatible full bundle. MIDI Bank data remains RAM-only.',shortcuts=['FUNC + RETRIG: Keys, key/scale, COLOR, SHAPE and MIDI ROOT/CHORD.','TRIG 1–7: I–VII; 8–14: an octave up; 15–16: I–II another octave up.','With Keys active, hold T1–T6: 9, 11, 13, 7sus4, parallel major/minor, target V7. Record HARMONY while holding a step or during live recording.']),
 'fr':dict(label='ChordKeys — intégration Model-TG',short='COLOR, voicings, locks HARMONY et accords MIDI avec Model-TG.',desc='Révision récente de ChordKeys par Nico Heuser, intégrée à Model-TG et aux mods Supermodel. Ce placement expérimental utilise le bundle Banque MIDI ; le cocher sélectionne le bundle complet compatible. Les données de Banque MIDI restent en RAM.',shortcuts=['FUNC + RETRIG : Keys, tonique/gamme, COLOR, SHAPE et MIDI ROOT/CHORD.','TRIG 1–7 : I–VII ; 8–14 : une octave plus haut ; 15–16 : I–II encore une octave plus haut.','Keys actif, tenir T1–T6 : 9, 11, 13, 7sus4, parallèle majeur/mineur, V7 cible. Enregistrer HARMONY en tenant un pas ou en live-rec.'])}
tail='\n// Intégration expérimentale isolée : code MIT, aucune image OS distribuée.\n(()=>{\n'
tail+='const tg='+json.dumps(tg,ensure_ascii=False)+'; const bank='+json.dumps(bank,ensure_ascii=False)+'; const chordBank='+json.dumps(chordbank,ensure_ascii=False)+'; const chord='+json.dumps(chord,ensure_ascii=False)+'; const refs='+json.dumps(refs)+'; const texts='+json.dumps(texts,ensure_ascii=False)+';\n'
tail+='''const chosenChord=()=>!!document.getElementById('feat-chord-keys')?.checked;
for(const t of tg){Object.assign(window.MC_TWEAKS.tweaks.find(x=>x.id===t.id),t);window.MCFlasherApp.REF_MODS[t.id]=refs[t.id];}
const b=window.MC_TWEAKS.tweaks.find(x=>x.id===bank.id);Object.assign(b,JSON.parse(JSON.stringify(bank)));
Object.defineProperty(b.append,'parts',{get:()=>chosenChord()?chordBank.append.parts:bank.append.parts,configurable:true});
Object.defineProperty(b.append,'compressed_hex',{get:()=>chosenChord()?chordBank.append.compressed_hex:bank.append.compressed_hex,configurable:true});
window.MCFlasherApp.REF_MODS[bank.id]={w:refs[bank.id].w};
Object.defineProperty(window.MCFlasherApp.REF_MODS[bank.id],'p',{get:()=>refs[bank.id+(chosenChord()?'-chord':'')].p});
window.MC_TWEAKS.tweaks.push(chord);window.MCFlasherApp.REF_MODS[chord.id]=refs[chord.id];
const f=window.MC_TWEAKS.features.find(x=>x.id==='chord-keys');f.variants=[{id:chord.id,label:null}];f.excludes=[];f.requires='midi-bank-bundle';f.status='experimental';f.credit={kind:'by',who:'Nico Heuser · 18nelli18 integration',repo:'byNicoHeuser/Modded-Cycles'};f.license='LICENSE-ChordKeys.txt';
for(const key of ['label','short','desc'])Object.defineProperty(f,key,{get:()=>(texts[document.documentElement.lang]||texts.en)[key],configurable:true});
for(const g of window.MC_TWEAKS.features){if(g.excludes)g.excludes=g.excludes.filter(id=>id!=='chord-keys');}
function untestedTG(v){if(!v||typeof v!=='object')return;for(const k of Object.keys(v)){if(k==='tg_tested')v[k]=false;else untestedTG(v[k]);}}
for(const g of window.MC_TWEAKS.features)if(g.engines)untestedTG(g);
const model=window.MC_TWEAKS.features.find(x=>x.id==='model-tg');model.status='experimental';model.credit={kind:'by',who:'TinyGregAudio · Slice varispeed by roterodamus',repo:'roterodamus/Model-TG'};
for(const key of Object.keys(window.MCFlasherApp.REF_MAINOS))if(key.split('+').some(id=>id.startsWith('model-tg')||id===bank.id||id==='chord-keys'))delete window.MCFlasherApp.REF_MAINOS[key];
document.addEventListener('change',event=>{if(event.target.id==='feat-chord-keys'&&event.target.checked)document.getElementById('select-all').click();},true);
window.MCFlasherApp.applyLang(document.documentElement.lang||'en');
})();
'''
tail+='\n(()=>{const e=window.MC_TWEAKS.tweaks.find(t=>t.id==="syntakt-tg-sd-cp-toy-bits-swarm-macro-acid");e.append={...e.append,compress_cost:512};window.MCFlasherApp.REF_MODS[e.id]={w:window.MCFlasherApp.REF_MODS[e.id].w,p:'+json.dumps(engine_compress['sha256'])+'};})();\n'
(OUT/'bundle.js').write_text((OUT/'bundle.js').read_text()+tail)
app=(OUT/'app.js').read_text()
# Les textes FEAT ont priorité sur les getters de la carte : remplacer l’entrée
# finale des textes brefs à la source, dans les deux langues.
# Un bloc d’override local s’exécute dans la portée de FEAT, avant l’export.
at=app.index('window.MCFlasherApp =')
app=app[:at]+'for(const L of ["en","fr"])Object.assign(FEAT[L]["chord-keys"],'+json.dumps(texts,ensure_ascii=False)+'[L]);\n'+app[at:]
modeltexts={'en':{'short':'Sampler, FX and roterodamus Slice varispeed.','desc':'Model-TG by TinyGregAudio with roterodamus’s Slice update. A note chooses the slice at its trigger; PITCH changes its playback speed without selecting another slice. Experimental integration.','shortcuts':['SETTINGS + PRESET: playback mode. SETTINGS + PUNCH: mode options. In Slice mode, notes select slices; PITCH changes playback speed.']},'fr':{'short':'Sampler, effets et Slice varispeed de roterodamus.','desc':'Model-TG de TinyGregAudio avec la mise à jour Slice de roterodamus. La note choisit la tranche au trig ; PITCH règle sa vitesse sans sélectionner une autre tranche. Intégration expérimentale.','shortcuts':['SETTINGS + PRESET : mode de lecture. SETTINGS + PUNCH : options. En Slice, les notes choisissent les tranches ; PITCH règle la vitesse.']}}
at=app.index('window.MCFlasherApp =');app=app[:at]+'for(const L of ["en","fr"])Object.assign(FEAT[L]["model-tg"],'+json.dumps(modeltexts,ensure_ascii=False)+'[L]);\n'+app[at:]
(OUT/'app.js').write_text(app)
builder=(OUT/'builder.js').read_text();builder=builder.replace('function buildPayload(ap, syntaktRaw, mainOs) {',pathlib.Path('tools/aplib_cost.js').read_text()+'\nfunction buildPayload(ap, syntaktRaw, mainOs) {',1).replace('return ap.compress_depth ? aplibDensePack(out, ap.compress_depth) : aplibPack(out);','return ap.compress_cost ? aplibCostPack(out, ap.compress_cost) : ap.compress_depth ? aplibDensePack(out, ap.compress_depth) : aplibPack(out);',1);(OUT/'builder.js').write_text(builder)
for p in OUT.iterdir():
 if p.is_file() and p.suffix in ('.js','.html','.md'):p.write_text(p.read_text().replace('2026-10-13-tempo-routing-main',STAMP))
html=(OUT/'index.html').read_text();html=html.replace('<main', '<div class="notice" role="note"><span data-l="en">Experimental ChordKeys + roterodamus Model-TG integration. Main flasher unchanged. MIDI Bank remains RAM-only.</span><span data-l="fr">Intégration expérimentale ChordKeys + Model-TG roterodamus. Flasher principal inchangé. Banque MIDI en RAM uniquement.</span></div>\n<main',1);(OUT/'index.html').write_text(html)
shutil.copyfile('tools/machines/chord_keys_compat/LICENSE',OUT/'LICENSE-ChordKeys.txt')
for name,obj in [('chord-keys',chord),('midi-bank',bank),('midi-bank-chord',chordbank),('model-tg',tg[0]),('model-tg-st',tg[1]),('placement',load('work/chord-supermodel-safe-layout.json'))]:
 (OUT/'source'/('integration-'+name+'.json')).write_text(json.dumps(obj,ensure_ascii=False,indent=1)+'\n')
(OUT/'ABOUT.md').write_text('''# Supermodel integration test — 13 October 2026

Current ChordKeys (Nico Heuser / 18nelli18 PR87), roterodamus Slice varispeed,
and the existing Supermodel selection. Experimental until hardware confirmation.
Select ChordKeys to select the compatible MIDI Bank bundle. B-side data remains
RAM-only. Clearing tracks/LFOs with Undo is still a separate pending change.
The main flasher and earlier test pages are unchanged.

ChordKeys récent (Nico Heuser / PR87 de 18nelli18), Slice varispeed de roterodamus
et sélection Supermodel existante. Expérimental avant confirmation matérielle.
Cocher ChordKeys sélectionne le bundle Banque MIDI compatible. Données B en RAM.
Clear piste/LFO avec Undo reste un changement séparé à venir. Flasher principal
et tests antérieurs inchangés.
''')
print('ok : candidat isolé '+str(OUT))

if whole_refs:
 with (OUT/'bundle.js').open('a') as f:f.write('\n// Verified integration whole-image references.\nObject.assign(window.MCFlasherApp.REF_MAINOS,'+json.dumps(whole_refs,separators=(',',':'))+');\n')
(OUT/'source/integration-engine-compression.json').write_text(json.dumps(engine_compress,ensure_ascii=False,indent=1)+'\n')
if ref_text:(OUT/'source/integration-reference-check.json').write_text(ref_text)
if a.check:
 names=['index.html','app.js','bundle.js','builder.js','LICENSE-ChordKeys.txt','ABOUT.md']
 names += ['source/integration-'+x+'.json' for x in ('chord-keys','midi-bank','midi-bank-chord','model-tg','model-tg-st','placement','engine-compression')]
 for name in names:assert (OUT/name).read_bytes()==(TARGET/name).read_bytes(),name
 print('ok : candidat reproductible, recettes et références identiques')
 tmp.cleanup()
