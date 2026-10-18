"""Mesures par poste de l'étage de sortie, sur le banc, pour quelques scénarios.

    python3 mesure.py [scénario ...]      (silence, une, six, six_fx, queue_fx, mort_fx)
Écrit mesures_<scénario>.json et imprime un tableau.
"""
import json
import sys
import time
from collections import defaultdict

sys.dont_write_bytecode = True
import numpy as np        # noqa: E402

import banc               # noqa: E402
import trace              # noqa: E402

SCEN = {
    # nom : (envois delay, envois reverb, pistes déclenchées, bloc de mesure après le trig)
    "silence": dict(sends=None, tracks=(), wait=40),
    "une": dict(sends=None, tracks=(0,), wait=6),
    "six": dict(sends=None, tracks=range(6), wait=6),
    "six_fx": dict(sends=(40, 40), tracks=range(6), wait=6),
    "queue_fx": dict(sends=(40, 40), tracks=range(6), wait=600),      # 0,4 s après : voix éteintes, queues vivantes
}


def run(name, n_meas=3, flush=False, banc_kw=None):
    sc = SCEN[name]
    b = banc.Banc(**(banc_kw or {}))
    rig = b.rig
    if sc["sends"]:
        for t in range(6):
            b.param(t, 20, sc["sends"][0])
            b.param(t, 21, sc["sends"][1])
    for t in sc["tracks"]:
        rig.set_step(t, 0, vel=120, length=14)
    tr = trace.Tracer(b)
    for k in range(4):
        b.block()
    if sc["tracks"]:
        for t in sc["tracks"]:
            rig.schedule_step(t, 0, rig.now + rig.blk)
    for k in range(sc["wait"] - 1):
        b.block()
    tr.on = True
    b.block()                       # bloc d'amorce des caches simulés (non compté)
    tr.reset()
    outs = []
    for k in range(n_meas):
        if flush:
            tr.ic.flush()
            tr.dc.flush()
        info = b.block()
        outs.append(info)
    tr.on = False
    rows = tr.per_func()
    for d in rows.values():
        for k in list(d):
            d[k] = d[k] / n_meas
    ring = np.array([o["ring"] for o in outs])
    res = dict(scen=name, flush=flush, rows=rows, ring_peak=int(np.abs(ring).max()),
               vox_peak=int(np.abs(np.array([o["out"] for o in outs])).max()),
               dma=[(c, hex(s), hex(d), n) for c, s, d, n in b.dma.log[-37:]],
               csr_reads=b.dma.csr_reads)
    return res, tr


def table(res):
    rows = res["rows"]
    post = defaultdict(lambda: defaultdict(float))
    for f, d in rows.items():
        p = trace.POSTE.get(f)
        if p is None:
            continue
        for k, v in d.items():
            post[p][k] += v
    print(f"\n== {res['scen']}{' (caches vidés)' if res['flush'] else ''} : crête voix {res['vox_peak']}, "
          f"crête sortie {res['ring_peak']}")
    hdr = "poste                     instr   I-déf  D-déf  D-rec  SRAM l/é lignes  SDRAM l/é lignes  noncache é  % bloc"
    print(hdr)
    tot = defaultdict(float)
    for p in sorted(post):
        d = post[p]
        print(f"{p:24s} {d['ins']:7.0f} {d['imiss']:6.0f} {d['dmiss']:6.0f} {d['dwb']:6.0f}   "
              f"{d['sram_r_lines']:5.0f}/{d['sram_w_lines']:<5.0f}      {d['sdram_r_lines']:5.0f}/{d['sdram_w_lines']:<5.0f}"
              f"   {d['noncache_w_acc']:5.0f}     {d['pct']:5.2f}")
        for k, v in d.items():
            tot[k] += v
    print(f"{'TOTAL sortie':24s} {tot['ins']:7.0f} {tot['imiss']:6.0f} {tot['dmiss']:6.0f} {tot['dwb']:6.0f}   "
          f"{tot['sram_r_lines']:5.0f}/{tot['sram_w_lines']:<5.0f}      {tot['sdram_r_lines']:5.0f}/{tot['sdram_w_lines']:<5.0f}"
          f"   {tot['noncache_w_acc']:5.0f}     {tot['pct']:5.2f}")
    allc = sum(d["cycles"] for d in rows.values())
    print(f"bloc émulé entier (isr + fonction audio) : {sum(d['ins'] for d in rows.values()):.0f} instr, "
          f"{100 * allc / trace.CPB:.1f} % du bloc au modèle")
    others = sorted(((d["pct"], f) for f, d in rows.items() if f not in trace.POSTE), reverse=True)
    print("hors étage de sortie :", ", ".join(f"{f} {p:.1f}" for p, f in others[:8]))


if __name__ == "__main__":
    names = sys.argv[1:] or list(SCEN)
    for n in names:
        for flush in (False, True):
            t0 = time.time()
            res, tr = run(n, flush=flush)
            table(res)
            print(f"({time.time() - t0:.0f} s)")
            json.dump(res, open(f"mesures_{n}{'_froid' if flush else ''}.json", "w"), indent=1, default=str)
            if not flush:
                json.dump({hex(a): c for a, c in sorted(tr.pc_count.items())},
                          open(f"pc_{n}.json", "w"))
