#!/usr/bin/env python3
"""Compile la machine SD VINTAGE et écrit son tweak (étape 1 : à la place de SNARE).

Source : tools/machines/sdvintage/sdvintage.c (C, clean-room). Compilé pour le ColdFire
MCF54418 du Model:Cycles (m68k-linux-gnu-gcc, -mcpu=54418), lié à adresse fixe dans deux
masques de sprites libérés (tools/sprites.py), puis converti en écritures JSON :

  - le code dans les deux zones libérées (ancien contenu : 0xFF) ;
  - les deux redirections de sprites qui libèrent ces zones ;
  - les entrées SNARE des tables de machines (rendu 0x40118614, réglage 0x4011862c) ;
  - les valeurs par défaut des potards SNARE, adaptées au nouveau moteur.

Il n'a pas besoin de l'image firmware : les octets « old » sont des constantes de l'OS 1.13
(notes/14), vérifiées par build.py sur TON image au moment du build.

    python3 tools/gen_sdvintage.py            # compile et (ré)écrit 20-sdvintage-snare.json
    python3 tools/gen_sdvintage.py --check    # vérifie que le JSON versionné correspond au source

Toolchain : paquet Debian/Ubuntu gcc-m68k-linux-gnu, ou m68k-elf-gcc de Homebrew sur macOS
(pris automatiquement si le premier est absent ; M68K_CROSS=<préfixe> pour forcer). Un autre GCC peut
produire d'autres octets : --check le signalera, le JSON versionné reste la référence testée.
"""
import argparse
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

import sprites

HERE = pathlib.Path(__file__).resolve().parent
SRC_DIR = HERE / "machines" / "sdvintage"
DST = HERE.parent / "tweaks" / "model-cycles_OS1.13" / "20-sdvintage-snare.json"
BASE = 0x40000400
CROSS = os.environ.get("M68K_CROSS") or next(
    (c for c in ("m68k-linux-gnu-", "m68k-elf-") if shutil.which(c + "gcc")), "m68k-linux-gnu-")
CFLAGS = ["-mcpu=54418", "-O2", "-ffreestanding", "-fno-builtin", "-nostdlib", "-fno-pic", "-fno-common",
          "-ffunction-sections", "-fdata-sections", "-fomit-frame-pointer", "-Wall", "-Wextra", "-Werror"]

# OS 1.13 : tables des machines, index 1 = SNARE (notes/14 §2)
RENDER_TAB, UPDATE_TAB = 0x40118610, 0x40118628
STOCK = {"render": 0x400ab6e8, "update": 0x400ab3b0}
CAVES = {".cave_a": 0x4016cae8, ".cave_b": 0x4018a788}      # = link.ld
# Descripteurs de paramètres SNARE : champ « défaut » (mot 32 bits, valeur 8.8), notes/14 §1
# Défauts SD VINTAGE = ceux du vrai SD VINTAGE du Syntakt (INHM 0, FCMP 110, SWEP 74, MENV 80, DEC 33 ;
# descripteurs de son interface, notes/16 §4).
DEFAULTS = {  # nom: (va du champ, défaut d'origine, défaut SD VINTAGE)
    "color":   (0x4010e818, 0, 0),
    "shape":   (0x4010e850, 127, 110),
    "sweep":   (0x4010e888, 8, 74),
    "contour": (0x4010e8c0, 0, 80),
    "decay":   (0x4010e8f8, 40, 33),
}


def run(cmd, **kw):
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kw).stdout


