#!/usr/bin/env python3
"""Génère l'expérience MIDI OUT/THRU commutable avec FUNC + appui (note 50).

    python3 tools/gen_midi_live_both.py --cycles firmware/model-cycles_OS1.13.syx [--check]

Le sélecteur reste OUT/THR. En THR, FUNC + appui sur l'encodeur alterne le THRU stock
et l'émission MIDI combinée. Expérience isolée, à ne pas confondre avec le mod testé 44.
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
CAVE = 0x40167C50
CFG = 0x404E9B50


def stock_mainos(path):
    sys.path.insert(0, str(HERE))
    from mtlib.syx import unwrap
    from mtlib import aplib, container
    raw = pathlib.Path(path).read_bytes()
    stream, _ = unwrap(raw)
    c = container.parse(stream)
    sec = next(s for s in c["sections"] if s["id"] == 3)
    main, _ = aplib.depack(c["blob"][sec["off"]:sec["off"] + sec["size"]])
    device = json.loads((DEV / "device.json").read_text(encoding="utf-8"))
    if hashlib.sha256(raw).hexdigest() != device["stock_syx_sha256"]:
        raise SystemExit("!! ce n'est pas le fichier Model:Cycles OS 1.13 officiel attendu")
    if hashlib.sha256(main).hexdigest() != device["section_sha256"]:
        raise SystemExit("!! la section 3 ne correspond pas à l'OS 1.13 de référence")
    return main


def helper_code():
    """Construit les deux petits helpers et le callback stock de repli."""
    b = bytearray()
    labels, fixups = {}, []

    def emit(h):
        b.extend(bytes.fromhex(h))

    def label(name):
        labels[name] = len(b)

    def branch(op, name):
        fixups.append((len(b), name))
        b.extend(bytes.fromhex(op + "0000"))

    # Callback de la ligne OUT/THRU. L'index physique 10 correspond à FUNC;
    # 0x4007faf4 lit son état courant dans le bitmap scruté par l'OS.
    emit("4878000a4eb94007faf4588f4a80")
    branch("6700", "stock")
    emit("4eb940044df84a80")
    branch("6700", "stock")
    emit("1039404e9b500c000002")
    branch("6700", "set_thru")
    emit("7002")
    branch("6000", "write")
    label("set_thru")
    emit("7001")
    label("write")
    # Même chemin de copie/notification que le setter stock; un mot local aligné
    # évite l'écriture d'un octet directement dans la structure de configuration.
    emit("4e56fffc1d40ffff48780001486effff4879404e9b504eb940044b884fef000c4e5e4e75")
    label("stock")
    # Callback original inchangé pour l'appui normal, ou FUNC + OUT.
    emit("4eb940044df84a8057c0710044802f4000044ef940044dc2")

    entry_len = len(b)
    # Getter des portes MIDI : seule la valeur stock THRU (1) bloque la sortie
    # générée. La valeur cachée 2 garde le relais entrant et autorise la sortie.
    label("gate")
    emit("1039404e9b500c000001670470004e7570014e75")

    for pos, name in fixups:
        target = labels[name]
        # ColdFire Bcc.w displacement is relative to the extension word.
        disp = target - (pos + 2)
        if not -32768 <= disp <= 32767:
            raise SystemExit("!! branchement hors portée")
        b[pos + 2:pos + 4] = disp.to_bytes(2, "big", signed=True)

    # Keep a separated entry point for the gates, after callback + stock fallback.
    return bytes(b), entry_len


def generate(main):
    import build
    import sprites

    code, gate_off = helper_code()
    tweak = {
        "id": "midi-live-both", "order": 45,
        "name": "MIDI THRU combiné (FUNC + appui)",
        "description": [
            "Expérience : en THR, FUNC + appui sur l'encodeur OUT/THRU alterne entre le relais seul et le relais avec l'émission MIDI du Cycles.",
            "L'écran reste sur THR. Généré par tools/gen_midi_live_both.py (note 50).",
        ],
        "device": "Model:Cycles", "os": "1.13", "section": 3,
        "conflicts": ["midi-both", "midi-bth-three-state"], "writes": [],
    }

    def add(va, old, new, label):
        off = va - BASE
        if main[off:off + len(old)] != old:
            raise SystemExit(f"!! octets inattendus pour {label} à {va:#x}")
        tweak["writes"].append({"off": off, "old": old.hex(), "new": new.hex()})

    # Remplacement de l'entrée de callback par un saut vers le code expérimental.
    old_cb = bytes.fromhex("4eb940044df84a8057c0710044802f4000044ef940044dc2")
    new_cb = b"\x4e\xf9" + CAVE.to_bytes(4, "big") + b"\x4e\x71" * 9
    add(0x4003560A, old_cb, new_cb, "callback OUT/THRU")
    for va in (0x4000154A, 0x4000156A, 0x40001590):
        add(va, bytes.fromhex("4eb940044df8"),
            b"\x4e\xb9" + (CAVE + gate_off).to_bytes(4, "big"), f"porte MIDI {va:#x}")
    tweak["writes"].append(sprites.redirect_write(CAVE))
    add(CAVE, main[CAVE - BASE:CAVE - BASE + len(code)], code, "helpers MIDI")
    build.apply_writes(main, [tweak])
    return tweak


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cycles", required=True)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    content = json.dumps(generate(stock_mainos(args.cycles)), indent=1, ensure_ascii=False) + "\n"
    out = DEV / "45-midi-live-both.json"
    if args.check:
        ok = out.exists() and out.read_text(encoding="utf-8") == content
        print(f"{out.name}: {'à jour' if ok else 'NE CORRESPOND PAS'}")
        raise SystemExit(0 if ok else 1)
    out.write_text(content, encoding="utf-8")
    print(f"écrit : {out}")


if __name__ == "__main__":
    main()
