#!/usr/bin/env python3
"""Preuve d'intégration du prototype aux adresses de ses masques réels.

Charge le vrai Model-TG avec le tweak. Allocation, présentation, dessin,
delta encodeur et objet piste simulés. Constructeur/destructeur OS couverts
séparément ; le lecteur de
touches, getter de longueur et setter de notes de l'OS restent exécutés.
La propagation des événements au moteur audio n'est pas encore couverte.
"""
import argparse
import json
import pathlib
import random
import struct
import sys

from unicorn import Uc, UC_ARCH_M68K, UC_MODE_BIG_ENDIAN, UC_HOOK_CODE
from unicorn import m68k_const as mk

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import build
from test_sdvintage import main_os_from_syx

ROOT = HERE.parents[1]
STACK, STOP, EVENT, OBJ, VT, RAW, GET, SIGNAL, HEAP = (
    0x93008000, 0x9300f000, 0x93001000, 0x93000000, 0x93000100,
    0x93002000, 0x9300d000, 0x9300d100, 0x93100000)


class Rig:
    def __init__(self, stock, base, tweak, real_ui=False):
        self.u = u = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
        u.ctl_set_cpu_model(mk.UC_CPU_M68K_ANY)
        u.mem_map(0x40000000, 0x02400000)
        u.mem_map(0x93000000, 0x200000)
        img, _ = build.apply_writes(stock, [base, tweak])
        payload, _ = build.build_payload([base], stock, None)
        u.mem_write(build.BASE, bytes(img) + payload)
        u.reg_write(mk.UC_M68K_REG_SR, 0x2000)
        self.s = {n: int(v, 16) for n, v in tweak["symbols"].items()}
        self.heap, self.new_count, self.fail_new, self.present = HEAP, 0, 0, []
        self.free, self.rects, self.texts, self.signals = [], [], [], []
        self.delta = 0
        self.track = OBJ
        self.stubs = {
            0x400802e0: self.new,
            0x400a22b0: lambda a: self.construct(a),
            0x400d0974: lambda a: 0x93005000,
            0x400060d8: lambda a: 0x93005000,
            0x4007700e: self.show,
            0x400cf23c: lambda a: 0,
            0x400f4486: lambda a: self.free.append(a[0]) or 0,
            0x400f43ca: lambda a: 0,
            0x40076082: lambda a: 0,
            0x400cf866: lambda a: 0x93005000,
            0x4000f23e: lambda a: self.track,
            0x4006f73a: lambda a: self.delta,
            0x40070dea: lambda a: self.rects.append(a[:6]) or 0,
            0x40071a04: self.draw_text,
            SIGNAL: self.signal,
        }
        if real_ui:
            for addr in (0x400a22b0, 0x400f4486, 0x400f43ca):
                del self.stubs[addr]
            self.stubs[0x400802ec] = lambda a: self.free.append(a[0]) or 0
        for addr in self.stubs:
            u.hook_add(UC_HOOK_CODE, self.stub, begin=addr, end=addr)
        self.w32(0x40fe4178, 1)
        self.w32(OBJ, VT)
        self.w32(VT + 40, GET)
        self.w32(VT + 16, SIGNAL)
        u.mem_write(GET, b"\x20\x3c" + struct.pack(">I", RAW) + b"\x4e\x75")
        rng = random.Random(55)
        raw = bytearray(rng.getrandbits(8) for _ in range(722))
        raw[580:644] = bytes([255] * 64)
        raw[713:715] = struct.pack(">H", 16)
        u.mem_write(RAW, bytes(raw))
        self.original = bytes(raw)

    def w32(self, addr, value):
        self.u.mem_write(addr, struct.pack(">I", value & 0xffffffff))

    def r32(self, addr):
        return struct.unpack(">I", self.u.mem_read(addr, 4))[0]

    def stub(self, u, addr, size, data):
        sp = u.reg_read(mk.UC_M68K_REG_A7)
        args = struct.unpack(">8I", u.mem_read(sp + 4, 32))
        result = self.stubs[addr](args)
        u.reg_write(mk.UC_M68K_REG_D0, (result or 0) & 0xffffffff)
        u.reg_write(mk.UC_M68K_REG_PC, self.r32(sp))
        u.reg_write(mk.UC_M68K_REG_A7, sp + 4)

    def new(self, args):
        self.new_count += 1
        if self.new_count == self.fail_new:
            return 0
        addr, self.heap = self.heap, self.heap + ((args[0] + 15) & ~15)
        self.u.mem_write(addr, b"\xa5" * args[0])
        return addr

    def construct(self, args):
        self.u.mem_write(args[0], bytes(208))
        return args[0]

    def show(self, args):
        self.present.append((self.r32(args[1]), self.r32(args[1] + 4)))
        return 0

    def string(self, addr):
        data = bytearray()
        while True:
            b = self.u.mem_read(addr + len(data), 1)[0]
            if not b:
                return data.decode("ascii")
            data.append(b)
            assert len(data) < 100

    def draw_text(self, args):
        ctx, font, x, y, flags, fmt, value, _ = args
        assert 0 <= x <= 127 and 0 <= y <= 55
        f = self.string(fmt)
        self.texts.append((x, y, self.string(value) if f == "%s" else str(value)))
        return 0

    def signal(self, args):
        assert args[0] == OBJ and self.r32(args[1]) == 0x400ff59c
        self.signals.append(self.r32(args[1] + 4))
        return 0

    def call(self, name, *args):
        fn = self.s[name] if isinstance(name, str) else name
        self.u.mem_write(STACK, struct.pack(">" + "I" * (len(args) + 1), STOP, *args))
        self.u.reg_write(mk.UC_M68K_REG_A7, STACK)
        self.u.emu_start(fn, STOP, count=500000)
        assert self.u.reg_read(mk.UC_M68K_REG_PC) == STOP, (name, hex(self.u.reg_read(mk.UC_M68K_REG_PC)))
        assert self.u.reg_read(mk.UC_M68K_REG_A7) == STACK + 4, name
        return self.u.reg_read(mk.UC_M68K_REG_D0)

    def event(self, code, flags=1, time=1):
        self.u.mem_write(EVENT, struct.pack(">6I", 0, 0, time, code, flags, 127))
        return EVENT

    def knob(self, delta):
        self.delta = delta
        self.event(1)
        self.call("sg_enc", self.r32(self.s["sg_obj"]), EVENT)

    def click(self):
        self.event(32, 16)
        self.call("sg_menu_key", self.r32(self.s["sg_obj"]), EVENT)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cycles", required=True)
    ap.add_argument("--scroll", action="store_true", default=True)
    args = ap.parse_args()
    stock = main_os_from_syx(args.cycles)
    folder = ""
    for variant, dep in (("scale-gen", "model-tg"), ("scale-gen-st", "model-tg-st")):
        base = json.loads((ROOT / f"tweaks/model-cycles_OS1.13/30-{dep}.json").read_text())
        tweak = json.loads((ROOT / f"tweaks/model-cycles_OS1.13/{folder}49-{variant}.json").read_text())
        r = Rig(stock, base, tweak)
        r.call(0x4007240c, r.event(13, 1, 1))
        assert r.call(0x4007240c, r.event(15, 1, 2)) == 0
        obj = r.r32(r.s["sg_obj"])
        assert obj and len(r.present) == 1
        assert r.r32(obj) == r.s["sg_vt"] + 8
        assert r.r32(obj + 4) == r.s["sg_vt"] + 0x58
        r.call(0x4007240c, r.event(15, 16, 3))
        r.call(0x4007240c, r.event(13, 16, 4))
        r.call("sg_render", obj, 0x93006000)
        labels = ["Scale", "Root", "Low note", "High note", "Density %", "Rand velocity", "Rand decay", "Rand pan", "Generate", "Undo"]
        assert len(r.texts) == (8 if args.scroll else 13), r.texts
        assert [t[2] for t in r.texts if t[0] == 2] == labels[:4 if args.scroll else 7]
        if args.scroll:
            for row in range(10):
                for editing in (0, 1):
                    r.w32(r.s["sg_row"], row)
                    r.w32(r.s["sg_edit"], editing)
                    r.u.reg_write(mk.UC_M68K_REG_D5, 0x12345678)
                    r.texts.clear(); r.rects.clear()
                    r.call("sg_render", obj, 0x93006000)
                    assert r.u.reg_read(mk.UC_M68K_REG_D5) == 0x12345678
                    first = min(6, max(0, row - 2))
                    shown = [t for t in r.texts if t[0] == 2]
                    assert [t[2] for t in shown] == labels[first:first + 4]
                    assert [t[1] for t in shown] == [49, 34, 19, 4]
                    assert all(4 <= t[1] <= 49 for t in r.texts)
                    ctx, x, bottom, right, top, color = r.rects[-1]
                    assert (x, right, color) == (64 if editing else 0, 127, 0xffffffff)
                    assert top == 62 - 15 * (row - first) and bottom == top - 13
                    assert 4 <= bottom < top <= 62
            r.w32(r.s["sg_row"], 0); r.w32(r.s["sg_edit"], 0)
            print(f"ok : {variant}, quatre lignes, dix sélections, édition, marges et registre D5 conservé")
        r.knob(1)
        assert r.r32(r.s["sg_row"]) == 1
        r.knob(-1)
        assert r.r32(r.s["sg_row"]) == 0
        r.click()
        assert r.r32(r.s["sg_edit"]) == 1
        r.knob(1)
        r.click()
        for _ in range(8):
            r.knob(1)
        assert r.r32(r.s["sg_row"]) == 8
        r.click()
        generated = bytes(r.u.mem_read(RAW, 722))
        assert generated != r.original
        assert r.r32(r.s["sg_undo_valid"]) == 1
        assert r.signals == list(range(16))
        for step in range(16):
            flags = struct.unpack_from(">H", generated, step * 2)[0]
            if flags & 1:
                assert generated[580 + step] % 12 in (0, 2, 4, 5, 7, 9, 11)
        r.knob(1)
        r.click()
        assert bytes(r.u.mem_read(RAW, 722)) == r.original
        assert r.r32(r.s["sg_undo_valid"]) == 0
        r.w32(0x40a78874, 1)
        r.knob(-1)
        before_seed = r.r32(r.s["sg_config"] + 24)
        r.click()
        assert bytes(r.u.mem_read(RAW, 722)) == r.original
        assert r.r32(r.s["sg_config"] + 24) == before_seed
        assert r.r32(r.s["sg_error"]) == 1
        r.w32(0x40a78874, 0)
        r.call("sg_dtor0", obj)
        assert r.r32(r.s["sg_obj"]) == 0
        r.call("sg_open")
        assert r.r32(r.s["sg_obj"]) and r.r32(r.s["sg_row"]) == 0
        assert r.r32(r.s["sg_undo_valid"]) == 0
        print(f"ok : {variant}, ouverture par vrai lecteur Model-TG, vtables, rendu, options, encodeur +/- et clic, Generate/Undo, transport, réouverture")
        # Bornes réelles des champs : la rotation ne déborde jamais.
        for row, offset, value, lo, hi in ((2, 8, 48, 0, 72),
                                          (3, 12, 72, 48, 127),
                                          (4, 4, 50, 0, 100)):
            b = Rig(stock, base, tweak)
            b.call("sg_open")
            b.w32(b.s["sg_row"], row)
            b.click()
            for _ in range(140):
                b.knob(-1)
            assert b.r32(b.s["sg_config"] + offset) == lo
            for _ in range(140):
                b.knob(1)
            assert b.r32(b.s["sg_config"] + offset) == hi
        r = Rig(stock, base, tweak)
        r.call("sg_open")
        r.call("sg_action_generate")
        changed = bytes(r.u.mem_read(RAW, 722))
        r.track = OBJ + 0x80
        r.call("sg_action_undo")
        assert bytes(r.u.mem_read(RAW, 722)) == changed
        r.track = OBJ
        r.call("sg_action_undo")
        assert bytes(r.u.mem_read(RAW, 722)) == r.original
        print(f"ok : {variant}, bornes notes/densité et Undo refusé sur une autre piste")
        r = Rig(stock, base, tweak, real_ui=True)
        for _ in range(2):
            r.call("sg_open")
            page = r.r32(r.s["sg_obj"])
            assert page and r.r32(page) == r.s["sg_vt"] + 8
            assert r.r32(page + 104) and r.r32(page + 108)
            r.call("sg_render", page, 0x93006000)
            r.call("sg_dtor1", page)
            assert r.r32(r.s["sg_obj"]) == 0 and page in r.free
        print(f"ok : {variant}, vrais constructeur/destructeur OS, observateurs et fermetures initialisés, destruction puis réouverture")
        for fail in (1, 2):
            r = Rig(stock, base, tweak)
            r.fail_new = fail
            r.call("sg_open")
            assert r.r32(r.s["sg_obj"]) == 0 and not r.present
            assert len(r.free) == (fail == 2)
        print(f"ok : {variant}, allocation page/holder refusée sans page pendante")
    print("Limite : allocation, affichage et présentation simulés ; démarrage complet et rendu audio non couverts.")


if __name__ == "__main__":
    main()
