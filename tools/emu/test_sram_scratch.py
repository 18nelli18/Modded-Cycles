#!/usr/bin/env python3
"""Preuve de l'emprunt de la SRAM interne par les moteurs du Syntakt (notes/26), sur le vrai code d'un tweak généré
par gen_syntakt_engines.py (SRAM_MAP : tampons de travail dans la zone de travail des machines d'origine, table de
sinus du Cycles).
  1. statique : dans le code de l'OS, seuls la remise à zéro des voix et les moteurs d'origine
     (0x400a7ab8..0x400ab800) désignent la zone empruntée ; la table de sinus du Syntakt est celle du Cycles ; les
     tampons déplacés tiennent dans la zone sans se chevaucher ;
  2. brouillon : avant le calcul de chaque voix, la zone empruntée est remplie de valeurs aléatoires ; les 6 sorties
     restent identiques, échantillon par échantillon (machines d'origine et du Syntakt mêlées, réglages aléatoires) ;
  3. les voix du Syntakt ne touchent, dans la zone, que les 128 premiers octets de chaque tampon déplacé ; elles
     n'écrivent jamais dans la table de sinus ; plus rien ne passe par l'ancienne place de ces données en SDRAM.

    python3 tools/emu/test_sram_scratch.py --cycles model-cycles_OS1.13.syx --syntakt Syntakt_OS1.42.syx --tweak ….json
"""
import argparse
import bisect
import json
import pathlib
import random
import re
import struct
import subprocess
import sys
import tempfile

import numpy as np
from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE, UC_MEM_WRITE
from unicorn import m68k_const as mk

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import build                        # noqa: E402
import gen_sdvintage_exact as gx    # noqa: E402
import gen_syntakt_engines as gs    # noqa: E402
import mcengine as E                # noqa: E402
import syntakt                      # noqa: E402
import test_sdvintage as T          # noqa: E402

ENGINES = (0x400a7ab8, 0x400ab800)  # remise à zéro des voix (0x400a7ab8) et moteurs d'origine
FAIL = []


def check(ok, msg):
    print(("  ok    " if ok else "  ECHEC ") + msg, flush=True)
    if not ok:
        FAIL.append(msg)


