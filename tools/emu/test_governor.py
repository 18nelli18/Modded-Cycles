#!/usr/bin/env python3
"""Preuve du régulateur de charge (notes/25, notes/30, notes/36), sur le vrai code d'un tweak généré par
gen_syntakt_engines.py (régulateur en assembleur, tools/gov_asm.py).

La sonde de la fonction audio n'est pas émulée (il faudrait toute l'interruption) : après chaque bloc de la boucle
des voix, le test appelle le vrai audio_end() avec un minuteur simulé réglé sur la charge voulue. Le mix de l'OS
n'est pas émulé non plus : le test pose les gains de mixeur des pistes (0x40a78b80..0x40a78c08) ; au départ, tous
au même niveau. Référence : le même firmware sans appel à audio_end() (charge nulle, arrêt des seules voix muettes).
Seuils : gs.GOV.
  - charge normale (50 %) : sortie identique à la référence ;
  - forte charge (80 %) : une voix s'arrête dès qu'elle reste sous -66 dB (16 blocs), identique jusque-là ;
  - blocs chargés mais sous le pic, charge soutenue encore basse (91 %) : aucune voix éteinte de force ;
  - pics isolés (un bloc à 99 % tous les 10, le reste à 75 %) : aucune voix éteinte (notes/36 : le pic doit durer
    deux blocs) ; deux blocs de suite à 99 % : une extinction ;
  - pic qui dure (95 %, puis 97 % : surcharge sévère) : la voix la moins audible dans le mix s'éteint par un fondu de
    8 (puis 2) blocs, juste assez pour repasser sous peak - margin, jamais une note de moins de 16 (4) blocs ; les
    autres restent identiques ; plus rien quand la charge retombe ; la voix éteinte repart à son trig suivant ;
  - mix : une piste mutée (gains nuls) part la première, même si c'est la plus forte ; puis une piste au volume bas ;
    à égalité (toutes mutées), la note la plus ancienne ;
  - charge soutenue qui suit les voix (chaque voix calculée coûte 7 % d'un bloc, mesurés comme tels, 46 % pour le reste ;
    6 voix : 88 %) : une
    seule voix éteinte, la charge soutenue retombe sous steal sans autre extinction (notes/36 : le code C continuait
    tant que la moyenne lente restait haute, et sa moyenne lente ne montait pas : arrondi) ;
  - moyenne lente partie de 0 sous une charge constante de 88 % : elle monte (au moins 75 % après 600 blocs).

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
import gov_asm                      # noqa: E402
import mcengine as E                # noqa: E402
import test_sdvintage as T          # noqa: E402

TIMER, BLOCK = 0xfc07000c, 90112
GAINS = (0x40a78c08, 0x40a78be8, 0x40a78bd0, 0x40a78bb8, 0x40a78b9c, 0x40a78b80)   # gov_gains.S
FULL = 0x20000000
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

    def play(setup, blocks, trigs, load=None, cost=4000, slow0=0, gains=None):
        """load : None (pas de régulation) ou fonction (bloc, voix calculées dans ce bloc) -> charge en % ; chaque voix
        calculée coûte `cost` ticks (le minuteur avance à chaque lecture pendant la boucle des voix). gains : {piste :
        gain de mixeur}. Rend les sorties et l'état par bloc."""
        e = E.Engine(img)
        e.uc.mem_map(0x40800000, 0x00800000)       # BSS de l'OS : gains du mixeur
        for t in range(6):
            for a in GAINS:
                e.uc.mem_write(a + 4 * t, struct.pack(">I", (gains or {}).get(t, FULL)))
        clock = {"t": 10_000_000, "fixed": None, "reads": 0}

        def read(uc, access, addr, size, value, ud):
            if clock["fixed"] is None:
                clock["t"] += cost // 2                  # voice_gate puis voice_after : `cost` par voix calculée
                clock["reads"] += 1
                v = clock["t"]
            else:
                v = clock["fixed"]
            uc.mem_write(TIMER, struct.pack(">I", v & 0xffffffff))
        e.uc.hook_add(UC_HOOK_MEM_READ, read, begin=TIMER, end=TIMER + 3)
        for t, kw in setup.items():
            e.set(t, **kw)
        e.uc.mem_write(gov_asm.x_var(tw, "X_SLOW"), struct.pack(">I", slow0 * 65536 // 100))   # charge soutenue déjà là
        out, fading, stolen, flen, state = [], [], [], [], []
        now = 10_000_000
        for b in range(blocks):
            clock["reads"] = 0
            out.append(e.block(trigs.get(b, 0)))
            if load is not None:
                e.uc.mem_write(sy["gov_t0_audio"], struct.pack(">I", now & 0xffffffff))
                clock["fixed"] = now + load(b, clock["reads"] // 2) * BLOCK // 100
                e.call(sy["audio_end"])
                clock["fixed"] = None
                now += BLOCK
            fading.append(bytes(e.uc.mem_read(sy["gov_fading"], 6)))
            flen.append(bytes(e.uc.mem_read(sy["gov_flen"], 6)))
            stolen.append(bytes(e.uc.mem_read(sy["gov_stolen"], 6)))
            state.append((bytes(e.uc.mem_read(sy["gov_quiet"], 6)), struct.unpack(">6H", e.uc.mem_read(sy["gov_age"], 12)),
                          struct.unpack(">6I", e.uc.mem_read(sy["gov_cost"], 24)),
                          struct.unpack(">I", e.uc.mem_read(sy["gov_pressure"], 4))[0],
                          struct.unpack(">I", e.uc.mem_read(sy["gov_slow"], 4))[0],
                          struct.unpack(">I", e.uc.mem_read(sy["gov_avg"], 4))[0]))
        check.unmapped = e.unmapped
        play.state, play.flen = state, flen
        return np.stack(out), fading, stolen      # out : blocs x 6 pistes x 32

    print("charge normale")
    setup = {0: eng(0, 40), 1: stock_m(1, 40), 2: eng(4, 40), 3: stock_m(4, 40)}
    ref, _, _ = play(setup, 300, {1: 0xf})
    mod, _, st = play(setup, 300, {1: 0xf}, load=lambda b, n: 50)
    check(np.array_equal(ref, mod) and not any(any(s) for s in st) and not check.unmapped,
          "50 % : sortie identique, aucune voix éteinte, aucun accès hors de la mémoire émulée")

    G = gs.GOV
    Q = lambda pct: pct * 256 // 100                # seuils, comme PCT() de bridge_engines.c

    def no_forced(load, label, setup=setup, trigs={1: 0xf}, ref=ref):
        """Pas d'extinction de force : seules les voix restées sous -66 dB (16 blocs) s'arrêtent."""
        mod, _, st = play(setup, 300, trigs, load=load)
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
    no_forced(lambda b, n: 80, "80 %")
    print("blocs chargés sous le pic, charge soutenue basse")
    no_forced(lambda b, n: 91, f"91 % pendant 300 blocs (pic {G['peak']} %, moyenne lente partie de 0)")

    long_ = {0: eng(0, 100), 1: stock_m(1, 100), 2: eng(4, 100), 3: stock_m(4, 100)}
    trigs = {1: 0xf, 250: 0x1}
    ref_l, _, _ = play(long_, 300, trigs)
    print("pics isolés")
    mod, _, st = play(long_, 300, trigs, load=lambda b, n: 99 if b % 10 == 5 else 75)
    check(np.array_equal(ref_l, mod) and not any(any(s) for s in st),
          "un bloc à 99 % tous les 10 blocs, 75 % sinon : sortie identique, aucune voix éteinte")
    mod, fading, st = play(long_, 300, trigs, load=lambda b, n: 99 if b in (40, 41) else 75)
    cut = sorted({t for b in range(300) for t in range(6) if fading[b][t]})
    first = next(b for b in range(300) if any(fading[b]))
    check(first == 41 and len(cut) >= 1, f"deux blocs de suite à 99 % (40, 41) : extinction au bloc {first}, pistes "
                                         f"{[t + 1 for t in cut]}")

    def overload(level, fade, min_age, label, gains=None, order=None):
        load = lambda b, n: level if b < 200 else 50
        mod, fading, stolen = play(long_, 300, trigs, load=load, gains=gains)
        fb = next(b for b in range(300) if any(fading[b]))
        quiet, age, cost, pressure, slow, avg = play.state[fb]   # état vu par le régulateur à la fin du bloc fb
        first = [t for t in range(6) if fading[fb][t]]
        # la voix éteinte la première est la moins audible dans le mix : somme des |x| de sa piste (après le bloc
        # fb-1... le régulateur lit la sortie du bloc qu'il vient de mesurer) x son plus grand gain de mixeur
        need = 16 if pressure else 64
        g = gains or {}
        cand = [t for t in range(6) if quiet[t] < need and age[t] >= min_age]
        key = {t: audible(mod[fb, t, :], g.get(t, FULL)) for t in cand}
        want = sorted(cand, key=lambda t: (key[t], -age[t], t))
        pk = (level * BLOCK // 100) * 256 // BLOCK  # charge du bloc, comme audio_end ; le pic dure (charge constante)
        excess = max((pk - Q(G["peak"] - G["margin"])) * (BLOCK >> 8), 0)
        sel, acc = [], 0
        for t in want:
            if acc >= excess or len(sel) == 2:
                break
            sel.append(t)
            acc += cost[t] + 1
        ok = sorted(first) == sorted(sel) and fb >= 2 and all(age[t] >= min_age for t in first)
        ok &= all(play.flen[fb][t] == fade for t in first)
        if order is not None:                    # ces pistes (sinon parmi les plus fortes) partent dans ce bloc
            ok &= all(t in first for t in order)
        for t in first:                          # fondu linéaire de 1 à 0 sur `fade` blocs, puis silence
            seg_r = ref_l[fb + 1:fb + 1 + fade, t, :].ravel().astype(float)
            seg_x = mod[fb + 1:fb + 1 + fade, t, :].ravel().astype(float)
            strong = np.nonzero(np.abs(seg_r) > 1e8)[0]
            n = 32 * fade
            ok &= np.all(np.abs(seg_x[strong] / seg_r[strong] - (n - strong) / n) < 0.02)
            ok &= not mod[fb + 1 + fade:250, t, :].any()
        for t in range(6):                       # les autres restent identiques jusqu'à leur propre extinction
            if t not in first:
                end = next((b for b in range(300) if fading[b][t]), 250)
                ok &= np.array_equal(ref_l[:min(end, 250) + 1, t, :], mod[:min(end, 250) + 1, t, :])
        late = [t for t in range(6) if any(stolen[b][t] for b in range(300))
                and next(b for b in range(300) if stolen[b][t]) > 230]
        ok &= not late and np.abs(mod[251:260, 0, :]).max() > 1e6 and len(first) <= 2
        check(ok, f"{label} : au bloc {fb}, extinction des pistes {[t + 1 for t in first]} (les moins audibles dans le "
                  f"mix, {acc} ticks pour {excess} à libérer), fondu de {fade} blocs puis silence, autres voix "
                  f"identiques ; plus rien après la surcharge ; retrig de la piste 1")
        return first

    def audible(x, gain):
        """Clé de gov_key.S : somme des |x| >> 8 (complément à un) sur la piste, >> 12, x (gain >> 16)."""
        a = sum(((int(v) if v >= 0 else ~int(v)) & 0xffffffff) >> 8 for v in x) >> 12
        return a * (gain >> 16)

    print("pic qui dure")
    base = overload(G["peak"] + 2, 8, 16, f"{G['peak'] + 2} % pendant 200 blocs")
    print("surcharge sévère")
    overload(G["severe"] + 1, 2, 4, f"{G['severe'] + 1} % pendant 200 blocs")
    print("audible dans le mix")
    loud = [t for t in (0, 2) if t not in base]
    overload(G["peak"] + 2, 8, 16, f"piste {loud[0] + 1} (parmi les plus fortes) mutée, gains nuls : elle part",
             gains={loud[0]: 0}, order=[loud[0]])
    overload(G["peak"] + 2, 8, 16, f"piste {loud[-1] + 1} (parmi les plus fortes) à -30 dB dans le mix : elle part",
             gains={loud[-1]: FULL // 32}, order=[loud[-1]])
    six = {0: eng(0, 100), 1: stock_m(1, 100), 2: eng(4, 100), 3: stock_m(4, 100), 4: eng(1, 100), 5: stock_m(0, 100)}
    mod, fading, _ = play(six, 120, {1: 0x8, 5: 0x2, 9: 0x20, 13: 0x1, 17: 0x10, 21: 0x4},
                          load=lambda b, n: G["peak"] + 2 if 60 <= b < 100 else 50, gains={t: 0 for t in range(6)})
    fb = next(b for b in range(120) if any(fading[b]))
    first = [t for t in range(6) if fading[fb][t]]
    check(fb == 61 and first == [1, 3], f"toutes les pistes mutées (clés nulles), jouées dans l'ordre 4, 2, 6, 1, 5, 3 : "
                                        f"au bloc {fb}, extinction des plus anciennes, pistes {[t + 1 for t in first]}")

    print("charge soutenue qui suit les voix")
    mod, fading, stolen = play(six, 400, {1: 0x3f}, load=lambda b, n: 46 + 7 * n, slow0=88,
                               cost=2 * 7 * BLOCK // 100)   # mesurés : la moitié (entre voice_gate et voice_after)
    cut = sorted({t for b in range(400) for t in range(6) if fading[b][t]})
    slow_end = play.state[-1][4] * 100 / 256
    check(len(cut) == 1 and slow_end < G["steal"],
          f"6 voix à 88 %, moyenne lente partie de 88 % : {len(cut)} voix éteinte (piste {[t + 1 for t in cut]}), "
          f"moyenne lente à {slow_end:.1f} % au bloc 400")
    mod, fading, _ = play(six, 600, {1: 0x3f}, load=lambda b, n: 88)
    slow = play.state[-1][4] * 100 / 256
    check(slow >= 75, f"moyenne lente partie de 0, charge de 88 % pendant 600 blocs : {slow:.1f} % (le code C restait à 0)")
    print("\nTOUT OK" if not FAIL else f"\n{len(FAIL)} ÉCHEC(S)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
