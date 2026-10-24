#!/usr/bin/env python3
"""Coût d'un bloc sur la machine, estimé en émulation (notes/77) : le vrai code de l'interruption audio (osbanc.OsBanc),
et un modèle de ce que le ColdFire V4 du Model:Cycles y ajoute, étalonné sur le firmware de mesure (notes/75) :

  - 1 cycle par instruction, sauf ce que donne le manuel (MCF5441x RM rev. 5, §3.3.5) : divisions 32 bits 35, 16 bits
    20, multiplications 4, movem 1 par registre, jsr/jmp par registre 5, MOVE vers MACSR 8 ;
  - rts : 2 cycles si la pile de retour matérielle le prédit, 9 sinon (§3.3.5.7) ; pile de retour modélisée sur
    RS_DEPTH entrées [HYP : sa profondeur] ;
  - EMAC : lire un accumulateur (move.l ACCx,Rx, movclr) moins de 4 instructions après un MAC vers lui attend la fin
    du pipeline (3 cycles juste après, §5.3.3, figure 5-9) ; +1 cycle par lecture avec la saturation ou l'arrondi
    (MACSR 7..4, note 2 de la table 3-18) ;
  - cache d'instructions 8 Ko, 4 voies, lignes de 16 o, compteur tournant (§6.3.1) ; une ligne absente : I_MISS
    cycles de plus en SDRAM, I_MISS_SR en SRAM (relevés BENCH de Maxime, 23/10/2026 : I-MISS 22,81 ; LINE SR 16,02
    contre LINE 8,04) ;
  - cache de données 8 Ko, 4 voies, copyback, allocation à l'écriture [HYP] ; une ligne absente D_MISS cycles
    (D-MISS 17 à 22), une ligne modifiée chassée D_PUSH [HYP] ; la SRAM à 0 ; la vue sans cache UNC par accès [HYP] ;
    les périphériques PERIPH [HYP].

Ce que le modèle ne voit pas : la prédiction des branchements conditionnels (1 cycle chacun), les attentes de calcul
d'adresse (§3.3.5.1 point 3), les accès de l'eDMA et de l'USB à la mémoire, et l'interface entre deux blocs (caches
gardés d'un bloc à l'autre, ou vidés : les deux sont donnés).

    python3 tools/emu/hwcost.py --cycles model-cycles_OS1.13.syx --syntakt Syntakt_OS1.42.syx [--project modal6] [--mhz 250]
"""
import argparse
import collections
import contextlib
import io
import pathlib
import struct
import sys

from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE
from unicorn import m68k_const as mk

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import gen_mesure as G              # noqa: E402
import inventory_code as I          # noqa: E402
import mcengine as E                # noqa: E402
import osbanc as O                  # noqa: E402
import seqrig as S                  # noqa: E402
import syntakt                      # noqa: E402
import test_macro_syntakt as tmx    # noqa: E402
import test_mesure as T             # noqa: E402
import test_modal as tmo            # noqa: E402

I_MISS, I_MISS_SR = 22.81, 16.02 - 8.04
D_MISS, D_PUSH, UNC, PERIPH = 20.0, 6.0, 20.0, 10.0
RS_DEPTH = 8
TICKS = 90112                         # minuteur DMA 0 par bloc (135,168 MHz)


class Cache:
    """8 Ko, 4 voies, lignes de 16 o ; voie libre la plus basse, sinon compteur tournant."""

    def __init__(self):
        self.clear()

    def clear(self):
        self.tags = [[None] * 4 for _ in range(128)]
        self.dirty = [[False] * 4 for _ in range(128)]
        self.rr = 0

    def access(self, line, write=False):
        """(absente, ligne modifiée chassée)"""
        s = line & 127
        w = self.tags[s]
        if line in w:
            if write:
                self.dirty[s][w.index(line)] = True
            return False, False
        if None in w:
            k = w.index(None)
        else:
            k = self.rr
            self.rr = (self.rr + 1) & 3
        pushed = self.dirty[s][k]
        w[k] = line
        self.dirty[s][k] = write
        return True, pushed


