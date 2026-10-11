#!/usr/bin/env python3
"""Flasher de test : quatre lignes défilantes pour le générateur (notes/53).

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
STAMP = "2026-10-10-scale-gen-scroll-01"
BANNER = '''<div class="alert bad" role="alert" id="test-build-notice"><span data-l="en"><strong>TEST: SCROLLING GENERATOR MENU</strong> — Four visible rows with more spacing and margins. Turn DATA to scroll. The generation engine is unchanged; this display layout awaits a hardware check. <a href="../flasher/">Main flasher</a>.</span><span data-l="fr"><strong>TEST : MENU DU GÉNÉRATEUR DÉFILANT</strong> — Quatre lignes visibles, plus espacées et avec des marges. Tournez DATA pour défiler. Le moteur de génération est inchangé ; cet affichage attend un essai sur machine. <a href="../flasher/">Flasher principal</a>.</span></div>'''
def render(cycles, syntakt):
    """Construit les références avec les variantes de test et tous les mods."""
    payload = catalog.read_js((PROD / "tweaks.js").read_text())
    overrides = [json.loads((ROOT / f"tweaks/model-cycles_OS1.13/experimental/scroll/49-{name}.json").read_text())
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
    files["tweaks.js"] = '/* Généré : variantes défilantes, remplace uniquement le générateur. */\n(function(tw, addon) { for (const t of addon.tweaks) { const i=tw.tweaks.findIndex(x=>x.id===t.id); if(i<0) throw Error("Generator missing"); tw.tweaks[i]=t; } tw.features[tw.features.findIndex(f=>f.id===addon.feature.id)]=addon.feature; })(window.MC_TWEAKS, '+json.dumps(addon,ensure_ascii=False,indent=1)+');\n'
    app=files["app.js"]
    for name,block in (("REF_MAINOS",main),("REF_MODS",mods)):
        match=refs.BLOCKS[name].search(app)
        assert match,name
        app=app[:match.start(2)]+"\n"+block+app[match.end(2):]
    app=app.replace('const GUIDE = "../guide/";', 'const GUIDE = "guide.html";')
    app=app.replace('Hardware tested by AveyCole on 10 October 2026.', 'Four-row scrolling layout: awaiting hardware display check. Generation engine previously hardware tested by AveyCole.')
    app=app.replace('Testé sur machine par AveyCole le 10/10/2026.', 'Affichage défilant à quatre lignes : essai écran sur machine attendu. Moteur de génération déjà testé par AveyCole.')
    files["app.js"]=app
    html=files["index.html"].replace('<script src="tweaks.js?', '<script src="../flasher/tweaks.js?v='+STAMP+'"></script>\n<script src="tweaks.js?',1)
    html=html.replace('<main class="wrap fl">','<main class="wrap fl">\n  '+BANNER,1)
    html=html.replace('<title>Model:Cycles', '<title>Scrolling Generator Test — Model:Cycles',1)
    html=re.sub(r'window.MC_BUILD = "[^"]+"',f'window.MC_BUILD = "{STAMP}"',html)
    files["index.html"]=re.sub(r'\?v=[^"\s]+',f'?v={STAMP}',html)
    guide=(ROOT / "docs/guide/index.html").read_text()
    guide=guide.replace('<section id="scale-gen">','<section id="scale-gen"><p><span data-l="en">Test layout: four visible rows; turn DATA to scroll through all seven options. Current font size retained with more spacing and margins.</span><span data-l="fr">Affichage de test : quatre lignes visibles ; tournez DATA pour parcourir les sept options. Police conservée avec plus d’espacement et des marges.</span></p>',1)
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
    print(f"ok : flasher de test défilant, {count} combinaisons vérifiées")
if __name__ == "__main__":
    main()
