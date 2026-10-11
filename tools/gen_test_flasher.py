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
STAMP = "2026-10-10-generator-select-all-test"

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cycles",required=True)
    ap.add_argument("--syntakt",required=True)
    ap.add_argument("--check",action="store_true")
    ap.add_argument("--second",action="store_true",help="construire le second flasher de test indépendant")
    ap.add_argument("--quarantine",action="store_true",help="retirer les extensions après incident matériel")
    a=ap.parse_args()
    global OUT, STAMP
    if a.second:
        OUT=ROOT/"docs/flasher-test-2"
        STAMP="2026-10-11-test-2-queue-values"
    else:
        STAMP="2026-10-10-generator-sequence-only-test"
    OUT.mkdir(parents=True,exist_ok=True)
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
    tw["tweaks"]=[t for t in tw["tweaks"] if not t["id"].startswith("scramble")]
    tw["features"]=[f for f in tw["features"] if f["id"]!="scramble"]
    for i,t in enumerate(tw["tweaks"]):
        if t["id"] in ("scale-gen","scale-gen-st"):
            advanced=json.loads((ROOT/f'tweaks/model-cycles_OS1.13/experimental/sequence-only/49-{t["id"]}.json').read_text())
            advanced["order"]=t["order"]
            tw["tweaks"][i]=advanced
    for f in tw["features"]:
        if f["id"]=="scale-gen":f["status"]="experimental"
    if a.second:
        for p in sorted((ROOT/"tweaks/model-cycles_OS1.13/experimental/queued").glob("*.json")):
            tw["tweaks"].append(json.loads(p.read_text()))
        for p in sorted((ROOT/"tweaks/model-cycles_OS1.13/experimental/scramble").glob("*.json")):
            tw["tweaks"].append(json.loads(p.read_text()))
        next(f for f in tw["features"] if f["id"]=="scale-gen")["queued"]={"scale-gen":"scale-gen-queued","scale-gen-st":"scale-gen-st-queued"}
        tw["features"].append(dict(id="scramble",cat="sound",label="SCRAMBLE",status="experimental",requires="model-tg",variants=[dict(id="scramble",label=None)],with_={}))
        tw["features"][-1].pop("with_")
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
    original_cards=ref_mainos.Cards
    if a.second:
        class SecondCards(original_cards):
            def options(self,f):
                out=super().options(f)
                return out+["scale-gen-queued"] if f["id"]=="scale-gen" else out
            def ids(self,sel):
                out=super().ids(sel)
                queued=sel.get("scale-gen","").endswith("-queued")
                return [(i+"-queued" if queued and not i.endswith("-queued") else i) if i.startswith("scale-gen") else (("scramble-st" if "syntakt" in sel or "macro" in sel else "scramble")+("-gen" if "scale-gen" in sel else "")+("-queued" if "scale-gen" in sel and queued else "")) if i.startswith("scramble") else i for i in out]
        ref_mainos.Cards=SecondCards
    try: refs,mods,n=ref_mainos.blocks(a.cycles,a.syntakt)
    finally:
        build.refs_into=scan
        ref_mainos.Cards=original_cards
    for name,body in (("REF_MAINOS",refs),("REF_MODS",mods)):
        pat=ref_mainos.BLOCKS[name]
        m=pat.search(files["app.js"])
        assert m,name
        files["app.js"]=files["app.js"][:m.start(2)]+"\n"+body+files["app.js"][m.end(2):]
    descriptions=[
        {"label":"Scale sequence generator","short":"Ranges, rhythm/notes, mutation, Euclid and a larger rounded entry popup.","desc":"SETTINGS + PAGE opens the generator. Click DATA to edit a field, turn to change it, click again to finish. Choose minimum/maximum velocity, decay and pan, Both/Rhythm/Notes, Mutation %, Random/Euclid rhythm, hits and rotation. PLAY/STOP previews; FUNC + track pads mute/unmute. Sound randomization is completely removed from this generator.","note":"Experimental extensions, awaiting hardware testing. Stop before Generate or Undo. Closing the page discards Undo. The crashing sound randomizer has been removed; SCRAMBLE is being developed as a separate mod."},
        {"label":"Générateur de séquence en gamme","short":"Plages, rythme/notes, mutation, Euclid et cartouche agrandi arrondi.","desc":"SETTINGS + PAGE ouvre le générateur. Cliquez DATA pour éditer, tournez pour régler et cliquez pour terminer. Réglez min/max de velocity, decay et pan, Both/Rhythm/Notes, Mutation %, rythme Random/Euclid, coups et rotation. PLAY/STOP permet l’écoute ; FUNC + pads coupe/rétablit les pistes. Le tirage du son est entièrement retiré du générateur.","note":"Extensions expérimentales, essais matériels attendus. Arrêtez avant Generate et Undo. Fermer la page efface Undo. Le tirage du son ayant planté est retiré ; SCRAMBLE est développé comme mod distinct."}
    ]
    if a.second:
        descriptions[0]["label"]="Sequence Generator"
        descriptions[1]["label"]="Générateur de séquence"
        descriptions[0]["note"]="Expanded menu confirmed working on hardware by AveyCole. Stop for Generate and Undo unless Queued generation is selected. Closing the page discards Undo and cancels a pending queue."
        descriptions[1]["note"]="Menu étendu confirmé sur machine par AveyCole. Arrêtez pour Generate et Undo, sauf avec génération au prochain cycle. Fermer la page efface Undo et annule la préparation."
    entries=iter(descriptions)
    files["app.js"]=re.sub(r'    "scale-gen": \{[^\n]+\},',lambda m:'    "scale-gen": '+json.dumps(next(entries),ensure_ascii=False)+',',files["app.js"])
    for name in ("index.html",):
        files[name]=re.sub(r"2026-10-10-scale-gen-dynamics-main|2026-10-11-scramble-main",STAMP,files[name])
    notice='<p id="test-build-notice" role="note"><span data-l="en">Experimental expanded generator: ranges, rhythm/notes, mutation, Euclidean rhythm and a larger rounded SEQ. GEN. popup. Sound randomization has been removed. Hardware testing required. Generate and Undo require stopped playback.</span><span data-l="fr">Générateur étendu expérimental : plages, rythme/notes, mutation, rythme euclidien et cartouche SEQ. GEN. agrandi arrondi. Tirage du son retiré. À tester sur la machine. Generate et Undo demandent la lecture arrêtée.</span></p>'
    files["index.html"]=files["index.html"].replace('<main',notice+'\n<main',1)
    if a.second:
        app=files["app.js"]
        app=app.replace('  // several variants of one mod', '  if (f.queued && sel.on) add(`<div class="variants"><label for="queue-scale-gen"><input type="checkbox" id="queue-scale-gen"${sel.queued ? " checked" : ""}><span>${esc(t("queued_generation"))}<small>${esc(t("queued_generation_note"))}</small></span></label></div>`);\n  // several variants of one mod')
        app=app.replace('    else if (el.name && el.name.startsWith("eng-")', '    else if (el.id === "queue-scale-gen") { selOf(f("scale-gen")).queued = el.checked; pick.swap = null; }\n    else if (el.name && el.name.startsWith("eng-")')
        app=app.replace('    const tk = tw.tweaks.find((x) => x.id === id);', '    if (f.queued && sel.queued) id = f.queued[id];\n    if (f.id === "scramble") id = (isOn("syntakt") || isOn("macro") ? "scramble-st" : "scramble") + (isOn("scale-gen") ? "-gen" + (selOf(featById("scale-gen")).queued ? "-queued" : "") : "");\n    const tk = tw.tweaks.find((x) => x.id === id);')
        app=app.replace('    out.push(l);', '    if (f.queued && sel.queued) l += " — " + t("queued_generation");\n    out.push(l);')
        # Les textes SCRAMBLE sont ajoutés aux deux dictionnaires FEAT.
        entries=iter([
            dict(label="SCRAMBLE",short="SETTINGS + TRACK randomizes the machine’s four controls, with a popup.",desc="One press of SETTINGS + TRACK randomizes only the active machine’s four parameters and displays SCRAMBLE. Works outside Sequence Generator; has no menu and does not generate notes or trigs. Requires Model-TG. Sampler is excluded.",note="Experimental: emulation checked, awaiting hardware testing. Sound changes have no Undo."),
            dict(label="SCRAMBLE",short="SETTINGS + TRACK tire les quatre contrôles machine et affiche un cartouche.",desc="SETTINGS + TRACK tire uniquement les quatre paramètres de la machine active et affiche SCRAMBLE. Fonctionne hors du générateur, sans menu ni notes/trigs générés. Demande Model-TG. Sampler exclu.",note="Expérimental : vérifié en émulation, à tester sur machine. Les changements du son n’ont pas de Undo.")])
        app=re.sub(r'    "scale-gen": \{[^\n]+\},',lambda m:m[0]+'\n    "scramble": '+json.dumps(next(entries),ensure_ascii=False)+',',app)
        app=app.replace('const GUIDE_OF = {','const GUIDE_OF = {\n  "scramble": "scramble",')
        app=app.replace("function wirePicker() {",(ROOT/"tools/test_flasher_2_ui.js").read_text()+"\nfunction wirePicker() {")
        files["app.js"]=app
        files["index.html"]=files["index.html"].replace(notice,'<p id="test-build-notice" role="note"><span data-l="en">Test Flasher 2: Sequence Generator with optional queued generation, standalone SCRAMBLE and compatible Select all. New firmware features are experimental and await hardware testing.</span><span data-l="fr">Flasher de test 2 : générateur avec option au prochain cycle, SCRAMBLE indépendant et sélection compatible. Les nouveaux comportements sont expérimentaux, à tester sur machine.</span></p>')
    if a.second: files["app.js"]=files["app.js"].replace("function wirePicker() {", (ROOT/"tools/test_flasher_select_all.js").read_text()+"\nfunction wirePicker() {\n  $(\"select-all\").addEventListener(\"click\", selectAllCompatible);")
    if a.second: files["index.html"]=files["index.html"].replace('<div id="features"></div>', '<p><button type="button" class="btn" id="select-all" data-i18n="select_all" aria-describedby="select-all-note">Select all</button></p><p id="select-all-note" data-i18n="select_all_note"></p><div id="features"></div>')
    files["guide.html"]=(ROOT/"docs/guide/index.html").read_text()
    files["app.js"]=files["app.js"].replace('const GUIDE = "../guide/";', 'const GUIDE = "guide.html";')
    section='<section id="scale-gen"><h2><span data-l="en">Expanded sequence generator — experimental</span><span data-l="fr">Générateur étendu — expérimental</span></h2><p><span data-l="en">Open with SETTINGS + PAGE. Turn DATA to scroll the four visible rows; click a field, turn to edit, then click to leave editing. Enable velocity, decay or pan and set each minimum and maximum. Regenerate selects Both, Rhythm or Notes. Mutation sets the percentage of steps eligible for changes. Euclid uses a hit count and rotation across the current track length. Generate and Undo require stopped playback. PLAY previews without closing the menu; FUNC + track pads mute or unmute tracks. Closing the page discards Undo. Sound randomization is entirely removed. The entry popup uses a larger rounded black box and larger white text. New features are emulation checked and await hardware testing.</span><span data-l="fr">Ouvrez avec SETTINGS + PAGE. Tournez DATA pour défiler sur quatre lignes ; cliquez un champ, tournez pour régler et cliquez pour quitter l’édition. Activez velocity, decay ou pan puis réglez chaque minimum et maximum. Regenerate choisit Both (les deux), Rhythm (rythme) ou Notes. Mutation règle le pourcentage de pas pouvant changer. Euclid utilise un nombre de coups et une rotation sur la longueur de piste actuelle. Generate et Undo demandent la lecture arrêtée. PLAY permet l’écoute dans le menu ; FUNC + pads de piste coupent ou rétablissent les pistes. Fermer la page efface Undo. Le tirage du son est entièrement retiré. Le cartouche utilise un grand fond noir arrondi et du texte blanc agrandi. Les nouveautés sont vérifiées en émulation et attendent les essais sur machine.</span></p></section>'
    files["guide.html"]=re.sub(r'<section id="scale-gen">.*?</section>',lambda m:section,files["guide.html"],flags=re.S)
    if a.second:
        files["guide.html"]=files["guide.html"].replace('</body>', '<section id="queued-generation"><h2>Queued generation / Génération au prochain cycle</h2><p><span data-l="en">Select Queued generation beneath Sequence Generator. While playing, Generate prepares the result; Queued appears until the next loop’s first trig is read. Cancel queue cancels. Stop to Undo. Shared pattern length and speed only; no pattern chains. Changing the pattern, editing the track, stopping or closing cancels pending generation.</span><span data-l="fr">Cochez Génération au prochain cycle sous le générateur. Pendant la lecture, Generate prépare le résultat ; Queued reste affiché jusqu’à la lecture du premier trig du cycle suivant. Cancel queue annule. Arrêtez pour Undo. Longueur/vitesse communes, sans chaîne. Changement de pattern, édition, arrêt et fermeture annulent la préparation.</span></p></section><section id="scramble"><h2>SCRAMBLE</h2><p><span data-l="en">Select SCRAMBLE independently. SETTINGS + TRACK changes the four machine controls once and displays SCRAMBLE, without a menu. Sampler excluded. Experimental; no sound Undo.</span><span data-l="fr">Cochez SCRAMBLE indépendamment. SETTINGS + TRACK tire les quatre contrôles machine une fois et affiche SCRAMBLE, sans menu. Sampler exclu. Expérimental ; pas de Undo du son.</span></p></section></body>')
    for name,text in files.items():
        text=text.rstrip()+"\n"
        if a.check:assert (OUT/name).read_text()==text,str(OUT/name)
        else:(OUT/name).write_text(text)
    print(f"ok : flasher expérimental autonome, {n} combinaisons validées")
if __name__=="__main__":main()
