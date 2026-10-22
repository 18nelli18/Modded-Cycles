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
        self.metadata = 0
        self.heap = HEAP + 0x40000
        self.jobs = []
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
            0x400d0f6c: self.modified,
            0x4008026a: lambda a: 0,
            0x400cfb90: lambda a: 0x44890000,
            0x40068d0a: self.enqueue,
            0x4000eae2: lambda a: 123,
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
        assert a[0] <= 32, a[0]
        out = self.heap
        self.heap += 32
        self.uc.mem_write(out, bytes(32))
        return out

    def notice(self, a):
        assert a[0] == MANAGER + 0x74 and a[1] < 96
        self.notices += 1
        return 0

    def modified(self, a):
        assert a[0] == MANAGER + 0x74
        self.metadata += 1
        return 0

    def enqueue(self, a):
        capture = self.r(a[2])
        self.jobs.append((self.r(a[2] + 12), self.r(capture), self.r(capture + 4), self.r(capture + 8)))
        return 1

    def drain(self):
        pending, self.jobs = self.jobs, []
        for callback, model, mirror, index in pending:
            self.w(0x44889000, 0x44889100)
            for i, value in enumerate((model, mirror, index)):
                self.w(0x44889100 + i * 4, value)
            self.call(callback, 0x44889000)

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
    check(rig.state('per_reload_keep') == 0, 'option de rechargement desactivee au demarrage')
    # Rechargement TEMP : seule la copie locale du record est transformee.
    rig.w(0x406fa02c, 123)
    rig.stubs[rig.s['per_temp_save_stock']] = lambda a: 1
    rig.stubs[rig.s['per_temp_reload_stock']] = lambda a: 1
    for m in range(15):
        rig.w(rig.s['per_amounts'] + m * 4, m + 11)
    rig.call('per_storage_edit')
    rig.call('per_temp_save', MANAGER, 1, 0, 1, 1)
    record = 0x44710000
    check(rig.call('per_temp_snapshot', 0, 123, record) == 1, 'record TEMP capture')
    saved = bytes(rig.uc.mem_read(record, 256))
    for enabled in (0, 1):
        rig.w(rig.s['per_reload_keep'], enabled)
        for m in range(15):
            rig.w(rig.s['per_amounts'] + m * 4, 127 - m)
        rig.call('per_temp_reload', MANAGER, 1, 0, 1, 1)
        check(all(rig.amount(m) == (127 - m if enabled and m in (4, 9, 14) else m + 11) for m in range(15)),
              'TEMP selectif M5/M10/M15 : option %d' % enabled)
    rig.call('per_temp_snapshot', 0, 123, record)
    check(bytes(rig.uc.mem_read(record, 256)) == saved, 'record TEMP inchange apres preservation')
    check(rig.state('per_reload_context') == 0, 'contexte TEMP nettoye')
    rig.w(rig.s['per_reload_keep'], 0)
    rig.call('per_temp_reload', MANAGER, 1, 0, 1, 1)
    check(all(rig.amount(m) == m + 11 for m in range(15)), 'retour OFF : les quinze montants TEMP sont restaures')

    # Temoin negatif : vrai ecouteur natif, puis modifications sans cet ecouteur.
    proof = Rig(patched, payload, manifest['symbols'])
    proof.call('per_storage_initialize')
    proof.call('per_storage_observe')
    proof.w(0x800017ec, 0x12345678)
    proof.call(0x4000e25c, 0x44886000, KIT, 0)
    check(proof.r(0x800017ec) == 0, 'ecouteur natif complet : reset audio reproduit')
    model = MANAGER + 0x74
    proof.w(model, 0x400fcf3c)
    proof.w(model + 0x10, KIT)
    proof.w(model + 0x44, 0)
    for offset, vector, mirror in ((0x20, 0x44884000, 0x44b00000), (0x2c, 0x44884010, 0x44c00000)):
        proof.w(model + offset, vector)
        proof.w(model + offset + 4, vector + 4)
        proof.w(vector, mirror)
    proof.w(0x800017ec, 0x12345678)
    for m in range(15):
        proof.w(proof.s['per_mode'], 2)
        proof.w(proof.s['per_selected'], m)
        proof.w(EVENT + 12, 16)
        proof.w(EVENT + 16, 127)
        proof.w(EVENT + 20, 0)
        proof.call(0x40006158, ROOT, EVENT)
        check(proof.amount(m) == 127 and proof.notices == 0 and proof.metadata == m + 1 and proof.r(0x800017ec) == 0x12345678,
              'M%d : modification sans reset du kit audio' % (m + 1))
        check(len(proof.jobs) == 2, 'M%d : deux miroirs natifs planifies' % (m + 1))
        proof.drain()
        a = bytes(proof.uc.mem_read(0x44b01d00, 256))
        b = bytes(proof.uc.mem_read(0x44c01d00, 256))
        proof.uc.mem_write(record, a)
        check(a == b and proof.call('per_record_valid', record) == 1,
              'M%d : vrais encodeurs des deux miroirs, record valide' % (m + 1))
    # Reglages par projet : vrais codecs natifs et zone reservee de 16 octets.
    settings, on, off, native = 0x40a700c0, 0x44720000, 0x44721000, 0x44722000
    rig.call(0x40061676, settings)
    check(rig.state('per_reload_keep') == 0, 'nouveau projet : RLD OFF')
    rig.call('per_settings_encode_stock', native, settings)
    rig.w(rig.s['per_reload_keep'], 1)
    rig.call(0x4005adc6, on, settings)
    check(bytes(rig.uc.mem_read(on, 496)) == bytes(rig.uc.mem_read(native, 496)),
          'reglages natifs identiques avant le record reserve')
    check(rig.r(on + 496) == 0x50524c44 and rig.r(on + 504) == 0x01000001,
          'record RLD ON versionne dans les derniers16 octets')
    rig.w(rig.s['per_reload_keep'], 0)
    rig.call(0x4005adc6, off, settings)
    for choice, encoded in ((1, on), (0, off), (1, on), (0, off)):
        rig.call(0x4005aa8e, settings, encoded)
        check(rig.state('per_reload_keep') == choice, 'projet charge : RLD %d' % choice)
    fresh = Rig(patched, payload, manifest['symbols'])
    fresh.uc.mem_write(on, bytes(rig.uc.mem_read(on, 512)))
    fresh.call(0x4005aa8e, settings, on)
    check(fresh.state('per_reload_keep') == 1, 'redemarrage simule : RLD ON relu du projet')
    fresh.uc.mem_write(off, bytes(rig.uc.mem_read(native, 512)))
    fresh.call(0x4005aa8e, settings, off)
    check(fresh.state('per_reload_keep') == 0, 'ancien projet sans record : RLD OFF')
    fresh.uc.mem_write(on + 508, bytes(4))
    fresh.w(fresh.s['per_reload_keep'], 1)
    fresh.call(0x4005aa8e, settings, on)
    check(fresh.state('per_reload_keep') == 0, 'record corrompu : RLD OFF')
    print('%d verifications ; voix DSP, MMC et combinaisons non emules' % checks)


if __name__ == '__main__':
    main()
