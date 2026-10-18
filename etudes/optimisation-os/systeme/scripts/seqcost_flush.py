#!/usr/bin/env python3
"""Coût du séquenceur dans l'interruption de rendu (0x40058ca0 -> 0x40059382), bloc par bloc, sur le vrai code de
l'OS 1.13 d'origine (seqrig.py du dépôt), et coût du constructeur d'événements d'un pas (0x400548ce, appelé
hors du rendu, par l'interruption logicielle du séquenceur, niveau 2).

Compte : instructions, lignes de 16 o de code et de données distinctes touchées.
Conversion (modèle des notes 27-28 et 31 §7) : 1,54 cycle par instruction + 15 cycles par ligne relue en SDRAM
(cache froid : toutes les lignes hors SRAM), 166 667 cycles par bloc.

    python3 seqcost.py sec3.bin
"""
import struct
import sys

sys.path.insert(0, "/home/user/Modded-Cycles/tools/emu")
sys.path.insert(0, "/home/user/Modded-Cycles/tools")

from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE  # noqa: E402

import mcengine as E                       # noqa: E402
import seqrig as S                         # noqa: E402

BLOCK_CYCLES = 166_667


class Counter:
    def __init__(self, uc):
        self.on = False
        self.n = 0
        self.code = set()
        self.data = set()
        uc.hook_add(UC_HOOK_CODE, self._code)
        uc.hook_add(UC_HOOK_MEM_READ | UC_HOOK_MEM_WRITE, self._mem)
        uc.ctl_flush_tb()

    def _code(self, uc, a, s, u):
        if self.on:
            self.n += 1
            self.code.add(a >> 4)

    def _mem(self, uc, acc, a, s, v, u):
        if self.on:
            self.data.add(a >> 4)

    def reset(self):
        self.n = 0
        self.code = set()
        self.data = set()

    def cost(self):
        sdram = lambda lines: sum(1 for x in lines if not (0x8000000 <= x < 0x8001000))   # hors SRAM (0x80000000)
        c = self.n * 1.54 + 15 * (sdram(self.code) + sdram(self.data))
        return dict(instr=self.n, code=len(self.code), data=len(self.data),
                    sdram=sdram(self.code) + sdram(self.data), pct=100 * c / BLOCK_CYCLES,
                    pct_warm=100 * self.n * 1.54 / BLOCK_CYCLES)


def isr_only(rig, cnt):
    """Le corps de l'interruption de rendu seul (jusqu'au jsr de la fonction audio), compté ; puis la fonction audio
    sans compter (les voix tournent, pour que l'état avance comme sur la machine)."""
    uc = rig.uc
    from unicorn import m68k_const as mk
    rig.w32(S.NOW, rig.now)
    fp0 = S.ISTACK - 4
    uc.reg_write(mk.UC_M68K_REG_A6, fp0)
    uc.reg_write(mk.UC_M68K_REG_A7, fp0 - 168)
    uc.reg_write(mk.UC_M68K_REG_D7, 0)
    cnt.reset()
    cnt.on = True
    uc.emu_start(0x40058ca0, 0x40059382, count=5_000_000)
    cnt.on = False
    res = cnt.cost()
    fp = uc.reg_read(mk.UC_M68K_REG_A6)
    rig.e.call(0x4005979e, fp - 44)
    rig.now += rig.blk
    return res


def main():
    img = open(sys.argv[1], "rb").read()

    def fresh(bpm=120):
        e = E.Engine(img)
        rig = S.Rig(e, bpm=bpm)
        return e, rig, Counter(e.uc)

    out = []
    # 1. à l'arrêt : aucun événement
    e, rig, cnt = fresh()
    r = [isr_only(rig, cnt) for _ in range(5)]
    out.append(("aucun événement (arrêt ou pas sans trig)", r[-1]))

    # 2. un trig par piste sur des blocs différents, puis 6 trigs dans le même bloc, avec et sans p-locks
    for label, ntr, locks in (("1 trig (piste 1), sans p-lock", 1, 0),
                              ("6 trigs dans le même bloc, sans p-lock", 6, 0),
                              ("1 trig, 10 p-locks (slots 9..0x12)", 1, 10),
                              ("6 trigs dans le même bloc, 10 p-locks chacun", 6, 10)):
        e, rig, cnt = fresh()
        build = []
        at = rig.now + 2 * rig.blk + rig.blk // 3
        for t in range(ntr):
            rig.set_step(t, 0, vel=110, length=S.LEN_1_16, note=50 + t)
            for k in range(locks):
                rig.set_lock(t, 0, 0x09 + k if k else 0x0a, (40 + 3 * k) << 8)
            cnt.reset()
            cnt.on = True
            rig.schedule_step(t, 0, at)
            cnt.on = False
            build.append(cnt.cost())
        blocks = [isr_only(rig, cnt) for _ in range(6)]
        worst = max(blocks, key=lambda x: x["instr"])
        out.append((label + " : bloc du trig", worst))
        out.append((label + " : construction des événements (hors rendu), par trig", build[-1]))
        out.append((label + " : bloc suivant", blocks[blocks.index(worst) + 1]))
    for label, c in out:
        print(f"{label:70s} {c['instr']:6d} instr  code {c['code']:4d} l  données {c['data']:4d} l  "
              f"-> {c['pct_warm']:5.2f} % chaud, {c['pct']:5.2f} % cache froid")


if __name__ == "__main__":
    main()
