"""Nouvelle page privée du profil complet ; main et anciens tests inchangés."""
import pathlib,json,re,shutil,hashlib
import ref_mainos
from chord_keys_pr87 import load_stock
P=pathlib.Path('work/sample-wizard-main');out=pathlib.Path('work/sample-wizard-integration-page');out.mkdir(exist_ok=True);base=pathlib.Path('work/sample-wizard-test-page');main=pathlib.Path('work/sample-wizard-current-main');stamp='2026-10-15-wizard-full-integration'
cat=json.load(open(P/'select-all.json'))
for t in cat:t.update(prototype_only=False,flashable=True,status='experimental')
# Aucun flux comprimé extrait du Syntakt : recette côté client seulement.
assert not any('compressed_hex' in t.get('append',{}) for t in cat if t.get('append',{}).get('syntakt'))
for name in ['index.html','app.js','style.css','guide.html','LICENSE-Sample-Wizard.txt']:shutil.copyfile(base/name,out/name)
for name in ['builder.js','flasher.js']:shutil.copyfile(main/name,out/name)
for f in main.glob('LICENSE*'):shutil.copyfile(f,out/f.name)
text=(base/'tweaks.js').read_text();data,_=json.JSONDecoder().raw_decode(text[text.index('{'):]);feature=data['features'][0];feature.update(id='sample-wizard',label='Sample Wizard — Full Supermodel Test',desc='Full integration profile: Sample Wizard and all compatible Supermodel features; no Model-TG.',status='experimental',variants=[dict(id='sample-wizard',label=None)])
(out/'tweaks.js').write_text('window.MC_TWEAKS = '+json.dumps(dict(device=data['device'],features=[feature],tweaks=cat))+';\n')
html=(out/'index.html').read_text();html=html.replace('2026-10-15-sample-wizard-first-test',stamp).replace('Sample Wizard<br><span>Supermodel Test</span>','Sample Wizard<br><span>Full Supermodel Test</span>')
notice='''<p class="alert"><span data-l="en"><strong>Full integration hardware test · Model-TG not required.</strong> This fixed profile includes Sample Wizard (upright hat and five-point stars), all six stock machines, five Syntakt machines, MACRO, corrected ACID, WAVE, ChordKeys, Second LFO, Sequence Genie, SCRAMBLE, slides/scale lock/mutes/preview and the compatible main-page controls. Main and earlier tests are unchanged. Supply official Cycles OS 1.13 and Syntakt OS 1.42. Samples and wavetables are uploaded separately. <a href="guide.html">Instructions</a>.</span><span data-l="fr"><strong>Test matériel de l'intégration complète · Model-TG non requis.</strong> Profil fixe : Sample Wizard (chapeau droit et étoiles à cinq branches), six machines stock, cinq machines Syntakt, MACRO, ACID corrigée, WAVE, ChordKeys, Second LFO, Sequence Genie, SCRAMBLE, slides/scale lock/mutes/preview et contrôles compatibles de main. Main et anciens tests inchangés. Fournir les OS officiels Cycles 1.13 et Syntakt 1.42. Samples et tables d'ondes transférés séparément. <a href="guide.html">Instructions</a>.</span></p>'''
html=re.sub(r'<p class="alert">.*?</p>',notice,html,count=1,flags=re.S);(out/'index.html').write_text(html)
# L'UI ne retire aucun élément du profil pendant cette validation : un seul
# choix explicite, détaillé, avant l'intégration des combinaisons individuelles.
(out/'bundle.js').write_text('''(()=>{const a=window.MCFlasherApp;window.MCMainClearResolve=out=>out.some(t=>t.id==='sample-wizard')?window.MC_TWEAKS.tweaks.map(t=>JSON.parse(JSON.stringify(t))):out;
const en={label:'Sample Wizard — Full Supermodel integration',short:'One fixed profile: all compatible main features, without Model-TG.',desc:'Adds Sample Wizard with Slice varispeed alongside stock, Syntakt, MACRO, corrected ACID and WAVE machines, ChordKeys, Second LFO, Sequence Genie, SCRAMBLE and the main controls. Hardware verification of this combination is pending. Individual combinations are still being prepared. WAVE needs uploaded wavetables; Wizard needs your uploaded samples.'};
const fr={label:'Sample Wizard — Intégration Supermodel complète',short:'Profil fixe : fonctions compatibles de main, sans Model-TG.',desc:'Sample Wizard et Slice varispeed avec machines stock, Syntakt, MACRO, ACID corrigée et WAVE, ChordKeys, Second LFO, Sequence Genie, SCRAMBLE et contrôles de main. Combinaison en attente de validation matérielle. Combinaisons individuelles en préparation. Charger vos tables WAVE et vos samples Wizard.'};
const apply=a.applyLang;a.applyLang=function(lang){const r=apply(lang);const row=document.getElementById('feat-sample-wizard')?.closest('.feat');return r;};
function ready(){a.setMachine('cyc');const el=document.getElementById('feat-sample-wizard');if(el&&!el.checked){el.checked=true;el.dispatchEvent(new Event('change',{bubbles:true}));}}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',ready);else ready();})();\n''')
# Les textes FEAT sont lexicaux ; l'injection précède leur export public.
app=(out/'app.js').read_text();anchor='window.MCFlasherApp = {'
insert="FEAT.en['sample-wizard']="+json.dumps(dict(label='Sample Wizard — Full Supermodel integration',short='Complete integration profile without Model-TG.',desc='Includes Sample Wizard, stock + Syntakt + MACRO + ACID + WAVE machines, ChordKeys, Second LFO, Sequence Genie, SCRAMBLE and main controls. This fixed combination awaits hardware verification. Upload your own samples/wavetables.'))+";\nFEAT.fr['sample-wizard']="+json.dumps(dict(label='Sample Wizard — Intégration Supermodel complète',short='Profil complet sans Model-TG.',desc='Sample Wizard, machines stock + Syntakt + MACRO + ACID + WAVE, ChordKeys, Second LFO, Sequence Genie, SCRAMBLE et contrôles de main. Combinaison en attente de validation matérielle. Charger vos samples/tables.'))+';\n'
app=app.replace(anchor,insert+anchor);(out/'app.js').write_text(app)
source=out/'source';source.mkdir(exist_ok=True)
for f in P.glob('*.py'):shutil.copyfile(f,source/f.name)
for f in P.glob('*.s'):shutil.copyfile(f,source/f.name)
for f in (P/'src').rglob('*'):
 if f.is_file() and (f.suffix in ['.s','.c','.h'] or f.parent.name=='sampler_icons' and f.suffix=='.bin'):
  dest=source/'sampler'/f.relative_to(P/'src');dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,dest)
for f in ['native-hat-A_48x33.png','native-hat-B_34x34.png']:shutil.copyfile(P/f,out/f)
(P/'main-os.bin').write_bytes(load_stock('firmware/model-cycles_OS1.13.syx'))
(P/'page-data.json').write_text(json.dumps(dict(folder=str(out),stamp=stamp)))
print('PASS page distincte préparée ; profil complet, sources MIT et icône ; aucune modification main.')
