"""Les prototypes ensemble contre l'OS d'origine, sur le banc : sortie identique, et gain par phase.

  p1 : Volume + Dist sans saturateur quand le wet est nul   (proto/vd_skip.S, détour 0x40057062)
  p2 : sommeil exact du delay et de la reverb                (proto/fx_lib.S, fx_dly.S, fx_rev.S)
  p3 : envois delay et reverb sautés quand gains et pentes sont nuls (proto/send_skip.S)
Phases (P blocs chacune ; 6 pistes, trig tous les 40 blocs ; les réglages glissent comme des potards) :
  1 réglages par défaut (envois 0, VOL+DIST 60)
  2 envoi delay 40 sur la piste 2, VOL+DIST 90 sur la piste 0
  3 envoi reverb 50 sur les pistes 1 et 4
  4 tout revient : envois 0, VOL+DIST 60
Compare à chaque bloc anneau, USB, voix, SRAM entière, EMAC ; lignes en DDR tous les 25 blocs. Compte les
instructions de tout l'étage de sortie (0x40056400..0x40058480 et les détours).

    python3 test_combo.py [P] [p1,p2,p3]
"""
import hashlib
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, "proto")
import numpy as np                     # noqa: E402
from unicorn import UC_HOOK_CODE       # noqa: E402

import asm                             # noqa: E402
import banc                            # noqa: E402

P = int(sys.argv[1]) if len(sys.argv) > 1 else 100
WHICH = (sys.argv[2] if len(sys.argv) > 2 else "p1,p2,p3").split(",")
BASE = 0x40000400
M_VD, M_LIB, M_DLY, M_REV, M_SND = 0x40152d38, 0x401592bc, 0x40185f48, 0x4018d918, 0x4015943c
STOCK = {0x40057062: "286f0038206f0040", 0x40057516: "2f03260dea83", 0x40057ac8: "2a7c8000a9b0",
         0x40057dc6: "207c8000ad20", 0x40056716: "4fefffe048d70cfc", 0x40056698: "4fefffd848d73cfc"}


