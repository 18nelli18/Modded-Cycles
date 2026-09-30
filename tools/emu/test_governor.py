#!/usr/bin/env python3
"""Preuve du régulateur de charge (notes/25), sur le vrai code d'un tweak généré par gen_syntakt_engines.py.

La sonde de la fonction audio n'est pas émulée (il faudrait toute l'interruption) : après chaque bloc de la boucle
des voix, le test appelle le vrai audio_end() avec un minuteur simulé réglé sur la charge voulue. Référence : le
même firmware sans appel à audio_end() (charge nulle, arrêt des seules voix muettes).
  - charge normale (50 %) : sortie identique à la référence ;
  - forte charge (80 %) : une voix s'arrête dès qu'elle reste sous -66 dB (16 blocs), identique jusque-là ;
  - surcharge (90 %) : la voix calculée la plus faible (celles du Syntakt comptent double) s'éteint par un fondu
    de 8 blocs, une à la fois, jamais une note de moins de 16 blocs ; les autres restent identiques ; la voix
    éteinte repart à son trig suivant.

    python3 tools/emu/test_governor.py --cycles model-cycles_OS1.13.syx --syntakt Syntakt_OS1.41.syx --tweak ….json
"""
import argparse
import json
import pathlib
import struct
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import build                        # noqa: E402
import gen_syntakt_engines as gs    # noqa: E402
import mcengine as E                # noqa: E402
import test_sdvintage as T          # noqa: E402

TIMER, BLOCK = 0xfc07000c, 90112
FAIL = []