class Cost:
    """Les cycles d'un bloc, par poste (inventory_code.Tracer : la tête, chaque poste de la fonction audio, chaque
    piste de la boucle des voix)."""

    FIELDS = ("instr", "base", "emac", "omc", "rts", "imiss", "imiss_sr", "dmiss", "dpush", "unc", "periph")

    def __init__(self, b, flush=False):
        self.b, self.uc, self.flush = b, b.uc, flush
        self.tr = I.Tracer(b, [])
        self.ic, self.dc = Cache(), Cache()
        self.cls = {}
        self.emac = b.e.emac
        self.n = 0
        self.last_mac = [-99] * 4
        self.rstack = []
        self.cur = collections.defaultdict(lambda: collections.Counter())
        self.uc.hook_add(UC_HOOK_CODE, self._code)
        self.uc.hook_add(UC_HOOK_MEM_READ, self._mem)
        self.uc.hook_add(UC_HOOK_MEM_WRITE, self._memw)
        self.pending_ret = None

    def stage(self):
        st = self.tr.stage
        return st if not st.startswith("voice:") else "voice:" + st.split(":")[1] + ":" + st.split(":")[2]

    def _class(self, addr, size):
        ins = self.emac.ops.get(addr)
        if ins is not None:
            sz, mn, ops = ins
            args = [a.strip() for a in ops.split(",")]
            if mn in ("macl", "msacl", "macw", "msacw"):
                return ("mac", int(args[-1][4]))
            if mn == "movclrl":
                return ("racc", int(args[0][4]))
            if mn == "movel" and args[0].startswith("%acc") and args[0][4].isdigit() and not args[1].startswith("%acc"):
                return ("racc", int(args[0][4]))
            if mn == "movel" and args[1] == "%macsr":
                return ("cyc", 8)
            return ("cyc", 1)
        op, = struct.unpack(">H", bytes(self.uc.mem_read(addr, 2)))
        if op == 0x4e75:
            return ("rts",)
        if (op & 0xffc0) == 0x4e80:
            return ("jsr", 5 if (op & 0x38) in (0x10, 0x28, 0x30) else 2)
        if (op & 0xffc0) == 0x4ec0:
            return ("cyc", 5 if (op & 0x38) in (0x10, 0x28, 0x30) else 2)
        if (op & 0xff00) == 0x6100:
            return ("jsr", 2)
        if (op & 0xffc0) == 0x4c40:
            return ("cyc", 35)
        if (op & 0xf1c0) in (0x81c0, 0x80c0):
            return ("cyc", 20)
        if (op & 0xffc0) == 0x4c00 or (op & 0xf1c0) in (0xc1c0, 0xc0c0):
            return ("cyc", 4)
        if (op & 0xfb80) == 0x4880 and (op & 0x38) != 0:          # movem.l (pas ext)
            mask, = struct.unpack(">H", bytes(self.uc.mem_read(addr + 2, 2)))
            return ("cyc", max(1, bin(mask).count("1")))
        return ("cyc", 1)

    def _code(self, uc, addr, size, ud):
        c = self.cur[self.stage()]
        self.n += 1
        c["instr"] += 1
        if self.pending_ret is not None:                          # cible du jsr/bsr précédent : on empile le retour
            self.rstack.append(self.pending_ret)
            if len(self.rstack) > RS_DEPTH:
                self.rstack.pop(0)
            self.pending_ret = None
        k = self.cls.get(addr)
        if k is None or (0x80000000 <= addr < 0x80010000):        # la SRAM peut changer (chargeur)
            k = self.cls[addr] = self._class(addr, size)
        kind = k[0]
        if kind == "cyc":
            c["base"] += k[1]
        elif kind == "mac":
            c["base"] += 1
            self.last_mac[k[1]] = self.n
        elif kind == "racc":
            gap = self.n - self.last_mac[k[1]] - 1
            c["base"] += 1
            m = self.emac.macsr
            c["emac"] += max(0, 3 - gap)
            c["omc"] += 1 if m & 0x80 or m & 0x60 == 0x60 or m & 0x30 == 0x30 else 0
        elif kind == "jsr":
            c["base"] += k[1]
            self.pending_ret = addr + size
        elif kind == "rts":
            sp = uc.reg_read(mk.UC_M68K_REG_A7)
            ret, = struct.unpack(">I", bytes(uc.mem_read(sp, 4)))
            if self.rstack and self.rstack[-1] == ret:
                self.rstack.pop()
                c["base"] += 2
            else:
                if self.rstack:
                    self.rstack.pop()
                c["base"] += 2
                c["rts"] += 7
        line = addr >> 4
        if line != getattr(self, "_iline", None):
            self._iline = line
            miss, _ = self.ic.access(line)
            if miss:
                c["imiss_sr" if 0x80000000 <= addr < 0x80010000 else "imiss"] += 1

    def _data(self, addr, write):
        c = self.cur[self.stage()]
        if 0x80000000 <= addr < 0x90000000:
            return
        if 0xfc000000 <= addr:
            c["periph"] += 1
            return
        if 0x48000000 <= addr < 0x50000000:
            if not write:
                c["unc"] += 1
            return
        miss, pushed = self.dc.access(addr >> 4, write)
        if miss:
            c["dmiss"] += 1
        if pushed:
            c["dpush"] += 1

    def _mem(self, uc, access, addr, size, value, ud):
        self._data(addr, False)

    def _memw(self, uc, access, addr, size, value, ud):
        self._data(addr, True)

    def block(self):
        if self.flush:
            self.ic.clear()
            self.dc.clear()
        self.cur.clear()
        self.rstack = []
        self._iline = None
        self.tr.block()
        return {k: dict(v) for k, v in self.cur.items()}


