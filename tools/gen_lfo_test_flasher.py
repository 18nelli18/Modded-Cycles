#!/usr/bin/env python3
"""Note 58 : flasher LFO 2 autonome, catalogue principal testé conservé.

Première validation matérielle des contrôles/audio ; réglages RAM uniquement.
--cycles OS1.13.syx --syntakt OS1.42.syx [--check]. Aucun firmware distribué.
"""
import argparse
import copy
import json
import pathlib
import re
import build
import gen_flasher_tweaks as catalog
import ref_mainos

ROOT=pathlib.Path(__file__).resolve().parents[1]
PROD=ROOT/'docs/flasher'
OUT=ROOT/'docs/flasher-lfo-test'
STAMP='2026-10-11-lfo2-label-font-fix'
TEXT={
    'en':dict(label='Second LFO',short='Second press of LFO opens LFO 2. Settings are held in RAM only.',
        desc='Press LFO to open the native LFO page, then press LFO again for LFO 2. The stock parameter menu renderer supplies the left panel, four scrolling rows, fonts and selection cursor. Turn DATA to choose a row, click to edit, turn to adjust and click to finish. Track pads select one of six secondary LFOs without playing a note. LFO, RETURN or SETTINGS closes the page; PLAY/STOP works normally. The two LFOs have independent speed, multiplier, fade, destination, waveform, start phase, mode and depth. Their contributions add when targeting the same parameter. Labels sit to the left of their values, using the stock Wav, Mul, Dst and Dep labels. Destinations show the same parameter names as LFO 1 for the selected track; multipliers use its musical values. OFF remains available. This first hardware test keeps LFO 2 settings in RAM across page changes; they are not saved with patterns or projects and are lost on restart. Model-TG is optional.',
        note='Experimental: emulation checked, awaiting hardware verification. Pattern saving and combined audio timing remain under development.'),
    'fr':dict(label='Second LFO',short='Deuxième appui LFO : LFO 2. Réglages conservés en RAM seulement.',
        desc='Appuyez sur LFO pour sa page native, puis encore sur LFO pour LFO 2. Le rendu natif du menu fournit le panneau gauche, quatre lignes défilantes, les polices et le curseur. DATA choisit une ligne ; clic pour éditer, rotation pour régler, clic pour terminer. Les pads choisissent un des six LFO secondaires sans jouer de note. LFO, RETURN ou SETTINGS ferme la page ; PLAY/STOP reste disponible. Vitesse, multiplicateur, fondu, destination, forme, phase initiale, mode et profondeur sont indépendants. Les contributions sont additionnées pour une destination commune. Les libellés Wav, Mul, Dst et Dep natifs figurent à gauche des valeurs. Les destinations reprennent les noms de paramètres du LFO 1 pour la piste choisie et les multiplicateurs leurs valeurs musicales. OFF reste disponible. Ce premier essai matériel conserve les réglages en RAM entre les pages ; ils ne sont pas sauvés avec les patterns/projets et disparaissent au redémarrage. Model-TG est facultatif.',
        note='Expérimental : vérifié en émulation, essai matériel attendu. Sauvegarde et marge audio combinée en développement.'),
}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--cycles',required=True);ap.add_argument('--syntakt',required=True);ap.add_argument('--check',action='store_true')
    args=ap.parse_args()
    tw=catalog.read_js((PROD/'tweaks.js').read_text())
    lfo=json.loads((ROOT/'tweaks/model-cycles_OS1.13/experimental/lfo-secondary/52-lfo-secondary.json').read_text())
    assert lfo['id'] not in {t['id'] for t in tw['tweaks']}
    tw['tweaks'].append(lfo)
    tw['features'].append(dict(id='lfo-secondary',cat='seq',label='Second LFO',status='experimental',variants=[dict(id='lfo-secondary',label=None)]))
    compact=copy.deepcopy(tw);compact['tweaks'],compact['shared']=catalog.share(compact['tweaks'])
    files={p.name:p.read_text() for p in PROD.iterdir() if p.is_file() and p.suffix in ('.js','.css','.txt','.html')}
    files['tweaks.js']='/* Généré par tools/gen_lfo_test_flasher.py. */\nwindow.MC_TWEAKS = '+json.dumps(compact,ensure_ascii=False,indent=1)+';\n'+catalog.HYDRATE
    assert catalog.read_js(files['tweaks.js'])['tweaks']==tw['tweaks']
    stock=ref_mainos.main_os(args.cycles);zones=build.cave_zones(stock,tw['tweaks'])
    scan=build.refs_into;hits=scan(stock,zones) if zones else ([],[])
    def cached_refs(image,selected):
        assert image==stock
        return tuple([hit for hit in group if any(lo+build.BASE<=hit[1]<hi+build.BASE for lo,hi in selected)] for group in hits)
    original=ref_mainos.mc_tweaks
    build.refs_into=cached_refs;ref_mainos.mc_tweaks=lambda:tw
    try:refs,mods,count=ref_mainos.blocks(args.cycles,args.syntakt)
    finally:build.refs_into=scan;ref_mainos.mc_tweaks=original
    for name,body in (('REF_MAINOS',refs),('REF_MODS',mods)):
        match=ref_mainos.BLOCKS[name].search(files['app.js']);assert match,name
        files['app.js']=files['app.js'][:match.start(2)]+'\n'+body+files['app.js'][match.end(2):]
    injection='\n'.join(f'FEAT.{lang}["lfo-secondary"] = '+json.dumps(text,ensure_ascii=False)+';' for lang,text in TEXT.items())
    injection+='\nGUIDE_OF["lfo-secondary"] = "lfo-secondary";\n'
    files['app.js']=files['app.js'].replace('function featText(',injection+'\nfunction featText(',1)
    files['app.js']=files['app.js'].replace('const GUIDE = "../guide/"','const GUIDE = "guide.html"')
    # Le guide local comprend toutes les sections existantes et celle du LFO 2.
    guide=(ROOT/'docs/guide/index.html').read_text()
    section='<section id="lfo-secondary"><h2>Second LFO / Second LFO</h2>'
    for lang,text in TEXT.items():section+=f'<p data-l="{lang}">{text["desc"]}</p><p data-l="{lang}">{text["note"]}</p>'
    files['guide.html']=guide.replace('</main>',section+'</section>\n</main>',1)
    notice='<div class="alert" id="lfo-test-notice"><span data-l="en">LFO 2 hardware test — settings in RAM only; not saved with patterns/projects. The main flasher is unchanged.</span><span data-l="fr">Essai matériel LFO 2 — réglages en RAM seulement, sans sauvegarde pattern/projet. Le flasher principal reste inchangé.</span></div>'
    files['index.html']=files['index.html'].replace('<div id="errbar"',notice+'\n<div id="errbar"',1)
    files['index.html']=files['index.html'].replace('Model:Cycles Flasher</title>','Model:Cycles — LFO 2 Test</title>')
    files['index.html']=re.sub(r'2026-\d\d-\d\d-genie-queued-upstream-main',STAMP,files['index.html'])
    OUT.mkdir(parents=True,exist_ok=True)
    for name,body in files.items():
        body=body.rstrip()+'\n'
        if args.check:assert (OUT/name).read_text()==body,OUT/name
        else:(OUT/name).write_text(body)
    print('ok : flasher LFO 2 autonome, catalogue principal conservé,',count,'combinaisons validées')


if __name__=='__main__':main()
