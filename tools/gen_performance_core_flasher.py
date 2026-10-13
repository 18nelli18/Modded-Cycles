#!/usr/bin/env python3
"""Note65 : première page isolée du noyau performance sans sampler Model-TG.

--cycles OS1.13.syx --model-tg CLONE [--output DIR] [--check]. Les pages
principale et Test3 ne sont jamais écrites. Catalogue limité à la preuve du noyau.
"""
import argparse,copy,json,pathlib,re
import build,gen_flasher_tweaks as catalog,gen_performance_core as core,ref_mainos
ROOT=pathlib.Path(__file__).resolve().parents[1]
STAMP='2026-10-12-performance-midi-core-test'
TEXT={
'en':dict(label='Slide trigs + Scale Lock — standalone core',short='Retained Model-TG performance features, without its sampler.',desc='Hold SETTINGS and press a trig to toggle its slide. Scale Lock is available in the keyboard setup menu. This extracted core contains no sampler, master effects or extra Model-TG menus. Latching mute and trig preview are separate selections below. Sequence Genie, SCRAMBLE and MIDI Bank are not connected to this core yet; use the existing flasher for those features.',note='Experimental extraction: boot, scale mapping and six-machine audio verified in emulation. Awaiting hardware testing.'),
'fr':dict(label='Slides + Scale Lock — noyau autonome',short='Fonctions performance de Model-TG, sans son sampler.',desc='Maintenez SETTINGS et appuyez sur un trig pour basculer son slide. Scale Lock est disponible dans la configuration du clavier. Ce noyau extrait ne contient ni sampler, ni effets master, ni menus supplémentaires Model-TG. Mute verrouillé et écoute de pas restent deux sélections séparées ci-dessous. Sequence Genie, SCRAMBLE et banque MIDI ne sont pas encore reliés à ce noyau ; utilisez le flasher existant pour ces fonctions.',note='Extraction expérimentale : démarrage, gammes et audio des six machines vérifiés en émulation. Essai matériel attendu.')}

BUNDLE_TEXT={
'en':dict(label='Standalone MIDI performance bundle',short='Sequence Genie, SCRAMBLE, LFO2 and MIDI Bank with saving, without Model-TG.',desc='Includes slides, Scale Lock, latching mute, trig preview, arpeggiator and Live MIDI OUT + THRU. FUNC + SETTINGS + TRACK opens the B-side; RETURN leaves it. SETTINGS + PAGE opens Sequence Genie on the active side. MIDI lanes retain the stock-style keyboard, track/scale setup, chance and retrigger menus, step and track clipboard, live recording, editable MIDI channels and LFO-to-CC. LFO opens its first page, then a second press opens LFO2. B-side destinations cover CC 0–127 with common names. The Test3 sidecar saving and working autosave code is included for MIDI patterns, B-side LFOs and A-side LFO2. A-side LFO1 uses its native saving. This test has only the six stock sound machines; Syntakt, ACID, MACRO, sampler and sample preview are absent.',note='Experimental new bindings and startup layout: boot, MIDI routing, scheduler and simulated save/load verified. Hardware testing still required. Back up projects before testing persistence. Main and Test3 are unchanged.'),
'fr':dict(label='Pack performance MIDI autonome',short='Sequence Genie, SCRAMBLE, LFO2 et banque MIDI sauvegardable, sans Model-TG.',desc='Inclut slides, Scale Lock, mute verrouillé, écoute de trig, arpégiateur et MIDI OUT + THRU en direct. FUNC + SETTINGS + TRACK ouvre la face B ; RETURN en sort. SETTINGS + PAGE ouvre Sequence Genie du côté actif. Les voies MIDI conservent clavier, réglages piste/gamme, chance, retrigger, presse-papiers pas/piste, enregistrement live, canaux réglables et LFO CC. LFO ouvre sa première page, un second appui LFO2. Destinations B : CC 0–127 avec noms usuels. Le code sidecar et autosave working de Test3 conserve les patterns MIDI, LFO B et LFO2 A ; LFO1 A utilise sa sauvegarde native. Six machines natives seulement ; Syntakt, ACID, MACRO, sampler et préécoute absents.',note='Nouveaux bindings et démarrage expérimentaux : boot, routage MIDI, ordonnanceur et sauvegarde simulée vérifiés. Test matériel attendu. Sauvegardez vos projets avant cet essai de persistance. Principal et Test3 inchangés.')}

