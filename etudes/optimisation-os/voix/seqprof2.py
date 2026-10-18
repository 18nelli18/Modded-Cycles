"""Fonction audio 0x4005979e entière (seqrig, mixeur et effets sautés), OS d'origine contre prototypes
(arrêt des voix muettes + mix2 + PUNCH), 6 pistes KICK..CHORD, états joue / muette / arrêt ; instructions et cache."""
import sys, json, pickle
sys.path.insert(0, "proto")
from prof import *
import seqrig as S
import protos

STOCK = load_stock()
IMG, TWS, EXTRA = protos.image("idle", "mix2", "punch")
CPI, LINE, BLOCK = 1.54, 15, 166667


def setup(img, extra):
    e = E.Engine(img, extra_code=extra)
    rig = S.Rig(e, 120)
    for t in range(6):
        c, s, w, ct, d = E.DEFAULTS[t]
        for k, v in dict(machine=t, pitch=64, color=c, shape=s, sweep=w, contour=ct, punch=0, gate=0,
                         finetune=64, decay=d).items():
            rig.param(t, E.SLOT[k], v * 256)
    return e, rig


def measure(e, rig, nb, trig_block):
    if trig_block is not None:
        for t in range(6):
            rig.set_step(t, 0, vel=100)
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
    outs = []
    for b in range(nb):
        if trig_block is not None and b == trig_block:
            for t in range(6):
                rig.schedule_step(t, 0, rig.now + rig.blk // 3)
        box["on"] = b == nb - 1
        info = rig.block()
        outs.append(np.array(info["out"]).copy())
    e.call = orig
    return box["p"], outs


res = {}
for state, nb, tb in (("joue", 12, 1), ("muette", 2400, 1), ("arret", 80, None)):
    for name, img, extra in (("origine", STOCK, []), ("proto", IMG, EXTRA)):
        e, rig = setup(img, extra)
        p, outs = measure(e, rig, nb, tb)
        seq = p.seq
        (cold,), _, _ = simulate([seq])
        r2, _, _ = simulate([seq, seq])
        warm = r2[1]
        fc = lambda r: (r[0] + r[1] + r[2]) * LINE
        n = p.n
        vl = p.incl[0x400a7d4a]
        res.setdefault(state, {})[name] = dict(total=n, voice_loop=vl, cold=cold, warm=warm,
                                               code_lines=len({a >> 4 for a in p.addr}),
                                               outs=[o.tolist() for o in outs[-3:]])
        print(f"{state:6s} {name:7s} 0x4005979e {n:6d} instr (boucle des voix {vl:6d}) ; lignes de code "
              f"{len({a >> 4 for a in p.addr})} ; froid {100 * (n * CPI + fc(cold)) / BLOCK:5.1f} %, chaud "
              f"{100 * (n * CPI + fc(warm)) / BLOCK:5.1f} % d'un bloc (modèle 1,54 CPI + 15 cycles/ligne)", flush=True)
    o1 = np.array(res[state]["origine"]["outs"]); o2 = np.array(res[state]["proto"]["outs"])
    print(f"       sorties des 3 derniers blocs : identiques {np.array_equal(o1, o2)}, crête origine "
          f"{np.abs(o1).max():.0f}, écart max {np.abs(o1 - o2).max():.0f}", flush=True)
json.dump(res, open("seqprof2.json", "w"))