def build(which):
    img = open(banc.SEC3, "rb").read()
    patch, extra, marks = [], [], {}
    if "p1" in which:
        c, s = asm.assemble("proto/vd_skip.S", M_VD)
        patch += [(M_VD, c), (0x40057062, asm.jmp(0x40057062, s["vd_check"], 8))]
        extra.append((M_VD, len(c)))
        marks["p1 saturateur sauté (paires)"] = s["vd_hit"]
    if "p2" in which:
        c0, s0 = asm.assemble("proto/fx_lib.S", M_LIB)
        defs = [("ZSCAN", hex(s0["zscan"])), ("ZFILL", hex(s0["zfill"]))]
        c1, s1 = asm.assemble("proto/fx_dly.S", M_DLY, defs)
        c2, s2 = asm.assemble("proto/fx_rev.S", M_REV, defs)
        patch += [(M_LIB, c0), (M_DLY, c1), (M_REV, c2),
                  (0x40057516, asm.jmp(0x40057516, s1["dz_check"], 6)),
                  (0x40057ac8, asm.jmp(0x40057ac8, s2["rz_check"], 6)),
                  (0x40057dc6, asm.jmp(0x40057dc6, s2["rz_mod"], 6))]
        extra += [(M_LIB, len(c0)), (M_DLY, len(c1)), (M_REV, len(c2))]
        marks["p2 delay endormi"] = s1["dz_sleep"]
        marks["p2 reverb endormie"] = s2["rz_slept"]
    if "p3" in which:
        c, s = asm.assemble("proto/send_skip.S", M_SND)
        patch += [(M_SND, c), (0x40056716, asm.jmp(0x40056716, s["s6_check"], 8)),
                  (0x40056698, asm.jmp(0x40056698, s["s7_check"], 8))]
        extra.append((M_SND, len(c)))
        marks["p3 envoi sauté"] = s["zero_out"]
    for va, data in patch:
        if va in STOCK:
            assert img[va - BASE:va - BASE + len(STOCK[va]) // 2].hex() == STOCK[va], hex(va)
    return patch, extra, marks


class Count:
    def __init__(self, b, marks):
        self.n = 0
        self.hits = {k: 0 for k in marks}
        uc = b.uc
        for lo, hi in ((0x40056400, 0x40058480), (M_VD, M_VD + 192), (M_LIB, M_LIB + 192), (M_DLY, M_DLY + 272),
                       (M_REV, M_REV + 328), (M_SND, M_SND + 192)):
            uc.hook_add(UC_HOOK_CODE, self._hk, begin=lo, end=hi - 1)
        for k, a in marks.items():
            uc.hook_add(UC_HOOK_CODE, lambda *x, k=k: self._mk(k), begin=a, end=a)

    def _hk(self, uc, a, s, u):
        self.n += 1

    def _mk(self, k):
        self.hits[k] += 1


# p1 laisse dans 0x8000bc98..0x8000bd98 (sortie du saturateur, lue seulement par le fondu dry/wet du même bloc,
# multipliée par wet = 0) ce qui y était : seule différence d'état admise, et seulement avec p1.
MASK = (0x8000bc98, 0x8000bd98) if "p1" in WHICH else None


def snap(b, lines):
    uc = b.uc
    em = b.e.emac
    sram = bytearray(uc.mem_read(0x80000000, 0x10000))
    if MASK:
        sram[MASK[0] - 0x80000000:MASK[1] - 0x80000000] = bytes(MASK[1] - MASK[0])
    s = [bytes(sram), repr((list(em.acc), em.macsr)).encode()]
    if lines:
        h = hashlib.sha256()
        for a, n in ((0x4a400000, 0x400000), (0x4a340000, 0x90000), (0x4a3d0000, 0x8000)):
            h.update(bytes(uc.mem_read(a, n)))
        s.append(h.digest())
    return s


def main():
    patch, extra, marks = build(WHICH)
    A = banc.Banc()
    B = banc.Banc(patch=patch, extra_code=extra)
    cA, cB = Count(A, {}), Count(B, marks)
    for b in (A, B):
        for t in range(6):
            b.rig.set_step(t, 0, vel=110, length=14)
    first = None
    rows = []
    for k in range(4 * P):
        ph = k // P
        if k % P == 0:
            for b in (A, B):
                if ph == 1:
                    b.target(2, 20, 40)
                    b.target(0, 19, 90)
                elif ph == 2:
                    b.target(1, 21, 50)
                    b.target(4, 21, 50)
                elif ph == 3:
                    for t in range(6):
                        b.target(t, 20, 0)
                        b.target(t, 21, 0)
                    b.target(0, 19, 60)
            rows.append((cA.n, cB.n, dict(cB.hits)))
        if k % 40 == 2:
            for b in (A, B):
                for t in range(6):
                    b.rig.schedule_step(t, 0, b.rig.now + b.rig.blk)
        iA, iB = A.block(), B.block()
        lines = k % 25 == 24
        same = (np.array_equal(iA["ring"], iB["ring"]) and np.array_equal(iA["usb"], iB["usb"])
                and np.array_equal(iA["out"], iB["out"]) and snap(A, lines) == snap(B, lines))
        if not same and first is None:
            first = k
            sa, sb = snap(A, False)[0], snap(B, False)[0]
            diff = [0x80000000 + i for i in range(0, 0x10000, 4) if sa[i:i + 4] != sb[i:i + 4]]
            print("  premier écart au bloc", k, ": anneau identique", np.array_equal(iA["ring"], iB["ring"]),
                  "; SRAM", [hex(x) for x in diff[:20]], len(diff), flush=True)
    rows.append((cA.n, cB.n, dict(cB.hits)))
    print(("  ok    " if first is None else "  ECHEC ") + f"{'+'.join(WHICH)} : identique sur {4 * P} blocs "
          "(anneau, USB, voix, SRAM entière" + (" sauf 0x8000bc98..bd98" if MASK else "") + " et EMAC à chaque bloc ; lignes en DDR tous les 25 blocs)")
    names = ["défaut (envois 0, VOL+DIST 60)", "delay sur piste 2, VOL+DIST 90 piste 0", "+ reverb pistes 1 et 4",
             "tout revient à 0 / 60"]
    for i in range(4):
        (a0, b0, h0), (a1, b1, h1) = rows[i], rows[i + 1]
        s, m = (a1 - a0) / P, (b1 - b0) / P
        hits = ", ".join(f"{k} {h1[k] - h0[k]}" for k in h1)
        print(f"  phase {i + 1} ({names[i]}) : étage de sortie {s:.0f} -> {m:.0f} instr/bloc, gain {s - m:+.0f} = "
              f"{100 * 1.54 * (s - m) / 166667:+.2f} % d'un bloc ; sauts sur {P} blocs : {hits}")
    sys.exit(0 if first is None else 1)


if __name__ == "__main__":
    main()
