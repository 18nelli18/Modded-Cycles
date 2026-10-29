#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Preuve Unicorn des editions incrementales et des vrais jobs natifs (notes/58).

Le shim de file clone les foncteurs par leur gestionnaire natif ; les rappels,
encodeurs et destructeurs natifs sont executes. Tas, file et MMC sont controles,
sans simulation de l'ordonnancement physique. Aucun projet personnel requis.
  python3 tools/emu/test_performance15_storage.py --cycles firmware/model-cycles_OS1.13.syx
"""
import argparse
import json
from pathlib import Path
import random
import struct
import subprocess
import zlib
from unicorn import m68k_const as mk
from test_performance15 import Rig, KIT, PATTERN, MANAGER
import gen_performance15 as gen

QCOUNT, QOBJECT, SHIM = 0x44d80000, 0x44d70000, 0x44e00000
MODEL, MIRROR, SCRATCH = MANAGER + 0x74, 0x44a00000, 0x44900000


def build_shim(symbols):
    """Compile seulement le faux service de file, pas une routine native copiee."""
    out = gen.ROOT / 'build/performance15'
    source = out / 'mirror-proof.c'
    source.write_text('''typedef unsigned int u32;
 u32 test_queue(void*s,void*name,u32*fn,void*completion){
 volatile u32*count=(volatile u32*)0x44d80000;u32 n=*count;
 u32*out=(u32*)(0x44d70000+n*16);out[2]=fn[2];out[3]=fn[3];
 ((u32(*)(u32*,u32*,u32))fn[2])(out,fn,2);*count=n+1;return 1;
 }
 u32 test_followup(void*object){
 ((void(*)(void*,u32,u32,u32))NOTIFY)((void*)MODEL,0,MIRROR,0);
 return ((u32(*)(void*))ORIGINAL)(object);
 }
'''.replace('NOTIFY', hex(int(symbols['per_mirror_notify'], 16)))
   .replace('ORIGINAL', hex(int(symbols['pm_callback_a_original'], 16)))
   .replace('MODEL', hex(MODEL)).replace('MIRROR', hex(MIRROR)))
    subprocess.run([gen.CROSS+'gcc', '-mcpu=54418', '-Os', '-ffreestanding', '-fno-builtin', '-c', source, '-o', out/'mirror-proof.o'], check=True)
    subprocess.run([gen.CROSS+'ld', '-Ttext='+hex(SHIM), '-e', 'test_queue', out/'mirror-proof.o', '-o', out/'mirror-proof.elf'], check=True)
    subprocess.run([gen.CROSS+'objcopy', '-O', 'binary', '-j', '.text', out/'mirror-proof.elf', out/'mirror-proof.bin'], check=True)
    names = subprocess.check_output([gen.CROSS+'nm', out/'mirror-proof.elf'], text=True)
    syms = {p[2]:int(p[0],16) for line in names.splitlines() if len(p:=line.split())==3}
    return (out/'mirror-proof.bin').read_bytes(), syms


class QueueRig(Rig):
    def __init__(self, image, payload, symbols, shim, shim_symbols):
        self.followup = self.reject_epoch = self.fail_queue = self.collisions = False
        self.live = set()
        self.allocations = self.frees = 0
        self.shim_symbols = shim_symbols
        super().__init__(image, payload, symbols)
        self.stubs.pop(0x40068d0a)
        self.stubs[0x400802ec] = self.free
        self.uc.mem_write(SHIM, shim)
        self.call('per_storage_initialize')
        self.call('per_storage_observe')
        self.w(MODEL, 0x400fcf3c)
        self.w(MODEL+0x10, KIT)
        self.w(MODEL+0x44, 0)

    def allocate(self, a):
        if a[0] > 32:
            return super().allocate(a)
        p = super().allocate(a)
        if self.collisions:
            self.heap += 96
        self.live.add(p)
        self.allocations += 1
        return p

    def free(self, a):
        assert a[0] in self.live, hex(a[0])
        self.live.remove(a[0])
        self.frees += 1
        return 0

    def step(self, u, address, size, data):
        if address == 0x40068d0a:
            if self.fail_queue:
                self.ret(1)
            else:
                assert self.r(QCOUNT) < 256
                u.reg_write(mk.UC_M68K_REG_PC, self.shim_symbols['test_queue'])
            return
        if address == self.s.get('pm_callback_a_original') and self.followup:
            self.followup = False
            u.reg_write(mk.UC_M68K_REG_PC, self.shim_symbols['test_followup'])
            return
        if address == self.s.get('per_record_amount') and self.reject_epoch:
            self.reject_epoch = False
            self.w(self.s['per_edit_epoch'], self.state('per_edit_epoch')+1)
        super().step(u, address, size, data)

    def notify(self, dest=MIRROR, active=0):
        self.call('per_mirror_notify', MODEL, 0, dest, active)

    def destroy(self, index):
        obj = QOBJECT + index*16
        if self.r(obj+8):
            self.call(0x400cf044, obj)
            self.uc.mem_write(obj, bytes(16))

    def execute(self, index):
        obj = QOBJECT + index*16
        assert self.call(self.r(obj+12), obj)&255 == 1
        self.destroy(index)

    def cancel(self):
        for i in range(self.r(QCOUNT)):
            self.destroy(i)
        self.w(QCOUNT, 0)

    def record(self, slot=0):
        self.call('per_storage_snapshot', slot, SCRATCH)
        return bytes(self.uc.mem_read(SCRATCH, 256))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--cycles', required=True)
    args = ap.parse_args()
    _, image, manifest = gen.compile_mode(args.cycles)
    payload = (gen.ROOT/'build/performance15/payload.bin').read_bytes()
    shim, syms = build_shim(manifest['symbols'])
    rig = QueueRig(image, payload, manifest['symbols'], shim, syms)
    checks = 0

    def check(condition, label):
        nonlocal checks
        checks += 1
        if not condition:
            raise AssertionError(label)

    # Comparer chaque montant au serialiseur complet et a un CRC independant.
    rng = random.Random(5815)
    for i in range(60):
        route = rig.s['per_routes']+i*8
        rig.uc.mem_write(route, struct.pack('>BBBBhH', rng.randrange(7), rng.randrange(14), 1, 0, rng.randrange(-127,128), 0))
    for m in range(15):
        for amount in range(128):
            rig.w(rig.s['per_amounts']+m*4, amount)
            rig.call('per_record_routes', SCRATCH+512)
            golden = bytes(rig.uc.mem_read(SCRATCH+512, 256))
            rig.call('per_storage_amount_edit', m)
            record = rig.record()
            check(record == golden, 'M%d montant %d : record identique' % (m+1, amount))
            check(int.from_bytes(record[12:16], 'big') == zlib.crc32(record[16:]), 'CRC independant')
            check(rig.call('per_record_valid', SCRATCH) == 1, 'record relisible')
    generation = rig.state('per_saved_generation')
    before = rig.r(generation)
    rig.reject_epoch = True
    rig.w(rig.s['per_amounts'], 99)
    rig.call('per_storage_amount_edit', 0)
    check(rig.r(generation) == before, 'changement de contexte : publication refusee')
    rig.call('per_storage_amount_edit', 0)
    check(rig.r(generation) == before+1, 'edition suivante : repli complet')
    epoch = rig.state('per_edit_epoch')
    rig.call('per_storage_load', KIT)
    check(rig.state('per_edit_epoch') == epoch+1 and not rig.state('per_amount_cache_valid'), 'chargement invalide le cache')

    # Deux formats natifs, dernier record lu au moment du rappel.
    for offset, vector, mirror in ((0x20, 0x44884000, MIRROR), (0x2c, 0x44884010, MIRROR+0x20000)):
        rig.w(MODEL+offset, vector)
        rig.w(MODEL+offset+4, vector+4)
        rig.w(vector, mirror)
    metadata = rig.metadata
    for amount in range(128):
        rig.w(rig.s['per_amounts'], amount)
        rig.call('per_storage_amount_edit', 0)
    check(rig.r(QCOUNT) == 2, '128 editions : un job en attente par miroir')
    check(rig.metadata == metadata+128, 'chaque edition notifie le parent')
    latest = rig.record()
    rig.execute(0)
    rig.execute(1)
    check(bytes(rig.uc.mem_read(MIRROR+0x1d00,256)) == latest, 'premier vrai encodeur : dernier montant')
    check(bytes(rig.uc.mem_read(MIRROR+0x21d00,256)) == latest, 'second vrai encodeur : dernier montant')
    rig.cancel()
    # Annulation ancienne generation, suivi apres debut de rappel, tables pleines.
    rig.notify()
    rig.w(rig.s['per_edit_epoch'], rig.state('per_edit_epoch')+1)
    rig.notify()
    check(rig.r(QCOUNT) == 2, 'nouvelle epoque : nouveau job')
    rig.destroy(0)
    rig.notify()
    check(rig.r(QCOUNT) == 2, 'ancien destructeur ne libere pas le nouveau groupe')
    rig.execute(1)
    rig.cancel()
    rig.notify()
    rig.followup = True
    rig.execute(0)
    check(rig.r(QCOUNT) == 2, 'edition apres debut du rappel : job de suivi')
    rig.execute(1)
    rig.cancel()
    for i in range(10):
        rig.notify(MIRROR+i*0x2000)
    check(rig.r(QCOUNT) == 10, 'groupes pleins : repli natif sans perte')
    rig.cancel()
    rig.collisions = True
    for i in range(8):
        rig.notify(MIRROR+i*0x2000)
    check(rig.r(QCOUNT) == 8, 'collisions de pointeurs : repli natif')
    rig.cancel()
    rig.collisions = False
    rig.fail_queue = True
    rig.notify()
    rig.fail_queue = False
    rig.notify()
    check(rig.r(QCOUNT) == 1, 'file sans clone survivant : aucune reservation bloquee')
    rig.execute(0)
    rig.cancel()
    for _ in range(128):
        rig.notify()
        rig.execute(0)
        rig.cancel()
    check(not rig.live and rig.allocations == rig.frees, 'tous les payloads clones detruits')
    check(all(rig.r(rig.s['groups']+i*28) == 0 for i in range(8)), 'huit groupes liberes')
    check(all(rig.r(rig.s['owners']+i*8+4) == 0 for i in range(32)), 'proprietaires liberes')
    print(json.dumps(dict(checks=checks, amount_edits=1920, burst_edits=128, burst_native_jobs=2,
                          allocations=rig.allocations, frees=rig.frees, mismatches=0)))


if __name__ == '__main__':
    main()
