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

# Fonctionnalites proposees dans le flasher web, en cases a cocher. Une fonctionnalite peut
# avoir plusieurs variantes mutuellement exclusives (ex. la sortie 6 canaux) : elles s'affichent
# en sous-choix quand la case est cochee. Chaque variante pointe vers un tweak de tweaks/.
# Pour ajouter une fonctionnalite : ecrire son tweak JSON, puis l'ajouter ici.
FEATURES = [
    {
        "id": "usb6",
        "label": "Sortie USB 6 canaux separes",
        "desc": "Chaque piste sort sur son propre canal USB (48 kHz / 32 bits). Le mix stereo "
                "n'est plus envoye en USB : tu melanges les 6 pistes dans ton logiciel.",
        "variants": [
            {"file": "11-6ch-usbup", "label": "Garder la mise a jour de l'OS par USB (recommande)"},
            {"file": "10-6ch-multiout", "label": "Version de reference (la mise a jour par USB ne marche plus)"},
        ],
    },
    {
        "id": "sdvintage",
        "label": "Machine SD VINTAGE (caisse claire vintage)",
        "desc": "Ajoute un moteur de caisse claire facon Syntakt, a la place de la machine SNARE. "
                "PITCH l'accord, DECAY la longueur, COLOR le cote claquant, SHAPE la brillance, "
                "SWEEP le balayage, CONTOUR la duree du corps.",
        "variants": [
            {"file": "20-sdvintage-snare", "label": None},
        ],
    },
]


def render():
    device = json.loads((DEV_DIR / "device.json").read_text(encoding="utf-8"))
    tweaks, seen, features = [], {}, []
    for f in FEATURES:
        variants = []
        for v in f["variants"]:
            t = json.loads((DEV_DIR / f"{v['file']}.json").read_text(encoding="utf-8"))
            if t["id"] not in seen:
                seen[t["id"]] = True
                tweaks.append(t)
            variants.append({"id": t["id"], "label": v["label"]})
        features.append({"id": f["id"], "label": f["label"], "desc": f["desc"], "variants": variants})
    payload = {
        "device": {k: device[k] for k in ("device", "os", "section_sha256", "stock_syx_sha256")},
        "tweaks": tweaks,
        "features": features,
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
    print(f"ecrit : {OUT.relative_to(ROOT)} ({len(text)} o, {len(FEATURES)} fonctionnalites)")


if __name__ == "__main__":
    main()
