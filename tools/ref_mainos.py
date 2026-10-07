#!/usr/bin/env python3
"""Empreintes de référence du flasher web (REF_MAINOS dans docs/flasher/app.js).

Pour chaque combinaison que la page propose (cases de docs/flasher/tweaks.js, dans l'ordre des cartes ;
pour les vrais moteurs du Syntakt, chaque combinaison de moteurs cochés), calcule le SHA-256 du MAIN OS
modifié, exactement comme tools/build.py, puis réécrit le bloc REF_MAINOS de app.js (ou le vérifie).
Une carte « requires » (l'écoute des samples, un ajout à Model-TG) ne compte qu'avec la carte qu'elle demande :
la page coche l'autre avec elle.
Le flasher refuse tout firmware construit dont le MAIN OS ne correspond pas.

    python3 tools/ref_mainos.py --cycles model-cycles_OS1.13.syx --syntakt Syntakt_OS1.42.syx [--check]
"""
import argparse
import itertools
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "emu"))

import build                       # noqa: E402

ROOT = HERE.parent
TWEAKS_JS = ROOT / "docs" / "flasher" / "tweaks.js"
APP_JS = ROOT / "docs" / "flasher" / "app.js"
BLOCK = re.compile(r"(const REF_MAINOS = \{\n)(.*?)(\n\};\n)", re.S)


def mc_tweaks():
    text = TWEAKS_JS.read_text(encoding="utf-8")
    return json.loads(text[text.index("window.MC_TWEAKS = ") + len("window.MC_TWEAKS = "):text.rindex(";")])


def main_os(cycles):
    """MAIN OS décompressé du .syx officiel, comme tools/build.py."""
    c = build.container.parse(build.unwrap(pathlib.Path(cycles).read_bytes())[0])
    s3 = next(s for s in c["sections"] if s["id"] == 3)
    return build.aplib.depack(c["blob"][s3["off"]:s3["off"] + s3["size"]])[0]


def options(f):
    """Choix possibles d'une carte : ses variantes, ou ses combinaisons de moteurs."""
    return [c["id"] for c in f.get("combos") or f["variants"]]


def block(cycles, syntakt):
    tw = mc_tweaks()
    by_id = {t["id"]: t for t in tw["tweaks"]}
    base = [f for f in tw["features"] if not f.get("needs")]
    extra = [f for f in tw["features"] if f.get("needs")]
    if len(extra) > 1 or any(len(options(f)) != 1 for f in base):
        raise SystemExit("!! disposition des cartes inattendue : adapter ref_mainos.py")
    stock = main_os(cycles)
    # carte « requires » : la page ne la laisse cochée qu'avec la carte qu'elle demande (tweak de cette carte)
    cards = {g["id"]: g for g in base}
    need = {}
    for f in base:
        if f.get("requires"):
            if f["requires"] not in cards:
                raise SystemExit(f"!! la carte {f['id']} demande (requires) {f['requires']!r}, qui n'est pas une carte "
                                 "à variantes de tweaks.js : relancer tools/gen_flasher_tweaks.py, ou adapter ref_mainos.py")
            need[options(f)[0]] = options(cards[f["requires"]])[0]
    subsets = [c for r in range(len(base) + 1) for c in itertools.combinations([options(f)[0] for f in base], r)
               if all(need[i] in c for i in c if i in need)]
    payloads = {}
    # avec les moteurs du Syntakt, une carte « with » (Model-TG) prend un autre tweak, et les moteurs le leur (tg) ;
    # une carte « requires » de Model-TG (l'écoute des samples) prend la sienne en même temps que Model-TG
    alt = {options(f)[0]: f["with"][extra[0]["id"]] for f in base if extra and extra[0]["id"] in f.get("with", {})}
    tg_of = {c["id"]: c["tg"] for c in extra[0]["combos"]} if extra else {}

    def payload(apps):
        """Charges utiles des tweaks « append » choisis, l'une après l'autre (comme tools/build.py)."""
        key = tuple(t["id"] for t in apps)
        if key not in payloads:
            st = syntakt if any(t["append"].get("syntakt") for t in apps) else None
            payloads[key] = build.build_payload(apps, stock, st)[0]
        return payloads[key]
    lines = []
    for last in [None] + (options(extra[0]) if extra else []):
        if last:
            names = ", ".join(c["label"] for c in extra[0]["combos"] if c["id"] == last)
            lines.append(f"  // + real Syntakt engines {names} (tweak {last}), with the official Syntakt OS 1.42 or 1.41")
        for sub in subsets:
            ids = list(sub) + ([last] if last else [])
            if last and any(i in alt for i in sub if i not in need):   # version combinée (notes/31)
                ids = [alt.get(i, i) for i in sub] + [tg_of[last]]
            chosen = [by_id[i] for i in ids]
            if not ids or any(o in ids for t in chosen for o in t.get("conflicts", [])):
                continue                                  # cases incompatibles : la page ne les propose pas
            missing = [(t["id"], r) for t in chosen for r in t.get("requires", []) if r not in ids]
            if missing:                                   # comme build.check_conflicts : ne doit jamais arriver
                raise SystemExit(f"!! {missing[0][0]} demande {missing[0][1]} dans {'+'.join(ids)} : adapter ref_mainos.py")
            chosen.sort(key=lambda t: t["order"])
            apps = [t for t in chosen if t.get("append")]
            patched, _ = build.apply_writes(stock, chosen)
            lines.append(f'  "{"+".join(ids)}": "{build.sha(bytes(patched) + (payload(apps) if apps else b""))}",')
    return "\n".join(lines), len([x for x in lines if not x.lstrip().startswith("//")])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True, help="model-cycles_OS1.13.syx officiel")
    ap.add_argument("--syntakt", required=True, help="Syntakt_OS1.42.syx (ou 1.41) officiel")
    ap.add_argument("--check", action="store_true", help="vérifie que app.js est à jour")
    args = ap.parse_args()
    body, n = block(args.cycles, args.syntakt)
    app = APP_JS.read_text(encoding="utf-8")
    m = BLOCK.search(app)
    if not m:
        raise SystemExit("!! bloc REF_MAINOS introuvable dans app.js")
    if args.check:
        if m.group(2) != body:
            raise SystemExit(f"!! REF_MAINOS de app.js n'est pas à jour ({n} combinaisons) : relance tools/ref_mainos.py")
        print(f"REF_MAINOS est à jour ({n} combinaisons)")
        return
    APP_JS.write_text(app[:m.start(2)] + body + app[m.end(2):], encoding="utf-8")
    print(f"écrit : REF_MAINOS de {APP_JS.relative_to(ROOT)} ({n} combinaisons)")


if __name__ == "__main__":
    main()
