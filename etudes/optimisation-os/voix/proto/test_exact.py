"""Preuve des prototypes exacts : sorties ET états des 6 voix identiques à l'octet près à l'OS d'origine, bloc par
bloc, réglages / trigs / changements au hasard ; coût en instructions.
    python3 test_exact.py mix2 punch"""
import sys, random
import numpy as np
sys.path.insert(0, "/home/user/Modded-Cycles/tools/emu")
import mcengine as E
from unicorn import UC_HOOK_CODE
import protos

names = sys.argv[1:] or ["mix2", "punch"]
IMG, TWS, EXTRA = protos.image(*names)
STOCK = protos.SEC3.read_bytes()
FAIL = []


def run(img, extra, setup, blocks, trigs, changes):
    e = E.Engine(img, extra_code=extra)
    for t, kw in setup.items():
        e.set(t, **kw)
    n = [0]
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, u: n.__setitem__(0, n[0] + 1))
    outs, states, cost = [], [], []
    for b in range(blocks):
        for t, kw in changes.get(b, {}).items():
            e.set(t, **kw)
        n[0] = 0
        outs.append(e.block(trigs.get(b, 0)))
        states.append(bytes(e.uc.mem_read(E.VOICE0, 6 * E.VSTRIDE)))
        cost.append(n[0])
        assert not e.unmapped
    return np.stack(outs), states, cost


r = random.Random(int(sys.argv[0].__len__()) + len(names))
tr = tm = 0
NB = 250
for trial in range(8):
    setup = {t: dict(machine=r.randrange(6) if trial >= 2 else t, note=r.randint(30, 90), pitch=r.randint(40, 88),
                     color=r.randint(0, 127), shape=r.randint(0, 127), sweep=r.randint(0, 127),
                     contour=r.randint(0, 127), punch=r.randint(0, 1) if trial else 0, gate=r.randint(0, 1),
                     finetune=r.randint(0, 127), decay=r.randint(1, 127)) for t in range(6)}
    trigs = {1: 0x3f}
    for b in r.sample(range(2, NB), 25):
        trigs[b] = r.randrange(1, 64)
    changes = {}
    for b in r.sample(range(2, NB), 50):
        changes[b] = {r.randrange(6): {r.choice(["color", "shape", "sweep", "contour", "decay", "pitch", "punch"]):
                                       r.randint(0, 127)}}
        for t, kw in changes[b].items():
            if "punch" in kw:
                kw["punch"] &= 1
    ro, rs, rc = run(STOCK, [], setup, NB, trigs, changes)
    mo, ms, mc = run(IMG, EXTRA, setup, NB, trigs, changes)
    same = np.array_equal(ro, mo) and rs == ms
    tr += sum(rc); tm += sum(mc)
    msg = (f"essai {trial} : machines {[setup[t]['machine'] for t in range(6)]}, PUNCH "
           f"{[setup[t]['punch'] for t in range(6)]} : sorties et états identiques sur {NB} blocs ; instructions "
           f"{sum(rc) // NB} -> {sum(mc) // NB} par bloc ({100 * (sum(mc) - sum(rc)) / sum(rc):+.1f} %)")
    print(("  ok    " if same and np.abs(ro).max() > 0 else "  ECHEC ") + msg, flush=True)
    if not same:
        FAIL.append(trial)
print(f"{'+'.join(names)} : moyenne {tr // (8 * NB)} -> {tm // (8 * NB)} instructions par bloc ({100 * (tm - tr) / tr:+.1f} %)")
print("TOUT OK" if not FAIL else f"{len(FAIL)} ÉCHEC(S)")
