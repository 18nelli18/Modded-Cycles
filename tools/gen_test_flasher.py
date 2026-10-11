#!/usr/bin/env python3
"""Flasher de test : transport et variations du générateur (notes/53).

Le catalogue principal reste inchangé. Les deux variantes de test remplacent
le générateur dans cette page seulement ; toutes les empreintes sont recalculées.
"""
import argparse
import json
import pathlib
import re
import gen_flasher_tweaks as catalog
import ref_mainos as refs
ROOT = pathlib.Path(__file__).resolve().parent.parent
PROD = ROOT / "docs/flasher"
OUT = ROOT / "docs/flasher-test"
STAMP = "2026-10-10-scale-gen-dynamics-02"
BANNER = '<div class="alert bad" role="alert" id="test-build-notice"><span data-l="en"><strong>TEST: GENERATOR PREVIEW + RANDOMIZATION</strong> — PLAY/STOP inside the menu; optional velocity, decay and pan variation. Emulator checks pass; hardware test pending. <a href="../flasher/">Main flasher</a>.</span><span data-l="fr"><strong>TEST : ÉCOUTE ET VARIATIONS DU GÉNÉRATEUR</strong> — PLAY/STOP dans le menu ; velocity, decay et pan aléatoires en option. Émulation validée ; essai sur machine attendu. <a href="../flasher/">Flasher principal</a>.</span></div>'

