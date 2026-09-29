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
# avoir plusieurs variantes mutuellement exclusives : elles s'affichent en sous-choix quand la
# case est cochee. Chaque variante pointe vers un tweak de tweaks/.
# Le flasher web n'envoie que par USB (CONFIG > UPGRADE) : il ne propose que des tweaks qui gardent
# cette mise a jour par USB. 6ch-multiout (la casse) et sdvintage-snare restent dans build.py.
# status : "tested" (flashe sur un vrai Model:Cycles) ou "experimental".
# credit : auteur du travail d'origine, affiche sur la carte (voir aussi les credits de la page).
# Pour ajouter une fonctionnalite : ecrire son tweak JSON, puis l'ajouter ici.
FEATURES = [
    {
        "id": "usb6",
        "label": "Sortie USB 6 canaux separes",
        "desc": "Chaque piste sort sur son propre canal USB (48 kHz / 32 bits). Le mix stereo "
                "n'est plus envoye en USB : tu melanges les 6 pistes dans ton logiciel.",
        "status": "tested",
        "credit": {"kind": "based", "who": "scottmetoyer", "repo": "scottmetoyer/ms-multi-output"},
        "variants": [
            {"file": "11-6ch-usbup", "label": None},
        ],
    },
    {
        "id": "latching-mute",
        "label": "Mode mute verrouille",
        "desc": "Maintiens TRK et tape FUNC : le mode mute reste actif, tu mutes les pistes sans tenir FUNC. "
                "Un appui court sur FUNC en sort.",
        "status": "tested",
        "credit": {"kind": "by", "who": "drumkilla", "repo": "drumkilla/elektron-model-tweaks"},
        "variants": [
            {"file": "01-latching-mute", "label": None},
        ],
    },
    {
        "id": "trig-preview",
        "label": "Ecoute d'un pas (TRIG + PAGE)",
        "desc": "Sequenceur a l'arret, maintiens un pas et appuie sur PAGE : le pas joue avec sa note, "
                "sa longueur et ses p-locks.",
        "status": "tested",
        "credit": {"kind": "by", "who": "drumkilla", "repo": "drumkilla/elektron-model-tweaks"},
        "variants": [
            {"file": "02-trig-preview", "label": None},
        ],
    },
    {
        "id": "browser-scroll",
        "label": "Defilement des noms longs",
        "desc": "Dans le navigateur de sons, un nom trop long pour l'ecran defile.",
        "status": "tested",
        "credit": {"kind": "by", "who": "drumkilla", "repo": "drumkilla/elektron-model-tweaks"},
        "variants": [
            {"file": "03-browser-scroll", "label": None},
        ],
    },
    {
        "id": "sdvintage",
        "label": "Vrai moteur SD VINTAGE du Syntakt",
        "desc": "Le moteur SD VINTAGE du Syntakt remplace la machine SNARE, extrait de TON fichier "
                "Syntakt_OS1.41.syx (a deposer a l'etape 2). Identique au Syntakt en emulation.",
        "status": "experimental",
        "credit": None,
        "needs": "syntakt",
        "variants": [
            {"file": "21-sdvintage-exact", "label": None},
        ],
    },
]


def render():
    from crossflash import OFFICIAL            # empreintes des OS officiels, source unique (tools/crossflash.py)
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
        feat = {"id": f["id"], "label": f["label"], "desc": f["desc"], "status": f["status"],
                "credit": f["credit"], "variants": variants}
        if f.get("needs"):
            feat["needs"] = f["needs"]
        features.append(feat)
    payload = {
        "device": {k: device[k] for k in ("device", "os", "section_sha256", "stock_syx_sha256", "cave_refs_ok")
                   if k in device},
        "tweaks": tweaks,
        "features": features,
        # onglet « OS Samples » : l'OS Model:Samples officiel, mis dans le conteneur du Cycles (crossflash)
        "samples": {"syx_sha256": OFFICIAL["samples"]["syx"], "main_sha256": OFFICIAL["samples"]["main"],
                    "download": "https://www.elektron.se/support-downloads/modelsamples"},
        # fonctionnalités « needs: syntakt » : le fichier officiel Syntakt_OS1.41.syx de l'utilisateur
        "syntakt": {"download": "https://www.elektron.se/support-downloads/syntakt"},
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
