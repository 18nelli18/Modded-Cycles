#!/usr/bin/env python3
"""Preuve du régulateur de charge (notes/25, notes/30), sur le vrai code d'un tweak généré par gen_syntakt_engines.py.

La sonde de la fonction audio n'est pas émulée (il faudrait toute l'interruption) : après chaque bloc de la boucle
des voix, le test appelle le vrai audio_end() avec un minuteur simulé réglé sur la charge voulue. Référence : le
même firmware sans appel à audio_end() (charge nulle, arrêt des seules voix muettes). Seuils : gs.GOV.
  - charge normale (50 %) : sortie identique à la référence ;
  - forte charge (80 %) : une voix s'arrête dès qu'elle reste sous -66 dB (16 blocs), identique jusque-là ;
  - blocs chargés mais sous le pic, charge soutenue encore basse (91 %) : aucune voix éteinte de force ;
  - charge soutenue au-dessus de steal (moyenne lente déjà à 88 %) : les voix les plus faibles s'éteignent par
    un fondu de 8 blocs, juste assez pour revenir à target, jamais une note de moins de 16 blocs ;
  - un bloc au-dessus de peak (95 %), puis au-dessus de severe (97 %) : idem pour revenir sous peak - margin,
    fondus de 8 puis 2 blocs ; les autres voix restent identiques ; la voix éteinte repart à son trig suivant.

    python3 tools/emu/test_governor.py --cycles model-cycles_OS1.13.syx --syntakt Syntakt_OS1.42.syx --tweak ….json
"""
import argparse
import json
import pathlib
import struct
import sys

