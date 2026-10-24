#!/usr/bin/env python3
"""Preuve de l'étage de sortie allégé (notes/78, tweaks/model-cycles_OS1.13/71-out-sleep.json) dans le Modded Cycles
OS : « base » = l'OS de os.json sans out-sleep, « allégé » = avec. Le vrai code de l'interruption audio, étage de
sortie compris (osbanc.OsBanc : Model-TG, nos machines, Volume + Dist, envois, mixeur, delay, reverb, master, anneau
du codec, copie USB, eDMA simulé), les deux firmwares côte à côte, comparés à chaque bloc : anneau du codec, USB,
sortie des 6 voix, SRAM entière (sauf 0x8000bc98..0x8000bd98, la sortie du saturateur que le raccourci ne réécrit pas,
lue x 0), EMAC ; lignes du delay et de la reverb (DDR) tous les 10 blocs.

Scénarios :
  defaut       les 6 machines d'origine (par Model-TG), un trig tous les 40 blocs, réglages par défaut ;
  projet       MODAL, SNARE, METAL, ACID, KICK, CPVtg (le projet du relevé de Maxime, notes/77) ;
  envois       envois delay 40 et reverb 40 sur les 6 pistes : delay et reverb en service ;
  dist         VOL+DIST 100 sur les pistes 1-3, 80 sur 4-6 : le saturateur en service ;
  glissements  réglages tournés comme des potards (le lissage de l'OS glisse) : envoi delay 40 piste 3 et VOL+DIST 90
               piste 1, puis reverb 50 pistes 2 et 5, puis tout revient ; Delay Time et Reverb Size changés ;
  machines     les 15 machines tour à tour sur les pistes, envois 30/30 sur une piste.

    python3 tools/emu/test_out_sleep.py --cycles model-cycles_OS1.13.syx --syntakt Syntakt_OS1.42.syx \
        [--scenario defaut,projet,envois,dist,glissements,machines] [--blocks N]
"""
import argparse
import contextlib
import hashlib
import io
import json
import os
import pathlib
import struct
import sys
import tempfile

import numpy as np
from unicorn import UC_HOOK_CODE

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import emac                         # noqa: E402
import gen_mesure as G              # noqa: E402
import mcengine as E                # noqa: E402
import osbanc as O                  # noqa: E402
import seqrig as S                  # noqa: E402
import syntakt                      # noqa: E402
import test_macro_syntakt as tmx    # noqa: E402
import test_mesure as T             # noqa: E402
import test_modal as tmo            # noqa: E402

TID = "out-sleep"
BASE = 0x40000400
P1_STALE = (0x8000bc98, 0x8000bd98)   # sortie du saturateur, non réécrite quand il est sauté (lue x 0)
LINES = ((0x4a400000, 0x400000), (0x4a340000, 0x90000), (0x4a3d0000, 0x8000))   # delay, reverb (vues sans cache)
SLOT_DIST, SLOT_DLY, SLOT_REV = 19, 20, 21
FAILS = []


def check(ok, msg):
    print(("  ok    " if ok else "  ÉCHEC ") + msg, flush=True)
    if not ok:
        FAILS.append(msg)


def firmwares(cycles, syntakt_path):
    stock = T.stock_of(cycles)
    ctx = dict(syntakt=syntakt_path, st_img=syntakt.dsp_image(syntakt_path), chord=tmx.chord_tables(stock))
    tw = G.os_tweaks()
    if TID not in {t["id"] for t in tw}:          # pas encore dans os.json : ajouté pour « allégé »
        tw = sorted(tw + [json.loads((G.DEV / "71-out-sleep.json").read_text(encoding="utf-8"))],
                    key=lambda t: t["order"])
    base = [t for t in tw if t["id"] != TID]
    with contextlib.redirect_stdout(io.StringIO()):
        return tmo.Fw(stock, base, ctx), tmo.Fw(stock, tw, ctx), next(t for t in tw if t["id"] == TID)


