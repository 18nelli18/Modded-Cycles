"""Les queues du delay et de la reverb s'éteignent-elles exactement (zéros) une fois l'entrée nulle ?

Envois delay/reverb sur les 6 pistes, un trig des 6 pistes, puis on laisse tout s'éteindre. À chaque bloc : crête
des voix, de la sortie du delay (0x8000ba90, lue juste après l'appel 0x4005699c), de ce qu'il écrit dans sa
ligne (0x8000b590, 32 trames), de la sortie de la reverb (0x8000bb90) et de ses 17 tampons d'écriture, et l'état
interne (SRAM 0x8000a100..0x8000b990 hors tampons DMA). Les voix sont calculées par l'OS tant qu'elles ne sont
pas muettes depuis 200 blocs ; ensuite la boucle des voix est remplacée par des zéros (ce qu'elle rend, vérifié).

    python3 queue.py [blocs] [envoi_delay] [envoi_reverb]
"""
import struct
import sys
import time

sys.dont_write_bytecode = True
import numpy as np                     # noqa: E402
from unicorn import UC_HOOK_CODE       # noqa: E402
from unicorn import m68k_const as mk   # noqa: E402

import banc                            # noqa: E402

N = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
DS = int(sys.argv[2]) if len(sys.argv) > 2 else 40
RS = int(sys.argv[3]) if len(sys.argv) > 3 else 40

# états : tout 0x8000a100..0x8000b990 sauf les tampons DMA (lus ou écrits par l'eDMA) et les TCD en SRAM
DMA_BUFS = [(0x8000b590, 0x8000b7b0), (0x8000a9b0 - 16, 0x8000afe0 + 8 * 160), (0x8000a560, 0x8000a990),
            (0x8000b900, 0x8000b980)]


def state_mask():
    m = np.ones((0x8000b990 - 0x8000a100) // 4, bool)
    for lo, hi in DMA_BUFS:
        m[max(0, (lo - 0x8000a100) // 4):max(0, (hi - 0x8000a100) // 4)] = False
    return m


class Probe:
    def __init__(self, b):
        self.b = b
        self.snap = {}
        uc = b.uc
        uc.hook_add(UC_HOOK_CODE, self._after_delay, begin=0x400569a2, end=0x400569a2)
        uc.hook_add(UC_HOOK_CODE, self._after_rev, begin=0x40056a32, end=0x40056a32)
        self.skip_voices = False
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
        if not self.skip_voices:
            return
        uc.mem_write(0x80001858, bytes(6 * 128))
        sp = uc.reg_read(mk.UC_M68K_REG_A7)
        uc.reg_write(mk.UC_M68K_REG_PC, struct.unpack(">I", uc.mem_read(sp, 4))[0])
        uc.reg_write(mk.UC_M68K_REG_A7, sp + 4)


def main():
    b = banc.Banc()
    rig = b.rig
    for t in range(6):
        b.param(t, 20, DS)
        b.param(t, 21, RS)
        rig.set_step(t, 0, vel=120, length=14)
    pr = Probe(b)
    msk = state_mask()
    quiet = 0
    t0 = time.time()
    last = None
    first_dead = {}
    for k in range(N):
        if k == 4:
            for t in range(6):
                rig.schedule_step(t, 0, rig.now + rig.blk)
        info = b.block()
        sn = pr.snap
        vox = int(np.abs(info["out"]).max())
        quiet = quiet + 1 if vox == 0 else 0
        if not pr.skip_voices and quiet >= 200:
            pr.skip_voices = True
            print(f"bloc {k} : voix muettes depuis 200 blocs, boucle des voix remplacée par des zéros", flush=True)
        st = b.r32s(0x8000a100, (0x8000b990 - 0x8000a100) // 4)[msk]
        row = dict(vox=vox, din=int(np.abs(sn["din"]).max()), dout=int(np.abs(sn["dout"]).max()),
                   dline=int(np.abs(sn["dline"]).max()), rin=int(np.abs(sn["rin"]).max()),
                   rout=int(np.abs(sn["rout"]).max()), rline=int(np.abs(sn["rline"]).max()),
                   ring=int(np.abs(info["ring"]).max()))
        for key in ("dout", "dline", "rout", "rline", "ring"):
            if row[key] == 0 and key not in first_dead and row["vox"] == 0 and row["din"] == 0:
                first_dead[key] = k
            if row[key] != 0:
                first_dead.pop(key, None)
        if k % 100 == 0 or k == N - 1:
            nz = np.nonzero(st)[0]
            print(k, row, "état non nul :", len(nz), "mots", f"({time.time() - t0:.0f} s)", flush=True)
            last = (st, nz)
    print("dernier bloc non nul -> premier bloc nul (et resté nul) :", first_dead)
    st, nz = last
    addrs = [0x8000a100 + 4 * int(i) for i in np.nonzero(msk)[0][nz]]
    print("mots d'état non nuls à la fin :", [(hex(a), int(v)) for a, v in zip(addrs, st[nz])][:60])
    np.save("queue_etat.npy", st)


if __name__ == "__main__":
    main()
