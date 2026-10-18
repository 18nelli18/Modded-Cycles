#!/usr/bin/env python3
"""Génère tweaks/model-cycles_OS1.13/70-os-optimise.json : l'OS d'origine allégé, son identique, deux gels corrigés
(notes/70, d'après l'étude du 17-18/10/2026 archivée sous le tag git etude-optimisation-os-2026-10-18).

Le même travail, moins souvent : l'OS d'origine calcule tout à chaque bloc audio (0,67 ms), même ce qui ne peut
rien changer au son. Six raccourcis exacts (sortie identique à l'échantillon près, prouvée en émulation) :
  - saturateur de Dist sauté quand la part « wet » d'une paire de pistes est nulle (VOL+DIST <= 60) :
    vd_skip.S, détour 0x40057062 ;
  - envois delay et reverb sautés quand leurs gains et leurs pentes sont nuls : send_skip.S, détours 0x40056716
    et 0x40056698 ;
  - sommeil du delay et de la reverb tant que tout ce qu'ils lisent est nul (ils ne se rendorment pas avant le
    prochain allumage une fois servis : leurs restes ne sont jamais exactement nuls) : fx_lib.S, fx_dly.S,
    fx_rev.S, détours 0x40057516, 0x40057ac8, 0x40057dc6 ;
  - mix2 (0x400a9884) sans sa première boucle, dont la sortie est entièrement réécrite par la seconde : mix2.S,
    réécrit en place ;
  - PUNCH éteint par un chemin court (5 instructions par échantillon au lieu de 13) : punch.S, détour 0x400a9714 ;
  - arrêt des voix muettes : une voix sans trig dont la sortie reste sous -108 dB pendant 64 blocs n'est plus
    calculée (elle sort 0 au lieu de moins de -108 dB), et repart à son trig suivant : idle_stock.S, détours
    0x400a7dfe et 0x400a7e24.
Et deux gels de l'OS d'Elektron corrigés :
  - D1 : MACHINES gèle quand une piste porte une machine que le firmware n'a pas (projet fait avec MACRO, ACID ou
    les moteurs du Syntakt, rouvert ailleurs) : les accesseurs 0x4004df5c et 0x4004df76 rendaient l'entrée -1,
    76 o avant le tableau ; ils rendent CHORD (moveq #-1 -> moveq #6) ;
  - D2 : l'horloge MIDI sortante attend à IPL 7 une place dans un anneau que seul le niveau 4, masqué, peut vider
    (gel complet après une longue surcharge) : l'octet est jeté (bgt.s vers la sortie, 0x40001246).

Code dans sept masques de sprites libérés (tools/sprites.py), les mêmes que les fichiers d'essai testés sur la
machine le 18/10/2026 : octets identiques, sans le compteur de charge. Sans Model-TG, moteurs du Syntakt, MACRO ni
ACID : ces firmwares détournent la même boucle des voix et ont déjà leur arrêt des voix muettes.

tools/machines/os_optimise/ : sources. Preuve : tools/emu/test_os_optimise.py.

    python3 tools/gen_os_optimise.py --cycles model-cycles_OS1.13.syx [--check]
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

SRC = HERE / "machines" / "os_optimise"
DEV = HERE.parent / "tweaks" / "model-cycles_OS1.13"
OUT = DEV / "70-os-optimise.json"
BASE = build.BASE
CROSS = next((c for c in ("m68k-linux-gnu-", "m68k-elf-") if shutil.which(c + "as")), "m68k-linux-gnu-")
IDLE_N = 64                      # blocs faibles avant l'arrêt d'une voix (43 ms)
IDLE_T = 4096                    # seuil sur la sortie divisée par 2 : |x| < 4 096 = render sous 2^13 (-108 dB)
MASK = {                         # masques libérés (REGISTRY.md §1), un seul usage chacun
    "vd_skip": 0x4016dab8,       # 48x22
    "fx_lib": 0x4016fae8,        # 48x22
    "send_skip": 0x40170c48,     # 48x22
    "idle_stock": 0x40185f48,    # 34x34
    "punch": 0x40186238,         # 34x34
    "fx_dly": 0x40189618,        # 34x34
    "fx_rev": 0x4018d918,        # 41x41
}
MIX2 = 0x400a98c4                # 1re boucle de mix2, réécrite en place (64 o)
D1 = ((0x4004df66, "70ff", "7006"), (0x4004df80, "70ff", "7006"))
D2 = (0x40001246, "6ef2", "6e7e")
D2_EXIT = (0x400012c6, "241f261f4e75")    # move.l (sp)+,d2 ; move.l (sp)+,d3 ; rts : la sortie visée par D2
# familles qui détournent la boucle des voix ou y ajoutent des machines : pas encore avec l'OS optimisé (notes/70 §6)
VOICE_FAMILIES = ("model-tg", "macro", "acid", "syntakt-", "sdvintage-")
SYMBOLS = ("vd_check", "vd_hit", "s6_check", "s7_check", "zero_out", "zscan", "zfill", "dz_check", "dz_sleep",
           "rz_check", "rz_mod", "rz_slept", "p_short", "p_orig", "gate", "after", "QUIET")


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
        va = MASK[key]                                # masque libérable ; libre : tools/registry.py
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


def conflicts():
    """Les tweaks du dossier qui détournent la boucle des voix (VOICE_FAMILIES), triés."""
    ids = (json.loads(f.read_text(encoding="utf-8"))["id"] for f in DEV.glob("*.json") if f.name != "device.json")
    return sorted(i for i in ids if i.startswith(VOICE_FAMILIES))


def build_tweak(stock):
    w, syms = Writes(stock), {}

    # D1, D2 : deux gels de l'OS d'origine
    for va, old, new in D1:
        w.put(va, bytes.fromhex(new), old)
    va, ex = D2_EXIT
    if stock[va - BASE:va - BASE + 6].hex() != ex:
        raise SystemExit(f"!! {va:#x} n'est pas la sortie move.l (sp)+,d2 ; move.l (sp)+,d3 ; rts")
    w.put(D2[0], bytes.fromhex(D2[2]), D2[1])

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

    # mix2 sans sa boucle morte, en place
    code, _ = assemble("mix2.S", MIX2)
    if code[0x18:0x1c] != bytes.fromhex("6000") + (0x40 - 0x1a).to_bytes(2, "big"):
        raise SystemExit("!! mix2 : bra.w de fin inattendu")
    code = code[:0x1c] + bytes.fromhex("4e71") * ((0x40 - 0x1c) // 2)
    if stock[MIX2 - BASE:MIX2 - BASE + 8].hex() != "22115c8124730800":
        raise SystemExit("!! mix2 : octets d'origine inattendus en 0x400a98c4")
    w.put(MIX2, code)

    # PUNCH éteint par un chemin court
    code, s = assemble("punch.S", MASK["punch"])
    if s.get("pstub") != MASK["punch"]:
        raise SystemExit("!! punch : pstub n'est pas au début du masque")
    w.mask("punch", code)
    w.hook(0x400a9714, "2e2802a42213", s["pstub"], 6)
    syms.update(s)

    # arrêt des voix muettes
    code, s = assemble("idle_stock.S", MASK["idle_stock"], (("IDLE_N", IDLE_N), ("IDLE_T", IDLE_T)))
    w.mask("idle_stock", code)
    w.hook(0x400a7dfe, "b08465222046", s["gate"], 6)
    w.hook(0x400a7e24, "269522434280", s["after"], 6)
    syms.update(s)

    w.list.sort(key=lambda x: x["off"])
    used = sum(n for _, n, _ in w.masks)
    tweak = {
        "id": "os-optimise",
        "order": 70,
        "name": "OS optimisé : moins de charge, son identique, deux gels corrigés",
        "description": [
            "Le même son, moins de calcul : saturateur de Dist sauté quand VOL+DIST ne distord pas, envois à 0 sautés, "
            "delay et reverb endormis tant que rien n'y entre ni n'en sort, mix2 sans sa boucle morte, PUNCH éteint "
            "par un chemin court, voix muettes depuis 64 blocs plus calculées (0 au lieu de moins de -108 dB).",
            "Mesuré sur la machine (18/10/2026, 6 pistes, un trig par pas) : charge moyenne 72 -> 20 % à l'arrêt, "
            "77 -> 65 % en lecture, 77 -> 73 % avec delay et reverb en service.",
            "Une fois servis, le delay et la reverb ne se rendorment plus avant le prochain allumage.",
            "Gels corrigés : MACHINES sur une machine que le firmware n'a pas (D1), horloge MIDI sortante qui fige "
            "tout après une longue surcharge (D2).",
            "Pas avec Model-TG, les moteurs du Syntakt, MACRO ni ACID (même boucle des voix).",
            f"Code dans sept masques de sprites libérés (tools/sprites.py) : {used} o. "
            "Généré par tools/gen_os_optimise.py, notes/70.",
        ],
        "device": "Model:Cycles",
        "os": "1.13",
        "section": 3,
        "conflicts": conflicts(),
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
