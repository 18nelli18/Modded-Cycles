#!/usr/bin/env python3
"""Page séparée Supermodel909 : installer un SysEx préparé, sans samples publiés.

Les transports sont ceux du flasher main ; seul le fichier signé épinglé est accepté.
"""
import argparse,json,pathlib,shutil,re

def generate(base,out,digest):
 out.mkdir(parents=True,exist_ok=True)
 for name in ['builder.js','flasher.js','style.css']:shutil.copyfile(base/name,out/name)
 html=(base/'index.html').read_text().replace('2026-10-14-bank-optional-acid-test','2026-10-14-supermodel-909-control-all')
 html=html.replace('<title>Modded Cycles: A.V.\'s Supermodel Edition.</title>',"<title>Supermodel 909 — A.V.'s Edition</title>")
 html=html.replace("<h1>Modded Cycles:<br><span>A.V.'s Supermodel Edition.</span></h1>","<h1>Supermodel 909<br><span>A.V.'s Edition</span></h1>")
 html=html.replace('</head>','''<style>#step-choose,.super-save-note,.ver,.quick-reference,.top nav{display:none!important}.fl-head{display:block}.wrap.fl{max-width:1000px}.fl-head h1{font-size:clamp(34px,5vw,58px);line-height:1.1}.edition-profile{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px 24px;list-style:none;padding:0}.edition-profile li{padding:8px 0;border-bottom:1px solid var(--line)}.edition-profile li::before{content:"✓ ";font-weight:700}.notice{max-width:1000px;margin:22px auto;padding:20px 24px;text-align:left}.build-steps{grid-template-columns:repeat(3,1fr)}@media(max-width:600px){.edition-profile{grid-template-columns:1fr}}</style></head>''')
 profile=[('Full 909 kit: kick, snare, hats, rim/clap, toms, cymbal','Kit 909 complet : kick, snare, hats, rim/clap, toms, cymbale'),('ACID','ACID'),('SCRAMBLE','SCRAMBLE'),('Parallel six-track MIDI Bank','Banque MIDI parallèle de six pistes'),('MIDI Out/Thru','MIDI Out/Thru'),('Sequence Genie','Sequence Genie'),('Latching mute mode','Mode mute verrouillé'),('Second LFO','Second LFO'),('Control All Config — including active-track selection','Control All Config — piste active sélectionnable')]
 cards=''.join('<li><span data-l="en">'+en+'</span><span data-l="fr">'+fr+'</span></li>' for en,fr in profile)
 notice='''<section class="notice" role="note"><strong><span data-l="en">909 voices hardware tested</span><span data-l="fr">Voix 909 testées sur machine</span></strong><p><span data-l="en">Dedicated edition. The six stock machines are replaced by the 909 kit. Model-TG support is included. Control All Config has been added; this updated combination still needs its hardware check.</span><span data-l="fr">Édition dédiée. Les six machines stock sont remplacées par le kit 909. Support Model-TG inclus. Control All Config ajouté ; cette combinaison actualisée reste à vérifier sur machine.</span></p><ul class="edition-profile">'''+cards+'''</ul><p><span data-l="en">Upload your prepared <b>Supermodel-909-ControlAll.syx</b> file below. The browser does not find or download it automatically. Your samples stay in that local firmware file and are not hosted here.</span><span data-l="fr">Chargez votre fichier préparé <b>Supermodel-909-ControlAll.syx</b> ci-dessous. Le navigateur ne le trouve ni ne le télécharge automatiquement. Vos samples restent dans ce fichier local et ne sont pas hébergés ici.</span></p><p><span data-l="en">Start with an empty project when changing from stock machines. MIDI Bank data is RAM-only. Control All: hold TRACK + TRIG 1–6 to include/exclude each audio track, including the selected track; TRACK + knob controls included tracks.</span><span data-l="fr">Partez d’un projet vide si vous quittez les machines stock. Banque MIDI en RAM uniquement. Control All : TRACK + TRIG 1–6 inclut/exclut chaque piste audio, même la piste active ; TRACK + potentiomètre agit sur les pistes incluses.</span></p></section>'''
 html=re.sub(r'<div class="notice" role="note">.*?</div>',lambda _:notice,html,count=1,flags=re.S)
 nav=''.join(f'<a href="#{id}"><b>{n}</b><span data-l="en">{en}</span><span data-l="fr">{fr}</span></a>' for n,id,en,fr in [(1,'step-file','Load 909 firmware','Charger le firmware 909'),(2,'step-connect','Connect MIDI','Connexion MIDI'),(3,'step-flash','Install','Installer')]);html=re.sub(r'<nav class="build-steps".*?</nav>',lambda _:'<nav class="build-steps" aria-label="Installation">'+nav+'</nav>',html,flags=re.S)
 for id,n in [('step-file',1),('step-connect',2),('step-flash',3)]:html=re.sub(r'(<section class="step" id="'+id+r'"[^>]*>\s*<header><span class="num">)\d+',lambda m:m[1]+str(n),html)
 html=html.replace('<script src="tweaks.js','<script src="profile.js').replace('<script src="bundle.js','<script src="edition.js')
 (out/'index.html').write_text(html)
 app=(base/'app.js').read_text();pairs=[('Load your official OS file','Load your prepared 909 firmware'),('Déposez votre fichier d\'OS officiel','Chargez votre firmware 909 préparé'),('Drop model-cycles_OS1.13.syx here','Choose Supermodel-909-ControlAll.syx'),('Déposez model-cycles_OS1.13.syx ici','Choisissez Supermodel-909-ControlAll.syx')]
 for old,new in pairs:app=app.replace(old,new)
 app=re.sub(r'get_os: `[^`]+`',lambda _:'''get_os: "Use the prepared Supermodel-909-ControlAll.syx file supplied with this edition. Do not select the official stock OS here.",'''.rstrip(','),app,count=1)
 # Le second dictionnaire est français.
 i=app.index('get_os:',app.index('get_os:')+1);end=app.index('\n',i);app=app[:i]+'''get_os: "Utilisez le fichier Supermodel-909-ControlAll.syx fourni avec cette édition. Ne chargez pas l’OS stock ici.",'''+app[end:]
 needle='    const sha = window.MCBuilder.hex(window.MCBuilder.sha256(raw));';assert app.count(needle)>=1
 app=app.replace(needle,needle+f'''\n    if (sha !== "{digest}") throw new Error(document.documentElement.lang === "fr" ? "Ce fichier n’est pas le firmware Supermodel 909 + Control All attendu." : "This is not the expected Supermodel 909 + Control All firmware file.");\n    st.machine = "cyc"; st.mode = "mods";''',1)
 (out/'app.js').write_text(app)
 device=json.loads(pathlib.Path('tweaks/model-cycles_OS1.13/device.json').read_text());(out/'profile.js').write_text('window.MC_TWEAKS = '+json.dumps({'device':device,'features':[],'tweaks':[]})+';\n')
 (out/'edition.js').write_text('// Installateur de fichier préparé ; aucun firmware ni sample dans la page.\n')
 (out/'ABOUT.md').write_text('# Supermodel 909 Edition\n\nSeparate installer, main flasher unchanged. Loads the prepared signed local firmware; it never downloads firmware or uploads sample audio. Uses the same MIDI classic and fast transports as main.\n\n909 voices reported working on hardware by A.V.; Control All Config added afterwards. The updated combination needs hardware confirmation. MIDI Bank remains RAM-only.\n')
 shutil.copyfile('work/model909/LICENSE',out/'LICENSE-Model909.txt')
 (out/'BUILD.json').write_text(json.dumps({'prepared_syx_sha256':digest,'main_os_sha256':'9772a613818d54ccf98badabcb0e1e809e1c50f2cb5f2ecc1a4d8a9c8bb20730','voice_hardware_tested':True,'control_all_combination_hardware_tested':False,'samples_hosted':False},indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--base',required=True);p.add_argument('--output',required=True);p.add_argument('--sha',required=True);a=p.parse_args();generate(pathlib.Path(a.base),pathlib.Path(a.output),a.sha)
