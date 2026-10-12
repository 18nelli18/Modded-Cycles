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
STAMP='2026-10-11-midi-bank-trig-leds'


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
    texts={
      'en': {'label':'MIDI OUT Bank','short':'Six MIDI-only lanes on channels 7–12. Experimental; RAM only.',
             'desc':'FUNC + SETTINGS + PAGE switches between the audio tracks and six independent MIDI-only lanes on channels 7–12. FUNC + pad toggles the lane MIDI OUT. Tap a trig to add/remove it; hold a trig and turn DATA to choose its note. Several held trigs transpose together. The main display shows the note on the left and Vol (note velocity) in the middle. DATA selects a step when no trig is held; click DATA for settings and EXIT to return. PAGE changes step page. The trig lights show the MIDI lane steps and its playback position; returning to audio restores the audio-track lights. Stop playback before first opening after boot. This experimental version uses one RAM bank shared across patterns, lost on restart; pattern/project saving is unfinished. Selecting this mod selects its validated compatible Select All bundle with Model-TG, Live MIDI OUT + THRU, LFO 2, queued Sequence Generator and SCRAMBLE. If you change its required mods, uncheck MIDI OUT Bank or use Select all again. This editing update awaits hardware verification.'},
      'fr': {'label':'Banque MIDI OUT','short':'Six voies MIDI seules sur les canaux 7–12. Expérimental ; RAM seulement.',
             'desc':'FUNC + SETTINGS + PAGE bascule entre les pistes audio et six voies MIDI indépendantes sur les canaux 7–12. FUNC + pad bascule MIDI OUT de la voie. Appuyez brièvement sur un trig pour ajouter/retirer le pas ; maintenez-le et tournez DATA pour choisir sa note. Plusieurs trigs tenus sont transposés ensemble. La vue principale affiche la note à gauche et Vol (vélocité) au centre. DATA sélectionne un pas sans trig tenu ; cliquez DATA pour les réglages, EXIT pour revenir. PAGE change la page. Les LED affichent les pas MIDI et leur position de lecture ; revenir aux pistes audio rétablit leurs LED. Arrêtez la lecture avant la première ouverture après démarrage. Une banque RAM partagée entre patterns, perdue au redémarrage ; sauvegarde pattern/projet inachevée. Ce mod sélectionne son bundle Tout sélectionner compatible validé avec Model-TG, MIDI OUT + THRU en direct, LFO 2, génération différée et SCRAMBLE. Si vous modifiez ses mods requis, décochez la banque MIDI OUT ou cliquez de nouveau sur Tout sélectionner. Cette nouvelle édition attend une validation matérielle.'}}
    html=(PROD/'index.html').read_text()
    html=re.sub(r'2026-\d\d-\d\d-lfo2-main',STAMP,html)
    for filename in ('style.css','builder.js','flasher.js','tweaks.js','app.js'):
        html=html.replace('"'+filename+'?v=','"../flasher/'+filename+'?v=')
    # Le script principal exporte les références avant DOMContentLoaded ;
    # l'extension ajoute seulement carte/recette/références avant init.
    html=html.replace('</body>', '<script src="bundle.js?v='+STAMP+'"></script>\n</body>')
    bundle='/* Généré par tools/gen_midi_test_flasher.py ; aucune image firmware. */\n'
    bundle+='window.MC_BUNDLE_IDS = '+json.dumps(ids)+';\n'
    bundle+='window.MC_TWEAKS.tweaks.push('+json.dumps(tweak,ensure_ascii=False,indent=1)+');\n'
    feature={'id':'midi-bank-bundle','cat':'seq','status':'experimental','label':'MIDI OUT Bank',
             'desc':texts['fr']['desc'],'requires':'model-tg',
             'credit':{'kind':'based','who':'TinyGregAudio','repo':'TinyGregAudio/Model-TG'},
             'license':'LICENSE-Model-TG','variants':[{'id':tweak['id'],'label':None}]}
    bundle+='const bankTexts = '+json.dumps(texts,ensure_ascii=False)+';\n'
    bundle+='const bankFeature = '+json.dumps(feature,ensure_ascii=False)+';\n'
    bundle+='''for (const key of ["label", "desc"]) Object.defineProperty(bankFeature, key, {
  get: () => (bankTexts[document.documentElement.lang] || bankTexts.en)[key], configurable: true
});
window.MC_TWEAKS.features.push(bankFeature);
'''
    bundle+='Object.assign(window.MCFlasherApp.REF_MODS, '+json.dumps({tweak['id']:mods[tweak['id']]})+');\n'
    bundle+='Object.assign(window.MCFlasherApp.REF_MAINOS, '+json.dumps({key:hashlib.sha256(image).hexdigest()})+');\n'
    bundle+='''// Utiliser le vrai bouton Select all avant de cocher la carte.
document.addEventListener("change", event => {
  if (event.target.id === "feat-midi-bank-bundle" && event.target.checked) {
    document.getElementById("select-all").click();
  }
}, true);
'''
    return {'index.html':html,'bundle.js':bundle}



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
