#!/usr/bin/env python3
"""Preuve de l'arrêt des voix muettes (notes/23), dans les tweaks générés par gen_syntakt_engines.py.

Pour chaque machine d'origine (et un moteur du Syntakt), sur le vrai code de l'OS, on compare le firmware modifié
au Cycles d'origine (ou au tweak sans l'arrêt des voix muettes, pour les moteurs du Syntakt) :
  - son : identique échantillon par échantillon tant que la voix est calculée ; ensuite la référence reste sous
    le seuil (IDLE_THR), la voix modifiée sort des zéros ;
  - coût : instructions par bloc de la boucle des voix, une fois les 6 voix muettes ;
  - redéclenchement après l'arrêt : écart avec la référence (rapporté à la crête du son).

    python3 tools/emu/test_idle.py --cycles model-cycles_OS1.13.syx --syntakt Syntakt_OS1.42.syx --tweak ….json
"""
import argparse
import json
import pathlib
import sys

import numpy as np
from unicorn import UC_HOOK_CODE

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import build                        # noqa: E402
import gen_syntakt_engines as gs    # noqa: E402
import mcengine as E                # noqa: E402
import test_sdvintage as T          # noqa: E402

FAIL = []
NAMES = ["KICK", "SNARE", "METAL", "PERC", "TONE", "CHORD"]


def check(ok, msg):
    print(("  ok    " if ok else "  ECHEC ") + msg, flush=True)
    if not ok:
        FAIL.append(msg)


def firmware(stock, path, syntakt):
    tw = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    p, _ = build.apply_writes(stock, [tw])
    pl, _ = build.build_payload([tw], stock, syntakt)
    return bytes(p) + pl


def play(img, setup, blocks, trigs, count=False):
    """setup : {piste: réglages} ; trigs : {bloc: masque}. Rend les sorties (6 x 32 par bloc) et le coût par bloc."""
    e = E.Engine(img)
    for t, kw in setup.items():
        e.set(t, **kw)
    n = [0]
    if count:
        e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, u: n.__setitem__(0, n[0] + 1))
    out, cost = [], []
    for b in range(blocks):
        n[0] = 0
        out.append(e.block(trigs.get(b, 0)))
        cost.append(n[0])
    return np.concatenate(out, axis=1), cost


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True)
    ap.add_argument("--syntakt", required=True)
    ap.add_argument("--tweak", required=True, help="tweak généré (avec l'arrêt des voix muettes)")
    ap.add_argument("--ref", help="le même tweak sans l'arrêt des voix muettes (référence des moteurs du Syntakt)")
    args = ap.parse_args()
    stock = T.main_os_from_syx(args.cycles)
    img = firmware(stock, args.tweak, args.syntakt)
    thr = gs.IDLE_THR
    base = dict(note=60, pitch=64, color=64, shape=64, sweep=64, contour=64, punch=0, gate=0, finetune=64)

    print("machines d'origine : son, arrêt, redéclenchement")
    for m in range(6):
        setup = {0: dict(base, machine=m, decay=20)}
        trigs = {1: 1, 700: 1}
        ref, _ = play(stock, setup, 900, trigs)
        mod, _ = play(img, setup, 900, trigs)
        r, x = ref[0].reshape(-1, 32), mod[0].reshape(-1, 32)
        diff = np.nonzero(np.any(r != x, axis=1))[0]
        first = int(diff[0]) if len(diff) else None
        # jusqu'au 1er écart, identique ; entre l'arrêt et le 2e trig, la référence reste sous le seuil
        quiet = first is None or first >= 700 or (np.abs(r[first:700]).max() < thr and not x[first:700].any())
        after = np.abs(r[700:] - x[700:]).max() / max(1, np.abs(r[700:]).max())
        check(quiet and after < 1e-3,
              f"{NAMES[m]:5s} DEC 20 : identique jusqu'au bloc {first if first is not None else '—'} ; puis référence "
              f"sous {thr} ; 2e trig (bloc 700) : écart {after:.1e} de la crête")

    print("coût : 6 voix d'origine déclenchées au bloc 1, puis rien")
    setup = {t: dict(base, machine=t, decay=20) for t in range(6)}
    _, c_ref = play(stock, setup, 700, {1: 0x3f}, count=True)
    _, c_mod = play(img, setup, 700, {1: 0x3f}, count=True)
    check(c_mod[-1] < c_ref[-1] / 3,
          f"instructions par bloc au bloc 699 : Cycles d'origine {c_ref[-1]}, modifié {c_mod[-1]} ; "
          f"au bloc 5 (tout joue) : {c_ref[5]} / {c_mod[5]}")
    print("   machines arrêtées au fil des blocs (modifié) :",
          {b: c_mod[b] for b in (5, 100, 200, 300, 400, 500, 600, 699)})

    if args.ref:
        print("moteur du Syntakt")
        img_ref = firmware(stock, args.ref, args.syntakt)
        tw = json.loads(pathlib.Path(args.tweak).read_text(encoding="utf-8"))
        code = tw["id"].split("-")[1]
        mdef = gs.CATALOG[code]
        kw = dict(base, machine=6, color=mdef["knobs"][0][2], shape=mdef["knobs"][1][2], sweep=mdef["knobs"][2][2],
                  contour=mdef["knobs"][3][2], decay=10)
        ref, cr = play(img_ref, {0: kw}, 1400, {1: 1, 1200: 1}, count=True)
        mod, cm = play(img, {0: kw}, 1400, {1: 1, 1200: 1}, count=True)
        r, x = ref[0].reshape(-1, 32), mod[0].reshape(-1, 32)
        diff = np.nonzero(np.any(r != x, axis=1))[0]
        first = int(diff[0]) if len(diff) else None
        quiet = first is None or first >= 1200 or (np.abs(r[first:1200]).max() < thr and not x[first:1200].any())
        # Un moteur du Syntakt ne remet pas ses oscillateurs à zéro au trig : après l'arrêt, la note repart avec
        # une autre phase qu'avec la référence (comme deux notes jouées à des moments différents). On vérifie
        # que la 2e note a le même niveau que la référence et que la 1re note.
        rms = lambda y: float(np.sqrt(np.mean(y.astype(np.float64) ** 2)))
        db = lambda a, b: 20 * np.log10(a / b)
        d2, d1 = db(rms(x[1200:1300]), rms(r[1200:1300])), db(rms(x[1200:1300]), rms(x[1:101]))
        check(quiet and abs(d2) < 1 and abs(d1) < 1 and cm[1190] < cr[1190] / 3,
              f"{mdef['name']} DEC 10 : identique jusqu'au bloc {first} ; 2e note : {d2:+.2f} dB / référence, "
              f"{d1:+.2f} dB / 1re note ; coût au bloc 1190 : {cr[1190]} -> {cm[1190]}")
    print("\nTOUT OK" if not FAIL else f"\n{len(FAIL)} ÉCHEC(S)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
