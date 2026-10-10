#!/usr/bin/env python3
"""Flasher de test : catalogue de production complet + générateur en gamme.

Ne modifie jamais docs/flasher/. Recalcule toutes les empreintes avec les OS
locaux officiels. Exemple : python3 tools/gen_test_flasher.py --cycles
firmware/model-cycles_OS1.13.syx --syntakt firmware/Syntakt_OS1.42.syx [--check].
Le générateur reste expérimental, à la demande explicite d'aveycole (note 53).
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
STAMP = "2026-10-10-scale-gen-01"
FEATURE = {
    "id": "scale-gen", "cat": "seq", "status": "experimental",
    "label": "Générateur de séquence en gamme (test)",
    "desc": "SETTINGS + PAGE : notes en gamme, densité, bornes de notes et Undo. Transport arrêté. Demande Model-TG.",
    "credit": {"kind": "based", "who": "TinyGregAudio", "repo": "TinyGregAudio/Model-TG"},
    "license": "LICENSE-Model-TG", "requires": "model-tg",
    "variants": [{"file": "49-scale-gen", "label": None}],
    "with": {"syntakt": "49-scale-gen-st", "macro": "49-scale-gen-st"},
}
TEXT = {
    "en": {"label": "Scale sequence generator (test)",
           "short": "SETTINGS + PAGE: generate notes and trigs in your scale. Stopped transport only.",
           "desc": "Hold SETTINGS and press PAGE. Turn DATA to select Scale, Root, Low note, High note or Density; press to edit. Select Generate and press DATA to fill the active track length with notes and trigs. Undo restores the last generation while the page stays open. Note limits are inclusive MIDI numbers. Requires Model-TG and shares its Scale and Root settings.",
           "note": "Experimental hardware test: not hardware verified. Stop playback before Generate or Undo. Closing the page discards Undo. Parameter locks are retained; existing conditions and retrig settings can affect the generated trigs."},
    "fr": {"label": "Générateur de séquence en gamme (test)",
           "short": "SETTINGS + PAGE : générez notes et trigs en gamme. Transport arrêté uniquement.",
           "desc": "Maintenez SETTINGS et appuyez sur PAGE. Tournez DATA pour choisir Scale, Root, Low note, High note ou Density ; appuyez pour éditer. Choisissez Generate et appuyez sur DATA pour remplir la longueur active de la piste de notes et de trigs. Undo restaure la dernière génération tant que la page reste ouverte. Les bornes sont des numéros MIDI inclusifs. Demande Model-TG et partage ses réglages Scale et Root.",
           "note": "Essai matériel expérimental : non vérifié sur machine. Arrêtez la lecture avant Generate ou Undo. Fermer la page efface Undo. Les p-locks restent ; les conditions et réglages de retrig existants peuvent influencer les nouveaux trigs."},
}
BANNER = '''<div class="alert bad" role="alert" id="test-build-notice"><span data-l="en"><strong>EXPERIMENTAL TEST FLASHER</strong> — All existing mods plus the scale sequence generator. The generator has passed emulation checks but has not been tested on hardware. Use SETTINGS + PAGE with playback stopped. <a href="../flasher/">Production flasher</a>.</span><span data-l="fr"><strong>FLASHER DE TEST EXPÉRIMENTAL</strong> — Tous les mods existants et le générateur en gamme. Le générateur passe les vérifications en émulation mais n'a pas été essayé sur machine. Utilisez SETTINGS + PAGE, lecture arrêtée. <a href="../flasher/">Flasher de production</a>.</span></div>'''
GUIDE = '''<section id="scale-gen"><h2><span data-l="en">Test: scale sequence generator</span><span data-l="fr">Test : générateur de séquence en gamme</span></h2>
<p><span data-l="en">Requires Model-TG. Experimental: emulation checks passed; no hardware result yet.</span><span data-l="fr">Demande Model-TG. Expérimental : vérifications en émulation réussies, pas encore de résultat matériel.</span></p>
<ol><li><span data-l="en">Stop playback. Hold <b>SETTINGS</b> and press <b>PAGE</b>.</span><span data-l="fr">Arrêtez la lecture. Maintenez <b>SETTINGS</b> et appuyez sur <b>PAGE</b>.</span></li>
<li><span data-l="en">Turn <b>DATA</b> to select a field, press to edit, turn to change it, press to finish. Scale and Root share Model-TG's settings. Low/High note are inclusive MIDI numbers (default 48–72); Density is a per-step probability (default 50%).</span><span data-l="fr">Tournez <b>DATA</b> pour choisir un champ, appuyez pour éditer, tournez pour modifier, appuyez pour terminer. Scale et Root partagent les réglages Model-TG. Low/High note sont les bornes MIDI incluses (48–72 par défaut) ; Density est une probabilité par pas (50 % par défaut).</span></li>
<li><span data-l="en">Select <b>Generate</b> and press <b>DATA</b>. It replaces note trigs across the active length of the current track. Select <b>Undo</b> to restore the last generation.</span><span data-l="fr">Choisissez <b>Generate</b> et appuyez sur <b>DATA</b>. Les trigs de notes sont remplacés dans la longueur active de la piste courante. Choisissez <b>Undo</b> pour restaurer la dernière génération.</span></li></ol>
<p><span data-l="en">Undo lasts only while this page is open. BACK closes it. Parameter locks are retained; existing conditions and retrig settings still apply. Generate and Undo refuse active transport. “Check range/stop” means stop playback or choose a range containing a note of your scale.</span><span data-l="fr">Undo ne reste disponible que dans cette page. BACK la ferme. Les p-locks sont conservés ; les conditions et réglages de retrig existants restent actifs. Generate et Undo refusent le transport actif. « Check range/stop » demande d'arrêter la lecture ou de choisir une plage contenant une note de la gamme.</span></p></section>'''


def clean(path):
    """Retire la sortie shell accidentelle présente dans la base, jamais du JS."""
    return "\n".join(line for line in path.read_text().splitlines()
                     if not line.startswith("/opt/homebrew/Library/Homebrew/cmd/shellenv.sh:")) + "\n"


def render(cycles, syntakt):
    """Retourne les fichiers de test, sans toucher aux sources de production."""
    catalog.FEATURES = [f for f in catalog.FEATURES if f["id"] != "scale-gen"] + [FEATURE]
    tweaks = catalog.render()
    payload = catalog.read_js(tweaks)
    # Réutiliser le catalogue de production, puis ajouter deux petits tweaks.
    # Cela évite de republier plusieurs Mo de tables identiques.
    addon = {"tweaks": [t for t in payload["tweaks"] if t["id"] in ("scale-gen", "scale-gen-st")],
             "feature": next(f for f in payload["features"] if f["id"] == "scale-gen")}
    tweaks = "/* Généré par tools/gen_test_flasher.py ; catalogue de production chargé avant. */\n"
    tweaks += "(function (tw, addon) { tw.tweaks.push(...addon.tweaks); tw.features.push(addon.feature); })(window.MC_TWEAKS, " + json.dumps(addon, ensure_ascii=False, indent=1) + ");\n"
    refs.mc_tweaks = lambda: payload
    # Scanner une seule fois la réunion des caves de l'image officielle.
    # Le filtrage par combinaison garde exactement les contrôles dirty/patched.
    stock = refs.main_os(cycles)
    union = refs.build.cave_zones(stock, payload["tweaks"])
    hits = refs.build.refs_into(stock, union)
    scan = refs.build.refs_into
    def cached_scan(image, zones):
        assert image == stock
        return tuple([h for h in group if any(lo <= h[1] - refs.build.BASE < hi for lo, hi in zones)]
                     for group in hits)
    refs.build.refs_into = cached_scan
    refs.main_os = lambda path: stock
    print("ok : image officielle et références des caves relevées", flush=True)
    try:
        main, mods, count = refs.blocks(cycles, syntakt)
    finally:
        refs.build.refs_into = scan
    app = clean(PROD / "app.js")
    for key, value in (("REF_MAINOS", main), ("REF_MODS", mods)):
        match = refs.BLOCKS[key].search(app)
        assert match, key
        app = app[:match.start(2)] + "\n" + value + app[match.end(2):]
    start = app.index("const FEAT = {")
    before, body = app[:start], app[start:]
    for lang, text in TEXT.items():
        body = body.replace(f"  {lang}: {{", f"  {lang}: {{\n    \"scale-gen\": " + json.dumps(text, ensure_ascii=False) + ",", 1)
    app = (before + body).replace('const GUIDE = "../guide/";', 'const GUIDE = "guide.html";')
    app = app.replace("const GUIDE_OF = {", 'const GUIDE_OF = {\n  "scale-gen": "scale-gen",', 1)
    html = clean(PROD / "index.html")
    html = re.sub(r"<title>.*?</title>", "<title>Model:Cycles — Scale Generator Test Flasher</title>", html)
    html = html.replace('<script src="tweaks.js?', '<script src="../flasher/tweaks.js?v=' + STAMP + '"></script>\n<script src="tweaks.js?', 1)
    html = html.replace('<main class="wrap fl">' , '<main class="wrap fl">\n  ' + BANNER, 1)
    html = html.replace('../assets/release.js?', 'release.js?')
    html = re.sub(r'window.MC_BUILD = "[^"]+"', f'window.MC_BUILD = "{STAMP}"', html)
    html = re.sub(r'\?v=[^"\s]+', f'?v={STAMP}', html)
    guide = clean(ROOT / "docs/guide/index.html").replace("</main>", GUIDE + "\n</main>", 1)
    guide = guide.replace('../assets/release.js?', 'release.js?')
    files = {"release.js": clean(ROOT / "docs/assets/release.js"), "app.js": app, "tweaks.js": tweaks, "index.html": html, "guide.html": guide}
    for name in ("builder.js", "flasher.js", "style.css", "LICENSE-Model-TG.txt", "LICENSE-Braids.txt"):
        files[name] = clean(PROD / name)
    return {name: text.rstrip() + "\n" for name, text in files.items()}, count


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cycles", required=True)
    ap.add_argument("--syntakt", required=True)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    files, count = render(args.cycles, args.syntakt)
    OUT.mkdir(parents=True, exist_ok=True)
    for name, text in files.items():
        path = OUT / name
        if args.check:
            assert path.exists() and path.read_text() == text, f"{path} pas à jour"
        else:
            path.write_text(text)
    print(f"ok : flasher-test, catalogue de production complet + générateur ; {count} empreintes de combinaisons")


if __name__ == "__main__":
    main()
