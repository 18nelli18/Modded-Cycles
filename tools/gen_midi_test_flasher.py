#!/usr/bin/env python3
"""Note 57 : installateur sélectionnable Select All + banque MIDI expérimentale.

--cycles OS1.13.syx --syntakt OS1.42.syx --model-tg clone [--check].
Fichiers OS locaux, Web MIDI, transferts rapide/classique ; aucun firmware distribué.
"""
import argparse
import hashlib
import json
import pathlib
import re
import build
import gen_midi_bank_bundle as bank
import ref_mainos

ROOT=pathlib.Path(__file__).resolve().parents[1]
PROD=ROOT/'docs/flasher'
OUT=ROOT/'docs/flasher-midi-test'
STAMP='2026-10-11-midi-bank-main-flasher'


def files_for(tweak,chosen,image):
    ids=[*bank.IDS,tweak['id']];key='+'.join(ids)
    tweaks=chosen+[tweak]
    mods={}
    apps=sorted((t for t in tweaks if t.get('append')),key=lambda t:t['order'])
    for t in tweaks:
        item={'w':hashlib.sha256(ref_mainos.writes_bytes(t)).hexdigest()}
        if t.get('append'):
            n=apps.index(t);lo=int(t['append']['at'],16)-build.BASE
            hi=int(apps[n+1]['append']['at'],16)-build.BASE if n+1<len(apps) else len(image)
            item['p']=hashlib.sha256(image[lo:hi]).hexdigest()
        mods[t['id']]=item
    app=(PROD/'app.js').read_text()
    for name,values in (('REF_MODS',mods),('REF_MAINOS',{key:hashlib.sha256(image).hexdigest()})):
        m=ref_mainos.BLOCKS[name].search(app);assert m,name
        text=m.group(2).rstrip()+'\n'+'\n'.join('  '+json.dumps(k)+': '+json.dumps(v)+',' for k,v in values.items())
        app=app[:m.start(2)]+text+app[m.end(2):]
    # Seule extension de la logique principale : la carte banque MIDI et
    # sa sélection du bundle compatible. Aucun changement de transport.
    app=app.replace('function chosenTweaks() {','function baseChosenTweaks() {',1)
    a=app.index('function chosenLabels()')
    app=app[:a]+'''function chosenTweaks() {
  const out = baseChosenTweaks();
  if (!isOn("midi-bank-bundle")) return out;
  const base = out.filter(t => t.id !== "midi-bank-bundle");
  if (base.map(t => t.id).join("+") !== window.MC_BUNDLE_IDS.slice(0,-1).join("+")) {
    selOf(featById("midi-bank-bundle")).on = false;
    renderFeatures();
    return base;
  }
  return out;
}
'''+app[a:]
    app=app.replace('function setOn(f, on) {','''function setOn(f, on) {
  if (f.id === "midi-bank-bundle" && on) {
    selectAllCompatible();
    return;
  }''',1)
    app=app.replace('if (preferred.includes(f) || includedBy(f)) continue;',
                    'if (f.id === "midi-bank-bundle" || preferred.includes(f) || includedBy(f)) continue;',1)
    app=app.replace('  const generator = featById("scale-gen");',
                    '  selOf(featById("midi-bank-bundle")).on = true;\n  const generator = featById("scale-gen");',1)
    texts={
      'en': {'label':'MIDI OUT Bank','short':'Six MIDI-only lanes on channels 7–12. Experimental; RAM only.',
             'desc':'FUNC + SETTINGS + PAGE switches between the audio tracks and six independent MIDI-only lanes on channels 7–12. FUNC + pad toggles the lane MIDI OUT. Trigs edit steps; PAGE changes step page; DATA chooses a setting, click to edit. Stop playback before first opening after boot. This experimental version uses one RAM bank shared across patterns, lost on restart; pattern/project saving is unfinished. Selecting this mod selects its validated compatible Select All bundle with Model-TG, Live MIDI OUT + THRU, LFO 2, queued Sequence Generator and SCRAMBLE. Changing that combination removes MIDI OUT Bank. Hardware verification is pending.'},
      'fr': {'label':'Banque MIDI OUT','short':'Six voies MIDI seules sur les canaux 7–12. Expérimental ; RAM seulement.',
             'desc':'FUNC + SETTINGS + PAGE bascule entre les pistes audio et six voies MIDI indépendantes sur les canaux 7–12. FUNC + pad bascule MIDI OUT de la voie. Les trigs éditent les pas ; PAGE change la page ; DATA choisit un réglage, clic pour éditer. Arrêtez la lecture avant la première ouverture après démarrage. Une banque RAM partagée entre patterns, perdue au redémarrage ; sauvegarde pattern/projet inachevée. Ce mod sélectionne son bundle Tout sélectionner compatible validé avec Model-TG, MIDI OUT + THRU en direct, LFO 2, génération différée et SCRAMBLE. Modifier la combinaison retire la banque MIDI OUT. Validation matérielle en attente.'}}
    extra='\n'.join('FEAT.'+lang+'["midi-bank-bundle"] = '+json.dumps(value,ensure_ascii=False)+';' for lang,value in texts.items())
    app=app.replace('function init() {',extra+'\nfunction init() {',1)
    html=(PROD/'index.html').read_text()
    html=re.sub(r'2026-\d\d-\d\d-lfo2-main',STAMP,html)
    for filename in ('style.css','builder.js','flasher.js','tweaks.js'):
        html=html.replace('"'+filename+'?v=','"../flasher/'+filename+'?v=')
    html=html.replace('<script src="app.js?', '<script src="bundle.js?v='+STAMP+'"></script>\n<script src="app.js?')
    bundle='/* Généré par tools/gen_midi_test_flasher.py ; aucune image firmware. */\n'
    bundle+='window.MC_BUNDLE_IDS = '+json.dumps(ids)+';\n'
    bundle+='window.MC_TWEAKS.tweaks.push('+json.dumps(tweak,ensure_ascii=False,indent=1)+');\n'
    feature={'id':'midi-bank-bundle','cat':'seq','status':'experimental','label':'MIDI OUT Bank',
             'desc':texts['fr']['desc'],'requires':'model-tg',
             'credit':{'kind':'based','who':'TinyGregAudio','repo':'TinyGregAudio/Model-TG'},
             'license':'LICENSE-Model-TG','variants':[{'id':tweak['id'],'label':None}]}
    bundle+='window.MC_TWEAKS.features.push('+json.dumps(feature,ensure_ascii=False)+');\n'
    return {'index.html':html,'app.js':app,'bundle.js':bundle}



def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--cycles',required=True);ap.add_argument('--syntakt',required=True)
    ap.add_argument('--model-tg',required=True);ap.add_argument('--cross',default='m68k-elf-')
    ap.add_argument('--check',action='store_true');args=ap.parse_args()
    tweak,chosen,image=bank.generate(bank.main_os_from_syx(args.cycles),args.syntakt,args.model_tg,args.cross)
    assert bank.OUT.read_text()==json.dumps(tweak,indent=1,ensure_ascii=False)+'\n','régénérer le tweak candidat'
    OUT.mkdir(parents=True,exist_ok=True)
    for name,body in files_for(tweak,chosen,image).items():
        body=body.rstrip()+'\n'
        if args.check:assert (OUT/name).read_text()==body,OUT/name
        else:(OUT/name).write_text(body)
    print('ok : installateur sélectionnable MIDI Bank + Select All TG, fichiers OS/MIDI/transferts, état expérimental et limites RAM visibles')


if __name__=='__main__':main()
