#!/usr/bin/env python3
"""Génère tweaks/model-cycles_OS1.13/71-out-sleep.json : l'étage de sortie allégé, son identique (notes/78).

Les raccourcis de l'étage de sortie de l'OS optimisé (notes/70, PR #98), testés sur la machine le 18/10/2026 (son
identique ; delay et reverb endormis -7 points, saturateur -2, envois -1), repris pour le Modded Cycles OS. L'OS
d'origine calcule tout l'étage de sortie à chaque bloc, même ce qui ne peut rien changer au son :
  - saturateur de Dist sauté quand la part « wet » d'une paire de pistes est nulle (VOL+DIST <= 60) :
    vd_skip.S, détour 0x40057062 ;
  - envois delay et reverb sautés quand leurs gains et leurs pentes sont nuls : send_skip.S, détours 0x40056716
    et 0x40056698 ;
  - sommeil du delay et de la reverb tant que tout ce qu'ils lisent est nul : fx_lib.S, fx_dly.S, fx_rev.S, détours
    0x40057516, 0x40057ac8, 0x40057dc6. Une fois servis, ils ne se rendorment plus avant le prochain allumage (leurs
    restes ne sont jamais exactement nuls).
Sans ce que l'OS optimisé faisait dans la boucle des voix (mix2, voix muettes, PUNCH), que Model-TG et nos machines
détournent, ni ses deux correctifs de gels (une autre PR).

Code dans les masques de sprites des fichiers testés sur la machine (tools/sprites.py), octets identiques.
tools/machines/out_sleep/ : sources (celles de tools/machines/os_optimise/ de la PR #98, telles quelles). Preuve :
tools/emu/test_out_sleep.py.

    python3 tools/gen_out_sleep.py --cycles model-cycles_OS1.13.syx [--check]
"""
import argparse
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import build                     # noqa: E402
import sprites                   # noqa: E402

SRC = HERE / "machines" / "out_sleep"
DEV = HERE.parent / "tweaks" / "model-cycles_OS1.13"
OUT = DEV / "71-out-sleep.json"
BASE = build.BASE
CROSS = next((c for c in ("m68k-linux-gnu-", "m68k-elf-") if shutil.which(c + "as")), "m68k-linux-gnu-")
MASK = {                         # masques libérés (REGISTRY.md §1), ceux de l'OS optimisé testé le 18/10/2026
    "vd_skip": 0x4016dab8,       # 48x22
    "fx_lib": 0x4016fae8,        # 48x22
    "send_skip": 0x40170c48,     # 48x22
    "fx_dly": 0x40189618,        # 34x34
    "fx_rev": 0x4018d918,        # 41x41
}
SYMBOLS = ("vd_check", "vd_hit", "s6_check", "s7_check", "zero_out", "zscan", "zfill", "dz_check", "dz_sleep",
           "rz_check", "rz_mod", "rz_slept")


def assemble(src, at, defs=()):
    """Assemble src à l'adresse at : (octets de .text, {symbole : adresse})."""
    with tempfile.TemporaryDirectory() as d:
        o, elf, b = (pathlib.Path(d) / n for n in ("a.o", "a.elf", "a.bin"))
        cmd = [CROSS + "as", "-mcpu=54418", "-o", str(o), str(SRC / src)]
        for k, v in defs:
            cmd += ["--defsym", f"{k}={v:#x}"]
        subprocess.run(cmd, check=True)
        subprocess.run([CROSS + "ld", "-e", "0", f"-Ttext={at:#x}", "-o", str(elf), str(o)], check=True)
        subprocess.run([CROSS + "objcopy", "-O", "binary", "-j", ".text", str(elf), str(b)], check=True)
        nm = subprocess.run([CROSS + "nm", str(elf)], check=True, capture_output=True, text=True).stdout
        code = b.read_bytes()
    return code, {p[2]: int(p[0], 16) for p in (l.split() for l in nm.splitlines()) if len(p) == 3}


