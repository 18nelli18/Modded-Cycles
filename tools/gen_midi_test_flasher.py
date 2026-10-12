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
OUT=ROOT/'docs/flasher-midi-controls-test'
STAMP='2026-10-12-midi-bank-genie-overlay-fix'


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
      'en': {'label':'MIDI OUT Bank — controls test',
             'short':'B-side Sequence Genie, queued Generate/Undo and readable TR10–TR12. Experimental; RAM only.',
             'desc':'FUNC + SETTINGS + TRACK enters or leaves the B-side. Pads select lanes TR7–TR12 on MIDI channels 7–12; FUNC + pad toggles lane MIDI OUT. With REC enabled, tap a trig to add or remove a step, or hold it and turn DATA to choose its note. With REC disabled, trigs play the Model-TG scale/key keyboard. SETTINGS + trig toggles slide: the next note overlaps the previous note for synth legato. PAGE visits only pages within the lane length. FUNC + PAGE opens stock-style Scale Setup with all lane settings; DATA chooses a step outside that menu. Selected pads light and sequenced notes pulse their pads. TEMPO, REC and LFO keys are forwarded to their native handlers; complete behavior needs hardware verification. Stop playback before first opening after boot. Sequences follow active pattern changes in RAM and are lost on restart. Saving, project isolation and B-side LFO-to-CC routing remain unfinished. Use one project and restart before changing projects. This experimental build includes the compatible Select All bundle with Model-TG and Syntakt engines. The earlier controls were hardware tested on 12 October 2026, followed by a FUNC + pad routing bug report. The FUNC + pad MIDI mute fix was hardware tested. This new candidate restores FUNC + SETTINGS + TRACK exit and fits TR10–TR12 with a compact stock font. In B-side, SETTINGS + PAGE opens Sequence Genie for the selected MIDI lane: Generate and Undo apply immediately when stopped, or at the next loop of that lane during playback. Undo cancels a pending request. Editing the lane before the boundary cancels generation; switching patterns cancels pending changes. Scale/key, note range, density, velocity ranges, rhythm/notes target, mutation and Euclidean rhythm apply to MIDI notes. Decay and pan options affect audio lanes only. These additions need hardware testing; saving remains unfinished.'},
      'fr': {'label':'Banque MIDI OUT — test commandes',
             'short':'Sequence Genie côté B, Generate/Undo différés et TR10–TR12 lisibles. Expérimental ; RAM seulement.',
             'desc':'FUNC + SETTINGS + TRACK ouvre ou ferme la face B. Les pads sélectionnent TR7–TR12 sur les canaux MIDI 7–12 ; FUNC + pad bascule MIDI OUT. REC actif : appuyez sur un trig pour ajouter ou retirer un pas, ou maintenez-le et tournez DATA pour choisir sa note. REC inactif : les trigs jouent le clavier selon gamme et tonalité Model-TG. SETTINGS + trig bascule le slide : la note suivante chevauche la précédente pour le legato du synthé. PAGE visite seulement les pages de la longueur de voie. FUNC + PAGE ouvre Scale Setup de style stock avec tous les réglages de voie ; DATA choisit un pas hors menu. Le pad sélectionné est allumé et les notes séquencées font pulser les pads. TEMPO, REC et LFO sont transmis aux handlers natifs ; leur comportement complet reste à vérifier sur matériel. Arrêtez la lecture avant la première ouverture après démarrage. Les séquences suivent le pattern actif en RAM et disparaissent au redémarrage. Sauvegarde, isolation des projets et routage LFO vers CC restent inachevés. Utilisez un seul projet et redémarrez avant de changer de projet. Ce test inclut le bundle Tout sélectionner compatible avec Model-TG et les moteurs Syntakt. Les commandes précédentes ont été testées sur matériel le 12 octobre 2026, puis un défaut de routage FUNC + pad a été signalé. La correction FUNC + pad MIDI a été testée sur matériel. Ce nouveau candidat rétablit la sortie FUNC + SETTINGS + TRACK et affiche TR10–TR12 avec une police stock compacte. Côté B, SETTINGS + PAGE ouvre Sequence Genie pour la voie MIDI sélectionnée : Generate et Undo s’appliquent immédiatement à l’arrêt, ou au prochain tour de cette voie en lecture. Undo annule une demande en attente. Une édition de la voie ou un changement de pattern annule la demande. Gamme/tonalité, plage de notes, densité, plage de vélocité, cible rythme/notes, mutation et Euclide concernent les notes MIDI. Decay et pan concernent uniquement les pistes audio. Ces ajouts restent à tester sur matériel ; sauvegarde inachevée.'}}
    html=(PROD/'index.html').read_text()
    html=re.sub(r'<script src="../flasher-midi-test/bundle\.js[^"]*"></script>\n?', '', html)
    html=re.sub(r'2026-\d\d-\d\d-(?:lfo2-main|midi-bank-(?:tested-)?main|sequence-queue-included)',STAMP,html)
    for filename in ('style.css','builder.js','flasher.js','tweaks.js','app.js'):
        html=html.replace('"'+filename+'?v=','"../flasher/'+filename+'?v=')
    html=re.sub(r'window.MC_BUILD\s*=\s*[^;]+;', 'window.MC_BUILD = '+json.dumps(STAMP)+';', html)
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
    return {'index.html':html,'bundle.js':bundle,
            **{name:(PROD/name).read_text() for name in ('LICENSE-Model-TG.txt','LICENSE-Braids.txt')}}



def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--cycles',required=True);ap.add_argument('--syntakt',required=True)
    ap.add_argument('--model-tg',required=True);ap.add_argument('--cross',default='m68k-elf-')
    ap.add_argument('--check',action='store_true');args=ap.parse_args()
    tweak,chosen,image=bank.generate(bank.main_os_from_syx(args.cycles),args.syntakt,args.model_tg,args.cross,True,True)
    assert bank.OUT.read_text()==json.dumps(tweak,indent=1,ensure_ascii=False)+'\n','régénérer le tweak candidat'
    OUT.mkdir(parents=True,exist_ok=True)
    for name,body in files_for(tweak,chosen,image).items():
        body=body.rstrip()+'\n'
        if args.check:assert (OUT/name).read_text()==body,OUT/name
        else:(OUT/name).write_text(body)
    print('ok : installateur sélectionnable MIDI Bank + Select All TG, fichiers OS/MIDI/transferts, état expérimental et limites RAM visibles')


if __name__=='__main__':main()