class Bench:
    """Un banc ; avec le tweak : l'EMAC sur son code (masques), et les passages par ses chemins courts."""

    def __init__(self, fw, tweak=None):
        self.b = b = O.OsBanc(fw)
        self.uc = b.uc
        self.n = {}
        if tweak:
            for w in tweak["writes"]:
                va, n = w["off"] + BASE, len(w["new"]) // 2
                if n >= 16:                       # le code dans les masques : ses instructions EMAC
                    with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as f:
                        f.write(bytes(self.uc.mem_read(va, n)))
                    try:
                        b.e.emac.install(emac.disasm(f.name, va, va, va + n))
                    finally:
                        os.unlink(f.name)
            sym = {k: int(v, 16) for k, v in tweak["symbols"].items()}
            for name, key in (("saturateur sauté", "vd_hit"), ("delay endormi", "dz_sleep"),
                              ("reverb endormie", "rz_slept"), ("envoi sauté", "zero_out")):
                self.n[name] = 0
                self.uc.hook_add(UC_HOOK_CODE, lambda *x, k=name: self._inc(k), begin=sym[key], end=sym[key])

    def _inc(self, k):
        self.n[k] += 1

    def sram(self):
        s = bytearray(self.uc.mem_read(0x80000000, 0x10000))
        s[P1_STALE[0] - 0x80000000:P1_STALE[1] - 0x80000000] = bytes(P1_STALE[1] - P1_STALE[0])
        return bytes(s)

    def emac_state(self):
        em = self.b.e.emac
        return (tuple(em.acc), em.macsr)

    def lines(self):
        h = hashlib.sha256()
        for a, n in LINES:
            h.update(bytes(self.uc.mem_read(a, n)))
        return h.digest()

    def target(self, t, slot, value):
        """Comme un potard tourné : la cible seule, le lissage de l'OS y glisse."""
        j = (0xe + 0x42 * t + 2 * slot) // 2
        self.uc.mem_write(S.TARGETS + 2 * j, struct.pack(">h", value << 8))


SCEN = {
    "defaut": dict(mach=(0, 1, 2, 3, 4, 5)),
    "projet": dict(mach=(14, 1, 2, 13, 0, 8)),
    "envois": dict(mach=(0, 1, 2, 3, 4, 5), sends=(40, 40)),
    "dist": dict(mach=(0, 1, 2, 3, 4, 5), dist=(100, 100, 100, 80, 80, 80)),
    "glissements": dict(mach=(0, 1, 7, 12, 13, 14), glisse=True),
    "machines": dict(mach=(0, 1, 2, 3, 4, 5), tour=True),
}


def glisse(bench, k):
    if k % 100:
        return
    ph = k // 100
    if ph == 1:
        bench.target(2, SLOT_DLY, 40)
        bench.target(0, SLOT_DIST, 90)
        bench.b.param(6, 9, 60)                 # Delay Time
    elif ph == 2:
        bench.target(1, SLOT_REV, 50)
        bench.target(4, SLOT_REV, 50)
        bench.b.param(6, 11, 90)                # Reverb Size
    elif ph == 3:
        for t in range(6):
            bench.target(t, SLOT_DLY, 0)
            bench.target(t, SLOT_REV, 0)
        bench.target(0, SLOT_DIST, 60)


