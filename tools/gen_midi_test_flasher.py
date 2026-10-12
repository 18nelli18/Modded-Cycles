#!/usr/bin/env python3
"""Note 57 : installateur fixe Select All + banque MIDI expérimentale.

--cycles OS1.13.syx --syntakt OS1.42.syx --model-tg clone [--check].
Fichiers OS locaux, Web MIDI et transfert rapide ; aucun firmware distribué.
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
STAMP='2026-10-11-midi-bank-tg-first-test'


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
        text='\n'+'\n'.join('  '+json.dumps(k)+': '+json.dumps(v)+',' for k,v in values.items())
        app=app[:m.start(2)]+text+app[m.end(2):]
    a=app.index('function chosenTweaks() {');b=app.index('function chosenLabels()',a)
    app=app[:a]+'''function chosenTweaks() {
  return window.MC_BUNDLE_IDS.map(id => {
    const tweak = window.MC_TWEAKS.tweaks.find(t => t.id === id);
    if (!tweak) throw new Error("Missing bundle mod: " + id);
    return tweak;
  });
}
'''+app[b:]
    a=app.index('function chosenLabels()');b=app.index('// A mod whose engines',a)
    app=app[:a]+app[a:b].replace('return out;','return out.concat(t("bank_label"));')+app[b:]
    app=app.replace('  applyLang(st.lang);\n  update();','  applyLang(st.lang);\n  selectAllCompatible();\n  update();')
    app=re.sub(r'  try \{ st.method = localStorage.getItem\("mc-method"\).*?\n','  st.method = "fast";\n',app,count=1)
    app=app.replace('if (st.sending || (m !== "fast" && m !== "slow")) return;',
                    'if (st.sending || m !== "fast") return;')
    app=app.replace('function init() {',
        'Object.assign(T.en, {title:"MIDI Bank + Model-TG test", tagline:"Select All bundle with MIDI Bank. Hardware verification pending.", bank_label:"MIDI Bank (experimental, RAM only)"});\n'
        'Object.assign(T.fr, {title:"Essai banque MIDI + Model-TG", tagline:"Bundle Tout sélectionner avec banque MIDI. Validation matérielle en attente.", bank_label:"Banque MIDI (expérimentale, RAM seulement)"});\n'
        'function init() {')
    # Le bundle exige toujours les deux fichiers officiels ; aucun passage
    # transparent d'un OS déjà modifié qui pourrait masquer l'absence du mod.
    app=app.replace('    st.os = { raw, name, info, sha, stock };',
        '    if (!stock) throw new Error(st.lang === "fr" ? "Chargez le fichier officiel Model:Cycles OS 1.13." : "Load the official Model:Cycles OS 1.13 file.");\n'
        '    st.os = { raw, name, info, sha, stock };')
    html=(PROD/'index.html').read_text()
    html=re.sub(r'2026-\d\d-\d\d-lfo2-main',STAMP,html)
    html=html.replace('<title>Model:Cycles Flasher</title>','<title>Model:Cycles — MIDI Bank + Model-TG Test</title>')
    for filename in ('style.css','builder.js','flasher.js','tweaks.js'):
        html=html.replace('"'+filename+'?v=','"../flasher/'+filename+'?v=')
    html=html.replace('<script src="app.js?', '<script src="bundle.js?v='+STAMP+'"></script>\n<script src="app.js?')
    css='<style>#step-choose,#advanced,#m-slow,#alt{display:none!important} #midi-bank-notice{margin-block:1.5rem} #midi-bank-notice p:last-child{margin-bottom:0}</style>'
    html=html.replace('</head>',css+'\n</head>')
    notice='''<section class="alert" id="midi-bank-notice">
<h2><span data-l="en">Experimental MIDI Bank — Model-TG retained</span><span data-l="fr">Banque MIDI expérimentale — Model-TG conservé</span></h2>
<p data-l="en">This fixed test includes the compatible Select All mods, Model-TG, LFO 2, Sequence Genie, SCRAMBLE and Live MIDI OUT + THRU. Load your official Cycles and Syntakt OS files below, select the Model:Cycles MIDI port, then use fast transfer.</p>
<p data-l="fr">Cet essai fixe inclut les mods compatibles de Tout sélectionner, Model-TG, LFO 2, Sequence Genie, SCRAMBLE et MIDI OUT + THRU en direct. Chargez vos OS officiels Cycles et Syntakt ci-dessous, choisissez le port MIDI Model:Cycles puis le transfert rapide.</p>
<p data-l="en"><b>FUNC + SETTINGS + PAGE</b> switches pads 1–6 to the MIDI Bank; repeat to return to the audio tracks. Channels are fixed at 7–12. Trig keys toggle steps; PAGE moves through four pages. DATA chooses a row; click, turn to edit, then click to finish. FUNC + pad toggles that lane’s MIDI OUT. Both banks play independently; PLAY/STOP remains available. Stop playback before first opening the bank after boot.</p>
<p data-l="fr"><b>FUNC + SETTINGS + PAGE</b> bascule les pads 1–6 vers la banque MIDI ; répétez pour revenir aux pistes audio. Canaux fixes 7–12. Les trigs activent les pas ; PAGE parcourt quatre pages. DATA choisit une ligne ; clic, rotation pour éditer, puis clic pour terminer. FUNC + pad bascule MIDI OUT pour cette voie. Les deux banques jouent indépendamment ; PLAY/STOP reste disponible. Arrêtez la lecture avant la première ouverture après démarrage.</p>
<p data-l="en"><b>RAM only:</b> one MIDI Bank shared across pattern changes. Page changes retain it; restart clears it. Pattern/project saving is unfinished. MIDI Bank has passed emulation checks; this combined firmware still needs your hardware test.</p>
<p data-l="fr"><b>RAM seulement :</b> une banque MIDI commune aux changements de pattern. Elle reste entre les pages mais disparaît au redémarrage. Sauvegarde pattern/projet inachevée. Banque MIDI vérifiée en émulation ; ce firmware combiné attend encore votre essai matériel.</p>
</section>'''
    html=html.replace('<div id="errbar"',notice+'\n<div id="errbar"',1)
    for old,new in (('2','1'),('3','2'),('4','3')):
        html=html.replace('<span class="num">'+old+'</span>','<span class="num">'+new+'</span>')
    bundle='/* Généré par tools/gen_midi_test_flasher.py ; aucune image firmware. */\n'
    bundle+='window.MC_BUNDLE_IDS = '+json.dumps(ids)+';\n'
    bundle+='window.MC_TWEAKS.tweaks.push('+json.dumps(tweak,ensure_ascii=False,indent=1)+');\n'
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
    print('ok : installateur fixe MIDI Bank + Select All TG, fichiers OS/MIDI/transfert rapide, état expérimental et limites RAM visibles')


if __name__=='__main__':main()
