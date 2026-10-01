#!/usr/bin/env python3
"""Preuve du code du Syntakt en SRAM interne (notes/28), sur le vrai code d'un tweak généré par gen_syntakt_engines.py.
Les 30 tables d'ondes de CHORD quittent la SRAM pour la charge utile ; leur place reçoit le code et des tables du
Syntakt, recopiés au démarrage par le crochet (stub.S, vérifié par test_syntakt_machines.py ; mcengine fait de même).
  1. statique : la table de 32 pointeurs 0x40118590, lue par 0x400a8060 (update de CHORD), est le seul chemin vers
     ces tables ; dans le tweak, ses 31 pointeurs SRAM visent des copies identiques au contenu de démarrage ;
  2. CHORD : réglages aléatoires (dont SHAPE, qui choisit les tables), sortie identique à l'OS d'origine, avant et
     après le 1er déclenchement d'une machine ajoutée ; plus aucune lecture de ses anciennes tables en SRAM ;
  3. machines du Syntakt : tout leur code s'exécute en SRAM, rien dans la zone de transit ; aucune machine
     d'origine ne touche la zone reprise.

    python3 tools/emu/test_sram_code.py --cycles model-cycles_OS1.13.syx --syntakt Syntakt_OS1.41.syx --tweak ….json
"""
import argparse
import json
import pathlib
import random
import struct
import sys

import numpy as np
from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE
from unicorn import m68k_const as mk

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import build                        # noqa: E402
import gen_syntakt_engines as gs    # noqa: E402
import mcengine as E                # noqa: E402
import test_sdvintage as T          # noqa: E402
from test_sram_scratch import code_refs   # noqa: E402

FAIL = []


