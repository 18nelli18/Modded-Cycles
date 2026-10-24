#!/usr/bin/env python3
"""Preuve du code chaud en SRAM (notes/76), sur l'OS construit (os.json) : le vrai code de l'interruption audio,
étage de sortie compris (osbanc.OsBanc), chargeur inerte (le démarrage ne l'a pas lancé : l'OS d'avant) contre
chargeur lancé (hot_boot, comme le 2e étage du crochet de démarrage).

  1. démarrage : chaque détour (jmp vers son talon), ses instructions d'origine et le saut de retour ;
  2. son : les 6 voix, l'anneau du codec et la copie pour l'USB identiques, bloc par bloc, sur des projets de toutes
     les machines, avec changements de machine en cours de route (le code du Syntakt rendu à sa place avant son
     premier trig) ; la machine que le chargeur lit est celle que la boucle des voix joue ;
  3. pause des moteurs du Syntakt : un trig pendant que leur code revient en SRAM reste muet, puis la piste rejoue ;
  4. place : le code du Syntakt et ses tables rendus octet pour octet, la zone de transit intacte, et rien d'autre
     que le chargeur n'écrit dans les deux fins de SRAM ;
  5. modèle du cache d'instructions : défauts par bloc, avant et après.

    python3 tools/emu/test_sram_hot.py --cycles model-cycles_OS1.13.syx --syntakt Syntakt_OS1.42.syx [--quick]
"""
import argparse
import contextlib
import functools
import io
import pathlib
import struct
import sys

import numpy as np
from unicorn import UC_HOOK_MEM_WRITE
from unicorn import m68k_const as mk

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import gen_mesure as G              # noqa: E402
import gen_sram_hot as gh           # noqa: E402
import inventory_code as I          # noqa: E402
import mcengine as E                # noqa: E402
import osbanc as O                  # noqa: E402
import seqrig as S                  # noqa: E402
import syntakt                      # noqa: E402
import test_macro_syntakt as tmx    # noqa: E402
import test_mesure as T             # noqa: E402
import test_modal as tmo            # noqa: E402

FAILS = []
NAMES = gh.NAMES


def check(ok, msg):
    print(("  ok    " if ok else "  ÉCHEC ") + msg, flush=True)
    if not ok:
        FAILS.append(msg)


def firmware(cycles, syntakt_path):
    stock = T.stock_of(cycles)
    ctx = dict(syntakt=syntakt_path, st_img=syntakt.dsp_image(syntakt_path), chord=tmx.chord_tables(stock))
    with contextlib.redirect_stdout(io.StringIO()):
        return tmo.Fw(stock, G.os_tweaks(), ctx)


