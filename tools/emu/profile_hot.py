#!/usr/bin/env python3
"""Profil du code chaud du Modded Cycles OS (notes/76) : pour chaque machine, seule sur les 6 pistes, le code que
l'interruption audio exécute à chaque bloc, dans l'appel de la fonction audio (0x40059382 : là où le code chaud
peut tourner en SRAM). Écrit tools/machines/sram_hot/profile.json, que lit tools/gen_sram_hot.py :

  - "lines" : les lignes de 16 o exécutées (plages [début, fin) d'adresses), réunies sur les blocs mesurés ;
  - "calls" : les cibles des appels (jsr, bsr) et des sauts (jmp), avec leur nombre par bloc : les entrées des
    fonctions chaudes, et les points d'entrée que le code qui reste en SDRAM prend.

Le banc (osbanc.OsBanc) fait tourner le vrai code, étage de sortie compris, chargeur du code chaud inerte (son
démarrage, hot_boot, n'est pas appelé). Les adresses sont celles de l'OS construit (os.json).

    python3 tools/emu/profile_hot.py --cycles model-cycles_OS1.13.syx --syntakt Syntakt_OS1.42.syx [--check]
"""
import argparse
import collections
import contextlib
import io
import json
import pathlib
import struct
import sys

from unicorn import UC_HOOK_CODE

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import gen_mesure as G              # noqa: E402
import mcengine as E                # noqa: E402
import osbanc as O                  # noqa: E402
import seqrig as S                  # noqa: E402
import syntakt                      # noqa: E402
import test_macro_syntakt as tmx    # noqa: E402
import test_mesure as T             # noqa: E402
import test_modal as tmo            # noqa: E402

OUT = HERE.parent / "machines" / "sram_hot" / "profile.json"
NAMES = ["KICK", "SNARE", "METAL", "PERC", "TONE", "CHORD", "Sampler", "SDVtg", "CPVtg", "SYToy", "SYBit", "SYSwm",
         "MACRO", "ACID", "MODAL"]
# réglages des 6 pistes par machine : de quoi passer par ses chemins de code (MACRO : 6 modèles par passe, 3 passes ;
# MODAL : ses 4 modèles, 1, 2 et 4 voix)
KNOBS = [dict(color=c, shape=s, sweep=w, contour=n, decay=d) for c, s, w, n, d in
         ((64, 0, 40, 36, 64), (20, 40, 100, 90, 30), (110, 80, 10, 10, 120), (64, 127, 64, 64, 64),
          (90, 20, 80, 110, 90), (40, 100, 120, 50, 10))]
MODAL_PASS = [dict(shape=s, finetune=f) for s, f in ((0, 64), (1, 64), (2, 96), (3, 80), (0, 96), (2, 64))]
MACRO_PASSES = [(0, 7, 14, 21, 28, 35), (3, 10, 18, 26, 37, 44), (5, 12, 23, 31, 40, 46)]
BLOCKS, EVERY, SKIP = 22, 6, 4


def firmware(cycles, syntakt_path):
    stock = T.stock_of(cycles)
    ctx = dict(syntakt=syntakt_path, st_img=syntakt.dsp_image(syntakt_path), chord=tmx.chord_tables(stock))
    with contextlib.redirect_stdout(io.StringIO()):
        return tmo.Fw(stock, G.os_tweaks(), ctx)


class Window:
    """Code exécuté dans l'appel de 0x40059382 : lignes, et cibles des appels et des sauts."""

    def __init__(self, b, skip=()):
        self.on, self.skip = False, skip
        self.lines, self.calls = set(), collections.Counter()
        self.pending = None
        b.uc.hook_add(UC_HOOK_CODE, self._code)

    def _code(self, uc, addr, size, ud):
        if addr == O.AUDIO_CALL:
            self.on = True
            return
        if addr == O.AFTER_CALL:
            self.on = False
            return
        if not self.on or any(lo <= addr < hi for lo, hi in self.skip):
            self.pending = None
            return
        if self.pending is not None:
            self.calls[self.pending, addr] += 1
            self.pending = None
        self.lines.add(addr >> 4)
        op = struct.unpack(">H", bytes(uc.mem_read(addr, 2)))[0]
        if (op & 0xff80) == 0x4e80 or (op & 0xff00) == 0x6100:      # jsr, jmp ; bsr
            self.pending = "jmp" if (op & 0xffc0) == 0x4ec0 else "call"


def profile(fw, m, sets, skip=()):
    lines, calls = set(), collections.Counter()
    nb = 0
    for knobs in sets:
        b = O.OsBanc(fw)
        for t in range(6):
            b.rig.param(t, E.SLOT["machine"], m * 256)
            for k, v in dict(KNOBS[t], **knobs[t]).items():
                b.rig.param(t, E.SLOT[k], v * 256)
        w = Window(b, skip)
        for k in range(BLOCKS):
            if k % EVERY == 2:
                for t in range(6):
                    b.rig.set_step(t, 0, vel=100, length=S.LEN_1_16, note=40 + 5 * t)
                    b.rig.schedule_step(t, 0, b.rig.now + b.rig.blk // 2)
            if k == SKIP:                          # blocs mesurés : à partir du 1er trig
                w.lines.clear()
                w.calls.clear()
            b.block()
        lines |= w.lines
        calls.update(w.calls)
        nb += BLOCKS - SKIP
    runs, start = [], None
    for ln in sorted(lines) + [None]:
        if start is None:
            start = prev = ln
        elif ln != prev + 1:
            runs.append([f"{start << 4:#x}", f"{(prev + 1) << 4:#x}"])
            start = prev = ln
        else:
            prev = ln
    return dict(lines=runs, calls={f"{kind}:{a:#x}": round(n / nb, 2) for (kind, a), n in sorted(calls.items())})


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True)
    ap.add_argument("--syntakt", required=True)
    ap.add_argument("--check", action="store_true", help="compare avec le profil versionné")
    args = ap.parse_args()
    fw = firmware(args.cycles, args.syntakt)
    syms = {k: int(v, 16) for k, v in fw.mine.get("symbols", {}).items()}
    skip = [(syms["hot_code"], syms["hot_code_end"])] if "hot_code" in syms else []
    out = {}
    for m, name in enumerate(NAMES):
        if m == 12:
            sets = [[dict(shape=s) for s in p] for p in MACRO_PASSES]
        elif m == 14:
            sets = [MODAL_PASS]
        else:
            sets = [[{}] * 6]
        out[name] = profile(fw, m, sets, skip)
        n = sum(int(b, 16) - int(a, 16) for a, b in out[name]["lines"]) // 16
        print(f"  {name:8s} {n:5d} lignes, {len(out[name]['calls'])} cibles", flush=True)
    text = json.dumps(dict(about="tools/emu/profile_hot.py (notes/76)", machines=out), indent=1) + "\n"
    if args.check:
        if not OUT.exists() or OUT.read_text() != text:
            raise SystemExit(f"!! {OUT} n'est pas à jour : python3 tools/emu/profile_hot.py --cycles … --syntakt …")
        print(f"{OUT} à jour")
        return
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text)
    print(f"écrit {OUT}")


if __name__ == "__main__":
    main()
