#!/usr/bin/env python3
"""Le budget de charge des machines ajoutées (notes/81) : aucune ne doit dépasser BUDGET % du processeur par piste.

La mesure est celle de la page System de Model-TG (le temps de calcul d'une piste, en moyenne), prise par le modèle
du coût sur la machine (tools/emu/hwcost.py, notes/77 : instructions, attentes de l'EMAC, défauts des caches ; recoupé
par les relevés de Maxime, 30 % pour MODAL le 23/10/2026, 19 % à l'allumage le 25/10/2026) sur tout l'OS (os.json).
Une piste joue la machine, les cinq autres sont muettes. Le son est tenu (DECAY 110) : c'est le pire cas en continu.

Pour chaque machine : ses réglages par défaut et les extrêmes des potards qui changent le calcul, une note aiguë, et
(MODAL) la polyphonie avec toutes les voix qui sonnent, et un potard qui bouge à chaque bloc. Les machines d'origine
d'Elektron sont mesurées pour comparaison, sans contrôle.

    python3 tools/emu/test_budget.py --cycles model-cycles_OS1.13.syx --syntakt Syntakt_OS1.42.syx \\
        [--engines macro,modal,acid,syntakt] [--quick] [--jobs 8]
"""
import argparse
import collections
import concurrent.futures
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import gen_macro as gm              # noqa: E402
import gen_modal as gmo             # noqa: E402

BUDGET = 13.0                       # % du temps d'un bloc, par piste (la demande de Maxime, 26/10/2026)
PER = 250e6 * 32 / 48000            # cycles par bloc à 250 MHz (hwcost)
ORIGINE = ("KICK", "SNARE", "METAL", "PERC", "TONE", "CHORD")
SYNTAKT = ((7, "SDVtg"), (8, "CPVtg"), (9, "SYToy"), (10, "SYBit"), (11, "SYSwm"))
MACRO, ACID, MODAL = 12, 13, 14     # index des machines dans l'OS
POLY_FINE = {1: 64, 2: 80, 4: 96}   # FINE de MODAL : 1, 2, 4 voix


def configs(engines, quick):
    """(nom, machine, réglages, note, notes : 1 ou 5, potard qui bouge ou None, contrôlé)."""
    out = []
    if "origine" in engines:
        for m, name in enumerate(ORIGINE):
            out.append((f"origine {name}", m, dict(decay=110), 48, 1, None, False))
    if "syntakt" in engines:
        for m, name in SYNTAKT:
            for k, kw in enumerate([{}] + ([] if quick else [dict(color=127, shape=127, sweep=127, contour=127),
                                                             dict(color=0, shape=0, sweep=0, contour=0)])):
                out.append((f"syntakt {name} {('défaut', 'potards à 127', 'potards à 0')[k]}", m,
                            dict(kw, decay=110), 48, 1, None, True))
    if "acid" in engines:
        for k, kw in enumerate([{}] + ([] if quick else [dict(color=127, shape=127, sweep=127, contour=127)])):
            out.append((f"ACID {('défaut', 'potards à 127')[k]}", ACID, dict(kw, decay=110), 48, 1, None, True))
    if "macro" in engines:
        for i, name in enumerate(gm.MODELS):
            sets = [("défaut", dict(), 60, None)]
            if not quick:
                sets += [("TIMB 127 COLR 127", dict(color=127, sweep=127), 60, None),
                         ("TIMB 0 COLR 0", dict(color=0, sweep=0), 60, None),
                         ("TIMB 127 COLR 0", dict(color=127, sweep=0), 60, None),
                         ("note 110", dict(), 110, None),
                         ("BITS 2", dict(finetune=127), 60, None),
                         ("PITCH qui bouge", dict(), 60, "pitch"),
                         ("TIMBRE qui bouge", dict(), 60, "color")]
            for tag, kw, note, moving in sets:
                out.append((f"MACRO {i:2d} {name} {tag}", MACRO, dict(dict(color=64, sweep=64, decay=110), shape=i,
                                                                      **kw), note, 1, moving, True))
    if "modal" in engines:
        for shape in range(len(gmo.MODELS)):
            for nv, fine in POLY_FINE.items():
                base = dict(shape=shape, finetune=fine, color=64, sweep=40, contour=36, decay=110)
                sets = [("défaut", {}, None)]
                if not quick:
                    sets += [("brillant, structure haute", dict(color=127, contour=127, sweep=127), None),
                             ("sombre, structure basse", dict(color=0, contour=0, sweep=0), None),
                             ("COLOR qui bouge", {}, "color")]
                for tag, kw, moving in sets:
                    out.append((f"MODAL SHAPE {shape} {nv} voix {tag}", MODAL, dict(base, **kw), 48, 5, moving,
                                True))
    return out


