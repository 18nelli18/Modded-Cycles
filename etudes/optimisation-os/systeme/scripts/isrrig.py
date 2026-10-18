#!/usr/bin/env python3
"""Banc minimal des interruptions hors audio du Model:Cycles OS 1.13 d'origine (Unicorn, vrai code de l'OS).

Mémoire : image + BSS (0x40000000..0x42400000), SRAM interne remplie comme au démarrage (0x4000045c), registres
des périphériques en RAM simple (0xec000000.., 0xfc000000..), Rapid GPIO (0x8c000000) en RAM. Une interruption
est lancée à son adresse avec un cadre d'exception factice et arrêtée sur son rte. On compte les instructions,
les accès aux périphériques et les lignes de 16 o de code et de données touchées.

    python3 isrrig.py sec3.bin
"""
import struct
import sys

from unicorn import Uc, UC_ARCH_M68K, UC_MODE_BIG_ENDIAN, UC_HOOK_CODE, UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE
from unicorn import UC_HOOK_MEM_UNMAPPED
from unicorn import m68k_const as mk

BASE = 0x40000400
STACK = 0x90008000
STOP = 0x9f000000


class Rig:
    def __init__(self, img):
        self.img = img
        uc = self.uc = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
        uc.ctl_set_cpu_model(mk.UC_CPU_M68K_ANY)
        uc.mem_map(0x40000000, 0x02400000)
        uc.mem_map(0x80000000, 0x10000)
        uc.mem_map(0x8c000000, 0x1000)
        uc.mem_map(0x90000000, 0x10000)
        uc.mem_map(0x9f000000, 0x1000)
        uc.mem_map(0xec000000, 0x100000)
        uc.mem_map(0xfc000000, 0x100000)
        uc.mem_write(BASE, img)
        uc.mem_write(0x80000000, img[0x4019b590 - BASE:0x401a2a50 - BASE])
        uc.mem_write(0x80008000, img[0x401a2a50 - BASE:0x401aa140 - BASE])
        uc.mem_write(STOP, b"\x4e\x71" * 8)
        self.unmapped = []
        uc.hook_add(UC_HOOK_MEM_UNMAPPED, self._unm)
        self.on = False
        self.n = 0
        self.code = set()
        self.data = set()
        self.periph = 0
        self.byfn = {}
        self.stubs = {}
        uc.hook_add(UC_HOOK_CODE, self._code)
        uc.hook_add(UC_HOOK_MEM_READ | UC_HOOK_MEM_WRITE, self._mem)

    def _unm(self, uc, acc, a, s, v, u):
        self.unmapped.append((hex(uc.reg_read(mk.UC_M68K_REG_PC)), hex(a)))
        return False

    def _code(self, uc, a, s, u):
        if a in self.stubs:                       # fonction remplacée : rts immédiat, d0 rendu
            sp = uc.reg_read(mk.UC_M68K_REG_A7)
            uc.reg_write(mk.UC_M68K_REG_D0, self.stubs[a] & 0xffffffff)
            uc.reg_write(mk.UC_M68K_REG_PC, struct.unpack(">I", uc.mem_read(sp, 4))[0])
            uc.reg_write(mk.UC_M68K_REG_A7, sp + 4)
            self.stub_calls = getattr(self, "stub_calls", 0) + 1
            return
        if bytes(uc.mem_read(a, 2)) == b"\x4e\x73" and self.stop_on_rte:
            uc.emu_stop()
            self.hit_rte = True
            return
        if self.on:
            self.n += 1
            self.code.add(a >> 4)

    def _mem(self, uc, acc, a, s, v, u):
        if self.on:
            if a >= 0x8c000000 and not 0x90000000 <= a < 0xa0000000:
                self.periph += 1
            elif not 0x90000000 <= a < 0x91000000:     # pile exclue (toujours chaude)
                self.data.add(a >> 4)

    def w32(self, a, v):
        self.uc.mem_write(a, struct.pack(">I", v & 0xffffffff))

    def r32(self, a):
        return struct.unpack(">I", self.uc.mem_read(a, 4))[0]

    def w16(self, a, v):
        self.uc.mem_write(a, struct.pack(">H", v & 0xffff))

    def w8(self, a, v):
        self.uc.mem_write(a, bytes([v & 0xff]))

    def isr(self, entry, sr=0x2000):
        """Lance une interruption : cadre ColdFire (format/vecteur, SR, PC de retour) sur la pile."""
        sp = STACK - 0x100
        self.uc.mem_write(sp, struct.pack(">HHI", 0x4000, sr, STOP))
        self.uc.reg_write(mk.UC_M68K_REG_SR, 0x2600)
        self.uc.reg_write(mk.UC_M68K_REG_A7, sp)
        self.n, self.code, self.data, self.periph = 0, set(), set(), 0
        self.on, self.stop_on_rte, self.hit_rte = True, True, False
        self.uc.emu_start(entry, STOP, count=2_000_000)
        self.on = False
        assert self.hit_rte, hex(self.uc.reg_read(mk.UC_M68K_REG_PC))
        return dict(instr=self.n, code=len(self.code), data=len(self.data), periph=self.periph)

    def call(self, fn, *args):
        sp = STACK - 0x400
        self.uc.mem_write(sp, struct.pack(">I" + "I" * len(args), STOP, *[a & 0xffffffff for a in args]))
        self.uc.reg_write(mk.UC_M68K_REG_A7, sp)
        self.n, self.code, self.data, self.periph = 0, set(), set(), 0
        self.on, self.stop_on_rte = True, False
        self.uc.emu_start(fn, STOP, count=5_000_000)
        self.on = False
        return dict(instr=self.n, code=len(self.code), data=len(self.data), periph=self.periph)