def code_refs(img, lo, hi):
    """Instructions du code de l'OS (jusqu'aux données, 0x40118000) qui contiennent une constante dans [lo, hi)."""
    with tempfile.TemporaryDirectory() as d:
        path = pathlib.Path(d) / "os.bin"
        path.write_bytes(img)
        out = subprocess.run([gx.CROSS + "objdump", "-D", "-b", "binary", "-m", "m68k:isa-c:emac",
                              f"--adjust-vma={E.BASE:#x}", "--stop-address=0x40118000", str(path)],
                             capture_output=True, text=True, check=True).stdout
    starts = []
    for line in out.splitlines():
        m = re.match(r"\s*([0-9a-f]+):\t([0-9a-f ]+)\t(\S+)", line)
        if m and not m.group(3).startswith("."):
            starts.append((int(m.group(1), 16), len(m.group(2).replace(" ", "")) // 2))
    keys = [a for a, _ in starts]
    refs = []
    for off in range(0, 0x40118000 - E.BASE - 3, 2):
        if lo <= struct.unpack_from(">I", img, off)[0] < hi:
            va = off + E.BASE
            i = bisect.bisect_right(keys, va) - 1
            if i >= 0 and starts[i][0] + starts[i][1] > va:
                refs.append(starts[i][0])
    return refs


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True)
    ap.add_argument("--syntakt", required=True)
    ap.add_argument("--tweak", required=True, help="tweak généré avec les 5 moteurs")
    ap.add_argument("--runs", type=int, default=12)
    args = ap.parse_args()
    stock = T.main_os_from_syx(args.cycles)
    st_img = syntakt.dsp_image(args.syntakt)
    tw = json.loads(pathlib.Path(args.tweak).read_text(encoding="utf-8"))
    p, _ = build.apply_writes(stock, [tw])
    pl, _ = build.build_payload([tw], stock, args.syntakt)
    img = bytes(p) + pl
    lo, hi = gs.SCRATCH_POOL
    sine = gs.SINE
    codes = tw["id"].split("-")[1:]
    cat = [gs.CATALOG[c] for c in codes]

    print("statique")
    refs = code_refs(stock, lo, hi)
    check(refs and all(ENGINES[0] <= a < ENGINES[1] for a in refs),
          f"zone {lo:#x}..{hi:#x} : {len(refs)} références, toutes dans la remise à zéro et les moteurs d'origine "
          f"({min(refs):#x}..{max(refs):#x})")
    try:
        gs.check_sram_map(stock, st_img)
        ok = True
    except SystemExit:
        ok = False
    heads = sorted(gs.sram_moved(s + k * step) for s, step, n in gs.SCRATCH_HEADS for k in range(n))
    check(ok, f"{len(heads)} tampons de 128 o dans la zone ({heads[0]:#x}..{heads[-1] + 128:#x}), sans "
              f"chevauchement ; table de sinus {sine[0]:#x} identique à {sine[2]:#x} ({sine[1] - sine[0]} o)")

    allowed = set()
    for h in heads:
        allowed.update(range(h, h + 128))
    old = [(lo_ - 0x80000000 + gx.DST_SRAM, hi_ - 0x80000000 + gx.DST_SRAM) for lo_, hi_, _ in gs.SRAM_MAP]

    def run(seed, poison):
        rng = random.Random(seed)
        e = E.Engine(img)
        prng = np.random.default_rng(seed)
        machine = {}
        for t in range(6):
            m = rng.randrange(6 + len(cat))
            machine[t] = m
            if m >= 6:
                kn = cat[m - 6]["knobs"]
                knob = [rng.randint(*(k[3:5] if len(k) > 3 else (0, 127))) for k in kn]
            else:
                knob = [rng.randint(0, 127) for _ in range(4)]
            e.set(t, machine=m, note=rng.randint(24, 96), pitch=rng.randint(0, 127), color=knob[0], shape=knob[1],
                  sweep=knob[2], contour=knob[3], punch=rng.randint(0, 1), gate=rng.randint(0, 1),
                  finetune=rng.randint(0, 127), decay=rng.randint(10, 127))
        trigs = {b: rng.randrange(64) for b in rng.sample(range(2, 150), 12)}
        trigs[1] = 0x3f
        cur, bad, olds, sine_w = [None], [], [], []

        def at_voice(uc, a, size, ud):
            if a == gs.DISPATCH[0]:
                cur[0] = uc.reg_read(mk.UC_M68K_REG_D4)     # moteur calculé (KICK avant le 1er trig de la piste)
                if poison:
                    uc.mem_write(lo, prng.integers(0, 256, hi - lo, dtype=np.uint8).tobytes())
            else:
                cur[0] = None

        def in_pool(uc, access, addr, size, value, ud):
            if cur[0] is not None and cur[0] >= 6:
                bad.extend(x for x in range(addr, addr + size) if lo <= x < hi and x not in allowed)

        def in_old(uc, access, addr, size, value, ud):
            if any(a <= addr < b for a, b in old):
                olds.append(addr)

        def in_sine(uc, access, addr, size, value, ud):
            sine_w.append(addr)
        e.uc.hook_add(UC_HOOK_CODE, at_voice, begin=gs.DISPATCH[0], end=gs.DISPATCH[0])
        e.uc.hook_add(UC_HOOK_CODE, at_voice, begin=gs.DISPATCH[1], end=gs.DISPATCH[1])
        e.uc.hook_add(UC_HOOK_MEM_READ | UC_HOOK_MEM_WRITE, in_pool, begin=lo, end=hi - 1)
        e.uc.hook_add(UC_HOOK_MEM_READ | UC_HOOK_MEM_WRITE, in_old, begin=old[0][0] & ~0xffff, end=(old[0][0] | 0xffff))
        e.uc.hook_add(UC_HOOK_MEM_WRITE, in_sine, begin=sine[2], end=sine[2] + sine[1] - sine[0] - 1)
        out = np.stack([e.block(trigs.get(b, 0)) for b in range(150)])
        return out, machine, bad, olds, sine_w

    print("brouillon : zone remplie au hasard avant chaque voix")
    for seed in range(args.runs):
        ref, machine, bad, olds, sine_w = run(seed, False)
        mod, _, bad2, olds2, sine_w2 = run(seed, True)
        names = [cat[m - 6]["name"] if m >= 6 else ("KICK", "SNARE", "METAL", "PERC", "TONE", "CHORD")[m]
                 for m in machine.values()]
        loud = int(np.count_nonzero(np.abs(ref).max(axis=(0, 2)) > 1 << 20))
        check(np.array_equal(ref, mod) and not (bad or bad2 or olds or olds2 or sine_w or sine_w2),
              f"essai {seed:2d} {' '.join(f'{n:5s}' for n in names)} : 6 sorties identiques ({loud} pistes sonores) ; "
              f"hors des tampons : {len(set(bad + bad2))} o ; ancienne place : {len(olds + olds2)} ; sinus écrit : "
              f"{len(sine_w + sine_w2)}")
    print("\nTOUT OK" if not FAIL else f"\n{len(FAIL)} ÉCHEC(S)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