def check(ok, msg):
    print(("  ok    " if ok else "  ECHEC ") + msg, flush=True)
    if not ok:
        FAIL.append(msg)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True)
    ap.add_argument("--syntakt", required=True)
    ap.add_argument("--tweak", required=True, help="tweak généré avec les 5 moteurs")
    ap.add_argument("--runs", type=int, default=10)
    args = ap.parse_args()
    stock = T.main_os_from_syx(args.cycles)
    tw = json.loads(pathlib.Path(args.tweak).read_text(encoding="utf-8"))
    p, _ = build.apply_writes(stock, [tw])
    pl, _ = build.build_payload([tw], stock, args.syntakt)
    img = bytes(p) + pl
    u32 = lambda im, va: struct.unpack_from(">I", im, va - E.BASE)[0]
    banks = gs.CHORD_BANKS
    codes = tw["id"].split("-")[1:]
    cat = [gs.CATALOG[c] for c in codes]

    print("statique")
    ptr_tab = gs.CHORD_PTRS - 4
    refs = code_refs(stock, ptr_tab, ptr_tab + 0x80)
    old = [u32(stock, gs.CHORD_PTRS + 4 * i) for i in range(31)]
    starts = {lo + 0x404 * k for lo, hi in banks for k in range((hi - lo) // 0x404)}
    where = [off + E.BASE for off in range(0, len(stock) - 3, 2) if struct.unpack_from(">I", stock, off)[0] in starts]
    # 0x4010b2c8 vaut 0x8000d2c8 au milieu d'une suite décroissante de 20 nombres proches de -1 (0x80013dd8 ...
    # 0x8000991f, lue par 0x4005631a) : une table numérique, pas un pointeur
    num = [u32(stock, a) for a in range(0x4010b2a0, 0x4010b2f0, 4)]
    numeric = all(x > y for x, y in zip(num, num[1:]))
    where = [a for a in where if not (a == 0x4010b2c8 and numeric)]
    check(refs == [0x400a806c] and sorted(set(old)) == sorted(starts)
          and where == [gs.CHORD_PTRS + 4 * i for i in range(31)],
          f"table de pointeurs {ptr_tab:#x} : lue par {[hex(a) for a in refs]} seulement ; ses 31 pointeurs SRAM "
          f"visent les {len(starts)} tables de 1 028 o de {[f'{lo:#x}..{hi:#x}' for lo, hi in banks]}, et nulle "
          f"part ailleurs dans l'OS on ne trouve l'adresse d'une de ces tables")
    new = [u32(img, gs.CHORD_PTRS + 4 * i) for i in range(31)]
    same = all(pl[n - E.PAYLOAD_DST:n - E.PAYLOAD_DST + 0x404] == gs.sram_init(stock, gs.CY_SRAM_INIT, o, 0x404)
               for o, n in zip(old, new))     # charge utile : recopiée à PAYLOAD_DST au démarrage
    check(same and all(E.PAYLOAD_DST <= n < 0x43100000 for n in new),
          f"tweak : les 31 pointeurs visent la charge utile ({min(new):#x}..{max(new) + 0x404:#x}), copies "
          f"identiques au contenu de démarrage de la SRAM")

    def run(seed, image, first_syntakt):
        """6 pistes : CHORD sur 0, 2, 4 (réglages aléatoires), et sur 1, 3, 5 des machines du Syntakt déclenchées
        à partir du bloc first_syntakt (ou d'origine si image est l'OS d'origine). Rend les sorties des pistes
        CHORD, et où s'exécute le code / ce qui lit les zones surveillées."""
        rng = random.Random(seed)
        e = E.Engine(image)
        chord = dict(machine=5, note=rng.randint(36, 84), pitch=rng.randint(40, 88), punch=0, gate=rng.randint(0, 1),
                     finetune=64, decay=rng.randint(30, 127))
        for t in (0, 2, 4):
            e.set(t, **dict(chord, color=rng.randint(0, 127), shape=rng.randint(0, 127), sweep=rng.randint(0, 127),
                            contour=rng.randint(0, 127)))
        for k, t in enumerate((1, 3, 5)):        # machines ajoutées 6.. dans l'ordre du tweak ; SNARE sur l'OS d'origine
            e.set(t, machine=6 + (seed + k) % len(cat) if image is img else 1, note=60, pitch=64, color=64, shape=64,
                  sweep=64, contour=64, punch=0, gate=0, finetune=64, decay=60)
        stats = dict(stage=0, sram=0, stock=0)
        cur = [None]

        def at_voice(uc, a, size, ud):
            cur[0] = uc.reg_read(mk.UC_M68K_REG_D4) if a == gs.DISPATCH[0] else None

        def fetch(uc, a, size, ud):
            if E.PAYLOAD_DST <= a < 0x43020000:
                stats["stage"] += 1
            elif gs.SRAM_RUN[0] <= a < gs.SRAM_RUN[1]:
                stats["sram"] += 1

        def touch(uc, access, addr, size, value, ud):
            if image is img and cur[0] is not None and cur[0] < 6:
                stats["stock"] += 1              # une machine d'origine (CHORD...) lit l'ancienne place des tables
        e.uc.hook_add(UC_HOOK_CODE, at_voice, begin=gs.DISPATCH[0], end=gs.DISPATCH[0])
        e.uc.hook_add(UC_HOOK_CODE, at_voice, begin=gs.DISPATCH[1], end=gs.DISPATCH[1])
        e.uc.hook_add(UC_HOOK_CODE, fetch, begin=E.PAYLOAD_DST, end=0x4301ffff)
        e.uc.hook_add(UC_HOOK_CODE, fetch, begin=gs.SRAM_RUN[0], end=gs.SRAM_RUN[1] - 1)
        for lo, hi in banks:
            e.uc.hook_add(UC_HOOK_MEM_READ | UC_HOOK_MEM_WRITE, touch, begin=lo, end=hi - 1)
        out = []
        for b in range(120):
            mask = 0x15 if b in (1, 60) else 0
            if b == first_syntakt or b == 90:
                mask |= 0x2a
            if b in (40, 80):                    # SHAPE (choix des tables) et COLOR changent en cours de note
                for t in (0, 2, 4):
                    e.trk[t].update(shape=rng.randint(0, 127), color=rng.randint(0, 127))
            out.append(e.block(mask)[[0, 2, 4]])
        return np.stack(out), stats

    print("CHORD et machines du Syntakt")
    for seed in range(args.runs):
        ref, _ = run(seed, stock, 30)
        mod, st = run(seed, img, 30)
        loud = float(np.abs(ref).max())
        check(np.array_equal(ref, mod) and loud > 1e6 and st["sram"] > 0 and st["stage"] == 0 and st["stock"] == 0,
              f"essai {seed}: 3 pistes CHORD identiques à l'OS d'origine (crête {loud:.2e}), avant et après le 1er "
              f"trig du Syntakt (bloc 30) ; code du Syntakt : {st['sram']} instructions en SRAM, {st['stage']} en "
              f"transit ; accès des machines d'origine à l'ancienne place des tables : {st['stock']}")
    print("\nTOUT OK" if not FAIL else f"\n{len(FAIL)} ÉCHEC(S)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