def run(name, sc, fa, fb, tweak, blocks):
    print(f"\n{name} ({blocks} blocs)")
    B = {"base": Bench(fa), "allégé": Bench(fb, tweak)}
    for bench in B.values():
        for t, m in enumerate(sc["mach"]):
            bench.b.rig.param(t, E.SLOT["machine"], m * 256)
            if "sends" in sc:
                bench.b.param(t, SLOT_DLY, sc["sends"][0])
                bench.b.param(t, SLOT_REV, sc["sends"][1])
            if "dist" in sc:
                bench.b.param(t, SLOT_DIST, sc["dist"][t])
            bench.b.rig.set_step(t, 0, vel=100, length=S.LEN_1_16, note=40 + 4 * t)
    first, peak, nlines, sound = None, 0, 0, False
    for k in range(blocks):
        info = {}
        for n, bench in B.items():
            if sc.get("glisse"):
                glisse(bench, k)
            if sc.get("tour") and k % 60 == 30:
                t, m = (k // 60) % 6, (k // 60 + 3) % 15
                bench.b.rig.param(t, E.SLOT["machine"], m * 256)
                if k // 60 == 2:
                    bench.b.param(t, SLOT_DLY, 30)
                    bench.b.param(t, SLOT_REV, 30)
            if k % 40 == 2:
                for t in range(6):
                    bench.b.rig.schedule_step(t, 0, bench.b.rig.now + bench.b.rig.blk // 2)
            info[n] = bench.b.block()
        ia, ib = info["base"], info["allégé"]
        peak = max(peak, int(np.abs(ia["ring"]).max()))
        if first is None:
            why = [w for w, ok in (
                ("anneau du codec", np.array_equal(ia["ring"], ib["ring"])),
                ("USB", np.array_equal(ia["usb"], ib["usb"])),
                ("voix", np.array_equal(ia["out"], ib["out"])),
                ("SRAM", B["base"].sram() == B["allégé"].sram()),
                ("EMAC", B["base"].emac_state() == B["allégé"].emac_state())) if not ok]
            if not why and (k % 10 == 9 or k == blocks - 1):
                nlines += 1
                if B["base"].lines() != B["allégé"].lines():
                    why = ["lignes delay/reverb"]
            if why:
                first = (k, why)
        if k % 100 == 99:
            print(f"    … bloc {k + 1}", flush=True)
    hz = B["allégé"].n
    print("  chemins courts (allégé) : " + ", ".join(f"{k} {v}" for k, v in hz.items()))
    check(first is None, f"{name} : base = allégé sur {blocks} blocs (anneau, USB, 6 voix, SRAM, EMAC à chaque bloc ; "
          f"lignes du delay et de la reverb {nlines} fois)" +
          ("" if first is None else f" — premier écart au bloc {first[0]} : {first[1]}"))
    check(peak > 0, f"{name} : il y a du son (crête de l'anneau {peak})")
    return hz


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True)
    ap.add_argument("--syntakt", required=True)
    ap.add_argument("--scenario", default=",".join(SCEN))
    ap.add_argument("--blocks", type=int, default=400)
    args = ap.parse_args()
    fa, fb, tweak = firmwares(args.cycles, args.syntakt)
    print("écritures")
    d = [i for i in range(min(len(fa.img), len(fb.img))) if fa.img[i] != fb.img[i]]
    spans = [(w["off"], w["off"] + len(w["new"]) // 2) for w in tweak["writes"]]
    check(d and all(any(lo <= i < hi for lo, hi in spans) for i in d),
          f"{len(d)} octets changés dans l'image, tous dans les {len(tweak['writes'])} écritures du tweak")
    for name in args.scenario.split(","):
        sc = SCEN[name]
        hz = run(name, sc, fa, fb, tweak, args.blocks)
        n = args.blocks
        if name in ("defaut", "projet"):
            check(hz["delay endormi"] == n and hz["reverb endormie"] == n and hz["envoi sauté"] == 4 * n
                  and hz["saturateur sauté"] == 3 * n,
                  f"{name} : réglages par défaut : delay et reverb endormis à chaque bloc ({hz['delay endormi']}, "
                  f"{hz['reverb endormie']}), 4 envois sautés par bloc ({hz['envoi sauté']}), saturateur sauté pour "
                  f"les 3 paires ({hz['saturateur sauté']})")
        elif name == "envois":
            check(hz["delay endormi"] < 10 and hz["reverb endormie"] < 10 and hz["envoi sauté"] < 10,
                  f"{name} : envois en service : delay et reverb éveillés dès le 1er son ({hz['delay endormi']}, "
                  f"{hz['reverb endormie']} blocs endormis), envois calculés ({hz['envoi sauté']} sautés)")
        elif name == "dist":
            check(hz["saturateur sauté"] == 0, f"{name} : Dist en service : saturateur toujours calculé "
                  f"({hz['saturateur sauté']} sauts)")
        elif name == "glissements":
            check(0 < hz["delay endormi"] < n and 0 < hz["reverb endormie"] < n and 0 < hz["saturateur sauté"] < 3 * n,
                  f"{name} : les raccourcis s'enclenchent puis se relâchent (delay {hz['delay endormi']}, reverb "
                  f"{hz['reverb endormie']}, saturateur {hz['saturateur sauté']})")
    print("\nTOUT OK" if not FAILS else f"\n{len(FAILS)} ÉCHEC(S)")
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
