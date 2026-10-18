"""Preuve du prototype 2 (proto/fx_lib.S, fx_dly.S, fx_rev.S) : sommeil exact du delay et de la reverb.

OS d'origine contre OS modifié, côte à côte sur le même banc (banc.py), bloc par bloc. 6 pistes qui jouent
(trig tous les 40 blocs), puis on tourne les envois comme des potards (cibles, le lissage de l'OS glisse) :
  phase 1 : envois à 0                         -> delay et reverb dorment
  phase 2 : envoi reverb 40 sur les 6 pistes    -> la reverb se réveille, le delay dort
  phase 3 : envoi delay 40 en plus              -> les deux travaillent
  phase 4 : tous les envois à 0                 -> les restes (notes du rapport §3) les gardent éveillés
  phase 5 : Delay Time 127 puis 5, Fdbk 0, Size 127 (paramètres des effets qui glissent pendant les restes)
Compare à chaque bloc : anneau du codec, mix USB, toute la SRAM (64 Ko), accumulateurs et MACSR de l'EMAC ;
tous les 25 blocs : la ligne du delay (4 Mo) et les 17 lignes de la reverb en DDR (empreinte SHA-256).
Compte les instructions du delay et de la reverb (détours compris) par phase.

    python3 test_proto2.py [blocs_par_phase]
"""
import hashlib
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, "proto")
import numpy as np                     # noqa: E402
from unicorn import UC_HOOK_CODE       # noqa: E402

import asm                             # noqa: E402
import banc                            # noqa: E402

L, D, R = 0x401592bc, 0x40185f48, 0x4018d918      # masques libres 48x22, 34x34, 41x41 (REGISTRY.md §1)
P = int(sys.argv[1]) if len(sys.argv) > 1 else 120
STOCK = {0x40057516: "2f03260dea83", 0x40057ac8: "2a7c8000a9b0", 0x40057dc6: "207c8000ad20"}


def build():
    c0, s0 = asm.assemble("proto/fx_lib.S", L)
    defs = [("ZSCAN", hex(s0["zscan"])), ("ZFILL", hex(s0["zfill"]))]
    c1, s1 = asm.assemble("proto/fx_dly.S", D, defs)
    c2, s2 = asm.assemble("proto/fx_rev.S", R, defs)
    assert len(c0) <= 192 and len(c1) <= 272 and len(c2) <= 328
    img = open(banc.SEC3, "rb").read()
    for va, old in STOCK.items():
        assert img[va - 0x40000400:va - 0x40000400 + 6].hex() == old, hex(va)
    patch = [(L, c0), (D, c1), (R, c2),
             (0x40057516, asm.jmp(0x40057516, s1["dz_check"], 6)),
             (0x40057ac8, asm.jmp(0x40057ac8, s2["rz_check"], 6)),
             (0x40057dc6, asm.jmp(0x40057dc6, s2["rz_mod"], 6))]
    extra = [(L, len(c0)), (D, len(c1)), (R, len(c2))]
    return patch, extra, (s1["dz_sleep"], s2["rz_slept"])


class Count:
    def __init__(self, b, stubs):
        self.n = {"d": 0, "r": 0}
        self.cur = "d"
        self.sleep = {"d": 0, "r": 0}
        uc = b.uc
        uc.hook_add(UC_HOOK_CODE, lambda *a: self._set("d"), begin=0x40057488, end=0x40057488)
        uc.hook_add(UC_HOOK_CODE, lambda *a: self._set("r"), begin=0x400579c4, end=0x400579c4)
        for lo, hi in ((0x40057488, 0x4005770e), (0x400579c4, 0x40057fa8), (L, L + 192), (D, D + 272), (R, R + 328)):
            uc.hook_add(UC_HOOK_CODE, self._hk, begin=lo, end=hi - 1)
        if stubs:
            uc.hook_add(UC_HOOK_CODE, lambda *a: self._sl("d"), begin=stubs[0], end=stubs[0])
            uc.hook_add(UC_HOOK_CODE, lambda *a: self._sl("r"), begin=stubs[1], end=stubs[1])
        self.a3dc = []
        uc.hook_add(UC_HOOK_CODE, lambda uc_, *a: self.a3dc.append(int(b.r32s(0x8000a3dc, 1)[0])),
                    begin=0x40057ac8, end=0x40057ac8)
        uc.hook_add(UC_HOOK_CODE, lambda uc_, *a: self.a3dc.append(int(b.r32s(0x8000a3dc, 1)[0])),
                    begin=0x40057dcc, end=0x40057dcc)
        self.b = b

    def _set(self, w):
        self.cur = w

    def _hk(self, uc, a, s, u):
        self.n[self.cur] += 1

    def _sl(self, w):
        self.sleep[w] += 1


