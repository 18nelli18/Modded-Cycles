#!/usr/bin/env python3
"""Test3 MBK2 : notes, locks et deux LFO MIDI par pattern ; moteurs configurables.

Construire depuis les deux OS officiels ; aucun firmware distribué.
--base-page DIR --output-dir DIR --cycles SYX --syntakt SYX --model-tg DIR
"""
import argparse,pathlib,json,hashlib,re,html,shutil
import build,gen_midi_bank_bundle as bank,ref_mainos
from gen_midi_retrigger_test import replace_json
STAMP='2026-10-12-test-3-pattern-saving'
EN=('Experimental B-side pattern saving. MACRO is excluded; ACID and Model-TG remain included. '
    'Use a project saved to a normal project slot, and reload it after installing this build. '
    'Use the normal Save Project command to save all visited B-side patterns. MIDI SAVED confirms '
    'the extra save; MIDI SAVE ERR means it failed even if the audio project saved. '
    'Notes, velocity, length, routing, chance/retrigger/arp locks and both MIDI LFO configurations '
    'are stored per pattern and restored when that project loads or the device restarts. '
    'MIDI LOAD ERR leaves B-side playback/editing suspended; reload a known saved project. '
    'Missing records start empty; corrupted records are refused. Save As with a changed project '
    'identity is not supported yet: reload the destination project before editing its B-side. '
    'Audio-side LFO2 saving is not included. Extra MIDI records live in a separate ModdedCycles '
    'directory and are not part of a normal Elektron project backup or project SysEx export. '
    'This storage path has passed emulation with a simulated filesystem and needs hardware testing. '
    'FUNC + SETTINGS + TRACK enters B-side; SETTINGS + PAGE opens Sequence Genie; FUNC + PAGE opens '
    'Scale Setup. Hold a trig + RECORD to copy, or + STOP to paste, with stock COPY/PASTE popups. '
    '6-channel USB audio is optional.')
