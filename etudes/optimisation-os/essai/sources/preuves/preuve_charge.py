#!/usr/bin/env python3
"""Charge modélisée des deux fichiers d'essai, sur le banc de l'étage de sortie (banc_essai.py) et le modèle de cache
des notes 27-28 (trace.py de l'étude « sortie » : 1,54 cycle par instruction + 15 cycles par ligne de SDRAM
remplie ou recopiée, caches de 8 Ko, 166 667 cycles par bloc). Tout ce que le bloc exécute est compté : interruption
depuis 0x40058ca0 (séquenceur, lissage, LFO), fonction audio (voix, mixeur, effets, codec) et la sonde du compteur.
Hors modèle : l'entrée 0x40058c5e..0x40058ca0 et m_entry (une trentaine d'instructions, ~0,05 %), les interruptions
qui coupent l'audio (panneau, USB : 1 à 1,5 point selon la synthèse).

Scénarios (du démarrage, réglages par défaut, 120 BPM) :
  arret        aucun trig ; mesure aux blocs 100..119 (chaud) et 120..139 (caches vidés à chaque bloc) ;
  six          6 pistes, un trig sur chaque pas : une période de pas entière (188 blocs) en chaud, la suivante
               caches vidés : moyenne et pic (bloc du trig) ;
  envois       pareil, envois delay 40 et reverb 40 sur les 6 pistes ;
  dist         pareil, VOL+DIST 100 sur les 6 pistes ;
  apres        arrêt après avoir joué avec delay et reverb : envois 40/40, DECAY 20 (queues courtes, pour le banc),
               un trig des 6 pistes au bloc 2, puis rien ; mesure aux blocs 1 700..1 719 et 1 720..1 739, quand
               toutes les voix sont arrêtées (optimisé) et que delay et reverb ont des restes (p2 éveillé).

    python3 preuve_charge.py SCENARIO IMAGE [--out DOSSIER_DES_SYX]     (IMAGE : reference, optimise, officiel)
Écrit logs/charge_SCENARIO_IMAGE.json.
"""
import argparse
import json
import pathlib
import sys
import time

sys.dont_write_bytecode = True
import numpy as np                          # noqa: E402

import banc_essai as be                     # noqa: E402
import trace                                # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent


def block_cost(tr):
    rows = tr.per_func()
    cyc = sum(d["cycles"] for d in rows.values())
    ins = sum(d["ins"] for d in rows.values())
    voix = rows.get("voix (0x400a7d4a + machines)", {}).get("cycles", 0)
    return 100 * cyc / trace.CPB, ins, 100 * voix / trace.CPB


def cycles_so_far(tr):
    return trace.CPI * sum(tr.ins.values()) + trace.LINE_CYC * (sum(tr.imiss.values()) + sum(tr.dmiss.values()) +
                                                               sum(tr.dwb.values()))


def measure(b, tr, n, cold, before=None):
    out = []
    head = [0.0]
    b.at_call = lambda: head.__setitem__(0, cycles_so_far(tr))
    for k in range(n):
        if before:
            before()
        if cold:
            tr.ic.flush()
            tr.dc.flush()
        tr.reset()
        info = b.block()
        pct, ins, voix = block_cost(tr)
        out.append(dict(pct=pct, ins=ins, voix=voix, debut=100 * head[0] / trace.CPB, trig=info["trig"] & 0x3f))
    b.at_call = None
    return out


def summary(rows):
    p = np.array([r["pct"] for r in rows])
    return dict(n=len(rows), moyenne=round(float(p.mean()), 2), pic=round(float(p.max()), 2),
                mini=round(float(p.min()), 2), voix=round(float(np.mean([r["voix"] for r in rows])), 2),
                debut=round(float(np.mean([r["debut"] for r in rows])), 2),
                instr=round(float(np.mean([r["ins"] for r in rows]))))


def run(scen, img, opt):
    b = be.Banc(img)
    tr = trace.Tracer(b)
    res = {}
    if scen in ("arret", "apres"):
        if scen == "apres":
            for t in range(6):
                b.param(t, 20, 40)
                b.param(t, 21, 40)
                b.param(t, 18, 20)
                b.rig.set_step(t, 0, vel=100, length=be.seqrig.LEN_1_16)
        start = 100 if scen == "arret" else 1700
        for k in range(start - 1):
            if scen == "apres" and k == 1:
                for t in range(6):
                    b.rig.schedule_step(t, 0, b.rig.now + b.rig.blk)
            b.block()
        tr.on = True
        b.block()                                   # amorce des caches simulés
        res["chaud"] = measure(b, tr, 20, False)
        res["froid"] = measure(b, tr, 20, True)
        if opt:
            res["voix_arretees"] = sum(q >= 64 for q in b.quiet())
    else:
        for t in range(6):
            if scen == "envois":
                b.param(t, 20, 40)
                b.param(t, 21, 40)
            if scen == "dist":
                b.param(t, 19, 100)
        pat = be.Pattern(b)
        # 1re période (démarrage, 1er trig au bloc 2) non mesurée ; 2e en chaud ; 3e caches vidés
        t2 = pat.next + be.seqrig.STEP                  # heure du 2e trig
        while b.rig.now + b.rig.blk <= t2 - 4 * b.rig.blk:
            pat.tick()
            b.block()
        tr.on = True
        for _ in range(4):
            pat.tick()
            b.block()
        res["chaud"] = measure(b, tr, 188, False, pat.tick)
        res["froid"] = measure(b, tr, 188, True, pat.tick)
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scen", choices=["arret", "six", "envois", "dist", "apres"])
    ap.add_argument("image", choices=["officiel", "reference", "optimise"])
    ap.add_argument("--out", default=str(be.OUT))
    args = ap.parse_args()
    imgs = be.images(args.out)
    img = imgs[args.image]
    print(f"{args.image} MAIN OS {be.sha(img)} ; scénario {args.scen}", flush=True)
    t0 = time.time()
    res = run(args.scen, img, args.image == "optimise")
    s = {k: summary(v) for k, v in res.items() if k in ("chaud", "froid")}
    for k, v in s.items():
        trig = [i for i, r in enumerate(res[k]) if r["trig"]]
        print(f"  {k:5s} : {v['n']} blocs, moyenne {v['moyenne']:.1f} %, pic {v['pic']:.1f} %, mini {v['mini']:.1f} %, "
              f"voix {v['voix']:.1f} %, avant la fonction audio {v['debut']:.1f} %, {v['instr']} instructions/bloc ; "
              f"blocs de trig {trig[:4]}")
    if "voix_arretees" in res:
        print(f"  voix arrêtées pendant la mesure : {res['voix_arretees']} sur 6")
    out = dict(image=args.image, sha=be.sha(img), scen=args.scen, resume=s, blocs=res, secondes=round(time.time() - t0))
    (HERE / "logs").mkdir(exist_ok=True)
    (HERE / "logs" / f"charge_{args.scen}_{args.image}.json").write_text(json.dumps(out, indent=1))
    print(f"({time.time() - t0:.0f} s)")


if __name__ == "__main__":
    main()
