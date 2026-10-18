"""Profil de 0x4005979e (fonction audio sans mixeur ni effets) avec le vrai séquenceur (seqrig) : 6 pistes KICK..CHORD
aux réglages par défaut ; états : joue (trig des 6 au pas 0, bloc 10 après), muette (bloc 2000), arrêt (jamais de trig)."""
import sys, json
from prof import *
import seqrig as S

img = load_stock()
UPD = [0x400aa08c, 0x400ab3b0, 0x400aa49c, 0x400aa998, 0x400aa7b8, 0x400aae88]
REN = [0x400aa3c4, 0x400ab6e8, 0x400aa712, 0x400aacc2, 0x400aa930, 0x400ab24c]


def setup():
    e = E.Engine(img)
    rig = S.Rig(e, 120)
    for t in range(6):
        c, s, w, ct, d = E.DEFAULTS[t]
        for k, v in dict(machine=t, pitch=64, color=c, shape=s, sweep=w, contour=ct, punch=0, gate=0,
                         finetune=64, decay=d).items():
            rig.param(t, E.SLOT[k], v * 256)
    return e, rig


def measure(e, rig, nb, trig_block=None):
    if trig_block is not None:
        for t in range(6):
            rig.set_step(t, 0, vel=100)
    p = None
    orig = e.call
    box = {}
    def call(fn, *a):
        if fn == 0x4005979e and box.get("on"):
            box["p"] = Prof(e.uc, e.emac, record=True)
            r = orig(fn, *a)
            box["p"].close()
            return r
        return orig(fn, *a)
    e.call = call
    for b in range(nb):
        if trig_block is not None and b == trig_block:
            for t in range(6):
                rig.schedule_step(t, 0, rig.now + rig.blk // 3)
        box["on"] = b == nb - 1
        info = rig.block()
    e.call = orig
    return box["p"], info


res = {}
for state, nb, tb in (("joue", 12, 1), ("muette", 2400, 1), ("arret", 12, None)):
    e, rig = setup()
    p, info = measure(e, rig, nb, tb)
    peak = [int(abs(info["out"][t]).max()) for t in range(6)]
    top = sorted(((p.incl[f], p.excl[f], p.name(f), p.calls[f]) for f in p.incl), reverse=True)
    vl = p.incl[0x400a7d4a]
    print(f"== {state} : 0x4005979e total {p.n}, boucle des voix {vl}, crêtes {peak}")
    for inc, exc, n, c in top[:40]:
        print(f"   {n:28s} incl {inc:6d} excl {exc:6d} appels {c}")
    print("   lignes données", {r: len(s) for r, s in p.lines.items()}, "écrites", {r: len(s) for r, s in p.wlines.items()},
          "code", len({a >> 4 for a in p.addr}))
    res[state] = dict(total=p.n, voice_loop=vl, peak=peak,
                      fns={p.name(f): (p.incl[f], p.excl[f], p.calls[f]) for f in p.incl},
                      lines={r: len(s) for r, s in p.lines.items()})
    # code par fonction (lignes) et données par fonction
    import pickle
    pickle.dump(dict(seq=p.seq, addr=dict(p.addr), fnlines={p.name(f): {r: sorted(s) for r, s in d.items()} for f, d in p.fnlines.items()}),
                open(f"seq_{state}.pkl", "wb"))
json.dump(res, open("seqprof.json", "w"), indent=1)
