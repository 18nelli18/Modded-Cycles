"""Suite de test_proto.py (arrêté par sa limite de temps après 10 cas de la partie 1), mêmes cas, mêmes graines :
    python3 test_proto2.py 1   # partie 1 : les cas 11 à 18 (PERC réglages 1, 2 ; TONE ; CHORD)
    python3 test_proto2.py 2   # partie 2 : coût, 6 voix DECAY 20, instructions comptées aux blocs relevés seulement
    python3 test_proto2.py 3   # partie 3 : motifs au hasard (graines 100, 101), 1 000 blocs
"""
import sys, random
import numpy as np
import test_proto as P
from test_proto import E, STOCK, IMG, T, check, rnd_kw, compare, FAIL
from unicorn import UC_HOOK_CODE


def play(img, setup, blocks, trigs, changes=None, solo=None, count_at=()):
    e = E.Engine(img)
    for t, kw in setup.items():
        e.set(t, **kw)
    if solo is not None:
        e.solo(solo)
    n = [0]
    out, cost = [], {}
    for b in range(blocks):
        if changes and b in changes:
            for t, kw in changes[b].items():
                e.set(t, **kw)
        h = None
        if b in count_at:
            n[0] = 0
            h = e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, u: n.__setitem__(0, n[0] + 1))
            e.uc.ctl_flush_tb()
        out.append(e.block(trigs.get(b, 0)))
        if h is not None:
            e.uc.hook_del(h)
            cost[b] = n[0]
        assert not e.unmapped, e.unmapped[:3]
    return np.stack(out), cost


part = int(sys.argv[1])
if part == 1:
    rr = random.Random(1)
    i = 0
    for m in range(6):
        for k in range(3):
            if not k:
                e0 = E.Engine(STOCK); e0.machine_defaults(0, m); kw = dict(e0.trk[0])
            else:
                kw = rnd_kw(rr, m)
            i += 1
            if i <= 10:
                continue
            retrig = 900
            ref, _ = play(STOCK, {0: kw}, 1100, {1: 1, retrig: 1}, solo=0)
            mod, _ = play(IMG, {0: kw}, 1100, {1: 1, retrig: 1}, solo=0)
            first, quiet, after = compare(ref, mod, 0, retrig)
            others = np.array_equal(ref[:, 1:], mod[:, 1:])
            check(quiet and others and after < 1e-3,
                  f"{list(E.MACH)[m]:5s} réglages {k} (DEC {kw['decay']:3d}, PUNCH {kw['punch']}) : identique "
                  f"jusqu'au bloc {first if first is not None else '—'} ; ensuite référence sous le seuil ; 2e trig : "
                  f"écart {after:.1e} de la crête ; autres pistes : {'identiques' if others else 'DIFFÉRENTES'}")
elif part == 2:
    setup = {t: dict(E.Engine(STOCK).trk[t]) for t in range(6)}
    for t in range(6):
        c, s, w, ct, d = E.DEFAULTS[t]
        setup[t].update(machine=t, color=c, shape=s, sweep=w, contour=ct, decay=20)
    AT = (0, 1, 2, 5, 50, 100, 200, 400, 600, 800, 1199)
    ref, cr = play(STOCK, setup, 1200, {1: 0x3f}, count_at=AT)
    mod, cm = play(IMG, setup, 1200, {1: 0x3f}, count_at=AT)
    same = [compare(ref, mod, t, None)[1] for t in range(6)]
    stop = [compare(ref, mod, t, None)[0] for t in range(6)]
    check(all(same), f"6 voix (KICK..CHORD, DECAY 20) : identiques jusqu'à leur arrêt (blocs {stop}), puis sous le seuil")
    for b in AT:
        print(f"     bloc {b:4d} : d'origine {cr[b]:6d}  prototype {cm[b]:6d}  ({100 * (cm[b] - cr[b]) / cr[b]:+.1f} %)",
              flush=True)
    check(cm[5] <= cr[5] and cm[1199] < cr[1199] / 10, "jouant : pas plus cher ; muettes : moins d'un dixième")
else:
    for seed in range(2):
        r = random.Random(100 + seed)
        setup = {t: rnd_kw(r, r.randrange(6)) for t in range(6)}
        trigs = {}
        for t in range(6):
            for b in sorted(r.sample(range(1, 1000), r.randint(2, 6))):
                trigs[b] = trigs.get(b, 0) | (1 << t)
        changes = {b: {t: dict(color=r.randint(0, 127))} for b in r.sample(range(1, 1000), 20) for t in [r.randrange(6)]}
        ref, _ = play(STOCK, setup, 1000, trigs, changes=changes)
        mod, _ = play(IMG, setup, 1000, trigs, changes=changes)
        d = np.abs(ref - mod)
        peak = max(1, int(np.abs(ref).max()))
        stopped = (mod == 0).all(axis=2) & (ref != mod).any(axis=2)
        ok_stop = bool((np.abs(ref)[stopped] < T).all())
        live = ~stopped
        dl = float(d[live].max()) / peak if live.any() else 0
        nst = int(stopped.sum())
        check(ok_stop and dl < 1e-3, f"graine {100 + seed} : machines {[setup[t]['machine'] for t in range(6)]} ; "
              f"{nst} blocs-pistes arrêtés sur 6 000, référence sous le seuil ; ailleurs écart max {dl:.1e} de la crête ; "
              f"blocs identiques à l'octet près : {int((d.max(axis=(1, 2)) == 0).sum())}/1000")
print("TOUT OK" if not FAIL else f"{len(FAIL)} ÉCHEC(S)")
