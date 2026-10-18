"""Profil par machine d'origine : piste 0 seule calculée (solo), état joue / muette / jamais déclenchée."""
import sys, json
import numpy as np
from prof import *

img = load_stock()
MN = ["KICK", "SNARE", "METAL", "PERC", "TONE", "CHORD"]
UPD = {0: 0x400aa08c, 1: 0x400ab3b0, 2: 0x400aa49c, 3: 0x400aa998, 4: 0x400aa7b8, 5: 0x400aae88}
REN = {0: 0x400aa3c4, 1: 0x400ab6e8, 2: 0x400aa712, 3: 0x400aacc2, 4: 0x400aa930, 5: 0x400ab24c}
out = {}
for m in range(6):
    res = {}
    for state in ("joue", "trig", "muette", "jamais"):
        e = E.Engine(img)
        e.machine_defaults(0, m)
        e.solo(0)
        if state == "jamais":
            nb, trig = 6, {}
        elif state == "trig":
            nb, trig = 2, {1: 1}
        elif state == "joue":
            nb, trig = 11, {1: 1}
        else:
            nb, trig = 3001, {1: 1}
        peak = 0
        for b in range(nb):
            if b == nb - 1:
                p = Prof(e.uc, e.emac, record=False)
            o = e.block(trig.get(b, 0))
            if b == nb - 1:
                peak = int(np.abs(o[0]).max())
        p.close()
        d = dict(total=p.n, update=p.incl[UPD[m]], render=p.incl[REN[m]], peak=peak,
                 fns={p.name(f): (p.incl[f], p.excl[f], p.calls[f]) for f in p.incl},
                 lines={r: len(s) for r, s in p.lines.items()}, wlines={r: len(s) for r, s in p.wlines.items()},
                 code_lines=len({a >> 4 for a in p.addr}),
                 mem={f"{k[0]}:{k[1]}": v for k, v in p.mem.items()})
        res[state] = d
        print(f"{MN[m]:5s} {state:6s} total {p.n:6d} update {d['update']:5d} render {d['render']:5d} "
              f"crête {peak:11d} code {d['code_lines']} lignes, données {d['lines']}", flush=True)
    out[MN[m]] = res
json.dump(out, open("machines.json", "w"), indent=1)
