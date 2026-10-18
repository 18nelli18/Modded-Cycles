"""Ce que le delay (0x40057488) et la reverb (0x400579c4) lisent et écrivent, par phase, sur le banc.

Pour chaque appel : premier accès de chaque adresse dans les parties « signal » (lecture d'abord = entrée ou
état ; écriture d'abord = sortie ou temporaire), et valeurs écrites. Union sur des blocs avec signal (bruit dans
les voix, envois 40/40) puis sans. Sert à poser les conditions exactes du sommeil des effets (rapport §4).

    python3 analyse_rw.py [blocs]
"""
import json
import struct
import sys
from collections import defaultdict

sys.dont_write_bytecode = True
import numpy as np                                             # noqa: E402
from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE   # noqa: E402
from unicorn import m68k_const as mk                           # noqa: E402

import banc                                                    # noqa: E402

N = int(sys.argv[1]) if len(sys.argv) > 1 else 80

PH = [  # (début, fin, nom)
    (0x40057488, 0x40057516, "d.prologue"), (0x40057516, 0x40057704, "d.signal"), (0x40057704, 0x4005770e, "d.fin"),
    (0x400579c4, 0x40057ac8, "r.prologue"), (0x40057ac8, 0x40057d72, "r.signal1"),
    (0x40057d72, 0x40057dc6, "r.modulation"), (0x40057dc6, 0x40057f9e, "r.signal2"), (0x40057f9e, 0x40057fa8, "r.fin"),
]


def phase(a):
    for lo, hi, n in PH:
        if lo <= a < hi:
            return n
    return None


class RW:
    def __init__(self, b):
        self.b = b
        uc = b.uc
        self.cur = None
        self.first = {}                     # adresse -> 'r'/'w' (appel en cours, parties signal)
        self.reads_first = defaultdict(set)  # phase -> adresses lues avant d'être écrites (union)
        self.writes = defaultdict(set)       # phase -> adresses écrites (union)
        self.nzw = defaultdict(set)          # phase -> adresses écrites avec une valeur non nulle (blocs muets)
        self.quiet = False
        uc.hook_add(UC_HOOK_CODE, self._code, begin=0x40057488, end=0x4005770e)
        uc.hook_add(UC_HOOK_CODE, self._code, begin=0x400579c4, end=0x40057fa8)
        uc.hook_add(UC_HOOK_CODE, self._leave, begin=0x400569a2, end=0x400569a2)
        uc.hook_add(UC_HOOK_CODE, self._leave, begin=0x40056a32, end=0x40056a32)
        uc.hook_add(UC_HOOK_MEM_READ, self._r)
        uc.hook_add(UC_HOOK_MEM_WRITE, self._w)
        em = b.e.emac
        em.on_load = self._emac
        orig = em._ea

        def ea(spec):
            ad, post = orig(spec)
            self._emac(ad)
            return ad, post
        em._ea = ea

    def _code(self, uc, a, s, u):
        self.cur = a

    def _leave(self, uc, a, s, u):
        self.cur = None
        self.first = {}

    def _acc(self, pc, a, size, write, value=None):
        ph = phase(pc) if pc is not None else None
        if ph is None:
            return
        for x in range(a & ~3, a + size, 4):
            if x not in self.first:
                self.first[x] = "w" if write else "r"
                if not write:
                    self.reads_first[ph].add(x)
            if write:
                self.writes[ph].add(x)
                if self.quiet and value:
                    self.nzw[ph].add(x)

    def _r(self, uc, access, a, size, value, ud):
        self._acc(self.cur, a, size, False)

    def _w(self, uc, access, a, size, value, ud):
        self._acc(self.cur, a, size, True, value)

    def _emac(self, ad):
        pc = self.b.uc.reg_read(mk.UC_M68K_REG_PC)
        self._acc(pc, ad, 4, False)


def ranges(addrs):
    out = []
    for a in sorted(addrs):
        if out and a == out[-1][1]:
            out[-1][1] = a + 4
        else:
            out.append([a, a + 4])
    return [(hex(lo), hex(hi), (hi - lo) // 4) for lo, hi in out]


def main():
    b = banc.Banc()
    for t in range(6):
        b.param(t, 20, 40)
        b.param(t, 21, 40)
        b.rig.set_step(t, 0, vel=120, length=14)
    rw = RW(b)
    rng = np.random.default_rng(2)
    k = [0]

    def voices(uc, a, s, u):
        if 4 <= k[0] < N // 2:
            uc.mem_write(0x80001858, rng.integers(-(1 << 27), 1 << 27, 6 * 32).astype(">i4").tobytes())
        else:
            uc.mem_write(0x80001858, bytes(6 * 128))
        sp = uc.reg_read(mk.UC_M68K_REG_A7)
        uc.reg_write(mk.UC_M68K_REG_PC, struct.unpack(">I", uc.mem_read(sp, 4))[0])
        uc.reg_write(mk.UC_M68K_REG_A7, sp + 4)
    b.uc.hook_add(UC_HOOK_CODE, voices, begin=0x400a7d4a, end=0x400a7d4a)
    for k[0] in range(N):
        if k[0] == 2:
            for t in range(6):
                b.rig.schedule_step(t, 0, b.rig.now + b.rig.blk)
        b.block()
    print("journal eDMA du dernier bloc (canal, source, destination, octets) :")
    for c, s_, d, n in b.dma.log[-37:]:
        print(f"  ch{c} {s_:#x} -> {d:#x} {n}")
    res = {}
    for ph in sorted(set(rw.reads_first) | set(rw.writes)):
        res[ph] = dict(lu_d_abord=ranges(rw.reads_first[ph]), ecrit=ranges(rw.writes[ph]))
        print(f"\n== {ph}")
        print("  lu avant d'être écrit :", ranges(rw.reads_first[ph]))
        print("  écrit                 :", ranges(rw.writes[ph]))
    json.dump(res, open("analyse_rw.json", "w"), indent=1)


if __name__ == "__main__":
    main()