def cycles(c):
    return (c.get("base", 0) + c.get("emac", 0) + c.get("omc", 0) + c.get("rts", 0) + c.get("imiss", 0) * I_MISS
            + c.get("imiss_sr", 0) * I_MISS_SR + c.get("dmiss", 0) * D_MISS + c.get("dpush", 0) * D_PUSH
            + c.get("unc", 0) * UNC + c.get("periph", 0) * PERIPH)


PROJECTS = {
    # projet du relevé de Maxime (23/10/2026) : MODAL, SNARE, METAL, ACID, KICK, CPVtg
    "maxime": ((14, 1, 2, 13, 0, 8), {}),
    "modal6": ((14, 14, 14, 14, 14, 14), {}),
    "origine": ((0, 1, 2, 3, 4, 5), {}),
}


def firmware(cycles_path, syntakt_path, tweaks=None):
    stock = T.stock_of(cycles_path)
    ctx = dict(syntakt=syntakt_path, st_img=syntakt.dsp_image(syntakt_path), chord=tmx.chord_tables(stock))
    with contextlib.redirect_stdout(io.StringIO()):
        return tmo.Fw(stock, tweaks or G.os_tweaks(), ctx)


def run(fw, mach, knobs=None, blocks=120, steps=24, flush=False, skip=8):
    """Projet : machines, réglages ; un trig sur chaque piste tous les `steps` blocs (24 : des doubles croches à
    environ 470 BPM, ou des croches à 120 BPM pour 4 pistes en quinconce). Rend les postes moyennés."""
    b = O.OsBanc(fw)
    for t, m in enumerate(mach):
        b.rig.param(t, E.SLOT["machine"], m * 256)
        for k, v in (knobs or {}).get(t, {}).items():
            b.rig.param(t, E.SLOT[k], v * 256)
    cost = Cost(b, flush)
    tot = collections.defaultdict(collections.Counter)
    n = 0
    for k in range(blocks):
        if k % steps == 2:
            for t in range(6):
                b.rig.set_step(t, 0, vel=100, length=S.LEN_1_16, note=48)
                b.rig.schedule_step(t, 0, b.rig.now + b.rig.blk // 2)
        r = cost.block()
        if k >= skip:
            n += 1
            for st, c in r.items():
                tot[st].update(c)
    return {st: {k: v / n for k, v in c.items()} for st, c in tot.items()}


def report(res, mhz):
    per = mhz * 1e6 * 32 / 48000
    tracks, rest = [], []
    for st, c in res.items():
        (tracks if st.startswith("voice:") else rest).append((st, c))
    total = sum(cycles(c) for _, c in res.items())
    print(f"  total {cycles_sum(res) / per * 100:5.1f} % ({total:.0f} cycles par bloc à {mhz} MHz)")
    for st, c in sorted(tracks) + sorted(rest, key=lambda x: -cycles(x[1])):
        cy = cycles(c)
        parts = ", ".join(f"{k} {c.get(k, 0):.0f}" for k in Cost.FIELDS if c.get(k))
        print(f"  {st:16s} {cy / per * 100:5.1f} %  {cy:8.0f} cycles  ({parts})")


def cycles_sum(res):
    return sum(cycles(c) for c in res.values())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True)
    ap.add_argument("--syntakt", required=True)
    ap.add_argument("--project", default="maxime", choices=sorted(PROJECTS))
    ap.add_argument("--mhz", type=float, default=250.0)
    ap.add_argument("--blocks", type=int, default=120)
    args = ap.parse_args()
    fw = firmware(args.cycles, args.syntakt)
    mach, knobs = PROJECTS[args.project]
    for flush in (False, True):
        print(f"== {args.project}, caches {'vidés à chaque bloc' if flush else "gardés d'un bloc à l'autre"}")
        report(run(fw, mach, knobs, blocks=args.blocks, flush=flush), args.mhz)


if __name__ == "__main__":
    main()
