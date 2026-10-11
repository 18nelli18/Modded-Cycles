#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Génère 61-mchn-lfo.json : sélection de machine comme destination MCHN du LFO (notes/58).

Les accesseurs renvoient l'éligibilité et le libellé de l'identifiant Algorithm (41), indépendamment de la
copie des descripteurs choisie par les machines ajoutées. Leurs bornes et les plages des machines restent intactes.
Code : masque 48×22 libéré, sans allocation RAM. Les autres identifiants suivent les fonctions de l'OS.

    python3 tools/gen_mchn_lfo.py --cycles model-cycles_OS1.13.syx [--check]
"""
import argparse
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

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE.parent / "tweaks/model-cycles_OS1.13/61-mchn-lfo.json"
BASE = build.BASE
MASK = 0x40152d38
HOOKS = ((0x4005a860, "202f0004b280", "mchn_flags"),
         (0x4000b20a, "202f0008b280", "mchn_short"))


def main_os(path):
    stream, _ = unwrap(pathlib.Path(path).read_bytes())
    parsed = container.parse(stream)
    section = next(s for s in parsed["sections"] if s["id"] == 3)
    return aplib.depack(parsed["blob"][section["off"]:section["off"] + section["size"]])[0]


def build_tweak(stock):
    cross = next((c for c in ("m68k-linux-gnu-", "m68k-elf-") if shutil.which(c + "gcc")), "m68k-linux-gnu-")
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        obj, elf, binary = (tmp / n for n in ("mchn.o", "mchn.elf", "mchn.bin"))
        ld = tmp / "mchn.ld"
        ld.write_text(f"SECTIONS {{ . = {MASK:#x}; .text : {{ *(.text) }} }}\n")
        commands = [[cross + "gcc", "-mcpu=54418", "-c", str(HERE / "machines/mchn_lfo/mchn_lfo.S"), "-o", str(obj)],
                    [cross + "ld", "-T", str(ld), "-o", str(elf), str(obj)],
                    [cross + "objcopy", "-O", "binary", str(elf), str(binary)]]
        for command in commands:
            subprocess.run(command, check=True, capture_output=True)
        code = binary.read_bytes()
        symbols = {p[2]: int(p[0], 16) for line in subprocess.check_output([cross + "nm", str(elf)], text=True).splitlines()
                   if len(p := line.split()) == 3}
    size, reference, _, kept = sprites.MASKS[MASK]
    if len(code) > size or stock[MASK - BASE:MASK - BASE + size] != stock[kept - BASE:kept - BASE + size]:
        raise SystemExit("!! masque libre absent ou trop petit")
    pointer = struct.pack(">I", MASK)
    refs = [i for i in range(len(stock)) if stock.startswith(pointer, i)]
    if refs != [reference - BASE]:
        raise SystemExit("!! références inattendues au masque")
    writes = [sprites.redirect_write(MASK)]
    def write(va, old, new):
        if len(old) != len(new) or stock[va - BASE:va - BASE + len(old)] != old:
            raise SystemExit(f"!! octets d'origine inattendus en {va:#x}")
        writes.append(dict(off=va - BASE, old=old.hex(), new=new.hex()))
    write(MASK, stock[MASK - BASE:MASK - BASE + len(code)], code)
    for va, old, symbol in HOOKS:
        write(va, bytes.fromhex(old), struct.pack(">HI", 0x4ef9, symbols[symbol]))
    write(0x40129965, b"Algorithm\0", b"MCHN\0" + bytes(5))
    return dict(id="mchn-lfo", order=61, name="Machine comme destination du LFO (MCHN)",
                description=["Choisissez MCHN dans DEST du LFO pour moduler la sélection de machine.",
                             "Conserve la plage de machines de la combinaison installée ; les autres destinations restent identiques.",
                             "L'éligibilité partagée rend aussi MCHN disponible comme destination de vélocité.",
                             "Contribution de djd_oz, licence MIT. Statut expérimental : à vérifier par le mainteneur sur sa machine.",
                             f"{len(code)} o dans un masque 48×22 libéré ({MASK:#x}), sans état en RAM. "
                             "Généré par tools/gen_mchn_lfo.py, notes/58."],
                device="Model:Cycles", os="1.13", section=3,
                symbols={k: hex(symbols[k]) for k in ("mchn_flags", "mchn_short")},
                writes=sorted(writes, key=lambda w: w["off"]))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cycles", required=True)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    stock = main_os(args.cycles)
    if build.sha(stock) != json.loads((OUT.parent / "device.json").read_text())["section_sha256"]:
        raise SystemExit("!! MAIN OS 1.13 officiel requis")
    tweak = build_tweak(stock)
    build.apply_writes(stock, [tweak])
    text = json.dumps(tweak, indent=1, ensure_ascii=False) + "\n"
    if args.check:
        if not OUT.exists() or OUT.read_text() != text:
            raise SystemExit("!! JSON MCHN différent du générateur")
        print("ok : JSON MCHN à jour")
    else:
        OUT.write_text(text)
        print(f"écrit : {OUT.name}")

if __name__ == "__main__":
    main()