class Writes:
    def __init__(self, stock):
        self.stock, self.list, self.masks = stock, [], []

    def put(self, va, new, old=None):
        cur = self.stock[va - BASE:va - BASE + len(new)]
        if old is not None and cur != bytes.fromhex(old):
            raise SystemExit(f"!! {va:#x} : {old} attendu dans l'OS d'origine, {cur.hex()} trouvé")
        self.list.append({"off": va - BASE, "old": cur.hex(), "new": new.hex()})

    def mask(self, key, code):
        va = MASK[key]
        size = sprites.MASKS[va][0]
        if len(code) > size:
            raise SystemExit(f"!! {key} : {len(code)} o, le masque {va:#x} n'en a que {size}")
        self.put(va, code)
        self.list.append(sprites.redirect_write(va))
        self.masks.append((va, len(code), size))

    def hook(self, va, old, target, size):
        new = bytes.fromhex("4ef9") + target.to_bytes(4, "big") + bytes.fromhex("4e71") * ((size - 6) // 2)
        if len(new) != size or len(bytes.fromhex(old)) != size:
            raise SystemExit(f"!! détour {va:#x} : {size} o attendus")
        self.put(va, new, old)


def build_tweak(stock):
    w, syms = Writes(stock), {}
    # saturateur de Dist sauté
    code, s = assemble("vd_skip.S", MASK["vd_skip"])
    w.mask("vd_skip", code)
    w.hook(0x40057062, "286f0038206f0040", s["vd_check"], 8)
    syms.update(s)
    # sommeil du delay et de la reverb
    lib, sl = assemble("fx_lib.S", MASK["fx_lib"])
    defs = (("ZSCAN", sl["zscan"]), ("ZFILL", sl["zfill"]))
    dly, sd = assemble("fx_dly.S", MASK["fx_dly"], defs)
    rev, sr = assemble("fx_rev.S", MASK["fx_rev"], defs)
    w.mask("fx_lib", lib)
    w.mask("fx_dly", dly)
    w.mask("fx_rev", rev)
    w.hook(0x40057516, "2f03260dea83", sd["dz_check"], 6)
    w.hook(0x40057ac8, "2a7c8000a9b0", sr["rz_check"], 6)
    w.hook(0x40057dc6, "207c8000ad20", sr["rz_mod"], 6)
    syms.update(sl)
    syms.update(sd)
    syms.update(sr)
    # envois à gain nul sautés
    code, s = assemble("send_skip.S", MASK["send_skip"])
    w.mask("send_skip", code)
    w.hook(0x40056716, "4fefffe048d70cfc", s["s6_check"], 8)
    w.hook(0x40056698, "4fefffd848d73cfc", s["s7_check"], 8)
    syms.update(s)

    w.list.sort(key=lambda x: x["off"])
    used = sum(n for _, n, _ in w.masks)
    tweak = {
        "id": "out-sleep",
        "order": 71,
        "name": "Étage de sortie allégé : delay, reverb, Dist et envois sautés quand ils ne servent pas, son identique",
        "description": [
            "Delay et reverb endormis tant que rien n'y entre ni n'en sort, saturateur de Dist sauté quand VOL+DIST ne "
            "distord pas, envois à 0 sautés : les raccourcis de l'étage de sortie de l'OS optimisé (notes/70), "
            "repris pour le Modded Cycles OS (notes/78).",
            "Mesuré sur la machine avec l'OS d'origine (18/10/2026) : delay et reverb endormis -7 points, saturateur "
            "-2, envois -1 ; son identique.",
            "Une fois servis, le delay et la reverb ne se rendorment plus avant le prochain allumage.",
            f"Code dans cinq masques de sprites libérés (tools/sprites.py) : {used} o. "
            "Généré par tools/gen_out_sleep.py, notes/78.",
        ],
        "device": "Model:Cycles",
        "os": "1.13",
        "section": 3,
        "conflicts": ["os-optimise"],
        "symbols": {n: f"{syms[n]:#x}" for n in SYMBOLS},
        "writes": w.list,
    }
    return tweak, w.masks


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True, help="model-cycles_OS1.13.syx officiel")
    ap.add_argument("--check", action="store_true", help="vérifie que le JSON versionné correspond")
    args = ap.parse_args()
    stream, _ = build.unwrap(pathlib.Path(args.cycles).read_bytes())
    c = build.container.parse(stream)
    s3 = next(s for s in c["sections"] if s["id"] == 3)
    stock = build.aplib.depack(c["blob"][s3["off"]:s3["off"] + s3["size"]])[0]
    if build.sha(stock) != json.loads((DEV / "device.json").read_text(encoding="utf-8"))["section_sha256"]:
        raise SystemExit("!! ce n'est pas le MAIN OS 1.13 officiel")
    tweak, masks = build_tweak(stock)
    build.apply_writes(stock, [tweak])                # les octets d'origine collent
    text = json.dumps(tweak, indent=1, ensure_ascii=False) + "\n"
    for va, n, size in masks:
        print(f"  masque {va:#x} : {n}/{size} o")
    print("  " + tweak["description"][-1])
    if args.check:
        ok = OUT.exists() and OUT.read_text(encoding="utf-8") == text
        print(f"  {OUT.name} {'est à jour' if ok else 'NE CORRESPOND PAS (autres binutils ?)'}")
        raise SystemExit(0 if ok else 1)
    OUT.write_text(text, encoding="utf-8")
    print(f"  écrit : {OUT.relative_to(HERE.parent)} ({len(tweak['writes'])} écritures)")


if __name__ == "__main__":
    main()
