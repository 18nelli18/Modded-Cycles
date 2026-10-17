#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Preuve stock/modifié des raccourcis d'octave (notes/73), environ 10 secondes.

Exécute les callbacks KeyboardView et TrackSelectionView de l'OS, le getter des
modificateurs, le getter/setter KBT, l'affichage KBT de Track Setup et les listes
de notes tenues. Intercepte seulement les accès au projet/son, la livraison de
notification, le rendu et l'envoi audio. Les KeyEvent sont reconstruits ; la
lecture physique des touches et la pile complète des vues ne sont pas émulées.

    python3 tools/emu/test_octave_shortcuts.py --cycles model-cycles_OS1.13.syx \
        [--with 6ch-usbup,syntakt-sd-cp-toy-bits-swarm,arp,trig-hold,tempo-max \
         --syntakt Syntakt_OS1.42.syx]
"""
import argparse
import itertools
import json
import pathlib
import struct
import sys
from unicorn import Uc, UC_ARCH_M68K, UC_MODE_BIG_ENDIAN, UC_HOOK_CODE, UC_HOOK_MEM_UNMAPPED
from unicorn import m68k_const as mk

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import build
import gen_octave_shortcuts as gen
import sprites

BASE = build.BASE
STOP, STACK = 0x9f000000, 0x9e000000
VIEW, EVT, UI, SOUND, VT, RAW, RECORDS = (0x93000000 + 0x1000 * i for i in range(7))
GET, NOTIFY = 0x93008000, 0x93008020
REGS = [getattr(mk, "UC_M68K_REG_" + n) for n in
        ("D2", "D3", "D4", "D5", "D6", "D7", "A2", "A3", "A4", "A5", "A6")]


def u32(v):
    return struct.pack(">I", v & 0xffffffff)


class Rig:
    """Le code de l'OS avec six sons indépendants, une vue clavier et ses notes."""
    def __init__(self, image):
        self.uc = uc = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
        uc.ctl_set_cpu_model(mk.UC_CPU_M68K_ANY)
        uc.reg_write(mk.UC_M68K_REG_SR, 0x2700)
        uc.mem_map(0x40000000, 0x08000000)
        uc.mem_map(0x80000000, 0x00020000)
        uc.mem_map(0x90000000, 0x10000000)
        uc.mem_write(BASE, image)
        uc.mem_write(STOP, b"\x4e\x71")
        for t in range(6):
            self.w32(SOUND + t * 0x100, VT)
        self.w32(VT + 40, GET)
        self.w32(VT + 16, NOTIFY)
        self.w32(0x9300c000, VT)
        uc.hook_add(UC_HOOK_MEM_UNMAPPED, lambda u, access, addr, size, value, data:
                    print(f"Accès non mappé {addr:#x}, PC={u.reg_read(mk.UC_M68K_REG_PC):#x}", flush=True) or False)
        self.calls = self.checks = 0
        self.track = 0
        self.stubs = {
            0x400cf9a8: lambda a: UI,
            0x400cf866: lambda a: 0x93009000,
            0x4000f23e: lambda a: SOUND + self.track * 0x100,
            GET: lambda a: RAW + ((a[0] - SOUND) // 0x100) * 0x400,
            NOTIFY: self.notify,
            0x4000eb90: lambda a: 0x9300a000,
            0x40012442: lambda a: self.track,
            0x4000f208: lambda a: 0x9300b000,
            0x4000cfcc: lambda a: 0x9300c000,
            0x40015ac4: lambda a: 100,
            0x4000d0dc: lambda a: 0x9300d000,
            0x4000ccc0: lambda a: 0,
            0x40016086: lambda a: 0,
            0x400802e0: lambda a: 0x93010000,
            0x40019e7a: lambda a: self.played.append(a[2]) or 0,
            0x40019c84: lambda a: self.released.append(a[2]) or 0,
            0x4008f1f0: self.copy,
            0x40071a04: self.render,
        }
        for addr, fn in self.stubs.items():
            uc.hook_add(UC_HOOK_CODE, self.stub(fn), begin=addr, end=addr)
        self.reset()

    def w32(self, a, v):
        self.uc.mem_write(a, u32(v))

    def r32(self, a):
        return struct.unpack(">I", self.uc.mem_read(a, 4))[0]

    def assert_(self, ok, why):
        self.checks += 1
        if not ok:
            raise AssertionError(why)

    def stub(self, fn):
        def callback(uc, address, size, data):
            sp = uc.reg_read(mk.UC_M68K_REG_A7)
            args = struct.unpack(">8I", uc.mem_read(sp + 4, 32))
            value = fn(args)
            uc.reg_write(mk.UC_M68K_REG_D0, (value or 0) & 0xffffffff)
            uc.reg_write(mk.UC_M68K_REG_PC, self.r32(sp))
            uc.reg_write(mk.UC_M68K_REG_A7, sp + 4)
        return callback

    def notify(self, args):
        self.assert_(args[0] == SOUND + self.track * 0x100, "récepteur du setter")
        self.assert_(self.r32(args[1]) == 0x400ff5ac, "notification KBT stock")
        self.notifications += 1
        return 0

    def copy(self, args):
        self.uc.mem_write(args[0], bytes(self.uc.mem_read(args[1], args[2])))
        return args[0]

    def render(self, args):
        self.assert_(args[5] == 0x40127767, "format KBT du menu")
        self.rendered = args[7] - (1 << 32) if args[7] & 0x80000000 else args[7]
        return 0

    def reset(self, kbt=0, grid=False, blocked=False, live=False, track=0):
        self.track = track
        self.uc.mem_write(UI, bytes(0x200))
        self.uc.mem_write(UI + 0x165, bytes([int(grid), int(grid), int(live)]))
        self.uc.mem_write(UI + 0x185, bytes([int(blocked)]))
        self.uc.mem_write(RAW, bytes(0x1800))
        for t in range(6):
            self.uc.mem_write(RAW + t * 0x400 + 0x2d1, bytes([(kbt if t == track else 3 * t) & 255]))
        self.w32(VIEW + 0x94, RECORDS)
        self.w32(VIEW + 0x98, RECORDS)
        self.w32(VIEW + 0x9c, RECORDS + 0x1000)
        self.notifications = 0
        self.rendered = None
        self.played, self.released = [], []
        self.held = set()

    def key_state(self):
        raw = bytearray(4)
        for code in self.held:
            physical = self.r32(0x4010ae5c + 4 * code)
            raw[physical >> 3] |= 1 << (physical & 7)
        self.uc.mem_write(0x40f95744, bytes(raw))

    def call(self, addr, *args):
        uc = self.uc
        self.calls += 1
        self.key_state()
        uc.mem_write(STACK, u32(STOP) + b"".join(u32(a) for a in args))
        uc.reg_write(mk.UC_M68K_REG_A7, STACK)
        for i, r in enumerate(REGS):
            uc.reg_write(r, 0x11220000 + i)
        uc.emu_start(addr, STOP, count=20000)
        self.assert_(uc.reg_read(mk.UC_M68K_REG_PC) == STOP, "sortie de la routine")
        self.assert_(uc.reg_read(mk.UC_M68K_REG_A7) == STACK + 4, "pile équilibrée")
        self.assert_(all(uc.reg_read(r) == 0x11220000 + i for i, r in enumerate(REGS)), "ABI")
        return uc.reg_read(mk.UC_M68K_REG_D0) & 255

    def event(self, key, flags):
        self.w32(EVT + 12, key)
        self.w32(EVT + 16, flags)
        return self.call(self.r32(gen.HOOK), VIEW, EVT)

    def kbt(self, track=None):
        t = self.track if track is None else track
        return struct.unpack("b", self.uc.mem_read(RAW + t * 0x400 + 0x2d1, 1))[0]

    def snapshot(self):
        return (bytes(self.uc.mem_read(RAW, 0x1800)), self.notifications, self.played[:], self.released[:],
                bytes(self.uc.mem_read(RECORDS, self.r32(VIEW + 0x98) - RECORDS)))


def proof(stock_image, patched_image):
    a, b = Rig(stock_image), Rig(patched_image)
    for k, key, live in itertools.product(range(-60, 61), (30, 31), (False, True)):
        for rig in (a, b):
            rig.reset(k, live=live)
            rig.held = {2}
            rig.w32(EVT + 12, key)
            rig.w32(EVT + 16, 1)
            rig.assert_(rig.call(0x40024078, VIEW, EVT) == 0, "TrackSelectionView laisse passer le TRIG")
            rig.event(key, 1)
        expected = max(-60, min(60, k + (-12 if key == 30 else 12)))
        b.assert_(a.kbt() == k and a.notifications == 0, "KBT stock inchangé")
        b.assert_(b.kbt() == expected and b.notifications == 1, "KBT modifié via setter")
        b.assert_(not b.played and b.r32(VIEW + 0x98) == RECORDS, "aucune note du raccourci")
        b.call(0x4003e3b6, VIEW, 0)
        b.assert_(b.rendered == expected, "Track Setup affiche immédiatement KBT")
        b.event(key, 9)
        b.assert_(b.kbt() == expected and b.notifications == 1, "aucune répétition au maintien")
        b.held.clear()
        b.event(key, 0)
        b.assert_(not b.played and not b.released, "relâchement inoffensif")
    print("  ok    −60…+60, deux directions, clavier/live rec, limites, affichage et maintien")
    for key, flags, held, grid, blocked in itertools.product(
            range(16, 32), (0, 1, 9), (set(), {1}, {2, 1}, {2, 3}, {2, 4}, {2}), (False, True), (False, True)):
        combo = key in (30, 31) and held == {2} and flags & 1 and not grid and not blocked
        if combo:
            continue
        for rig in (a, b):
            rig.reset(0, grid, blocked)
            rig.held = held
        ra, rb = a.event(key, flags), b.event(key, flags)
        b.assert_(ra == rb and a.snapshot() == b.snapshot(), "événements hors raccourci identiques")
    print("  ok    tous les TRIG, modificateurs, mode grille et clavier désactivé : identiques au stock")
    for track in range(6):
        b.reset(5, track=track)
        before = [b.kbt(t) for t in range(6)]
        b.held = {2}
        b.event(31, 1)
        b.assert_(all(b.kbt(t) == (17 if t == track else before[t]) for t in range(6)), "seule la piste active change")
    print("  ok    six pistes : KBT indépendant, décalage par demi-tons conservé")
    for rig in (a, b):
        rig.reset()
        rig.event(23, 1)
        rig.held = {2}
        rig.event(31, 1)
        rig.event(23, 0)
    b.assert_(a.released == b.released == [59], "note-off du pitch d'origine")
    b.reset(5)
    b.event(30, 1)
    b.held = {2}
    b.event(30, 0)
    b.assert_(b.released == [71] and b.r32(VIEW + 0x98) == RECORDS, "relâchement du TRIG 15 avec TRACK tenu")
    print("  ok    notes déjà tenues : relâchement stock, aucune note bloquée")
    print(f"  ok    {a.calls + b.calls} appels, {a.checks + b.checks} assertions, pile et registres")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True)
    ap.add_argument("--with", dest="others", default="")
    ap.add_argument("--syntakt")
    args = ap.parse_args()
    stock = gen.main_os(args.cycles)
    tweak = gen.build_tweak(stock)
    stored = json.loads(gen.OUT.read_text(encoding="utf-8"))
    assert tweak == stored, "JSON à régénérer"
    by_id = {t["id"]: t for p in gen.OUT.parent.glob("[0-9]*.json")
             for t in [json.loads(p.read_text(encoding="utf-8"))]}
    others = [by_id[i] for i in args.others.split(",") if i]
    for t in others:
        if t["id"] in tweak["conflicts"] or tweak["id"] in t.get("conflicts", []):
            raise ValueError(f"Conflit avec {t['id']}")
    # Chaque octet hors des trois écritures reste celui de l'image de comparaison.
    payload, _ = build.build_payload(others, stock, args.syntakt)
    original = build.apply_writes(stock, sorted(others, key=lambda t: t["order"]))[0] + payload
    patched = build.apply_writes(stock, sorted(others + [tweak], key=lambda t: t["order"]))[0] + payload
    expected = bytearray(original)
    for w in tweak["writes"]:
        expected[w["off"]:w["off"] + len(bytes.fromhex(w["new"]))] = bytes.fromhex(w["new"])
    assert bytes(expected) == patched
    assert len(patched) == len(original)
    assert sprites.redirect_write(gen.MASK) in tweak["writes"]
    print("  ok    générateur reproductible, trois écritures seules, aucun chargeur ajouté")
    print("firmware : " + ", ".join(t["id"] for t in others + [tweak]))
    proof(original, patched)


if __name__ == "__main__":
    main()