def check(ok, msg):
    print(("  ok    " if ok else "  ECHEC ") + msg, flush=True)
    if not ok:
        FAIL.append(msg)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True)
    ap.add_argument("--syntakt", required=True)
    ap.add_argument("--tweak", required=True, help="tweak généré avec au moins SD, CP (machines 6, 7) : les 5 moteurs")
    args = ap.parse_args()
    stock = T.main_os_from_syx(args.cycles)
    tw = json.loads(pathlib.Path(args.tweak).read_text(encoding="utf-8"))
    p, _ = build.apply_writes(stock, [tw])
    pl, _ = build.build_payload([tw], stock, args.syntakt)
    img = bytes(p) + pl
    sy = {k: int(v, 16) for k, v in tw["gov"].items()}
    cat = list(gs.CATALOG.values())

    def eng(i, dec):
        m = cat[i]
        return dict(machine=6 + i, note=60, pitch=64, color=m["knobs"][0][2], shape=m["knobs"][1][2],
                    sweep=m["knobs"][2][2], contour=m["knobs"][3][2], punch=0, gate=0, finetune=64, decay=dec)

    def stock_m(m, dec):
        return dict(machine=m, note=60, pitch=64, color=64, shape=64, sweep=64, contour=64, punch=0, gate=0,
                    finetune=64, decay=dec)

    def play(setup, blocks, trigs, load=None):
        """load : None (pas de régulation) ou fonction bloc -> charge en % ; rend les sorties et l'état par bloc."""
        e = E.Engine(img)
        e.uc.mem_map(0xfc070000, 0x1000)
        for t, kw in setup.items():
            e.set(t, **kw)
        out, fading, stolen, peaks = [], [], [], []
        now = 10_000_000
        for b in range(blocks):
            out.append(e.block(trigs.get(b, 0)))
            if load is not None:
                e.uc.mem_write(sy["gov_t0_audio"], struct.pack(">I", now & 0xffffffff))
                e.uc.mem_write(TIMER, struct.pack(">I", (now + load(b) * BLOCK // 100) & 0xffffffff))
                e.call(sy["audio_end"])
                now += BLOCK
            fading.append(bytes(e.uc.mem_read(sy["gov_fading"], 6)))
            stolen.append(bytes(e.uc.mem_read(sy["gov_stolen"], 6)))
            peaks.append((struct.unpack(">6i", e.uc.mem_read(sy["gov_peak"], 24)), bytes(e.uc.mem_read(sy["gov_st"], 6)),
                          bytes(e.uc.mem_read(sy["gov_quiet"], 6)), struct.unpack(">6H", e.uc.mem_read(sy["gov_age"], 12))))
        play.peaks = peaks
        return np.stack(out), fading, stolen      # out : blocs x 6 pistes x 32

    print("charge normale")
    setup = {0: eng(0, 40), 1: stock_m(1, 40), 2: eng(4, 40), 3: stock_m(4, 40)}
    ref, _, _ = play(setup, 300, {1: 0xf})
    mod, _, st = play(setup, 300, {1: 0xf}, load=lambda b: 50)
    check(np.array_equal(ref, mod) and not any(any(s) for s in st), "50 % : sortie identique, aucune voix éteinte")

    print("forte charge")
    mod, _, st = play(setup, 300, {1: 0xf}, load=lambda b: 80)
    ok, stops = True, {}
    for t in range(4):
        r, x = ref[:, t, :], mod[:, t, :]
        diff = np.nonzero(np.any(r != x, axis=1))[0]
        if len(diff):
            f = int(diff[0])
            stops[t] = f
            ok &= np.abs(r[f:]).max() < (1 << 20) and not x[f:].any()
    check(ok and not any(any(s) for s in st),
          f"80 % : les voix s'arrêtent sous -66 dB (blocs {stops}), identiques avant, aucune éteinte de force")

    print("surcharge")
    setup = {0: eng(0, 100), 1: stock_m(1, 100), 2: eng(4, 100), 3: stock_m(4, 100)}
    trigs = {1: 0xf, 250: 0x1}
    load = lambda b: 90 if b < 200 else 50
    ref, _, _ = play(setup, 300, trigs)
    mod, fading, stolen = play(setup, 300, trigs, load=load)
    order = []
    for b in range(300):
        for t in range(6):
            if stolen[b][t] and t not in order:
                order.append(t)
    one = all(sum(1 for x in f if x) <= 1 for f in fading)
    first_fade = next(b for b in range(300) if any(fading[b]))
    ok = one and first_fade >= 16 and len(order) >= 1
    # la 1re voix éteinte est la plus faible des voix calculées au moment du choix (clé = crête, /2 pour le Syntakt)
    t0 = order[0]
    fb = next(b for b in range(300) if fading[b][t0])
    pk, st_, qu, age = play.peaks[fb]
    keys = {t: (pk[t] >> (1 if st_[t] else 0)) for t in range(4) if qu[t] < 64 and age[t] >= 16}
    ok &= t0 == min(keys, key=keys.get)
    # fondu : la voix éteinte suit la référence multipliée par une rampe linéaire de 1 à 0 sur 8 blocs, puis zéros
    seg_r, seg_x = ref[fb + 1:fb + 1 + 8, t0, :].ravel().astype(float), mod[fb + 1:fb + 1 + 8, t0, :].ravel().astype(float)
    strong = np.nonzero(np.abs(seg_r) > 1e8)[0]
    g = seg_x[strong] / seg_r[strong]
    ok &= len(strong) > 20 and np.all(np.abs(g - (256 - strong) / 256) < 0.01)
    ok &= not mod[fb + 9:250, t0, :].any()
    # les voix non éteintes restent identiques tant qu'elles le sont
    for t in range(4):
        if t not in order:
            ok &= np.array_equal(ref[:250, t, :], mod[:250, t, :])
    # après la surcharge, plus de nouvelle extinction ; la voix 0 repart à son trig (bloc 250)
    later = [t for t in order if next(b for b in range(300) if stolen[b][t]) > 215]
    ok &= not later and (0 not in order or np.abs(mod[251:260, 0, :]).max() > 1e6)
    check(ok, f"90 % : 1er fondu au bloc {first_fade} (piste {t0 + 1}, clés {keys}), voix éteintes dans l'ordre "
              f"{order} (une à la fois), fondu "
              f"progressif puis silence, autres voix identiques ; plus rien après la surcharge ; retrig de la piste 1")
    print("\nTOUT OK" if not FAIL else f"\n{len(FAIL)} ÉCHEC(S)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
