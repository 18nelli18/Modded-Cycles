"""Preuve du prototype 1 (proto/vd_skip.S) : Volume + Dist sans saturateur quand le wet est nul.

OS d'origine contre OS modifié, même banc (banc.py), 6 pistes qui jouent, envois delay/reverb, et VOL+DIST qui
passe le seuil dans les deux sens en glissant (lissage de l'OS) :
  blocs   0..49 : les 6 pistes à 60 (défaut)        -> les 3 paires sautent le saturateur
  blocs  50..99 : piste 1 -> 70, piste 4 -> 100, piste 3 -> 61 (le plus petit wet non nul)
  blocs 100..159: tout revient à 60 (glisse)        -> les paires sautent de nouveau dès que wet = 0 aux deux bouts
Vérifie, bloc par bloc : pistes après Volume + Dist (0x80001858), anneau du codec, mix USB ; compte les
instructions de 0x40056f58 (+ le détour).

    python3 test_proto1.py
"""
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, "proto")
import numpy as np                     # noqa: E402
from unicorn import UC_HOOK_CODE       # noqa: E402

import asm                             # noqa: E402
import banc                            # noqa: E402

STUB = 0x40152d38                      # masque 48x22 libre (REGISTRY.md §1) ; ici seulement pour l'émulation
HOOK = 0x40057062


def patch():
    code, sym = asm.assemble("proto/vd_skip.S", STUB)
    return [(HOOK, asm.jmp(HOOK, sym["vd_check"], 8)), (STUB, code)]


def run(b, n=160):
    rig = b.rig
    cnt = [0]
    def hk(uc, a, s, u):
        cnt[0] += 1
    b.uc.hook_add(UC_HOOK_CODE, hk, begin=0x40056f58, end=0x4005725e)
    b.uc.hook_add(UC_HOOK_CODE, hk, begin=STUB, end=STUB + 0x100)
    for t in range(6):
        b.param(t, 20, 30)
        b.param(t, 21, 30)
        rig.set_step(t, 0, vel=110, length=14)
    out, ins = [], []
    for k in range(n):
        if k % 40 == 2:
            for t in range(6):
                rig.schedule_step(t, 0, rig.now + rig.blk)
        if k == 50:
            b.target(1, 19, 70); b.target(4, 19, 100); b.target(3, 19, 61)
        if k == 100:
            for t in (1, 3, 4):
                b.target(t, 19, 60)
        c0 = cnt[0]
        info = b.block()
        ins.append(cnt[0] - c0)
        out.append((info["ring"].copy(), info["usb"].copy(), b.r32s(0x80001858, 6 * 32).reshape(6, 32)))
    return out, ins


def main():
    fails = 0
    ref, ins0 = run(banc.Banc())
    new, ins1 = run(banc.Banc(patch=patch()))
    first = None
    for k, (a, c) in enumerate(zip(ref, new)):
        same = all(np.array_equal(x, y) for x, y in zip(a, c))
        if not same and first is None:
            first = k
    ok = first is None
    print(("  ok    " if ok else "  ECHEC ") + f"sortie identique sur {len(ref)} blocs (anneau, USB, 6 pistes)"
          + ("" if ok else f" : premier écart au bloc {first}"))
    fails += not ok
    peak = max(int(np.abs(a[0]).max()) for a in ref)
    print(f"  (crête de l'anneau {peak}, crête des pistes {max(int(np.abs(a[2]).max()) for a in ref)})")
    for lo, hi, what in ((10, 50, "tout à 60"), (60, 100, "pistes 1, 3, 4 au-dessus de 60"),
                         (130, 160, "retour à 60")):
        a, b_ = np.mean(ins0[lo:hi]), np.mean(ins1[lo:hi])
        print(f"  blocs {lo}..{hi - 1} ({what}) : Volume + Dist {a:.0f} -> {b_:.0f} instructions par bloc "
              f"({a - b_:+.0f}, soit {100 * 1.54 * (a - b_) / 166667:.2f} % d'un bloc au modèle)")
    trans = [k for k in range(1, len(ins1)) if ins1[k] != ins1[k - 1]]
    print("  blocs où le coût change (entrées/sorties du saut) :", trans[:20])
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
