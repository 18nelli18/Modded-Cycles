"""Preuve du prototype idle-stock (arrêt des voix muettes sur l'OS d'origine), boucle des voix réelle (mcengine).

  1. son, machine par machine, réglages au hasard : identique tant que la voix est calculée ; puis la référence
     reste sous le seuil ; 2e trig : écart rapporté à la crête ;
  2. coût : instructions par bloc (6 voix qui jouent, 6 voix muettes, voix jamais déclenchées) ;
  3. 6 pistes mêlées, trigs au hasard (motif), 1 500 blocs : écarts.
"""
import sys, random, struct
import numpy as np
sys.path.insert(0, "/home/user/Modded-Cycles/tools/emu"); sys.path.insert(0, "/home/user/Modded-Cycles/tools")
sys.path.insert(0, "/tmp/claude-0/-home-user-Modded-Cycles/4cafd55d-d242-5df3-ad6a-3e64ee54ea56/scratchpad/optim/voix/proto")
import mcengine as E
from unicorn import UC_HOOK_CODE
import build_proto as B

STOCK = B.SEC3.read_bytes()
IMG, TW, SYM, LN = B.image()
T = 4096                        # seuil sur la piste divisée par 2 (= 2^13 en sortie de render)
FAIL = []


def check(ok, msg):
    print(("  ok    " if ok else "  ECHEC ") + msg, flush=True)
    if not ok:
        FAIL.append(msg)


def play(img, setup, blocks, trigs, count=False, changes=None, solo=None):
    e = E.Engine(img)
    for t, kw in setup.items():
        e.set(t, **kw)
    if solo is not None:
        e.solo(solo)
    n = [0]
    if count:
        e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, u: n.__setitem__(0, n[0] + 1))
    out, cost = [], []
    for b in range(blocks):
        if changes and b in changes:
            for t, kw in changes[b].items():
                e.set(t, **kw)
        n[0] = 0
        out.append(e.block(trigs.get(b, 0)))
        cost.append(n[0])
        assert not e.unmapped, e.unmapped[:3]
    return np.stack(out), cost          # (blocs, 6, 32)


def rnd_kw(r, m):
    return dict(machine=m, note=r.randint(36, 84), pitch=r.randint(40, 88), color=r.randint(0, 127),
                shape=r.randint(0, 127), sweep=r.randint(0, 127), contour=r.randint(0, 127),
                punch=r.randint(0, 1), gate=0, finetune=r.randint(0, 127), decay=r.randint(5, 40))


def compare(ref, mod, track, retrig):
    r, x = ref[:, track, :], mod[:, track, :]
    diff = np.nonzero(np.any(r != x, axis=1))[0]
    first = int(diff[0]) if len(diff) else None
    end = retrig if retrig else len(r)
    quiet = first is None or first >= end or (np.abs(r[first:end]).max() < T and not x[first:end].any())
    after = 0.0
    if retrig:
        after = float(np.abs(r[retrig:] - x[retrig:]).max()) / max(1, float(np.abs(r[retrig:]).max()))
    return first, quiet, after


def main():
    print(f"prototype : {LN} o de code ; écritures : " + ", ".join(f"{w['off'] + 0x40000400:#x}" for w in TW["writes"]))
    print("1. son, machine par machine (piste 0 seule calculée)")
    rr = random.Random(1)
    worst = 0.0
    for m in range(6):
        for k in range(3):
            kw = rnd_kw(rr, m) if k else dict(E.Engine.__init__.__defaults__ and {}, machine=m)
            if not k:
                e0 = E.Engine(STOCK); e0.machine_defaults(0, m); kw = dict(e0.trk[0])
            retrig = 900
            ref, _ = play(STOCK, {0: kw}, 1100, {1: 1, retrig: 1}, solo=0)
            mod, _ = play(IMG, {0: kw}, 1100, {1: 1, retrig: 1}, solo=0)
            first, quiet, after = compare(ref, mod, 0, retrig)
            others = np.array_equal(ref[:, 1:], mod[:, 1:])
            worst = max(worst, after)
            check(quiet and others and after < 1e-3,
                  f"{list(E.MACH)[m]:5s} réglages {k} (DEC {kw['decay']:3d}, PUNCH {kw['punch']}) : identique "
                  f"jusqu'au bloc {first if first is not None else '—'} ; ensuite référence sous le seuil ; 2e trig : "
                  f"écart {after:.1e} de la crête ; autres pistes : {'identiques' if others else 'DIFFÉRENTES'}")
    print("2. coût (instructions par bloc de la boucle des voix)")
    setup = {t: dict(E.Engine(STOCK).trk[t]) for t in range(6)}
    for t in range(6):
        c, s, w, ct, d = E.DEFAULTS[t]
        setup[t].update(machine=t, color=c, shape=s, sweep=w, contour=ct, decay=20)
    ref, cr = play(STOCK, setup, 1200, {1: 0x3f}, count=True)
    mod, cm = play(IMG, setup, 1200, {1: 0x3f}, count=True)
    same = [compare(ref, mod, t, None)[1] for t in range(6)]
    stop = [compare(ref, mod, t, None)[0] for t in range(6)]
    check(all(same), f"6 voix (KICK..CHORD, DECAY 20) : identiques jusqu'à leur arrêt (blocs {stop}), puis sous le seuil")
    for b in (0, 1, 2, 5, 50, 200, 400, 800, 1199):
        print(f"     bloc {b:4d} : d'origine {cr[b]:6d}  prototype {cm[b]:6d}  ({100 * (cm[b] - cr[b]) / cr[b]:+.1f} %)")
    check(cm[5] <= cr[5] and cm[1199] < cr[1199] / 10, "jouant : pas plus cher ; muettes : moins d'un dixième")
    print("3. motif : 6 pistes mêlées, réglages et trigs au hasard, 1 500 blocs")
    for seed in range(3):
        r = random.Random(100 + seed)
        setup = {t: rnd_kw(r, r.randrange(6)) for t in range(6)}
        trigs = {}
        for t in range(6):
            for b in sorted(r.sample(range(1, 1500), r.randint(2, 8))):
                trigs[b] = trigs.get(b, 0) | (1 << t)
        changes = {b: {t: dict(color=r.randint(0, 127))} for b in r.sample(range(1, 1500), 20) for t in [r.randrange(6)]}
        ref, cr = play(STOCK, setup, 1500, trigs, count=True, changes=changes)
        mod, cm = play(IMG, setup, 1500, trigs, count=True, changes=changes)
        d = np.abs(ref - mod)
        peak = max(1, int(np.abs(ref).max()))
        # écart hors des zones arrêtées : une voix arrêtée sort 0, la référence moins que le seuil
        stopped = (mod == 0).all(axis=2) & (ref != mod).any(axis=2)
        ok_stop = bool((np.abs(ref)[stopped] < T).all())
        live = ~stopped
        dl = float(d[live].max()) / peak if live.any() else 0
        check(ok_stop and dl < 1e-3, f"graine {seed} : machines {[setup[t]['machine'] for t in range(6)]} ; "
              f"blocs arrêtés : référence sous le seuil ; ailleurs écart max {dl:.1e} de la crête ; "
              f"instructions {sum(cr)} -> {sum(cm)} ({100 * (sum(cm) - sum(cr)) / sum(cr):+.1f} %)")
    print("\nTOUT OK" if not FAIL else f"\n{len(FAIL)} ÉCHEC(S)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