def render(cycles, syntakt):
    """Construit les références avec les variantes de test et tous les mods."""
    payload = catalog.read_js((PROD / "tweaks.js").read_text())
    overrides = [json.loads((ROOT / f"tweaks/model-cycles_OS1.13/experimental/dynamics/49-{name}.json").read_text())
                 for name in ("scale-gen", "scale-gen-st")]
    by_id = {t["id"]:t for t in overrides}
    payload["tweaks"] = [by_id.get(t["id"], t) for t in payload["tweaks"]]
    feature = next(f for f in payload["features"] if f["id"] == "scale-gen")
    feature["status"] = "experimental"
    stock = refs.main_os(cycles)
    union = refs.build.cave_zones(stock, payload["tweaks"])
    hits = refs.build.refs_into(stock, union)
    original_scan, original_main, original_catalog = refs.build.refs_into, refs.main_os, refs.mc_tweaks
    def cached_scan(image, zones):
        assert image == stock
        return tuple([h for h in group if any(lo <= h[1] - refs.build.BASE < hi for lo, hi in zones)] for group in hits)
    refs.build.refs_into = cached_scan
    refs.main_os = lambda path:stock
    refs.mc_tweaks = lambda:payload
    print("ok : image officielle et références des caves relevées", flush=True)
    try:
        main, mods, count = refs.blocks(cycles, syntakt)
    finally:
        refs.build.refs_into, refs.main_os, refs.mc_tweaks = original_scan, original_main, original_catalog
    files = {p.name:p.read_text() for p in PROD.iterdir() if p.is_file() and p.suffix in (".js", ".css", ".txt", ".html") and p.name != "tweaks.js"}
    addon = {"tweaks":overrides,"feature":feature}
    files["tweaks.js"] = '/* Généré : variantes transport et variations, remplace uniquement le générateur. */\n(function(tw, addon) { for (const t of addon.tweaks) { const i=tw.tweaks.findIndex(x=>x.id===t.id); if(i<0) throw Error("Generator missing"); tw.tweaks[i]=t; } tw.features[tw.features.findIndex(f=>f.id===addon.feature.id)]=addon.feature; })(window.MC_TWEAKS, '+json.dumps(addon,ensure_ascii=False,indent=1)+');\n'
    app=files["app.js"]
    for name,block in (("REF_MAINOS",main),("REF_MODS",mods)):
        match=refs.BLOCKS[name].search(app)
        assert match,name
        app=app[:match.start(2)]+"\n"+block+app[match.end(2):]
    app=app.replace('const GUIDE = "../guide/";', 'const GUIDE = "guide.html";')
    for lang,text in {
        "en": {"label":"Scale sequence generator", "short":"Preview with PLAY/STOP; optional velocity, decay and pan variation.", "desc":"Hold SETTINGS and press PAGE. Turn DATA to select a row, press to edit a field or switch Rand velocity, Rand decay and Rand pan On/Off. All three default Off. Generate writes the active track. PLAY/STOP audition it without leaving the menu. Stop before Generate or Undo; Undo restores the previous notes, trigs, velocity and parameter locks. Requires Model-TG; works with the available machines.", "note":"Experimental additions: hardware test pending. Velocity 1–127, decay 0–127, pan 0–127 (64 centre), per generated note trig only. Disabled options retain existing values and locks. Closing the page discards Undo. Existing conditions/retrig can affect playback."},
        "fr": {"label":"Générateur de séquence en gamme", "short":"Écoutez avec PLAY/STOP ; velocity, decay et pan aléatoires en option.", "desc":"Maintenez SETTINGS et appuyez sur PAGE. Tournez DATA pour choisir une ligne ; appuyez pour éditer ou activer Rand velocity, Rand decay et Rand pan. Les trois sont désactivés au départ. Generate écrit la piste active. PLAY/STOP permet de l’écouter sans fermer le menu. Arrêtez avant Generate ou Undo ; Undo restaure notes, trigs, velocity et p-locks. Demande Model-TG ; fonctionne avec les machines disponibles.", "note":"Ajouts expérimentaux : essai sur machine attendu. Velocity 1–127, decay 0–127, pan 0–127 (64 au centre), uniquement sur les trigs générés. Les options désactivées conservent les valeurs/verrous existants. Fermer la page efface Undo. Conditions/retrig existants peuvent influencer la lecture."}
    }.items():
        # Deux définitions FEAT, anglais puis français, dans l'ordre du fichier.
        pattern=r'(?m)^    ("scale-gen": )\{[^\n]+\},'
        matches=list(re.finditer(pattern,app))
        match=matches[0 if lang=="en" else 1]
        app=app[:match.start()]+'    '+match.group(1)+json.dumps(text,ensure_ascii=False)+','+app[match.end():]
    files["app.js"]=app
    html=files["index.html"].replace('<script src="tweaks.js?', '<script src="../flasher/tweaks.js?v='+STAMP+'"></script>\n<script src="tweaks.js?',1)
    html=html.replace('<main class="wrap fl">','<main class="wrap fl">\n  '+BANNER,1)
    html=html.replace('<title>Model:Cycles', '<title>Generator Preview Test — Model:Cycles',1)
    html=re.sub(r'window.MC_BUILD = "[^"]+"',f'window.MC_BUILD = "{STAMP}"',html)
    files["index.html"]=re.sub(r'\?v=[^"\s]+',f'?v={STAMP}',html)
    guide=(ROOT / "docs/guide/index.html").read_text()
    section = '<section id="scale-gen"><h2><span data-l="en">Sequence generator — test build</span><span data-l="fr">Générateur — version de test</span></h2><p><span data-l="en">Open with SETTINGS + PAGE. Turn DATA to scroll; click a field to edit. Click Rand velocity, Rand decay or Rand pan to toggle On/Off. All start Off. Select Generate and click DATA. Press PLAY to preview while the menu stays open, then STOP before Undo or generating again. Undo restores the last generation, including velocity and parameter locks; closing the page discards it. Randomization affects generated note trigs only: velocity 1–127, decay 0–127, pan 0–127 (64 centre). Existing locks for disabled options, other parameters and other tracks are preserved. Requires Model-TG and supports the available machines. New transport and randomization behavior is emulator checked; hardware testing pending.</span><span data-l="fr">Ouvrez avec SETTINGS + PAGE. Tournez DATA pour défiler ; cliquez un champ pour l’éditer. Cliquez Rand velocity, Rand decay ou Rand pan pour activer/désactiver. Tous commencent désactivés. Choisissez Generate et cliquez DATA. Appuyez sur PLAY pour écouter dans le menu, puis STOP avant Undo ou une nouvelle génération. Undo restaure la dernière génération, velocity et p-locks compris ; fermer la page efface Undo. Variations sur les trigs générés seulement : velocity 1–127, decay 0–127, pan 0–127 (64 au centre). Les verrous des options désactivées, autres paramètres et autres pistes sont conservés. Demande Model-TG et supporte les machines disponibles. Nouveaux comportements vérifiés en émulation ; essai matériel attendu.</span></p></section>'
    guide,n=re.subn(r'<section id="scale-gen">.*?</section>',lambda m:section,guide,count=1,flags=re.S)
    assert n==1
    files["guide.html"]=guide
    return {name:text.rstrip()+"\n" for name,text in files.items()},count

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cycles",required=True)
    ap.add_argument("--syntakt",required=True)
    ap.add_argument("--check",action="store_true")
    args=ap.parse_args()
    files,count=render(args.cycles,args.syntakt)
    for name,text in files.items():
        path=OUT/name
        if args.check:
            assert path.read_text()==text,str(path)
        else:
            path.write_text(text)
    print(f"ok : flasher de test transport et variations, {count} combinaisons vérifiées")
if __name__ == "__main__":
    main()