_FW = None


def _init(cycles, syntakt):
    global _FW
    import hwcost as H
    _FW = H.firmware(cycles, syntakt)


def measure(conf):
    """La part d'une piste : moyenne et pire bloc, en % d'un bloc, sur les blocs où elle sonne."""
    import hwcost as H
    import mcengine as E
    import osbanc as O
    import seqrig as S
    label, mach, kw, note, notes, moving, _ = conf
    b = O.OsBanc(_FW)
    b.rig.param(0, E.SLOT["machine"], mach * 256)
    for k, v in kw.items():
        b.rig.param(0, E.SLOT[k], v * 256)
    for t in range(1, 6):
        b.rig.param(t, E.SLOT["machine"], 0)
    c = H.Cost(b)
    trigs = (2, 14, 26, 38, 50) if notes > 1 else (2,)
    first, blocks = (52, 110) if notes > 1 else (10, 50)
    tot, n, worst = collections.Counter(), 0, 0.0
    for blk in range(blocks):
        if blk in trigs:
            b.rig.set_step(0, 0, vel=100, length=S.LEN_1_16, note=note + 3 * trigs.index(blk))
            b.rig.schedule_step(0, 0, b.rig.now + b.rig.blk // 2)
        if moving:
            b.rig.param(0, E.SLOT[moving], (blk * 7 % 128) * 256)
        r = c.block()
        v = next((x for s, x in r.items() if s.startswith("voice:0:")), {})
        if blk >= first:
            tot.update(v)
            n += 1
            worst = max(worst, H.cycles(v))
    avg = {k: x / n for k, x in tot.items()}
    return label, H.cycles(avg) / PER * 100, worst / PER * 100


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True, help="model-cycles_OS1.13.syx officiel")
    ap.add_argument("--syntakt", required=True, help="Syntakt_OS1.42.syx (ou 1.41) officiel")
    ap.add_argument("--engines", default="origine,syntakt,acid,macro,modal",
                    help="machines à mesurer : origine, syntakt, acid, macro, modal")
    ap.add_argument("--quick", action="store_true", help="réglages par défaut seulement")
    ap.add_argument("--jobs", type=int, default=max(1, min(8, (os.cpu_count() or 2) - 2)))
    ap.add_argument("--budget", type=float, default=BUDGET)
    args = ap.parse_args()
    engines = set(args.engines.split(","))
    confs = configs(engines, args.quick)
    checked = {c[0]: c[6] for c in confs}
    print(f"{len(confs)} mesures, {args.jobs} processus, budget {args.budget:.1f} % par piste (moyenne)")
    res = []
    with concurrent.futures.ProcessPoolExecutor(args.jobs, initializer=_init,
                                                initargs=(args.cycles, args.syntakt)) as ex:
        for label, avg, worst in ex.map(measure, confs):
            res.append((label, avg, worst))
            print(f"  {'ok   ' if not checked[label] or avg <= args.budget else 'ECHEC'} {label:52s} "
                  f"{avg:5.1f} % (pire bloc {worst:5.1f} %){'' if checked[label] else ' (comparaison)'}",
                  flush=True)
    fail = [r for r in res if checked[r[0]] and r[1] > args.budget]
    by = collections.defaultdict(list)
    for label, avg, _ in res:
        by[label.split()[0]].append(avg)
    print("\n  au pire, par machine : " + ", ".join(f"{k} {max(v):.1f} %" for k, v in sorted(by.items())))
    print("\nTOUT OK" if not fail else f"\n{len(fail)} ÉCHEC(S) : au-dessus de {args.budget:.1f} %")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
