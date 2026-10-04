#!/usr/bin/env python3
"""Génère tweaks/model-cycles_OS1.13/41-trig-hold.json : plus de temps pour effacer un trig en mode grille (notes/33).

L'OS d'origine efface un trig existant au relâchement de sa touche, sauf si l'appui a duré plus de 200 ms : passé ce
délai, il le considère comme maintenu (affichage de la note et de la vélocité du trig) et ne l'efface plus. Avec les
touches souples du Model:Cycles, un appui normal dépasse souvent ce délai. Le tweak porte ce délai à T_MS pour les pas
qui ont déjà un trig ; les tours de potard pendant l'appui gardent le trig, comme avant.

tools/machines/trig_hold/ : trig_hold.S (trois accroches et l'heure d'appui de chaque touche de pas), lié par
trig_hold.ld au début du masque de sprite libéré 0x4015c044 (tools/sprites.py), devant les stubs de 6ch-usbup.

    python3 tools/gen_trig_hold.py --cycles model-cycles_OS1.13.syx [--check]
"""
import argparse
import json
import pathlib
import struct
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "emu"))

import build                       # noqa: E402
import gen_sdvintage_exact as gx   # noqa: E402
import sprites                     # noqa: E402
import test_sdvintage as T         # noqa: E402

SRC = HERE / "machines" / "trig_hold"
OUT = HERE.parent / "tweaks" / "model-cycles_OS1.13" / "41-trig-hold.json"
BASE = gx.BASE
T_MS = 500                                             # délai avant qu'un appui sur un trig existant compte comme maintenu
DTIM_HZ = 135_168_000                                  # minuteur DMA 0 (horodatage des événements de touches, notes/23)
T_UNITS = round(T_MS * DTIM_HZ / 65536 / 1000)         # unités de 65 536 coups (trig_hold.S)
MASK = 0x4015c044                                      # masque libéré (720 o) ; 6ch-usbup en occupe le milieu
CAVE, ROOM = 0x4015c044, 0x4015c116 - 0x4015c044       # 210 o devant les stubs de 6ch-usbup
# (adresse, octets d'origine, symbole, rôle), dans PatternGridView::consumeKeyEvent (0x40022382), touches de pas
HOOKS = (
    (0x4002249c, "4eb940072490", "th_press",
     "appui : jsr 0x40072490 (FUNC tenu ?) -> jsr th_press (note l'heure de l'appui, même réponse)"),
    (0x40022d44, "4eb940072460", "th_hold",
     "maintien : jsr 0x40072460 (bit 3) -> jsr th_hold (accepté au bout de T_MS si un trig attend d'être effacé)"),
    (0x40022da6, "4eb94006b736", "th_release",
     "relâchement : jsr 0x4006b736 (maintien en cours ?) -> jsr th_release (ou appui plus long que T_MS)"),
)
SYMBOLS = ("th_t", "th_press", "th_hold", "th_release")    # pour tools/emu/test_trig_hold.py


def compile_hold():
    """(adresse, octets) de la section .cave, et les symboles."""
    with tempfile.TemporaryDirectory() as d:
        d = pathlib.Path(d)
        obj, elf, out = d / "th.o", d / "th.elf", d / "cave.bin"
        gx.run([gx.CROSS + "gcc", "-mcpu=54418", f"-DT_UNITS={T_UNITS}", "-c", str(SRC / "trig_hold.S"),
                "-o", str(obj)])
        gx.run([gx.CROSS + "ld", "-T", str(SRC / "trig_hold.ld"), "--no-warn-rwx-segments", "-o", str(elf), str(obj)])
        syms = {}
        for line in gx.run([gx.CROSS + "nm", str(elf)]).splitlines():
            p = line.split()
            if len(p) == 3:
                syms[p[2]] = int(p[0], 16)
        gx.run([gx.CROSS + "objcopy", "-O", "binary", "-j", ".cave", str(elf), str(out)])
        addr = int(subprocess.run([gx.CROSS + "objdump", "-h", str(elf)], capture_output=True, text=True,
                                  check=True).stdout.split(".cave")[1].split()[1], 16)
        return addr, out.read_bytes(), syms


def build_tweak(stock):
    addr, code, syms = compile_hold()
    if addr != CAVE or len(code) > ROOM:
        raise SystemExit(f"!! {len(code)} o à {addr:#x}, place {ROOM} o à {CAVE:#x}")
    old = stock[addr - BASE:addr - BASE + len(code)]
    if old != b"\xff" * len(code):
        raise SystemExit(f"!! la zone {addr:#x} n'est pas libre dans l'OS d'origine")
    writes = [{"off": addr - BASE, "old": old.hex(), "new": code.hex()}, sprites.redirect_write(MASK)]
    for va, old_hex, sym, _ in HOOKS:
        if stock[va - BASE:va - BASE + 6] != bytes.fromhex(old_hex):
            raise SystemExit(f"!! octets d'origine inattendus en {va:#x}")
        writes.append({"off": va - BASE, "old": old_hex, "new": struct.pack(">HI", 0x4eb9, syms[sym]).hex()})
    writes.sort(key=lambda w: w["off"])
    tweak = {
        "id": "trig-hold",
        "order": 41,
        "name": "Plus de temps pour effacer un trig",
        "description": [
            "Mode grille : un appui sur un pas qui a déjà un trig l'efface au relâchement s'il a duré moins de "
            f"{T_MS} ms (200 ms à l'origine).",
            f"Au-delà, le trig est maintenu (sa note et sa vélocité s'affichent) et reste. Pas vide : comme à l'origine.",
            "Un tour de potard pendant l'appui garde le trig, comme à l'origine. Même délai pour les changements de "
            "trig au relâchement (FUNC + pas, trig de lock).",
            f"Code et heures d'appui dans le masque de sprite libéré 0x4015c044 (tools/sprites.py) : {len(code)} o. "
            "Généré par tools/gen_trig_hold.py, notes/33.",
        ],
        "device": "Model:Cycles",
        "os": "1.13",
        "section": 3,
        "symbols": {n: f"{syms[n]:#x}" for n in SYMBOLS},
        "writes": writes,
    }
    return tweak


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True, help="model-cycles_OS1.13.syx officiel")
    ap.add_argument("--check", action="store_true", help="vérifie que le JSON versionné correspond")
    args = ap.parse_args()
    stock = T.main_os_from_syx(args.cycles)
    if build.sha(stock) != json.loads((OUT.parent / "device.json").read_text(encoding="utf-8"))["section_sha256"]:
        raise SystemExit("!! ce n'est pas le MAIN OS 1.13 officiel")
    tweak = build_tweak(stock)
    build.apply_writes(stock, [tweak])                # les octets d'origine collent
    text = json.dumps(tweak, indent=1) + "\n"
    print("  " + tweak["description"][-1])
    if args.check:
        ok = OUT.exists() and OUT.read_text(encoding="utf-8") == text
        print(f"  {OUT.name} {'est à jour' if ok else 'NE CORRESPOND PAS (autre binutils ?)'}")
        raise SystemExit(0 if ok else 1)
    OUT.write_text(text, encoding="utf-8")
    print(f"  écrit : {OUT.relative_to(HERE.parent)} ({len(tweak['writes'])} écritures, T = {T_MS} ms = {T_UNITS} unités)")


if __name__ == "__main__":
    main()