def generate(cycles,repo,midi_bundle=True):
 prod=ROOT/'docs/flasher'
 tw=catalog.read_js((prod/'tweaks.js').read_text())
 stock=ref_mainos.main_os(cycles);t,blob,s=core.generate(stock,repo)
 keep={'latching-mute','trig-preview','lfo-secondary'}
 tw['tweaks']=[t]+[x for x in tw['tweaks'] if x['id'] in keep]
 tw['features']=[dict(id=t['id'],label=TEXT['en']['label'],cat='pack',status='experimental',variants=[dict(id=t['id'],label=None)],credit=dict(kind='based',who='TinyGregAudio',repo='TinyGregAudio/Model-TG'),license='LICENSE-Model-TG.txt')]+[f for f in tw['features'] if f['id'] in keep]
 if midi_bundle:
  import gen_core_midi_bundle as midi
  bank,chosen,image=midi.generate(stock,repo);pack=midi.flatten(stock,bank,chosen,image)
  tw['tweaks'].insert(1,pack)
  tw['features'].insert(1,dict(id=pack['id'],label='Standalone MIDI performance bundle',cat='pack',status='experimental',variants=[dict(id=pack['id'],label=None)],includes=['performance-core','latching-mute','trig-preview','lfo-secondary'],credit=dict(kind='based',who='TinyGregAudio',repo='TinyGregAudio/Model-TG'),license='LICENSE-Model-TG.txt'))
 compact=copy.deepcopy(tw);compact['tweaks'],compact['shared']=catalog.share(compact['tweaks'])
 files={p.name:p.read_text() for p in prod.iterdir() if p.is_file() and p.suffix in ('.js','.css','.txt','.html') and p.name!='bundle.js'}
 files['tweaks.js']='/* Généré par tools/gen_performance_core_flasher.py. */\nwindow.MC_TWEAKS = '+json.dumps(compact,ensure_ascii=False,indent=1)+';\n'+catalog.HYDRATE
 original=ref_mainos.mc_tweaks;ref_mainos.mc_tweaks=lambda:tw
 try:refs,mods,count=ref_mainos.blocks(cycles,None)
 finally:ref_mainos.mc_tweaks=original
 for name,body in (('REF_MAINOS',refs),('REF_MODS',mods)):
  m=ref_mainos.BLOCKS[name].search(files['app.js']);assert m,name
  files['app.js']=files['app.js'][:m.start(2)]+'\n'+body+files['app.js'][m.end(2):]
 injection='T.en.title="Model:Cycles — Standalone Core Test"; T.fr.title="Model:Cycles — Essai noyau autonome";\nT.en.select_all_note="Selects the complete standalone MIDI bundle; its included features need no extra selections."; T.fr.select_all_note="Sélectionne le pack MIDI autonome complet ; ses fonctions incluses ne demandent aucune sélection supplémentaire.";\n'+'\n'.join('FEAT.'+lang+'["performance-core"] = '+json.dumps(text,ensure_ascii=False)+';' for lang,text in TEXT.items())+'\nGUIDE_OF["performance-core"]="performance-core";\n'
 anchor='function featText('
 # Avant le premier rendu des cartes, après la définition des textes et du guide.
 at=files['app.js'].find(anchor)
 if at<0:
  at=files['app.js'].find('function ft(')
 assert at>=0,'point d’injection des textes'
 if midi_bundle:
  for lang,text in BUNDLE_TEXT.items():injection+='\nFEAT.'+lang+'["performance-midi-core"] = '+json.dumps(text,ensure_ascii=False)+';'
  injection+='\nGUIDE_OF["performance-midi-core"]="performance-midi-core";\n'
 files['app.js']=files['app.js'][:at]+injection+'\n'+files['app.js'][at:]
 files['app.js']=files['app.js'].replace('const GUIDE = "../guide/"','const GUIDE = "guide.html"')
 if midi_bundle:files['app.js']=files['app.js'].replace('["model-tg", "midi-live-both", "scale-gen", "lfo-secondary"].map(featById)', '["performance-midi-core"].map(featById)')
 files['app.js']=files['app.js'].replace('Selects compatible mods, keeping Model-TG and Live MIDI OUT + THRU. Included mods stay part of Model-TG.','Selects the complete standalone MIDI bundle; its included features need no extra selections.').replace('Sélectionne les mods compatibles en conservant Model-TG et MIDI OUT + THRU en direct. Les mods inclus restent dans Model-TG.','Sélectionne le pack MIDI autonome complet ; ses fonctions incluses ne demandent aucune sélection supplémentaire.')
 html=files['index.html']
 html=re.sub(r'<script[^>]+src="[^"]*bundle\.js[^" ]*"[^>]*></script>','',html)
 html=re.sub(r'window.MC_BUILD = "[^"]+"','window.MC_BUILD = "'+STAMP+'"',html)
 html=re.sub(r'\?v=[^"\s<>]+','?v='+STAMP,html)
 html=html.replace('Model:Cycles Flasher</title>','Model:Cycles — Standalone Core Test</title>')
 notice='<div class="alert" id="core-test-notice"><span data-l="en">Experimental standalone core. Choose the MIDI performance bundle for Sequence Genie, SCRAMBLE, MIDI Bank, LFO-to-CC and saving without Model-TG. The smaller core-only selection has no MIDI Bank or saving. Uses stock Cycles machines; extra sound engines are not included. Main and Test3 are unchanged.</span><span data-l="fr">Noyau autonome expérimental. Choisissez le pack MIDI pour Sequence Genie, SCRAMBLE, banque MIDI, LFO CC et sauvegarde sans Model-TG. Le petit noyau seul n’a ni banque MIDI ni sauvegarde. Machines Cycles natives, sans moteurs supplémentaires. Principal et Test3 inchangés.</span></div>'
 files['index.html']=html.replace('<div id="errbar"',notice+'\n<div id="errbar"',1)
 files['guide.html']='<!doctype html><meta charset="utf-8"><title>Standalone core test</title><main>'+''.join('<section id="'+ident+'">'+''.join('<article lang="'+lang+'"><h1>'+text['label']+'</h1><p>'+text['desc']+'</p><p>'+text['note']+'</p></article>' for lang,text in texts.items())+'</section>' for ident,texts in [('performance-core',TEXT)]+([('performance-midi-core',BUNDLE_TEXT)] if midi_bundle else []))+'<p><a href="../guide/">Full guide / Guide complet</a></p></main>\n'
 return files,tw,count

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cycles',required=True);ap.add_argument('--model-tg',required=True);ap.add_argument('--output',default=str(ROOT/'docs/flasher-core-test'));ap.add_argument('--check',action='store_true');ap.add_argument('--midi-bundle',action='store_true',default=True);a=ap.parse_args()
 files,tw,count=generate(a.cycles,a.model_tg,a.midi_bundle);out=pathlib.Path(a.output);out.mkdir(parents=True,exist_ok=True)
 for name,text in files.items():
  text=text.rstrip()+'\n'
  if a.check:assert (out/name).read_text()==text,name
  else:(out/name).write_text(text)
 print('ok : page autonome',len(tw['features']),'cartes,',count,'combinaisons de référence ; aucune page existante écrite')
if __name__=='__main__':main()