class Run:
    """Un projet joué par le banc : machines et réglages des pistes, trigs ; changements en cours de route."""

    def __init__(self, fw, hot, mach, knobs=None, trace=False):
        self.b = b = O.OsBanc(fw, hot=hot)
        self.uc, self.sy = b.uc, b.syms
        for t, m in enumerate(mach):
            self.machine(t, m)
            for k, v in (knobs or {}).get(t, {}).items():
                b.rig.param(t, E.SLOT[k], v * 256)
        self.tr = I.Tracer(b, []) if trace else None
        self.res = []

    def machine(self, t, m):
        self.b.rig.param(t, E.SLOT["machine"], m * 256)

    def trig(self, tracks, note=None):
        for t in tracks:
            self.b.rig.set_step(t, 0, vel=100, length=S.LEN_1_16, note=note or 40 + 4 * t)
            self.b.rig.schedule_step(t, 0, self.b.rig.now + self.b.rig.blk // 2)

    def block(self):
        r = self.tr.block() if self.tr else (self.b.block(), None)[1]
        if self.tr:
            self.res.append(r)
        uc = self.uc
        idx = self.b.rig.r32(S.ISTACK - 4 - 44 + 40)
        return (bytes(uc.mem_read(0x80001858, 6 * 0x80)), bytes(uc.mem_read(O.RING + 256 * idx, 256)),
                bytes(uc.mem_read(O.USB_MIX, 256)), bytes(uc.mem_read(S.VOICE0, 6 * S.VSTRIDE)))

    def u8(self, name):
        return self.uc.mem_read(self.sy[name], 1)[0]

    def u32(self, name):
        return struct.unpack(">I", self.uc.mem_read(self.sy[name], 4))[0]


def play(fw, hot, mach, events, blocks, knobs=None, trace=False, each=None):
    """events : {bloc : [("trig", pistes) | ("machine", piste, machine)]}. Rend (sorties par bloc, Run)."""
    r = Run(fw, hot, mach, knobs, trace)
    outs = []
    for k in range(blocks):
        for ev in events.get(k, ()):
            if ev[0] == "trig":
                r.trig(ev[1])
            else:
                r.machine(ev[1], ev[2])
        outs.append(r.block())
        if each:
            each(r, k)
    return outs, r


def same(a, b):
    """(identique, 1er bloc différent, ce qui diffère)"""
    for k, (x, y) in enumerate(zip(a, b)):
        if x != y:
            return False, k, [n for n, i, j in zip(("voix", "anneau", "usb", "états"), x, y) if i != j]
    return len(a) == len(b), None, []


def every(n, tracks, upto, start=2):
    return {k: [("trig", tracks)] for k in range(start, upto, n)}


# --- 1. démarrage ---------------------------------------------------------------------------------------------------
def boot_test(fw):
    print("1. démarrage")
    r = Run(fw, False, (0, 1, 2, 3, 4, 5))
    uc, sy = r.uc, r.sy
    nu, nd, nr = struct.unpack(">3H", uc.mem_read(sy["hot_n"], 6))
    dets = [struct.unpack(">IHHHBB", bytes(uc.mem_read(sy["hot_dets"] + 12 * i, 12))) for i in range(nd)]
    before = {at: bytes(uc.mem_read(at, k)) for at, _, _, _, k, _ in dets}
    r.b.hot_boot()
    ok_patch = ok_orig = ok_tab = True
    live = 0
    for i, (at, unit, off, sm, k, _) in enumerate(dets):
        now = bytes(uc.mem_read(at, 6))
        orig = sy["hot_orig"] + 16 * i
        tab = struct.unpack(">I", uc.mem_read(sy["hot_tab"] + 4 * i, 4))[0]
        if sum(before[at]) & 0xffff != sm:
            ok_patch &= now == before[at][:6]                     # pas les octets attendus : pas de détour
            continue
        live += 1
        ok_patch &= now == b"\x4e\xf9" + (sy["hot_stubs"] + 8 * i).to_bytes(4, "big")
        ok_orig &= bytes(uc.mem_read(orig, k + 6)) == before[at] + b"\x4e\xf9" + (at + k).to_bytes(4, "big")
        ok_tab &= tab == orig
    check(live == nd, f"{live}/{nd} détours posés (octets d'origine attendus partout)")
    check(ok_patch, "chaque entrée : jmp vers son talon (hot_stubs + 8 i)")
    check(ok_orig and ok_tab, "chaque original : les instructions déplacées puis jmp entrée + k ; le talon y mène")
    stubs = bytes(uc.mem_read(sy["hot_stubs"], 8 * nd))
    check(all(stubs[8 * i:8 * i + 8] == b"\x2f\x39" + (sy["hot_tab"] + 4 * i).to_bytes(4, "big") + b"\x4e\x75"
              for i in range(nd)), "talons : move.l hot_tab + 4 i, -(sp) ; rts")
    check(r.u32("hot_booted") == 0x484f5421 and r.u8("hot_state") == 0, "chargeur lancé, rien de chargé")


# --- 2. son ---------------------------------------------------------------------------------------------------------
SCENES = [
    ("6 machines d'origine", (0, 1, 2, 3, 4, 5), None, every(6, range(6), 70), 70),
    ("MACRO, ACID, MODAL", (12, 13, 14, 12, 14, 14), {0: dict(shape=0), 3: dict(shape=25), 4: dict(shape=1),
                                                       5: dict(shape=2)}, every(6, range(6), 70), 70),
    ("5 moteurs du Syntakt et le Sampler", (7, 8, 9, 10, 11, 6), None, every(6, range(6), 60), 60),
    ("projet mêlé", (0, 1, 7, 12, 13, 5), {3: dict(shape=20)}, every(5, range(6), 60), 60),
]


def changes():
    """Projet d'origine, puis le Syntakt arrive (piste 2, SDVtg ; son code doit revenir), puis repart, puis MODAL,
    SY BITS (sa table) et SY SWARM ; trigs des pistes qui changent loin du changement."""
    ev = {k: [("trig", [0, 1, 3, 4, 5])] for k in range(2, 170, 6)}
    for k, t, m in ((30, 2, 7), (75, 2, 2), (100, 4, 14), (120, 2, 10), (145, 5, 11)):
        ev.setdefault(k, []).append(("machine", t, m))
        ev.setdefault(k + 22, []).append(("trig", [t]))
    return ev


def sound_test(fw, quick):
    print("2. son : chargeur inerte contre chargeur lancé")
    scenes = SCENES[:2] if quick else SCENES
    for name, mach, knobs, ev, n in scenes:
        a, _ = play(fw, False, mach, ev, n, knobs)
        b, r = play(fw, True, mach, ev, n, knobs)
        ok, k, what = same(a, b)
        check(ok and r.u8("hot_state") == 2, f"{name} : {n} blocs identiques, copies actives "
              f"({len(r.b.notes)} copies)" + ("" if ok else f" ; bloc {k} : {what}"))
    if quick:
        return
    seen = []

    def sig(r, k):                              # les machines jouées étaient dans la signature du chargeur
        m = [struct.unpack(">I", r.uc.mem_read(S.VOICE0 + S.VSTRIDE * t, 4))[0] for t in range(6)]
        seen.append((r.u32("hot_sig"), functools.reduce(lambda a, x: a | (1 << x if x < 15 else 0), m, 0)))
    a, _ = play(fw, False, (0, 1, 2, 3, 4, 5), changes(), 170)
    b, r = play(fw, True, (0, 1, 2, 3, 4, 5), changes(), 170, each=sig)
    ok, k, what = same(a, b)
    check(ok, "changements de machine (le Syntakt arrive, repart ; MODAL, SY BITS, SY SWARM) : 170 blocs identiques"
          + ("" if ok else f" ; bloc {k} : {what}"))
    check(all(not v & ~s for s, v in seen), "chaque machine jouée était dans la signature du chargeur (paramètre "
          "MACHINE et machine de la note en cours)")


# --- 3. pause des moteurs du Syntakt ------------------------------------------------------------------------------
def pause_test(fw):
    print("3. pause des moteurs du Syntakt pendant que leur code revient")
    log = []

    def watch(r, k):
        log.append((r.u32("st_away") >> 7 & 1, r.u8("hot_state")))
    ev = {k: [("trig", [0, 1, 3])] for k in range(2, 120, 6)}
    ev[40] = [("machine", 2, 7)]                 # SDVtg : son code a été recouvert, il revient
    for k in range(41, 120, 3):
        ev.setdefault(k, []).append(("trig", [2]))
    outs, r = play(fw, True, (0, 1, 2, 3, 4, 5), ev, 120, each=watch)
    v2 = [np.frombuffer(o[0], ">i4").reshape(6, 32)[2] for o in outs]
    away = [k for k, (a, _) in enumerate(log) if a and k >= 40]
    check(away and away[0] == 40 and away == list(range(40, away[-1] + 1)) and log[39][0],
          f"SD VINTAGE en pause tant que son code n'est pas revenu : jusqu'au bloc {away[-1] if away else '?'} "
          f"({len(away)} blocs après le choix de la machine, 2 Ko recopiés par bloc)")
    check(all(not v2[k].any() for k in away), "piste 2 muette pendant la pause, malgré ses trigs")
    after = [k for k in range(away[-1] + 1, 120) if v2[k].any()] if away else []
    check(bool(after) and log[-1][1] == 2, f"puis elle joue (dès le bloc {after[0] if after else '?'}), copies actives")
    st = r.b.syms
    regs = struct.unpack(">3H", r.uc.mem_read(st["hot_n"], 6))[2]
    rg = [struct.unpack(">IIIHH", bytes(r.uc.mem_read(st["hot_regs"] + 16 * i, 16))) for i in range(regs)]
    lo, hi, src = rg[0][:3]
    check(bytes(r.uc.mem_read(lo, hi - lo)) == bytes(r.uc.mem_read(src, hi - lo)),
          f"code du Syntakt rendu octet pour octet ({lo:#x}..{hi:#x}, depuis la zone de transit {src:#x})")
    return rg


# --- 4. place -------------------------------------------------------------------------------------------------------
def place_test(fw, rg):
    print("4. place : zone de transit, fins de SRAM")
    tails = [(lo, hi) for lo, hi, src, need, _ in rg if not need]
    transit = [(src, src + hi - lo) for lo, hi, src, need, _ in rg if need]
    r = Run(fw, True, (0, 1, 7, 12, 14, 5))
    t0 = [bytes(r.uc.mem_read(a, b - a)) for a, b in transit]
    hc = (r.sy["hot_code"], r.sy["hot_code_end"])
    bad = []

    def wr(uc, access, addr, size, value, ud):
        pc = uc.reg_read(mk.UC_M68K_REG_PC)
        if not hc[0] <= pc < hc[1]:
            bad.append((hex(pc), hex(addr)))
    for lo, hi in tails:
        r.uc.hook_add(UC_HOOK_MEM_WRITE, wr, begin=lo, end=hi - 1)
    for k in range(80):
        if k % 6 == 2:
            r.trig(range(6))
        if k == 40:
            r.machine(2, 2)                     # le Syntakt part : sa place sert
        r.block()
    t1 = [bytes(r.uc.mem_read(a, b - a)) for a, b in transit]
    check(t0 == t1, "zone de transit intacte (source du code et des tables du Syntakt rendus)")
    used = sum(1 for lo, hi in r.b.notes if any(a <= lo < b for a, b in tails))
    check(not bad and used, f"fins de SRAM : seul le chargeur y écrit ({used} copies) " + (str(bad[:3]) if bad else ""))


# --- 5. modèle du cache d'instructions ------------------------------------------------------------------------------
def cache_test(fw, quick):
    print("5. défauts du cache d'instructions par bloc (modèle, inventory_code.ICache : 8 Ko, 4 voies, lignes de "
          "16 o ; le code en SRAM y passe aussi, ses lignes absentes lues par la porte arrière de la SRAM)")
    for name, mach, knobs, ev, n in (SCENES[:2] if quick else SCENES):
        res, ins = [], []
        for hot in (False, True):
            _, r = play(fw, hot, mach, ev, 46, knobs, trace=True)
            rr = r.res[30:]                                          # copies en place
            res.append(I.misses(rr, split=True)[1])                  # cache gardé d'un bloc à l'autre
            ins.append(sum(d["instr"] for x in rr for k, d in x.items() if not k.startswith("_")) / len(rr))
        (d0, s0), (d1, s1) = res
        check(d1 < d0, f"{name} : lignes lues en SDRAM {d0:.0f} -> {d1:.0f}, en SRAM {s0:.0f} -> {s1:.0f} ; "
              f"instructions {ins[0]:.0f} -> {ins[1]:.0f} ({ins[1] - ins[0]:+.0f} : chargeur, talons)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True)
    ap.add_argument("--syntakt", required=True)
    ap.add_argument("--quick", action="store_true")
    args = ap.parse_args()
    fw = firmware(args.cycles, args.syntakt)
    boot_test(fw)
    sound_test(fw, args.quick)
    rg = pause_test(fw)
    place_test(fw, rg)
    cache_test(fw, args.quick)
    print("\nTOUT OK" if not FAILS else f"\n{len(FAILS)} ÉCHEC(S)")
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