def fmt(r):
    return f"{r['instr']:5d} instr, {r['periph']:3d} accès périph., code {r['code']:3d} l, données {r['data']:3d} l"


def panel(img):
    """Cycle de 12 interruptions du panneau (PIT3, niveau 6) et interruption logicielle des touches (niveau 3)."""
    r = Rig(img)
    r.w32(0x40000340, 0x40059cd0)
    # rappels du panneau, comme 0x40005590.. : touches 0x4007fbde, encodeurs 0x4007fe20, pads 0x400598b8
    r.w32(0x40a7925c, 0x4007fbde)
    r.w32(0x40a79258, 0x4007fe20)
    r.w32(0x40a79254, 0x400598b8)
    r.stubs[0x40001fba] = 0                      # boîte aux lettres de l'interface (postage) : rendue tout de suite
    r.w16(0x8c000002, 0xffff)                    # touches relâchées (1 = relâchée ?), état stable
    res = {}
    for cyc in range(30):                        # régime établi
        tot = []
        for k in range(12):
            entry = r.r32(0x40000340)
            x = r.isr(entry, 0x2500)             # l'interruption coupe le rendu audio (niveau 5)
            tot.append((hex(entry), x))
            if r.r32(0xfc04c014) & 4:
                r.w32(0xfc04c014, r.r32(0xfc04c014) & ~4)
                y = r.isr(0x40059e64, 0x2000)
                tot.append(("touches", y))
        res = tot
    return r, res


def main():
    img = open(sys.argv[1], "rb").read()
    r, res = panel(img)
    s = {}
    for name, x in res:
        s.setdefault(name, []).append(x)
    total_i = total_p = nisr = 0
    for name, xs in s.items():
        print(f"{name:12s} x{len(xs):2d}/ms : {fmt(xs[-1])}")
        total_i += sum(x["instr"] for x in xs)
        total_p += sum(x["periph"] for x in xs)
        nisr += len(xs)
    print(f"par ms : {nisr} interruptions, {total_i} instructions, {total_p} accès aux périphériques")
    print("hors mémoire :", r.unmapped[:5], "rappels remplacés :", getattr(r, "stub_calls", 0))


if __name__ == "__main__":
    main()