def compile_machine(tmp):
    obj, elf = tmp / "sdvintage.o", tmp / "sdvintage.elf"
    run([CROSS + "gcc", *CFLAGS, "-c", str(SRC_DIR / "sdvintage.c"), "-o", str(obj)])
    run([CROSS + "ld", "-T", str(SRC_DIR / "link.ld"), "-o", str(elf), str(obj)])
    heads = run([CROSS + "objdump", "-h", str(elf)])
    for bad in (" .data", " .bss"):
        if bad in heads:
            raise SystemExit(f"!! section {bad.strip()} interdite (tout doit être en lecture seule)")
    blobs = {}
    for sec, va in CAVES.items():
        out = tmp / (sec.strip(".") + ".bin")
        run([CROSS + "objcopy", "-O", "binary", "-j", sec, str(elf), str(out)])
        blobs[va] = out.read_bytes()
        size = sprites.MASKS[va][0]
        if len(blobs[va]) > size:
            raise SystemExit(f"!! {sec} : {len(blobs[va])} o > {size} o disponibles")
    syms = {}
    for line in run([CROSS + "nm", str(elf)]).splitlines():
        a, _, name = line.split()
        syms[name] = int(a, 16)
    return blobs, syms


def be32(x):
    return (x & 0xffffffff).to_bytes(4, "big").hex()


def derive(blobs, syms):
    writes = []
    for va, code in blobs.items():
        writes.append({"off": va - BASE, "old": "ff" * len(code), "new": code.hex()})
        writes.append(sprites.redirect_write(va))
    writes.append({"off": RENDER_TAB + 4 - BASE, "old": be32(STOCK["render"]), "new": be32(syms["sdv_render"])})
    writes.append({"off": UPDATE_TAB + 4 - BASE, "old": be32(STOCK["update"]), "new": be32(syms["sdv_update"])})
    for va, old, new in DEFAULTS.values():
        if new != old:
            writes.append({"off": va - BASE, "old": be32(old << 8), "new": be32(new << 8)})
    writes.sort(key=lambda w: w["off"])
    sizes = ", ".join(f"{len(c)} o @ 0x{va:08x}" for va, c in blobs.items())
    return {
        "id": "sdvintage-snare",
        "order": 20,
        "name": "Machine SD VINTAGE a la place de SNARE (etape 1)",
        "description": [                          # ASCII, comme les autres tweaks
            "Remplace le moteur de la machine SNARE par SD VINTAGE : caisse claire vintage (v2),",
            "recalee sur le vrai SD VINTAGE du Syntakt mesure en emulation (notes/16), clean-room.",
            "Potards au sens du Syntakt : PITCH = TUNE | COLOR = INHM (2e mode) | SHAPE = FCMP (amas aigu) |",
            "SWEEP = SWEP (balayage) | CONTOUR = MENV (2e mode) | DECAY = DEC. PUNCH, GATE, LFO : d'origine.",
            f"Code compile depuis tools/machines/sdvintage ({sizes}), dans deux masques de",
            "sprites liberes (tools/sprites.py). Defauts du Syntakt : COLOR 0, SHAPE 110, SWEEP 74, CONTOUR 80, DECAY 33.",
            "v1 validee sur materiel le 29/09/2026 ; v2 validee en emulation, a reecouter sur la machine.",
        ],
        "device": "Model:Cycles",
        "os": "1.13",
        "section": 3,
        "writes": writes,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="vérifie que le JSON versionné correspond au source")
    args = ap.parse_args()
    with tempfile.TemporaryDirectory() as d:
        blobs, syms = compile_machine(pathlib.Path(d))
    tweak = derive(blobs, syms)
    text = json.dumps(tweak, indent=1) + "\n"
    for va, code in blobs.items():
        print(f"  0x{va:08x} : {len(code)} o / {sprites.MASKS[va][0]}")
    print(f"  sdv_update 0x{syms['sdv_update']:08x}, sdv_render 0x{syms['sdv_render']:08x}, "
          f"{len(tweak['writes'])} écritures")
    if args.check:
        if not DST.exists() or DST.read_text(encoding="utf-8") != text:
            raise SystemExit(f"!! {DST.name} ne correspond pas au source (autre GCC ? relance sans --check)")
        print(f"  {DST.name} est à jour")
        return
    DST.write_text(text, encoding="utf-8")
    print(f"  écrit : {DST.relative_to(HERE.parent)}")


if __name__ == "__main__":
    sys.exit(main())
