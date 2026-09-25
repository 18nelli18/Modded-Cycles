#!/usr/bin/env python3
"""Embarque les tables de patchs dans docs/flasher/tweaks.js pour le flasher web.

Le flasher web (docs/flasher/) construit le .syx dans le navigateur ; il lui
faut les tweaks. Plutot que de les lire par fetch (chemins fragiles sous GitHub
Pages, ne marche pas en file://), on les embarque dans un petit .js genere ici,
a partir des JSON canoniques de tweaks/. Source unique : ce script recopie, il
n'invente rien.

    python3 tools/gen_flasher_tweaks.py           # (re)genere docs/flasher/tweaks.js
    python3 tools/gen_flasher_tweaks.py --check    # verifie qu'il est a jour (CI)
"""
import argparse
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
DEV_DIR = ROOT / "tweaks" / "model-cycles_OS1.13"
OUT = ROOT / "docs" / "flasher" / "tweaks.js"
# Tweaks proposes dans le flasher web (ceux qui produisent une image flashable) et leur
# place dans l'interface : « variant » = menu Sortie USB (un seul), « option » = case a cocher.
INCLUDE = {"10-6ch-multiout": "variant", "11-6ch-usbup": "variant", "20-sdvintage-snare": "option"}


def render():
    device = json.loads((DEV_DIR / "device.json").read_text(encoding="utf-8"))
    tweaks = []
    for name, role in INCLUDE.items():
        t = json.loads((DEV_DIR / f"{name}.json").read_text(encoding="utf-8"))
        t["web"] = role
        tweaks.append(t)
    payload = {
        "device": {k: device[k] for k in ("device", "os", "section_sha256", "stock_syx_sha256")},
        "tweaks": tweaks,
    }
    body = json.dumps(payload, ensure_ascii=False, indent=1)
    return (
        "/* Genere par tools/gen_flasher_tweaks.py depuis tweaks/model-cycles_OS1.13/.\n"
        " * NE PAS editer a la main : relance le script apres avoir change un tweak. */\n"
        "window.MC_TWEAKS = " + body + ";\n"
    )


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="verifie sans ecrire")
    args = ap.parse_args()
    text = render()
    if args.check:
        if not OUT.exists() or OUT.read_text(encoding="utf-8") != text:
            sys.exit("!! docs/flasher/tweaks.js n'est pas a jour : relance tools/gen_flasher_tweaks.py")
        print("docs/flasher/tweaks.js est a jour")
        return
    OUT.write_text(text, encoding="utf-8")
    print(f"ecrit : {OUT.relative_to(ROOT)} ({len(text)} o, {len(INCLUDE)} tweaks)")


if __name__ == "__main__":
    main()
