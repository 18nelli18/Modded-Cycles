#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Preuve Unicorn du prototype autonome Performance15 (notes/58).

Execute les instructions natives de repartition des touches, le constructeur
KeyEvent, l'activation IRQ et les encodeurs/decodage des kits. Les services UI,
le tas et la sortie du lissage audio sont interceptes, pas le code des macros.
Aucun test ne simule les voix DSP, le MMC physique ni les combinaisons de mods.
  python3 tools/emu/test_performance15.py --cycles firmware/model-cycles_OS1.13.syx
"""
import argparse
import json
import pathlib
import struct
import sys
from unicorn import Uc, UC_ARCH_M68K, UC_MODE_BIG_ENDIAN, UC_HOOK_CODE
from unicorn import m68k_const as mk

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import gen_performance15 as gen

BASE = 0x40000400
PATTERN, KIT, KIT_BYTES = 0x406fa040, 0x409c9c80, 0x1bb6
ROOT, LISTENER, EVENT, VIEW, UI, MANAGER = 0x44600000, 0x44601000, 0x44101000, 0x44300000, 0x44200000, 0x44880000
STACK, STOP, HEAP = 0x45001000, 0x44000000, 0x41800000


class Rig:
    def __init__(self, image, payload, symbols):
        self.uc = u = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
        u.ctl_set_cpu_model(mk.UC_CPU_M68K_ANY)
        u.reg_write(mk.UC_M68K_REG_SR, 0x2700)
        for address, size in [(0x40000000, 0x03000000), (0x44000000, 0x02000000), (0x80000000, 0x20000)]:
            u.mem_map(address, size)
        u.mem_write(BASE, image)
        u.mem_write(gen.RUNTIME, payload)
        self.s = {k: int(v, 16) for k, v in symbols.items()}
        self.listeners = self.dispatches = self.notices = self.keys = 0
        self.descriptor = 42
        self.smooth = None
        self.stubs = {
            0x4007faf4: lambda a: int(bool(self.keys & (1 << a[0]))),
            0x400cf9a8: lambda a: UI,
            0x400cf866: lambda a: MANAGER,
            0x40076082: lambda a: 0,
            0x40090f48: lambda a: 0,
            0x4005481a: lambda a: 0,
            0x4001e814: lambda a: self.descriptor,
            0x40080064: self.allocate,
            0x400d1f98: self.notice,
            0x4008f1f0: self.copy,
            0x40077720: self.dispatch,
            0x44004000: self.listener,
            0x40058474: self.smoothing,
        }
        u.hook_add(UC_HOOK_CODE, self.step)
        self.w(ROOT + 0x94, LISTENER)
        self.w(ROOT + 0x98, LISTENER + 16)
        self.w(LISTENER + 8, 1)
        self.w(LISTENER + 12, 0x44004000)
        self.w(0x406fa02c, 123)
        for i in range(2):
            self.w(PATTERN + i * 0x77f6 + 0x77f2, i)
        self.w(0x40a7887c, PATTERN)
        self.w(0x40a78888, KIT)
        self.w(self.s['per_main_view'], VIEW)
        for track in range(7):
            for slot in range(33):
                u.mem_write(0x800015ae + track * 66 + slot * 2, struct.pack('>H', 0x4000 if slot == 10 else 0x2000))

    def w(self, address, value):
        self.uc.mem_write(address, struct.pack('>I', value & 0xffffffff))

    def r(self, address):
        return struct.unpack('>I', self.uc.mem_read(address, 4))[0]

    def state(self, name):
        return self.r(self.s[name])

    def ret(self, result):
        u = self.uc
        sp = u.reg_read(mk.UC_M68K_REG_A7)
        u.reg_write(mk.UC_M68K_REG_D0, result & 0xffffffff)
        u.reg_write(mk.UC_M68K_REG_PC, self.r(sp))
        u.reg_write(mk.UC_M68K_REG_A7, sp + 4)

    def step(self, u, address, size, _):
        if address in self.stubs:
            sp = u.reg_read(mk.UC_M68K_REG_A7)
            args = struct.unpack('>5I', u.mem_read(sp + 4, 20))
            self.ret(self.stubs[address](args))

    def allocate(self, a):
        if a[0] == 53696:
            return HEAP
        if a[0] == 50304:
            return HEAP + 0x20000
        raise AssertionError('allocation non prevue : %d' % a[0])

    def notice(self, a):
        assert a[0] == MANAGER + 0x74 and a[1] < 96
        self.notices += 1
        return 0

    def copy(self, a):
        assert a[2] <= 0x10000
        self.uc.mem_write(a[0], bytes(self.uc.mem_read(a[1], a[2])))
        return a[0]

    def listener(self, a):
        assert a[0] == LISTENER and a[1] == EVENT
        self.listeners += 1
        return 0

    def dispatch(self, a):
        self.dispatches += 1
        return 0

    def smoothing(self, a):
        self.smooth = bytes(self.uc.mem_read(a[0], 476))
        return 0x8000100c

    def call(self, function, *args):
        address = self.s[function] if isinstance(function, str) else function
        self.uc.mem_write(STACK, struct.pack('>I' + 'I' * len(args), STOP, *args))
        self.uc.reg_write(mk.UC_M68K_REG_A7, STACK)
        self.uc.emu_start(address, STOP, count=5_000_000)
        assert self.uc.reg_read(mk.UC_M68K_REG_PC) == STOP, hex(self.uc.reg_read(mk.UC_M68K_REG_PC))
        assert self.uc.reg_read(mk.UC_M68K_REG_A7) == STACK + 4
        return self.uc.reg_read(mk.UC_M68K_REG_D0)

    def key(self, code, flags):
        self.call(0x4007238c, EVENT, code, flags, 0x7f, 0)
        self.call(0x400060fe, ROOT, EVENT)

    def gesture(self, code):
        for flags in (3, 11, 2, 18):
            self.key(code, flags)

    def turn(self, descriptor, delta):
        self.descriptor = descriptor
        self.w(EVENT + 12, 2)
        self.w(EVENT + 16, delta)
        self.w(EVENT + 20, 0)
        self.call(0x4001f4f0, VIEW, EVENT)

    def amount(self, index):
        return self.r(self.s['per_amounts'] + index * 4)

    def irq(self, index):
        self.uc.reg_write(mk.UC_M68K_REG_A0, PATTERN + index * 0x77f6)
        self.uc.reg_write(mk.UC_M68K_REG_D0, KIT + index * KIT_BYTES)
        self.uc.reg_write(mk.UC_M68K_REG_A1, 0x40a78888)
        self.uc.emu_start(0x40054d56, 0x40054d76, count=1_000_000)
        assert self.uc.reg_read(mk.UC_M68K_REG_PC) == 0x40054d76

    def audio(self):
        self.w(STACK, 0x800015a0)
        self.uc.reg_write(mk.UC_M68K_REG_A7, STACK)
        self.uc.emu_start(0x400597a8, 0x400597ae, count=1_000_000)
        assert self.uc.reg_read(mk.UC_M68K_REG_PC) == 0x400597ae
        return self.smooth


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--cycles', required=True)
    args = ap.parse_args()
    stock, patched, manifest = gen.compile_mode(args.cycles)
    payload = (gen.ROOT / 'build/performance15/payload.bin').read_bytes()
    old, rig = [Rig(image, payload, manifest['symbols']) for image in (stock, patched)]
    checks = 0

    def check(condition, text):
        nonlocal checks
        assert condition, text
        checks += 1
        print('ok', text)

    # Vraie entree de demarrage : copie SRAM native, puis charge utile ajoutee.
    for r in (old, rig):
        r.uc.mem_write(gen.RUNTIME, bytes(len(payload)))
        r.call(0x4000045c)
    check(bytes(rig.uc.mem_read(gen.RUNTIME, len(payload))) == payload,
          'vrai crochet de demarrage : charge utile copiee et pile restauree')
    check(bytes(old.uc.mem_read(gen.RUNTIME, len(payload))) == bytes(len(payload)),
          'demarrage d origine : aucune charge utile Performance')
    for r in (old, rig):
        r.w(r.s['per_main_view'], VIEW)
        for track in range(7):
            for slot in range(33):
                r.uc.mem_write(0x800015ae + track * 66 + slot * 2,
                               struct.pack('>H', 0x4000 if slot == 10 else 0x2000))
    # Comparaison de la vraie boucle native, sans detournement des touches ordinaires.
    for r in (old, rig):
        r.key(10, 1)
        r.key(10, 0)
    check(old.listeners == rig.listeners == old.dispatches == rig.dispatches == 2,
          'transport ordinaire : boucle native identique, origine et prototype')
    rig.call('per_storage_initialize')
    rig.call('per_storage_observe')
    rig.w(rig.s['per_mode'], 2)
    rig.w(rig.s['per_selected'], 0)
    rig.turn(47, 12)
    rig.turn(42, 1)
    rig.turn(24, 6)
    rig.turn(46, 3)
    rig.turn(47, -30)
    rig.turn(42, 1)
    rig.turn(24, 1)
    rig.turn(46, 10)
    rig.turn(47, 16)
    # Une identite future doit rester inactive et conservee, sans alias.
    rig.uc.mem_write(rig.s['per_routes'] + 24, struct.pack('>BBBBhH', 0, 255, 0, 1, 1, 0x7fff))
    rig.w(rig.s['per_mode'], 1)
    rig.turn(42, 127)
    check(rig.amount(0) == 127, 'M1 a 127 par le vrai gestionnaire de potard')
    target = rig.audio()
    check(old.audio() != target and target == rig.audio(), 'cible audio modulee et maintenue sans nouveau tour de potard')
    canonical = bytes(rig.uc.mem_read(0x800015a0, 476))
    for mode in (1, 2):
        for selected in range(15):
            rig.w(rig.s['per_mode'], mode)
            rig.w(rig.s['per_selected'], 0)
            rig.gesture(9)
            row = bytes(rig.uc.mem_read(rig.s['per_routes'], 32))
            rig.w(rig.s['per_selected'], selected)
            before = rig.listeners
            rig.gesture(11)
            check(rig.amount(selected) == 127 and bytes(rig.uc.mem_read(rig.s['per_routes'] + selected * 32, 32)) == row,
                  'quatre destinations et montant : mode %d, M%d' % (mode, selected + 1))
            rig.gesture(10)
            check(rig.amount(selected) == 0 and bytes(rig.uc.mem_read(rig.s['per_routes'] + selected * 32, 32)) == bytes(32),
                  'effacement : mode %d, M%d' % (mode, selected + 1))
            rig.gesture(11)
            check(rig.amount(selected) == 127 and rig.listeners == before,
                  'collage repete sans ecouteur natif : mode %d, M%d' % (mode, selected + 1))
    check(bytes(rig.uc.mem_read(0x800015a0, 476)) == canonical, 'sources natives preservees')
    rig.irq(1)
    check(rig.state('per_active_kit') == KIT + KIT_BYTES and rig.amount(0) == 0, 'activation IRQ du vrai bloc natif : A2 neutre')
    rig.irq(0)
    check(rig.amount(0) == 127, 'retour A1 : montant du motif restaure')
    encoded = 0x44700000
    check(rig.call(0x4005b2ae, encoded, KIT, 0) & 255 == 1, 'vrai encodeur de kit avec extension')
    rig.w(rig.s['per_selected'], 0)
    rig.gesture(10)
    rig.call(0x4005d080, KIT, encoded, 0)
    check(rig.amount(0) == 127, 'vrai decodeur de kit : montant restaure')
    rig.w(0x406fa02c, 124)
    rig.call('per_tick', ROOT)
    check(rig.state('per_clip_valid') == 0, 'presse-papiers vide apres changement de projet')
    print('%d verifications ; voix DSP, MMC et combinaisons non emules' % checks)


if __name__ == '__main__':
    main()
