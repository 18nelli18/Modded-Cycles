#!/usr/bin/env python3
"""Fait aussi sortir le MIDI généré quand OUT/THRU est réglé sur THRU (notes/50).

    python3 tools/gen_midi_both.py --cycles firmware/model-cycles_OS1.13.syx [--check]

Le relais entrant reste celui de l'OS ; les trois portes d'émission sont ouvertes.
"""
import argparse
import hashlib
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
DEV = ROOT / "tweaks" / "model-cycles_OS1.13"
BASE = 0x40000400
def stock_mainos(path):
    """Lit et vérifie la section 3 de l'OS officiel fourni."""
    sys.path.insert(0, str(HERE))
    from mtlib.syx import unwrap
    from mtlib import aplib, container
    raw = pathlib.Path(path).read_bytes()
    stream, _ = unwrap(raw)
    c = container.parse(stream)
    s = next(s for s in c["sections"] if s["id"] == 3)
    main, _ = aplib.depack(c["blob"][s["off"]:s["off"] + s["size"]])
    device = json.loads((DEV / "device.json").read_text(encoding="utf-8"))
    if hashlib.sha256(raw).hexdigest() != device["stock_syx_sha256"]:
        raise SystemExit("!! ce n'est pas le fichier Model:Cycles OS 1.13 officiel attendu")
    if hashlib.sha256(main).hexdigest() != device["section_sha256"]:
        raise SystemExit("!! la section 3 ne correspond pas à l'OS 1.13 de référence")
    return main


def generate(main):
    tweak = {
        "id": "midi-both", "order": 44,
        "name": "MIDI OUT avec THRU",
        "description": [
            "Avec THRU sélectionné, le Cycles relaie toujours le MIDI reçu et envoie aussi son horloge et ses messages",
            "de piste/paramètres. OUT garde son comportement normal. Généré par tools/gen_midi_both.py (note 50).",
        ],
        "device": "Model:Cycles", "os": "1.13", "section": 3,
        "conflicts": [],
        "writes": [],
    }

    def add(va, old, new, label):
        off = va - BASE
        if main[off:off + len(old)] != old:
            raise SystemExit(f"!! octets inattendus pour {label} à {va:#x}")
        tweak["writes"].append({"off": off, "old": old.hex(), "new": new.hex()})

    # Le THRU d'origine relaie l'entrée mais bloque les messages générés.
    # Ces appels alimentent le test stock qui saute l'émission en mode THRU.
    # Un D0 nul conserve la suite normale et laisse sortir horloge et paramètres.
    for va in (0x4000154A, 0x4000156A, 0x40001590):
        add(va, bytes.fromhex("4eb940044df8"), bytes.fromhex("70004e714e71"), f"porte de sortie {va:#x}")
    import build
    build.apply_writes(main, [tweak])
    return tweak


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cycles", required=True)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    content = json.dumps(generate(stock_mainos(args.cycles)), indent=1, ensure_ascii=False) + "\n"
    out = DEV / "44-midi-both.json"
    if args.check:
        ok = out.exists() and out.read_text(encoding="utf-8") == content
        print(f"{out.name}: {'à jour' if ok else 'NE CORRESPOND PAS'}")
        raise SystemExit(0 if ok else 1)
    out.write_text(content, encoding="utf-8")
    print(f"écrit : {out}")


if __name__ == "__main__":
    main()
