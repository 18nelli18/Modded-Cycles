#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Génère 49-octave-shortcuts.json : TRACK + TRIG 1/16 règle KBT de −/+12 (notes/73).

Le callback KeyboardView rejoint le setter KBT de l'OS. Code original MIT dans
machines/octave_shortcuts, placé dans un masque partagé exclusivement avec Chord Keys.
Aucun chargeur de démarrage, état global ni changement des LED.

    python3 tools/gen_octave_shortcuts.py --cycles model-cycles_OS1.13.syx [--check]
"""
import argparse
import hashlib
import json
import pathlib
import shutil
import struct
import subprocess
import tempfile

import build
import sprites
from mtlib import aplib, container
from mtlib.syx import unwrap

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "tools/machines/octave_shortcuts"
OUT = ROOT / "tweaks/model-cycles_OS1.13/49-octave-shortcuts.json"
BASE = build.BASE
MASK = 0x4018d4a8
HOOK = 0x400ff9cc
CROSS = next((p for p in ("m68k-linux-gnu-", "m68k-elf-") if shutil.which(p + "as")), "m68k-linux-gnu-")


def main_os(path):
    stream, _ = unwrap(pathlib.Path(path).read_bytes())
    c = container.parse(stream)
    section = next(s for s in c["sections"] if s["id"] == 3)
    return aplib.depack(c["blob"][section["off"]:section["off"] + section["size"]])[0]


def build_tweak(stock):
    device = json.loads((OUT.parent / "device.json").read_text(encoding="utf-8"))
    if hashlib.sha256(stock).hexdigest() != device["section_sha256"]:
        raise ValueError("MAIN OS officiel 1.13 requis")
    if stock[HOOK - BASE:HOOK - BASE + 4] != struct.pack(">I", 0x4001a0d2):
        raise ValueError("Callback KeyboardView inattendu")
    size, _, _, shared = sprites.MASKS[MASK]
    if stock[MASK - BASE:MASK - BASE + size] != stock[shared - BASE:shared - BASE + size]:
        raise ValueError("Masques de sprite différents")
    with tempfile.TemporaryDirectory() as folder:
        folder = pathlib.Path(folder)
        obj, elf, binary = folder / "oct.o", folder / "oct.elf", folder / "oct.bin"
        subprocess.run([CROSS + "as", "-mcpu=54418", str(SRC / "octave_shortcuts.S"), "-o", str(obj)], check=True)
        subprocess.run([CROSS + "ld", "-T", str(SRC / "octave_shortcuts.ld"), "-o", str(elf), str(obj)], check=True)
        symbols = {p[2]: int(p[0], 16) for line in subprocess.check_output([CROSS + "nm", str(elf)], text=True).splitlines()
                   if len(p := line.split()) == 3}
        subprocess.run([CROSS + "objcopy", "-O", "binary", "-j", ".cave", str(elf), str(binary)], check=True)
        code = binary.read_bytes()
    if symbols["octave_keyboard"] != MASK or len(code) > size:
        raise ValueError("Code trop grand ou mal placé")
    writes = [sprites.redirect_write(MASK),
              {"off": MASK - BASE, "old": stock[MASK - BASE:MASK - BASE + len(code)].hex(), "new": code.hex()},
              {"off": HOOK - BASE, "old": stock[HOOK - BASE:HOOK - BASE + 4].hex(),
               "new": struct.pack(">I", symbols["octave_keyboard"]).hex()}]
    tweak = {
        "id": "octave-shortcuts", "order": 49,
        "name": "Octave du clavier avec TRACK + TRIG 1/16",
        "description": [
            "Hors mode grille, TRACK + TRIG 1 descend KBT de 12 demi-tons ; TRACK + TRIG 16 le monte de 12.",
            "Le KBT réel de la piste est changé par le setter de l'OS : Track Setup affiche la même valeur, "
            "bornée entre −60 et +60. Le décalage par demi-tons est conservé sauf à ces bornes.",
            "Un changement par appui, aucun au maintien. Les raccourcis ne jouent ni n'enregistrent une note. "
            "Les relâchements gardent le traitement stock. FUNC, PATTERN ou RETRIG tenus : traitement stock.",
            "Clavier et enregistrement live ; mode grille inchangé. Aucun éclairage ajouté. Incompatible avec Chord Keys et Model-TG.",
            f"Code original MIT : {len(code)} o dans le masque 0x4018d4a8, redirigé vers 0x40172220 ; "
            "partagé avec Chord Keys, les deux mods étant exclusifs. Généré par tools/gen_octave_shortcuts.py, notes/73.",
        ],
        "device": "Model:Cycles", "os": "1.13", "section": 3,
        "conflicts": ["chord-keys", "model-tg", "model-tg-st"],
        "symbols": {"octave_keyboard": hex(symbols["octave_keyboard"])},
        "writes": sorted(writes, key=lambda w: w["off"]),
    }
    build.apply_writes(stock, [tweak])
    return tweak


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True, help="model-cycles_OS1.13.syx officiel")
    ap.add_argument("--check", action="store_true", help="vérifie le JSON versionné")
    args = ap.parse_args()
    tweak = build_tweak(main_os(args.cycles))
    text = json.dumps(tweak, indent=1, ensure_ascii=False) + "\n"
    if args.check:
        ok = OUT.exists() and OUT.read_text(encoding="utf-8") == text
        print(f"{OUT.name} : {'à jour' if ok else 'différent'}")
        raise SystemExit(0 if ok else 1)
    OUT.write_text(text, encoding="utf-8")
    print(f"{OUT.name} : {len(tweak['writes'])} écritures")


if __name__ == "__main__":
    main()
