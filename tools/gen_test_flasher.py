#!/usr/bin/env python3
"""Catalogue expérimental autonome ; le flasher principal reste inchangé (notes/54)."""
import argparse
import copy
import json
import pathlib
import re
import gen_flasher_tweaks as catalog
import ref_mainos
import build
ROOT = pathlib.Path(__file__).resolve().parent.parent
PROD = ROOT / "docs/flasher"
OUT = ROOT / "docs/flasher-test"
STAMP = "2026-10-10-generator-advanced-test"

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cycles",required=True)
    ap.add_argument("--syntakt",required=True)
    ap.add_argument("--check",action="store_true")
    ap.add_argument("--quarantine",action="store_true",help="retirer les extensions après incident matériel")
    a=ap.parse_args()
    if a.quarantine:
        files={p.name:p.read_text() for p in PROD.iterdir() if p.is_file() and p.suffix in (".js",".css",".txt",".html")}
        files["guide.html"]=(ROOT/"docs/guide/index.html").read_text()
        files["index.html"]=files["index.html"].replace("2026-10-10-scale-gen-dynamics-main","2026-10-10-sound-withdrawn")
        notice='<p id="sound-withdrawn" role="alert"><span data-l="en">Sound randomization withdrawn after a reported hardware crash. This page temporarily uses the hardware-tested main catalog. Expanded experimental features will return in a separate build after investigation.</span><span data-l="fr">Tirage du son retiré après un plantage matériel signalé. Cette page utilise temporairement le catalogue principal testé sur machine. Les extensions expérimentales reviendront dans un build distinct après investigation.</span></p>'
        files["index.html"]=files["index.html"].replace('<main',notice+'\n<main',1)
        for name,text in files.items():
            text=text.rstrip()+"\n"
            if a.check:assert (OUT/name).read_text()==text,str(OUT/name)
            else:(OUT/name).write_text(text)
        print("ok : extensions retirées, catalogue principal testé restauré")
        return
    tw=catalog.read_js((PROD/"tweaks.js").read_text())
    for i,t in enumerate(tw["tweaks"]):
        if t["id"] in ("scale-gen","scale-gen-st"):
            advanced=json.loads((ROOT/f'tweaks/model-cycles_OS1.13/experimental/advanced/49-{t["id"]}.json').read_text())
            advanced["order"]=t["order"]
            tw["tweaks"][i]=advanced
    for f in tw["features"]:
        if f["id"]=="scale-gen":f["status"]="experimental"
    compact=copy.deepcopy(tw)
    compact["tweaks"],compact["shared"]=catalog.share(compact["tweaks"])
    files={p.name:p.read_text() for p in PROD.iterdir() if p.is_file() and p.suffix in (".js",".css",".txt",".html")}
    files["tweaks.js"]="/* Généré par tools/gen_test_flasher.py. */\nwindow.MC_TWEAKS = "+json.dumps(compact,ensure_ascii=False,indent=1)+";\n"+catalog.HYDRATE
    assert catalog.read_js(files["tweaks.js"])["tweaks"]==tw["tweaks"]
    # Une seule analyse de toutes les caves ; filtrage exact pour chaque sélection.
    stock=ref_mainos.main_os(a.cycles)
    zones=build.cave_zones(stock,tw["tweaks"])
    scan=build.refs_into
    hits=scan(stock,zones) if zones else ([],[])
    def cached_refs(image,selected):
        assert image==stock
        return tuple([h for h in group if any(lo+build.BASE<=h[1]<hi+build.BASE for lo,hi in selected)] for group in hits)
    build.refs_into=cached_refs
    ref_mainos.mc_tweaks=lambda:tw
    try: refs,mods,n=ref_mainos.blocks(a.cycles,a.syntakt)
    finally:build.refs_into=scan
    for name,body in (("REF_MAINOS",refs),("REF_MODS",mods)):
        pat=ref_mainos.BLOCKS[name]
        m=pat.search(files["app.js"])
        assert m,name
        files["app.js"]=files["app.js"][:m.start(2)]+"\n"+body+files["app.js"][m.end(2):]
    descriptions=[
        {"label":"Scale sequence generator","short":"Ranges, rhythm/notes, mutation, Euclid and separate sound randomization.","desc":"SETTINGS + PAGE opens the generator. Click DATA to edit a field, turn to change it, click again to finish. Choose minimum/maximum velocity, decay and pan, Both/Rhythm/Notes, Mutation %, Random/Euclid rhythm, hits and rotation. PLAY/STOP previews; FUNC + track pads mute/unmute. SETTINGS + TRACK opens directly at Sound amount %, Random sound and Undo sound. It uses the same page with independent sound Undo.","note":"Experimental extensions, awaiting hardware testing. Stop before generating, randomizing sound or undoing. Closing the page discards both Undo snapshots. Sound randomization changes four machine controls and decay within firmware ranges; Sampler excluded. Six stock machines checked in emulation; added machines need testing."},
        {"label":"Générateur de séquence en gamme","short":"Plages, rythme/notes, mutation, Euclid et tirage du son indépendant.","desc":"SETTINGS + PAGE ouvre le générateur. Cliquez DATA pour éditer, tournez pour régler et cliquez pour terminer. Réglez min/max de velocity, decay et pan, Both/Rhythm/Notes, Mutation %, rythme Random/Euclid, coups et rotation. PLAY/STOP permet l’écoute ; FUNC + pads coupe/rétablit les pistes. SETTINGS + TRACK ouvre directement Sound amount %, Random sound et Undo sound. Même page, Undo du son indépendant.","note":"Extensions expérimentales, essais matériels attendus. Arrêtez avant Generate, Random sound et Undo. Fermer la page efface les deux snapshots Undo. Le tirage du son modifie quatre contrôles machine et decay selon les plages du firmware ; Sampler exclu. Six machines stock vérifiées en émulation ; machines ajoutées à tester."}
    ]
    entries=iter(descriptions)
    files["app.js"]=re.sub(r'    "scale-gen": \{[^\n]+\},',lambda m:'    "scale-gen": '+json.dumps(next(entries),ensure_ascii=False)+',',files["app.js"])
    for name in ("index.html",):
        files[name]=re.sub(r"2026-10-10-scale-gen-dynamics-main",STAMP,files[name])
    notice='<p id="test-build-notice" role="note"><span data-l="en">Experimental expanded generator: ranges, rhythm/notes, mutation, Euclidean rhythm and sound randomization. Hardware testing required. Generate and Undo require stopped playback.</span><span data-l="fr">Générateur étendu expérimental : plages, rythme/notes, mutation, rythme euclidien et sons aléatoires. À tester sur la machine. Generate et Undo demandent la lecture arrêtée.</span></p>'
    files["index.html"]=files["index.html"].replace('<main',notice+'\n<main',1)
    files["guide.html"]=(ROOT/"docs/guide/index.html").read_text()
    files["app.js"]=files["app.js"].replace('const GUIDE = "../guide/";', 'const GUIDE = "guide.html";')
    section='<section id="scale-gen"><h2><span data-l="en">Expanded sequence generator — experimental</span><span data-l="fr">Générateur étendu — expérimental</span></h2><p><span data-l="en">Open with SETTINGS + PAGE. Turn DATA to scroll the four visible rows; click a field, turn to edit, then click to leave editing. Enable velocity, decay or pan and set each minimum and maximum. Regenerate selects Both, Rhythm or Notes. Mutation sets the percentage of steps eligible for changes. Euclid uses a hit count and rotation across the current track length. Generate and Undo require stopped playback. PLAY previews without closing the menu; FUNC + track pads mute or unmute tracks. Closing the page discards Undo. SETTINGS + TRACK opens the sound controls: Sound amount, Random sound and independent Undo sound. Sound randomization changes the four machine controls and decay within the selected machine’s firmware ranges; pitch, level, effects, pattern and locks are preserved. Sampler is excluded. New features are emulation checked and await hardware testing.</span><span data-l="fr">Ouvrez avec SETTINGS + PAGE. Tournez DATA pour défiler sur quatre lignes ; cliquez un champ, tournez pour régler et cliquez pour quitter l’édition. Activez velocity, decay ou pan puis réglez chaque minimum et maximum. Regenerate choisit Both (les deux), Rhythm (rythme) ou Notes. Mutation règle le pourcentage de pas pouvant changer. Euclid utilise un nombre de coups et une rotation sur la longueur de piste actuelle. Generate et Undo demandent la lecture arrêtée. PLAY permet l’écoute dans le menu ; FUNC + pads de piste coupent ou rétablissent les pistes. Fermer la page efface Undo. SETTINGS + TRACK ouvre les réglages du son : Sound amount, Random sound et Undo sound indépendant. Le tirage modifie les quatre paramètres machine et decay selon les plages du firmware ; hauteur, niveau, effets, motif et verrous restent conservés. Sampler exclu. Les nouveautés sont vérifiées en émulation et attendent les essais sur machine.</span></p></section>'
    files["guide.html"]=re.sub(r'<section id="scale-gen">.*?</section>',lambda m:section,files["guide.html"],flags=re.S)
    for name,text in files.items():
        text=text.rstrip()+"\n"
        if a.check:assert (OUT/name).read_text()==text,str(OUT/name)
        else:(OUT/name).write_text(text)
    print(f"ok : flasher expérimental autonome, {n} combinaisons validées")
if __name__=="__main__":main()
