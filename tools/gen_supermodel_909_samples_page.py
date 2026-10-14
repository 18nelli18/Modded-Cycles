#!/usr/bin/env python3
"""Page 909 à quatre WAV locaux ; aucun firmware ou audio utilisateur publié."""
import argparse,json,pathlib,re,shutil
from gen_supermodel_909_installer import generate
p=argparse.ArgumentParser();p.add_argument('--base',required=True);p.add_argument('--output',required=True);a=p.parse_args()
base=pathlib.Path(a.base);out=pathlib.Path(a.output);generate(base,out,'unused')
cat=json.loads(pathlib.Path('work/model909/requested-catalog-private.json').read_text())['tweaks']
engine=json.loads(pathlib.Path('work/model909/sample-template.json').read_text())
cat=[engine if t['id']==engine['id'] else t for t in cat]
cat.append(json.loads(pathlib.Path('work/model909/boot-909.json').read_text()));cat.sort(key=lambda t:t['order'])
assert all(not t.get('append',{}).get('syntakt') for t in cat)
device=json.loads(pathlib.Path('tweaks/model-cycles_OS1.13/device.json').read_text())
(out/'profile.js').write_text('window.MC_TWEAKS = '+json.dumps({'device':device,'features':[],'tweaks':cat},separators=(',',':'))+';\n')
shutil.copyfile('tools/web/model909/samples.js',out/'samples.js')
html=(out/'index.html').read_text().replace('2026-10-14-supermodel-909-control-all','2026-10-14-supermodel-909-local-samples')
html=re.sub(r'<p><span data-l="en">Upload your prepared.*?</p>', '<p><span data-l="en">Choose your four WAV samples and the official Model:Cycles OS 1.13. Firmware is built locally in your browser. No samples are uploaded or included with this page.</span><span data-l="fr">Choisissez vos quatre WAV et l’OS officiel Model:Cycles 1.13. Le firmware est construit localement dans votre navigateur. Aucun sample n’est envoyé ni fourni avec cette page.</span></p>',html,flags=re.S)
slots=[('ch','Closed hat','Hi-hat fermé'),('oh','Open hat','Hi-hat ouvert'),('crash','Crash','Crash'),('ride','Ride','Ride')]
fields=''.join(f'<label><span data-l="en">{en}</span><span data-l="fr">{fr}</span><input id="sample-{key}" type="file" accept=".wav,audio/wav"><output id="sample-status-{key}" aria-live="polite"></output></label>' for key,en,fr in slots)
section='<section class="step" id="step-samples"><header><span class="num">1</span><h2><span data-l="en">Choose your samples</span><span data-l="fr">Choisir vos samples</span></h2></header><div class="sample-slots">'+fields+'</div><p id="samples-status" role="status"><span data-l="en">All four WAV files are required. PCM and floating-point WAVs are supported; audio is mixed to mono and converted to 32 kHz.</span><span data-l="fr">Quatre fichiers WAV requis. PCM et flottant acceptés ; conversion mono à 32 kHz.</span></p></section>'
html=html.replace('</ul><p>', '<li>SUPERMODEL by A.V. — 909 EDITION</li></ul><p>',1)
html=html.replace('  <section class="step" id="step-file"',section+'\n  <section class="step" id="step-file"',1)
html=html.replace('</head>','<style>.sample-slots{display:grid;grid-template-columns:1fr 1fr;gap:20px}.sample-slots label{display:grid;gap:8px;font-weight:600}.sample-slots output{font-weight:400;font-size:13px}.sample-slots input{max-width:100%}.build-steps{grid-template-columns:repeat(4,1fr)}@media(max-width:600px){.sample-slots{grid-template-columns:1fr}}</style></head>')
nav=''.join(f'<a href="#{id}"><b>{n}</b><span data-l="en">{en}</span><span data-l="fr">{fr}</span></a>' for n,id,en,fr in [(1,'step-samples','Choose samples','Choisir les samples'),(2,'step-file','Load official OS','Charger l’OS officiel'),(3,'step-connect','Connect MIDI','Connexion MIDI'),(4,'step-flash','Install','Installer')])
html=re.sub(r'<nav class="build-steps".*?</nav>',lambda _:'<nav class="build-steps" aria-label="Installation">'+nav+'</nav>',html,flags=re.S)
for id,n in [('step-file',2),('step-connect',3),('step-flash',4)]:html=re.sub(r'(<section class="step" id="'+id+r'"[^>]*>\s*<header><span class="num">)\d+',lambda m:m[1]+str(n),html)
html=html.replace('<script src="app.js','<script src="samples.js"></script>\n<script src="edition.js"></script>\n<script src="app.js')
html=html.replace('</head>','<link rel="stylesheet" href="909.css?v=2026-10-14-supermodel-909-local-samples"></head>')
html=html.replace("<h1>Supermodel 909<br><span>A.V.'s Edition</span></h1>","<h1>SUPERMODEL 909<span>by A.V. · 909 EDITION</span></h1>")
html=re.sub(r'<script src="edition.js\?[^>]+></script>','',html)
html=html.replace('2026-10-14-supermodel-909-local-samples','2026-10-14-supermodel-909-ready')
(out/'index.html').write_text(html)
app=(base/'app.js').read_text().replace('Model:Cycles Flasher','Supermodel 909 — A.V.’s Edition').replace('Flasher Model:Cycles','Supermodel 909 — Édition A.V.')
app=app.replace('Select at least one mod, or switch to “Official firmware”.','Choose all four WAV samples (step 1).').replace('Cochez au moins un mod, ou passez sur « Firmware officiel ».','Choisissez les quatre samples WAV (étape 1).')
needle='    const sha = window.MCBuilder.hex(window.MCBuilder.sha256(raw));'
app=app.replace(needle,needle+'''\n    if (sha !== window.MC_TWEAKS.device.stock_syx_sha256) throw new Error(document.documentElement.lang === "fr" ? "Choisissez l’OS officiel Model:Cycles 1.13." : "Choose the official Model:Cycles OS 1.13.");\n    st.machine = "cyc"; st.mode = "mods";''',1)
app=app.replace('function chosenLabels() {','function chosenLabels() {\n  if (window.MC909Labels) return window.MC909Labels;',1)
app=app.replace('opts.refMods = REF_MODS;', 'opts.refMods = window.MC909Refs(raw, tweaks);',1)
(out/'app.js').write_text(app)
shutil.copyfile('tools/web/model909/edition.js',out/'edition.js')
shutil.copyfile('tools/web/model909/909.css',out/'909.css')
(out/'BUILD.json').write_text(json.dumps({'samples_hosted':False,'sample_capacity_bytes':engine['sample_slots']['capacity'],'sample_rate':32000,'voice_hardware_tested':True,'browser_upload_combination_hardware_tested':False},indent=2)+'\n')
(out/'ABOUT.md').write_text('# Supermodel 909 — A.V.’s Edition\n\nSeparate browser builder: four local WAV inputs plus the official Cycles OS 1.13. Audio never leaves the browser. Six stock engines are replaced by Model909; ACID, SCRAMBLE, MIDI Bank, Out/Thru, Sequence Genie, latching mute, Second LFO and Control All Config are included. MIDI Bank remains RAM-only. Same MIDI classic/fast transports as main.\n\n909 voices reported working on hardware; browser upload combination awaits testing. Model909 by DMDaudio (MIT); see LICENSE-Model909.txt. Main flasher unchanged.\n')
print('Page locale à quatre WAV',out)