FR=('Sauvegarde expérimentale des patterns B. MACRO exclu ; ACID et Model-TG conservés. '
    'Utilisez un projet enregistré dans un slot normal et rechargez-le après installation. '
    'Save Project sauvegarde les patterns B visités. MIDI SAVED confirme cette sauvegarde ; '
    'MIDI SAVE ERR indique un échec même si le projet audio est sauvegardé. Notes, vélocité, '
    'longueur, routage, locks chance/retrigger/arp et les deux configurations LFO MIDI sont '
    'conservés par pattern et restaurés au chargement du projet ou au redémarrage. '
    'MIDI LOAD ERR suspend lecture/édition B : rechargez un projet sauvegardé connu. '
    'Les fichiers absents donnent des voies vides ; les fichiers corrompus sont refusés. '
    'Save As avec nouvelle identité de projet reste non géré : rechargez la destination avant '
    'édition B. La sauvegarde du LFO2 audio reste absente. Les fichiers MIDI annexes sont dans '
    'un dossier ModdedCycles séparé, hors backup projet Elektron ou export SysEx normal. '
    'Chaîne validée en émulation avec filesystem simulé, matériel à tester. '
    'FUNC + SETTINGS + TRACK ouvre B ; SETTINGS + PAGE ouvre Sequence Genie ; FUNC + PAGE ouvre '
    'Scale Setup. TRIG + RECORD copie, TRIG + STOP colle avec popups natifs COPY/PASTE. USB6 facultatif.')

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 for name in ('base-page','output-dir','cycles','syntakt','model-tg'):ap.add_argument('--'+name,required=True)
 ap.add_argument('--engines',choices=('both','acid','macro'),default='both');ap.add_argument('--cross',default='m68k-elf-');a=ap.parse_args();base=pathlib.Path(a.base_page);out=pathlib.Path(a.output_dir)
 if a.engines!='both':
  bank.IDS=tuple(x.replace('syntakt-tg-sd-cp-toy-bits-swarm-macro-acid','syntakt-tg-sd-cp-toy-bits-swarm-'+a.engines) for x in bank.IDS)
 excluded=[] if a.engines=='both' else ['macro' if a.engines=='acid' else 'acid']
 en=EN.replace('MACRO is excluded; ACID and Model-TG remain included.', 'ACID, MACRO and Model-TG remain included.' if not excluded else 'Choose ACID or MACRO when space requires it; this candidate includes '+a.engines.upper()+' and Model-TG.')
 fr=FR.replace('MACRO exclu ; ACID et Model-TG conservés.', 'ACID, MACRO et Model-TG conservés.' if not excluded else 'Choix ACID ou MACRO selon place disponible ; candidat '+a.engines.upper()+' avec Model-TG.')
 # Compression sans octets firmware embarqués ; reconstruite depuis l'OS fourni.
 original_catalog=build.load_catalog
 def saving_catalog():
  catalog=original_catalog()
  for tweak in catalog['model-cycles_OS1.13'][1].values():
   if tweak['id'].startswith('syntakt-tg-sd-cp-toy-bits-swarm'):
    tweak['append']['compress_depth']=32
  return catalog
 build.load_catalog=saving_catalog
 stock=bank.main_os_from_syx(a.cycles)
 tweak,chosen,image=bank.generate(stock,a.syntakt,a.model_tg,a.cross,True,True,True,8,True,True,True,True,True)
 tweak['requires']=[x for x in tweak['requires'] if x!='6ch-usbup'];tweak['status']='experimental'
 tweak['name']='Banque MIDI OUT — sauvegarde MBK2 expérimentale'
 tweak['description']=[fr]
 without=[t for t in chosen if t['id']!='6ch-usbup'];alternate,_=build.apply_writes(stock,without+[tweak]);alternate+=image[len(stock):]
 refs={'+'.join([name for name in bank.IDS if name in {t['id'] for t in ts}]+[tweak['id']]):hashlib.sha256(img).hexdigest() for ts,img in ((chosen,image),(without,alternate))}
 mod={'w':hashlib.sha256(ref_mainos.writes_bytes(tweak)).hexdigest(),'p':hashlib.sha256(image[int(tweak['append']['at'],16)-build.BASE:]).hexdigest()}
 engine=next(t for t in chosen if t['id'].startswith('syntakt-tg-sd-cp-toy-bits-swarm'))
 import syntakt
 engine_ref={'w':hashlib.sha256(ref_mainos.writes_bytes(engine)).hexdigest(),'p':hashlib.sha256(build.payload_image(engine,build.payload_runtime(engine,stock,syntakt.dsp_image(a.syntakt)))).hexdigest()}
 bundle=(base/'bundle.js').read_text();bundle+='\nwindow.MC_TWEAKS.tweaks.find(t=>t.id==='+json.dumps(engine['id'])+').append.compress_depth=32;\n';bundle=replace_json(bundle,'window.MC_BUNDLE_IDS = ',list(bank.IDS)+[tweak['id']])
 bundle=replace_json(bundle,'window.MC_TWEAKS.tweaks.push(',tweak)
 bundle=replace_json(bundle,'const bankTexts = ',{'en':{'label':'MIDI OUT Bank — Pattern Saving Test','short':'Saves notes, locks and MIDI LFO settings by pattern. Experimental.','desc':en},'fr':{'label':'Banque MIDI OUT — test sauvegarde','short':'Notes, locks et LFO MIDI sauvegardés par pattern. Expérimental.','desc':fr}})
 start=bundle.index('const bankFeature = ')+len('const bankFeature = ');feature,_=json.JSONDecoder().raw_decode(bundle[start:]);feature.update(status='experimental',excludes=excluded,desc=fr)
 bundle=replace_json(bundle,'const bankFeature = ',feature)
 bundle=replace_json(bundle,'Object.assign(window.MCFlasherApp.REF_MODS, ',{tweak['id']:mod,engine['id']:engine_ref});bundle=replace_json(bundle,'Object.assign(window.MCFlasherApp.REF_MAINOS, ',refs)
 page=(base/'index.html').read_text();page=re.sub(r'window.MC_BUILD\s*=\s*[^;]+;','window.MC_BUILD = '+json.dumps(STAMP)+';',page);page=re.sub(r'(bundle\.js|builder\.js)\?v=[^"\s<]+',lambda m:m.group(1)+'?v='+STAMP,page)
 out.mkdir(parents=True,exist_ok=True)
 for name in ('builder.js','app.js','tweaks.js','flasher.js','style.css'):shutil.copyfile(base/name,out/name)
 builder=(out/'builder.js').read_text();dense=pathlib.Path(__file__).with_name('aplib_dense.js').read_text();builder=builder.replace('function aplibPack(data) {',dense+'\nfunction aplibPack(data) {').replace('return aplibPack(out);','return ap.compress_depth ? aplibDensePack(out, ap.compress_depth) : aplibPack(out);');(out/'builder.js').write_text(builder)
 (out/'index.html').write_text(page);(out/'bundle.js').write_text(bundle)
 (out/'ABOUT.md').write_text('# '+STAMP+'\n\n'+en+'\n\n'+fr+'\n')
 guide=(base/'guide.html').read_text();guide=re.sub(r'<section id="midi-retrigger-test">.*?</section>','',guide,flags=re.S);guide=guide.replace('</main>','<section id="midi-pattern-saving"><h2>Pattern Saving Test</h2><p data-l="en">'+html.escape(en)+'</p><p data-l="fr">'+html.escape(fr)+'</p></section>\n</main>');(out/'guide.html').write_text(guide)
 (out/'source').mkdir(exist_ok=True);(out/'source/midi-storage.json').write_text(json.dumps(tweak,indent=1,ensure_ascii=False)+'\n')
 print('ok : candidat MBK2, moteurs '+a.engines+', marge',build.END_LIMIT-build.BASE-len(image));print(refs)
if __name__=='__main__':main()