import numpy as np
from unicorn import UC_HOOK_MEM_READ

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

    def play(setup, blocks, trigs, load=None, cost=4000, slow0=0):
        """load : None (pas de régulation) ou fonction bloc -> charge en % ; chaque voix calculée coûte `cost` ticks
        (le minuteur avance à chaque lecture pendant la boucle des voix). Rend les sorties et l'état par bloc."""
        e = E.Engine(img)
        clock = {"t": 10_000_000, "fixed": None}

        def read(uc, access, addr, size, value, ud):
            if clock["fixed"] is None:
                clock["t"] += cost // 2                  # voice_gate puis voice_after : `cost` par voix calculée
                v = clock["t"]
            else:
                v = clock["fixed"]
            uc.mem_write(TIMER, struct.pack(">I", v & 0xffffffff))
        e.uc.hook_add(UC_HOOK_MEM_READ, read, begin=TIMER, end=TIMER + 3)
        for t, kw in setup.items():
            e.set(t, **kw)
        e.uc.mem_write(sy["gov_slow"], struct.pack(">I", slow0 * 256 // 100))   # charge soutenue déjà là
        out, fading, stolen, flen = [], [], [], []
        peaks = []
        now = 10_000_000
        for b in range(blocks):
            out.append(e.block(trigs.get(b, 0)))
            if load is not None:
                e.uc.mem_write(sy["gov_t0_audio"], struct.pack(">I", now & 0xffffffff))
                clock["fixed"] = now + load(b) * BLOCK // 100
                e.call(sy["audio_end"])
                clock["fixed"] = None
                now += BLOCK
            fading.append(bytes(e.uc.mem_read(sy["gov_fading"], 6)))
            flen.append(bytes(e.uc.mem_read(sy["gov_flen"], 6)))
            stolen.append(bytes(e.uc.mem_read(sy["gov_stolen"], 6)))
            peaks.append((struct.unpack(">6i", e.uc.mem_read(sy["gov_peak"], 24)), bytes(e.uc.mem_read(sy["gov_st"], 6)),
                          bytes(e.uc.mem_read(sy["gov_quiet"], 6)), struct.unpack(">6H", e.uc.mem_read(sy["gov_age"], 12)),
                          struct.unpack(">6I", e.uc.mem_read(sy["gov_cost"], 24)),
                          struct.unpack(">I", e.uc.mem_read(sy["gov_pressure"], 4))[0],
                          struct.unpack(">I", e.uc.mem_read(sy["gov_slow"], 4))[0]))
        play.peaks, play.flen = peaks, flen
        return np.stack(out), fading, stolen      # out : blocs x 6 pistes x 32

    print("charge normale")
    setup = {0: eng(0, 40), 1: stock_m(1, 40), 2: eng(4, 40), 3: stock_m(4, 40)}
    ref, _, _ = play(setup, 300, {1: 0xf})
    mod, _, st = play(setup, 300, {1: 0xf}, load=lambda b: 50)
    check(np.array_equal(ref, mod) and not any(any(s) for s in st), "50 % : sortie identique, aucune voix éteinte")

    G = gs.GOV
    Q = lambda pct: pct * 256 // 100                # seuils, comme PCT() de bridge_engines.c

    def no_forced(level, label):
        """Pas d'extinction de force : seules les voix restées sous -66 dB (16 blocs) s'arrêtent."""
        mod, _, st = play(setup, 300, {1: 0xf}, load=lambda b: level)
        ok, stops = True, {}
        for t in range(4):
            r, x = ref[:, t, :], mod[:, t, :]
            diff = np.nonzero(np.any(r != x, axis=1))[0]
            if len(diff):
                f = int(diff[0])
                stops[t] = f
                ok &= np.abs(r[f:]).max() < (1 << 20) and not x[f:].any()
        check(ok and not any(any(s) for s in st),
              f"{label} : les voix s'arrêtent sous -66 dB (blocs {stops}), identiques avant, aucune éteinte de force")

    print("forte charge")
    no_forced(80, "80 %")
    print("blocs chargés sous le pic, charge soutenue basse")
    no_forced(91, f"91 % pendant 300 blocs (pic {G['peak']} %, moyenne lente partie de 0)")

    def overload(level, slow0, fade, min_age, label):
        setup = {0: eng(0, 100), 1: stock_m(1, 100), 2: eng(4, 100), 3: stock_m(4, 100)}
        trigs = {1: 0xf, 250: 0x1}
        load = lambda b: level if b < 200 else 50
        ref, _, _ = play(setup, 300, trigs)
        mod, fading, stolen = play(setup, 300, trigs, load=load, slow0=slow0)
        fb = next(b for b in range(300) if any(fading[b]))
        pk, st_, qu, age, cost, pressure, slow = play.peaks[fb]  # état vu par le régulateur à la fin du bloc fb
        first = [t for t in range(6) if fading[fb][t]]
        # les voix éteintes au 1er choix sont les plus faibles (clé = crête), juste assez pour libérer le temps
        # manquant : charge soutenue - target, ou charge du bloc - (peak - margin)
        need = 16 if pressure else 64
        cand = sorted((t for t in range(6) if qu[t] < need and age[t] >= min_age), key=lambda t: pk[t])
        load_q = (level * BLOCK // 100) * 256 // BLOCK
        excess = (slow - Q(G["target"])) * (BLOCK >> 8) if slow >= Q(G["steal"]) else 0
        if load_q >= Q(G["peak"]):
            excess = max(excess, (load_q - Q(G["peak"] - G["margin"])) * (BLOCK >> 8))
        want, acc = [], 0
        for t in cand:
            if acc >= excess or len(want) == 2:        # 2 voix par bloc au plus
                break
            want.append(t)
            acc += cost[t] + 1
        ok = sorted(first) == sorted(want) and all(age[t] >= min_age for t in first) and all(play.flen[fb][t] == fade for t in first)
        # fondu linéaire de 1 à 0 sur `fade` blocs, puis silence
        for t in first:
            seg_r = ref[fb + 1:fb + 1 + fade, t, :].ravel().astype(float)
            seg_x = mod[fb + 1:fb + 1 + fade, t, :].ravel().astype(float)
            if not np.abs(ref[fb:fb + 2, t, :]).max():
                continue                                  # voix muette (jamais jouée) : rien à fondre
            strong = np.nonzero(np.abs(seg_r) > 1e8)[0]
            n = 32 * fade
            g = seg_x[strong] / seg_r[strong]
            ok &= np.all(np.abs(g - (n - strong) / n) < 0.02)
            ok &= not mod[fb + 1 + fade:250, t, :].any()
        # les autres restent identiques jusqu'à leur propre extinction
        for t in range(6):
            if t not in first:
                end = next((b for b in range(300) if fading[b][t]), 250)
                ok &= np.array_equal(ref[:min(end, 250) + 1, t, :], mod[:min(end, 250) + 1, t, :])
        # plus de nouvelle extinction quand la charge est retombée (la moyenne lente redescend en une quinzaine de
        # blocs) ; la piste 1 repart à son trig (bloc 250)
        late = [t for t in range(6) if any(stolen[b][t] for b in range(300))
                and next(b for b in range(300) if stolen[b][t]) > 230]
        ok &= not late and np.abs(mod[251:260, 0, :]).max() > 1e6 and len(first) <= 2
        check(ok, f"{label} : au bloc {fb}, extinction simultanée des pistes {[t + 1 for t in first]} "
                  f"(les plus faibles, {acc} ticks pour {excess} à libérer), fondu de {fade} blocs puis silence, autres "
                  f"voix identiques ; plus rien après la surcharge ; retrig de la piste 1")

    print("charge soutenue")
    overload(G["steal"] + 2, G["steal"] + 2, 8, 16, f"{G['steal'] + 2} %, moyenne lente déjà à {G['steal'] + 2} %")
    print("bloc au-dessus du pic")
    overload(G["peak"] + 2, 0, 8, 16, f"{G['peak'] + 2} %, moyenne lente partie de 0")
    print("bloc au-dessus du seuil sévère")
    overload(G["severe"] + 1, 0, 2, 4, f"{G['severe'] + 1} %, moyenne lente partie de 0")
    print("\nTOUT OK" if not FAIL else f"\n{len(FAIL)} ÉCHEC(S)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
