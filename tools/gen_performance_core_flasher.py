#!/usr/bin/env python3
"""Note65 : première page isolée du noyau performance sans sampler Model-TG.

--cycles OS1.13.syx --model-tg CLONE [--output DIR] [--check]. Les pages
principale et Test3 ne sont jamais écrites. Catalogue limité à la preuve du noyau.
"""
import argparse,copy,json,pathlib,re
import build,gen_flasher_tweaks as catalog,gen_performance_core as core,ref_mainos
ROOT=pathlib.Path(__file__).resolve().parents[1]
STAMP='2026-10-12-performance-core-test'
TEXT={
'en':dict(label='Slide trigs + Scale Lock — standalone core',short='Retained Model-TG performance features, without its sampler.',desc='Hold SETTINGS and press a trig to toggle its slide. Scale Lock is available in the keyboard setup menu. This extracted core contains no sampler, master effects or extra Model-TG menus. Latching mute and trig preview are separate selections below. Sequence Genie, SCRAMBLE and MIDI Bank are not connected to this core yet; use the existing flasher for those features.',note='Experimental extraction: boot, scale mapping and six-machine audio verified in emulation. Awaiting hardware testing.'),
'fr':dict(label='Slides + Scale Lock — noyau autonome',short='Fonctions performance de Model-TG, sans son sampler.',desc='Maintenez SETTINGS et appuyez sur un trig pour basculer son slide. Scale Lock est disponible dans la configuration du clavier. Ce noyau extrait ne contient ni sampler, ni effets master, ni menus supplémentaires Model-TG. Mute verrouillé et écoute de pas restent deux sélections séparées ci-dessous. Sequence Genie, SCRAMBLE et banque MIDI ne sont pas encore reliés à ce noyau ; utilisez le flasher existant pour ces fonctions.',note='Extraction expérimentale : démarrage, gammes et audio des six machines vérifiés en émulation. Essai matériel attendu.')}

def generate(cycles,repo):
 prod=ROOT/'docs/flasher'
 tw=catalog.read_js((prod/'tweaks.js').read_text())
 stock=ref_mainos.main_os(cycles);t,blob,s=core.generate(stock,repo)
 keep={'latching-mute','trig-preview','lfo-secondary'}
 tw['tweaks']=[t]+[x for x in tw['tweaks'] if x['id'] in keep]
 tw['features']=[dict(id=t['id'],label=TEXT['en']['label'],cat='pack',status='experimental',variants=[dict(id=t['id'],label=None)],credit=dict(kind='based',who='TinyGregAudio',repo='TinyGregAudio/Model-TG'),license='LICENSE-Model-TG.txt')]+[f for f in tw['features'] if f['id'] in keep]
 compact=copy.deepcopy(tw);compact['tweaks'],compact['shared']=catalog.share(compact['tweaks'])
 files={p.name:p.read_text() for p in prod.iterdir() if p.is_file() and p.suffix in ('.js','.css','.txt','.html') and p.name!='bundle.js'}
 files['tweaks.js']='/* Généré par tools/gen_performance_core_flasher.py. */\nwindow.MC_TWEAKS = '+json.dumps(compact,ensure_ascii=False,indent=1)+';\n'+catalog.HYDRATE
 original=ref_mainos.mc_tweaks;ref_mainos.mc_tweaks=lambda:tw
 try:refs,mods,count=ref_mainos.blocks(cycles,None)
 finally:ref_mainos.mc_tweaks=original
 for name,body in (('REF_MAINOS',refs),('REF_MODS',mods)):
  m=ref_mainos.BLOCKS[name].search(files['app.js']);assert m,name
  files['app.js']=files['app.js'][:m.start(2)]+'\n'+body+files['app.js'][m.end(2):]
 injection='T.en.title="Model:Cycles — Standalone Core Test"; T.fr.title="Model:Cycles — Essai noyau autonome";\nT.en.select_all_note="Selects all four options on this standalone core test page."; T.fr.select_all_note="Sélectionne les quatre options de cet essai du noyau autonome.";\n'+'\n'.join('FEAT.'+lang+'["performance-core"] = '+json.dumps(text,ensure_ascii=False)+';' for lang,text in TEXT.items())+'\nGUIDE_OF["performance-core"]="performance-core";\n'
 anchor='function featText('
 # Avant le premier rendu des cartes, après la définition des textes et du guide.
 at=files['app.js'].find(anchor)
 if at<0:
  at=files['app.js'].find('function ft(')
 assert at>=0,'point d’injection des textes'
 files['app.js']=files['app.js'][:at]+injection+'\n'+files['app.js'][at:]
 files['app.js']=files['app.js'].replace('const GUIDE = "../guide/"','const GUIDE = "guide.html"')
 html=files['index.html']
 html=re.sub(r'<script[^>]+src="[^"]*bundle\.js[^" ]*"[^>]*></script>','',html)
 html=re.sub(r'window.MC_BUILD = "[^"]+"','window.MC_BUILD = "'+STAMP+'"',html)
 html=re.sub(r'\?v=[^"\s<>]+','?v='+STAMP,html)
 html=html.replace('Model:Cycles Flasher</title>','Model:Cycles — Standalone Core Test</title>')
 notice='<div class="alert" id="core-test-notice"><span data-l="en">Standalone performance core test. No Model-TG sampler. Main and Test3 are unchanged. Sequence Genie, SCRAMBLE, MIDI Bank and their saving are not included in this first extraction test. LFO2 settings remain in RAM.</span><span data-l="fr">Essai du noyau performance autonome, sans sampler Model-TG. Principal et Test3 inchangés. Sequence Genie, SCRAMBLE, banque MIDI et leur sauvegarde sont absents de ce premier essai d’extraction. LFO2 conserve ses réglages en RAM.</span></div>'
 files['index.html']=html.replace('<div id="errbar"',notice+'\n<div id="errbar"',1)
 files['guide.html']='<!doctype html><meta charset="utf-8"><title>Standalone core test</title><main id="performance-core">'+''.join('<section lang="'+lang+'"><h1>'+text['label']+'</h1><p>'+text['desc']+'</p><p>'+text['note']+'</p></section>' for lang,text in TEXT.items())+'<p><a href="../guide/">Full guide / Guide complet</a></p></main>\n'
 return files,tw,count

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cycles',required=True);ap.add_argument('--model-tg',required=True);ap.add_argument('--output',default=str(ROOT/'docs/flasher-core-test'));ap.add_argument('--check',action='store_true');a=ap.parse_args()
 files,tw,count=generate(a.cycles,a.model_tg);out=pathlib.Path(a.output);out.mkdir(parents=True,exist_ok=True)
 for name,text in files.items():
  text=text.rstrip()+'\n'
  if a.check:assert (out/name).read_text()==text,name
  else:(out/name).write_text(text)
 print('ok : page autonome',len(tw['features']),'cartes,',count,'combinaisons de référence ; aucune page existante écrite')
if __name__=='__main__':main()
