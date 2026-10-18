"""Version rapide de queue.py : la boucle des voix est remplacée par une salve de bruit (blocs 4..23) puis des
zéros, pour voir vite si les queues du delay et de la reverb finissent à zéro exactement, et en combien de blocs.

    python3 queue2.py blocs envoi_delay envoi_reverb delay_time fdbk size [tone]
Tout le reste (vélocité, Volume+Dist, mixeur, delay, reverb, master, anneau) est le code de l'OS.
"""
import struct
import sys
import time

sys.dont_write_bytecode = True
import numpy as np                     # noqa: E402
from unicorn import UC_HOOK_CODE       # noqa: E402
from unicorn import m68k_const as mk   # noqa: E402

import banc                            # noqa: E402
from queue import state_mask           # noqa: E402

N, DS, RS, DT, FB, SZ = (int(x) for x in sys.argv[1:7])
TONE = int(sys.argv[7]) if len(sys.argv) > 7 else 64


class Probe:
    def __init__(self, b):
        self.b = b
        self.snap = {}
        self.k = 0
        self.rng = np.random.default_rng(1)
        uc = b.uc
        uc.hook_add(UC_HOOK_CODE, self._after_delay, begin=0x400569a2, end=0x400569a2)
        uc.hook_add(UC_HOOK_CODE, self._after_rev, begin=0x40056a32, end=0x40056a32)
        uc.hook_add(UC_HOOK_CODE, self._voices, begin=0x400a7d4a, end=0x400a7d4a)

    def _after_delay(self, uc, a, s, u):
        self.snap["dout"] = self.b.r32s(0x8000ba90, 64)
        self.snap["dline"] = self.b.r32s(0x8000b590, 64)
        self.snap["din"] = self.b.r32s(0x8000b990, 64)

    def _after_rev(self, uc, a, s, u):
        self.snap["rout"] = self.b.r32s(0x8000bb90, 64)
        self.snap["rin"] = self.b.r32s(0x8000b990, 64)
        w = [self.b.r32s(0x8000afe0 + 160 * k, 32) for k in range(8)]
        w += [self.b.r32s(0x8000a9b0 + 176 * k, 32) for k in range(9)]
        self.snap["rline"] = np.concatenate(w)

    def _voices(self, uc, a, s, u):
        if 4 <= self.k < 24:
            v = self.rng.integers(-(1 << 27), 1 << 27, 6 * 32).astype(">i4")
            uc.mem_write(0x80001858, v.tobytes())
        else:
            uc.mem_write(0x80001858, bytes(6 * 128))
        sp = uc.reg_read(mk.UC_M68K_REG_A7)
        uc.reg_write(mk.UC_M68K_REG_PC, struct.unpack(">I", uc.mem_read(sp, 4))[0])
        uc.reg_write(mk.UC_M68K_REG_A7, sp + 4)


def main():
    b = banc.Banc()
    for t in range(6):
        b.param(t, 20, DS)
        b.param(t, 21, RS)
    for slot, v in ((9, DT), (10, FB), (11, SZ), (12, TONE)):
        b.param(6, slot, v)
    for t in range(6):
        b.rig.set_step(t, 0, vel=120, length=14)     # trig : l'OS pose le gain de vélocité (0x40fe4c90)
    pr = Probe(b)
    msk = state_mask()
    t0 = time.time()
    last_nz = {}
    hist = []
    for k in range(N):
        pr.k = k
        if k == 2:
            for t in range(6):
                b.rig.schedule_step(t, 0, b.rig.now + b.rig.blk)
        info = b.block()
        sn = pr.snap
        st = b.r32s(0x8000a100, (0x8000b990 - 0x8000a100) // 4)[msk]
        row = dict(din=int(np.abs(sn["din"]).max()), dout=int(np.abs(sn["dout"]).max()),
                   dline=int(np.abs(sn["dline"]).max()), rin=int(np.abs(sn["rin"]).max()),
                   rout=int(np.abs(sn["rout"]).max()), rline=int(np.abs(sn["rline"]).max()),
                   ring=int(np.abs(info["ring"]).max()), usb=int(np.abs(info["usb"]).max()))
        for key, v in row.items():
            if v:
                last_nz[key] = k
        hist.append([row[x] for x in ("din", "dout", "dline", "rin", "rout", "rline", "ring", "usb")])
        if k % 250 == 0 or k == N - 1:
            print(k, row, "état non nul :", int(np.count_nonzero(st)), "mots", f"({time.time() - t0:.0f} s)",
                  flush=True)
    print("dernier bloc non nul par signal :", last_nz)
    nz = np.nonzero(st)[0]
    addrs = [0x8000a100 + 4 * int(i) for i in np.nonzero(msk)[0][nz]]
    print("mots d'état non nuls à la fin :", len(addrs), [(hex(a), int(v)) for a, v in zip(addrs, st[nz])][:80])
    np.save(f"queue2_{DS}_{RS}_{DT}_{FB}_{SZ}_{TONE}.npy", np.array(hist))


if __name__ == "__main__":
    main()
