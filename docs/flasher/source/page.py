"""Copie du vrai checklist main : Wizard ajouté, Model-TG retiré."""
import pathlib,json,re,shutil
P=pathlib.Path('work/sample-wizard-options');base=pathlib.Path('work/sample-wizard-current-main');out=pathlib.Path('work/sample-wizard-options-page');out.mkdir(exist_ok=True);stamp='2026-10-15-wizard-selectable-options'
for f in base.iterdir():
 if f.is_file():shutil.copyfile(f,out/f.name)
app=(out/'app.js').read_text().replace('loadSamples, loadSyntakt, setMode,','loadSamples, loadSyntakt, chosenEngines, setMode,')
app=app.replace('const preferred = ["supermodel-performance",', 'const preferred = ["sample-wizard", "chord-keys", "wave-supermodel", "supermodel-performance",')
anchor='window.MCFlasherApp = {'
texts={'en':dict(label='Sample Wizard',short='Independent sampler with Slice varispeed; works with the other Supermodel options.',desc='Adds Wizard as machine 7. Each machine and feature remains separately selectable. Includes sample playback modes, sample browser and Slice varispeed. Upload your own samples with Elektron Transfer in SMP mode; return to CYC before a firmware upgrade.',shortcuts=['FUNC + MACHINES: sample browser.','SETTINGS + MACHINES: playback mode. SETTINGS + PUNCH: mode options.','Slice: notes choose the slice; PITCH changes its speed/pitch.']), 'fr':dict(label='Sample Wizard',short='Sampler autonome avec Slice varispeed ; compatible avec les options Supermodel.',desc='Ajoute Wizard comme machine 7. Machines et fonctions restent sélectionnables séparément. Modes de lecture, navigateur et Slice varispeed inclus. Transférer vos samples en mode SMP ; revenir à CYC avant une mise à jour.',shortcuts=['FUNC + MACHINES : navigateur.','SETTINGS + MACHINES : mode de lecture. SETTINGS + PUNCH : options.','Slice : notes = tranche ; PITCH = vitesse/hauteur.'])}
app=app.replace(anchor,'\n'+''.join('FEAT.'+lang+"['sample-wizard']="+json.dumps(text)+';\n' for lang,text in texts.items())+"GUIDE_OF['sample-wizard']='sample-wizard';\nFEAT.en['sample-preview'].desc='Preview samples in the Sample Wizard browser. Requires Sample Wizard; uses browser hooks that cannot be combined with WAVE or ChordKeys in this test.'; FEAT.fr['sample-preview'].desc='Préécoute dans le navigateur Sample Wizard. Exige Wizard ; ses hooks navigateur ne se combinent pas à WAVE ou ChordKeys dans ce test.';\n"+anchor);(out/'app.js').write_text(app)
html=(out/'index.html').read_text().replace('app_v2.js','app.js').replace('tweaks_v2.js','tweaks.js');html=re.sub(r'(?<=[?&])v=[^"\'&<> ]+','v='+stamp,html);html=re.sub(r'window.MC_BUILD\s*=\s*["\'][^"\']+["\']',"window.MC_BUILD='"+stamp+"'",html)
html=html.replace('<main class="wrap fl">','''<main class="wrap fl"><p class="alert"><span data-l="en"><strong>Sample Wizard integration test — full selectable checklist.</strong> Choose Sample Wizard and any compatible options below, or use Select all. Model-TG is omitted. Syntakt is optional: its official OS file is needed only when you select its machines. Main is unchanged.</span><span data-l="fr"><strong>Test Sample Wizard — checklist complète et sélectionnable.</strong> Choisir Wizard et les options compatibles, ou Tout sélectionner. Model-TG est retiré. Syntakt reste facultatif : son OS officiel n'est demandé que pour ses machines. Main inchangé.</span></p>''',1)
html=html.replace('</body>','<script src="catalogue.js?v='+stamp+'"></script><script src="compose.js?v='+stamp+'"></script><script src="wizard-refs.js?v='+stamp+'"></script><script src="wizard.js?v='+stamp+'"></script></body>');(out/'index.html').write_text(html)
for name in ['catalogue.js','compose.js']:shutil.copyfile(P/name,out/name)
# Les sources et le guide du sampler restent accessibles dans ce test.
old=pathlib.Path('work/sample-wizard-integration-page')
for name in ['guide.html','LICENSE-Sample-Wizard.txt','native-hat-A_48x33.png','native-hat-B_34x34.png']:shutil.copyfile(old/name,out/name)
for f in P.glob('*.py'):
 dest=out/'source'/f.name;dest.parent.mkdir(exist_ok=True);shutil.copyfile(f,dest)
for f in P.glob('*.js'):
 if f.name in ['catalogue.js']:continue
 dest=out/'source'/f.name;shutil.copyfile(f,dest)
print('PASS copie main avec véritable checklist préparée.',flush=True)
