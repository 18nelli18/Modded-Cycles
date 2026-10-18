#!/usr/bin/env python3
"""Profondeur de pile de la boucle des 6 voix (0x400a7d4a), OS d'origine et machines ajoutées en charge utile.

Crochet d'écriture mémoire sur la zone de pile du banc (mcengine) : l'adresse la plus basse écrite, comptée depuis le
SP d'entrée de la boucle (adresse de retour comprise). Les 6 pistes sur la même machine, trig au bloc 1, 40 blocs.

    python3 mesure_pile.py
"""
import json
import struct
import sys

sys.path.insert(0, "/home/user/Modded-Cycles/tools/emu")
sys.path.insert(0, "/home/user/Modded-Cycles/tools")
import build                    # noqa: E402
import mcengine as E            # noqa: E402
import test_sdvintage as T      # noqa: E402
from unicorn import UC_HOOK_MEM_WRITE   # noqa: E402

CYCLES = "/home/user/Modded-Cycles/firmware/model-cycles_OS1.13.syx"
DEV = E.os.path.join("/home/user/Modded-Cycles/tweaks/model-cycles_OS1.13")


def depth(eng, setup, blocks=40):
    low = {"a": 1 << 32}

    def hk(uc, access, addr, size, value, ud):
        low["a"] = min(low["a"], addr)
    eng.uc.hook_add(UC_HOOK_MEM_WRITE, hk, begin=0x90000000, end=E.STACK - 0x100 - 1)
    for t in range(6):
        setup(eng, t)
    for b in range(blocks):
        eng.block(0x3f if b == 1 else 0)
    return E.STACK - 0x100 - low["a"]


def main():
    stock = T.main_os_from_syx(CYCLES)
    rows = []
    for name, m in E.MACH.items():
        e = E.Engine(stock)
        rows.append((f"origine {name}", depth(e, lambda e, t: e.machine_defaults(t, m))))
    for fname, idx, label in (("25-macro.json", 6, "MACRO (7e machine)"), ("26-acid.json", 6, "ACID (7e machine)")):
        tw = json.loads(open(E.os.path.join(DEV, fname), encoding="utf-8").read())
        p, _ = build.apply_writes(stock, [tw])
        pl, _ = build.build_payload([tw], stock, None)
        img = bytes(p) + pl
        payload = None
        if tw.get("append", {}).get("dest"):
            payload = (int(tw["append"]["dest"], 16), build.payload_runtime(tw, stock, None))
        e = E.Engine(img, payload=payload)
        rows.append((label, depth(e, lambda e, t: e.set(t, machine=idx, decay=100, color=64, shape=20))))
        print("  accès hors carte :", len(e.unmapped), file=sys.stderr)
    for k, v in rows:
        print(f"{k:<24} {v:5} o sous l'entrée de la boucle des voix")


if __name__ == "__main__":
    main()