def snap(b, lines):
    uc = b.uc
    em = b.e.emac
    s = [bytes(uc.mem_read(0x80000000, 0x10000)), repr((list(em.acc), em.macsr)).encode()]
    if lines:
        h = hashlib.sha256()
        h.update(bytes(uc.mem_read(0x4a400000, 0x400000)))
        h.update(bytes(uc.mem_read(0x4a340000, 0x90000)))
        h.update(bytes(uc.mem_read(0x4a3d0000, 0x8000)))
        s.append(h.digest())
    return s


def main():
    patch, extra, stubs = build()
    A = banc.Banc()
    B = banc.Banc(patch=patch, extra_code=extra)
    cA, cB = Count(A, None), Count(B, stubs)
    for b in (A, B):
        for t in range(6):
            b.rig.set_step(t, 0, vel=110, length=14)
    phases = []
    fails = 0
    first_diff = None
    reverb_sleep_slot = []
    for k in range(5 * P):
        ph = k // P
        if k % P == 0:
            for b in (A, B):
                if ph == 1:
                    for t in range(6):
                        b.target(t, 21, 40)
                elif ph == 2:
                    for t in range(6):
                        b.target(t, 20, 40)
                elif ph == 3:
                    for t in range(6):
                        b.target(t, 20, 0)
                        b.target(t, 21, 0)
                elif ph == 4:
                    b.target(6, 9, 127)
                    b.target(6, 10, 0)
                    b.target(6, 11, 127)
            phases.append(dict(d0=cA.n["d"], r0=cA.n["r"], d1=cB.n["d"], r1=cB.n["r"],
                               sd=cB.sleep["d"], sr=cB.sleep["r"]))
        if ph == 4 and k % P == P // 2:
            for b in (A, B):
                b.target(6, 9, 5)
        if k % 40 == 2:
            for b in (A, B):
                for t in range(6):
                    b.rig.schedule_step(t, 0, b.rig.now + b.rig.blk)
        iA, iB = A.block(), B.block()
        lines = k % 25 == 24
        same = (np.array_equal(iA["ring"], iB["ring"]) and np.array_equal(iA["usb"], iB["usb"])
                and np.array_equal(iA["out"], iB["out"]) and snap(A, lines) == snap(B, lines))
        if not same and first_diff is None:
            first_diff = k
            sa, sb = snap(A, False)[0], snap(B, False)[0]
            diff = [0x80000000 + i for i in range(0, 0x10000, 4) if sa[i:i + 4] != sb[i:i + 4]]
            print("  premier écart au bloc", k, ": anneau", np.array_equal(iA["ring"], iB["ring"]),
                  "SRAM", [hex(x) for x in diff[:20]], len(diff), flush=True)
        if k % 50 == 49:
            print(f"  bloc {k} phase {ph + 1} : crête anneau {int(np.abs(iA['ring']).max())}, sommeils "
                  f"delay {cB.sleep['d']} reverb {cB.sleep['r']}", flush=True)
    phases.append(dict(d0=cA.n["d"], r0=cA.n["r"], d1=cB.n["d"], r1=cB.n["r"], sd=cB.sleep["d"], sr=cB.sleep["r"]))
    ok = first_diff is None
    fails += not ok
    print(("  ok    " if ok else "  ECHEC ") + f"identique sur {5 * P} blocs : anneau, USB, voix, SRAM entière, "
          "EMAC à chaque bloc ; lignes en DDR tous les 25 blocs")
    names = ["envois 0", "reverb seule", "delay + reverb", "restes (envois 0)", "restes, paramètres FX qui glissent"]
    for i in range(5):
        a, z = phases[i], phases[i + 1]
        d0, r0 = (z["d0"] - a["d0"]) / P, (z["r0"] - a["r0"]) / P
        d1, r1 = (z["d1"] - a["d1"]) / P, (z["r1"] - a["r1"]) / P
        g = (d0 + r0) - (d1 + r1)
        print(f"  phase {i + 1} ({names[i]}) : delay {d0:.0f} -> {d1:.0f}, reverb {r0:.0f} -> {r1:.0f} instr/bloc ; "
              f"gain {g:+.0f} instr = {100 * 1.54 * g / 166667:+.2f} % d'un bloc ; blocs en sommeil delay "
              f"{z['sd'] - a['sd']}, reverb {z['sr'] - a['sr']} / {P}")
    print("  a3dc (décalage de lecture des lignes modulées) : min", min(cB.a3dc), "max", max(cB.a3dc))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
