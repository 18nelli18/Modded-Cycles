"""Note 108 : page de test 909 avec supports actuels, sans toucher aux pages publiees."""

import argparse,pathlib,shutil,tempfile,re,json

ROOT=pathlib.Path(__file__).resolve().parents[1];STAMP='2026-10-16-909-current-test-1'

def main():

 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args();expected=ROOT/'docs/flasher-supermodel-909-current-test';tmp=tempfile.TemporaryDirectory(dir=ROOT/'build') if a.check else None;out=pathlib.Path(tmp.name) if tmp else expected;out.mkdir(exist_ok=True)

 for src in (ROOT/'docs/flasher').iterdir():

  if src.is_file() and src.suffix!='.wav':shutil.copyfile(src,out/src.name)

 app=(out/'app.js').read_text(encoding='utf-8').replace('function chosenLabels() {','function chosenLabels() {\n  if(window.MC909CurrentLabels)return window.MC909CurrentLabels;',1)
 guard='    const sha = window.MCBuilder.hex(window.MCBuilder.sha256(raw));'
 assert guard in app
 app=app.replace(guard,guard+'''
    if (sha !== window.MC_TWEAKS.device.stock_syx_sha256) throw new Error(document.documentElement.lang==='fr' ? 'Choisissez l OS officiel Model:Cycles 1.13.' : 'Choose the official Model:Cycles OS 1.13.');
    st.machine='cyc'; st.mode='mods';''',1)
 (out/'app.js').write_text(app,encoding='utf-8')

 for name,source in [('909-data.js',ROOT/'build/909-current/engine-data.js'),('909-current.js',ROOT/'tools/web/model909/current.js'),('samples.js',ROOT/'tools/web/model909/samples.js'),('LICENSE-Model909.txt',ROOT/'tools/machines/model909_full/LICENSE')]:shutil.copyfile(source,out/name)

 html=(out/'index.html').read_text(encoding='utf-8');html=re.sub(r'(?<=\?v=)[\w.-]+',STAMP,html);html=re.sub(r"window.MC_BUILD='[^']+'",f"window.MC_BUILD='{STAMP}'",html)

 html=html.replace("<title>A.V.'s Supermodel Edition.</title>",'<title>Supermodel 909 — current modules test</title>');html=re.sub(r'<h1>.*?</h1>','<h1>Supermodel 909<br><span data-l="en">Current modules test</span><span data-l="fr">Test modules actuels</span></h1>',html,count=1,flags=re.S)

 html=re.sub(r'<p class="alert"><span data-l="en"><strong>Looking for the 909 kit\?.*?</p>','',html,count=1,flags=re.S)
 notice='''<p class="alert"><span data-l="en"><strong>Supermodel 909 — current modules test.</strong> Six 909 machines, current Sample Wizard replacing Model-TG, current ACID, SCRAMBLE, Sequence Genie, Second LFO, latching mute, MIDI Out/Thru, Control All Config and held TRACK + RETRIG beat repeat with division popup. MIDI Bank uses current project saving and stock-style B mute lights. Saved MIDI loads only when entering B-side while playback is stopped. Choose four local WAVs plus your official Cycles OS 1.13; no Syntakt file needed. Samples stay in your browser. Start with a fresh test project when switching samplers. New combination is experimental; released 909 and main are unchanged.</span><span data-l="fr"><strong>Supermodel 909 — test modules actuels.</strong> Six machines 909, Sample Wizard actuel a la place de Model-TG, ACID, SCRAMBLE, Sequence Genie, Second LFO, mute verrouille, Out/Thru, Control All Config et repeat TRACK + RETRIG maintenus avec popup division. Banque MIDI : sauvegarde projet actuelle et LEDs mute B natives. MIDI sauvegarde charge uniquement en entrant cote B, lecture arretee. Quatre WAV locaux et OS Cycles 1.13 officiel ; aucun fichier Syntakt requis. Samples dans le navigateur. Utiliser un projet de test neuf lors du changement de sampler. Nouvelle combinaison experimentale ; 909 publie et principal inchanges.</span></p>'''

 html=html.replace('<main class="wrap fl">','<main class="wrap fl">'+notice)

 fields=''.join(f'<label>{en} / {fr}<input id="sample-{key}" type="file" accept=".wav,audio/wav"><output id="sample-status-{key}" aria-live="polite"></output></label>' for key,en,fr in [('ch','Closed hat','Hi-hat ferme'),('oh','Open hat','Hi-hat ouvert'),('crash','Crash','Crash'),('ride','Ride','Ride')])

 html=html.replace('  <section class="step" id="step-file"','<section class="step" id="step-samples"><h2>909 WAV samples / Samples WAV 909</h2>'+fields+'<p id="samples-status" role="status">4 WAV required / 4 WAV requis</p></section>\n  <section class="step" id="step-file"',1)

 html=re.sub(r'<nav class="build-steps".*?</nav>','<nav class="build-steps"><a href="#step-samples">1 WAV</a><a href="#step-file">2 OS</a><a href="#step-connect">3 MIDI</a><a href="#step-flash">4 Install / Installer</a></nav>',html,count=1,flags=re.S)

 html=html.replace('</head>','<style>#step-choose{display:none!important}#step-samples label{display:grid;gap:8px;margin:16px 0}#step-samples output{font-size:13px}</style></head>')

 html=html.replace('../assets/release.js?','909-release.js?').replace('</body>',f'<script src="samples.js?v={STAMP}"></script><script src="909-data.js?v={STAMP}"></script><script src="909-current.js?v={STAMP}"></script></body>');(out/'index.html').write_text(html,encoding='utf-8')

 (out/'909-release.js').write_text('window.MC_RELEASES='+json.dumps([dict(version='909-current-preview.1',date='2026-10-16',changes=[dict(en='Experimental 909 rebuild on current Sample Wizard, MIDI saving, B mute lighting, Sequence Genie and Control All Beat Repeat. Hardware verification pending.',fr='909 experimental sur Sample Wizard actuel, sauvegarde MIDI, LEDs mute B, Genie et repeat Control All. Verification materielle attendue.')])])+';\n')

 (out/'TEST-NOTES.md').write_text('Experimental 909 combination. Four local WAVs and official Cycles 1.13 required. Sample Wizard replaces Model-TG; no Model-TG install path. Test all six 909 voices and types, ACID, Wizard, sample upload/cache invalidation, MIDI project saving to existing/blank slots, stopped B entry reload, FUNC mute lights, Genie Loop/Page on A/B, Second LFO, SCRAMBLE, latching mute, Out/Thru and held TRACK+RETRIG repeat/Control All mask/popup. No promotion before hardware verification.\n\nCombinaison 909 experimentale. Quatre WAV locaux et OS officiel Cycles 1.13. Sample Wizard remplace Model-TG. Verifier six voix/types 909, ACID, Wizard, fichiers/cache, sauvegarde MIDI cases vides/existantes et chargement en B lecture arretee, LEDs FUNC, Genie Loop/Page A/B, Second LFO, SCRAMBLE, mute verrouille, Out/Thru et repeat maintenu/masque/popup. Promotion seulement apres verification machine.\n',encoding='utf-8')

 for src in out.iterdir():

  if src.suffix in ('.js','.html','.css','.md','.txt'):src.write_text('\n'.join(line.rstrip() for line in src.read_text(encoding='utf-8').splitlines()).rstrip()+'\n',encoding='utf-8')

 if a.check:

  for src in out.iterdir():assert src.read_bytes().replace(b'\r\n',b'\n')==(expected/src.name).read_bytes().replace(b'\r\n',b'\n'),src.name

 print('PASS page 909 actuelle separee')

if __name__=='__main__':main()
