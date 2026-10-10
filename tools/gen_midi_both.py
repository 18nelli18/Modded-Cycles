#!/usr/bin/env python3
"""Ajoute le choix MIDI BTH (OUT + THRU) au Model:Cycles (notes/50).

    python3 tools/gen_midi_both.py --cycles firmware/model-cycles_OS1.13.syx [--check]

Le petit adaptateur 68 octets tient dans un masque de sprite 35x35 libéré.
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
HELPER = 0x40167C50


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


def helpers():
    """Génère le sélecteur OUT/THR/BTH et le filtre qui bloque seulement en THRU."""
    menu = bytearray.fromhex(
        "4eb940044df8"          # jsr getter OUT/THRU (identifiant 0x50)
        "0c8000000002"          # cmpi.l #2,d0
        "6714"                  # beq BTH
        "4a80"                  # tst.l d0
        "6708"                  # beq OUT
        "203c40127281"          # move.l #THR,d0
        "4e75"
        "203c40127bad"          # move.l #OUT,d0
        "4e75"
        "203c00000000"          # move.l #BTH,d0
        "4e75"
    )
    menu[34:40] = b"\x20\x3c" + (HELPER + len(menu)).to_bytes(4, "big")
    menu += b"BTH\0"
    output = bytes.fromhex(
        "4eb940044df8"          # getter OUT/THRU (identifiant 0x50)
        "0c8000000001"          # compare à THRU
        "57c0"                  # seq d0
        "0280000000ff"          # renvoie 0 ou 255
        "4e75"
    )
    return bytes(menu + output)


def generate(main):
    tweak = {
        "id": "midi-both", "order": 44,
        "name": "MIDI OUT + THRU (BTH)",
        "description": [
            "Ajoute BTH au réglage CONFIG > MIDI > PORTS > OUT/THRU : envoie l'horloge et les messages MIDI du Cycles",
            "tout en relayant les messages reçus. OUT et THR gardent leur comportement d'origine. Généré par",
            "tools/gen_midi_both.py (note 50). Le helper est dans le masque 35x35 libéré 0x40167c50.",
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

    # Le masque 35x35 est identique aux autres, désormais renvoyés vers celui gardé.
    sys.path.insert(0, str(HERE))
    import sprites
    tweak["writes"].append(sprites.redirect_write(HELPER))
    helper = helpers()
    add(HELPER, main[HELPER - BASE:HELPER - BASE + len(helper)], helper, "helper MIDI")

    old_menu = bytes.fromhex("4eb940044df84a806708263c401272816006263c40127bad")
    new_menu = b"\x4e\xb9" + HELPER.to_bytes(4, "big") + b"\x26\x00" + b"\x4e\x71" * 8
    add(0x40035FD8, old_menu, new_menu, "menu OUT/THRU")
    add(0x40036008, bytes.fromhex("48780002"), bytes.fromhex("48780003"), "nombre de choix")
    for va in (0x4000154A, 0x4000156A, 0x40001590):
        add(va, bytes.fromhex("4eb940044df8"), b"\x4e\xb9" + (HELPER + 46).to_bytes(4, "big"), f"porte de sortie {va:#x}")
    sys.path.insert(0, str(HERE))
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
