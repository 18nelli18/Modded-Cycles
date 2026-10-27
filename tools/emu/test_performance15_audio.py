#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Preuve audio autonome du mode Performance (notes/58), environ 15 secondes.

Execute le vrai lissage EMAC de l'OS officiel face aux memes cibles calculees
sans le crochet. Verifie SRAM/fallback, registres, masque IRQ et restauration.
L'observation du motif stable est substituee ; la preuve principale couvre ses
codecs. Pas de voix DSP, de MMC, de concurrence IRQ ni de cycles physiques.
  python3 tools/emu/test_performance15_audio.py --cycles firmware/model-cycles_OS1.13.syx
"""
import argparse
import json
from pathlib import Path
import random
import re
import struct
import subprocess

from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn import m68k_const as mk
import emac
from test_performance15 import Rig
import gen_performance15 as gen

SOURCE = 0x800015a0
REGISTERS = [getattr(mk, 'UC_M68K_REG_D%d' % i) for i in range(2, 8)] + [
    getattr(mk, 'UC_M68K_REG_A%d' % i) for i in range(2, 7)]


def instructions(image):
    """Decode localement le lissage ; respecte le prefixe de toolchain detecte."""
    output = subprocess.check_output([
        gen.CROSS + 'objdump', '-D', '-b', 'binary', '-m', 'm68k:isa-c:emac',
        '--adjust-vma=0x40000400', '--start-address=0x40058474',
        '--stop-address=0x40058502', str(image)], text=True)
    result = {}
    for line in output.splitlines():
        m = re.match(r'\s*([0-9a-f]+):\t([0-9a-f ]+)\t(\S+)\s*(.*)$', line)
        if m:
            result[int(m[1], 16)] = (len(m[2].replace(' ', '')) // 2, m[3], m[4].strip())
    assert len(result) > 30
    return result


def rig(image, payload, manifest, decoded):
    r = Rig(image, payload, manifest['symbols'])
    del r.stubs[0x40058474]
    r.stubs[r.s['per_storage_observe']] = lambda a: 0
    e = emac.EMAC(r.uc)
    e.install(decoded)
    e.macsr = 0x20
    return r, e


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--cycles', required=True)
    ap.add_argument('--previous-build', type=Path, help='comparaison facultative avec une construction locale precedente')
    args = ap.parse_args()
    stock, patched, manifest = gen.compile_mode(args.cycles)
    out = gen.ROOT / 'build/performance15'
    payload = (out / 'payload.bin').read_bytes()
    decoded = instructions(out / 'mainos.bin')
    native, ne = rig(stock, payload, manifest, decoded)
    actual, ae = rig(patched, payload, manifest, decoded)
    params = gen.load_registry().parameters
    sound = [p for p in params if p['backend'] == 'sound']
    fx = [p for p in params if p['backend'] == 'fx']
    assert len(sound) == 13 and len(fx) == 4
    randomizer = random.Random(0x50455246)
    cases = []
    for mask in range(64):
        cases.append((mask, [0] * 6, 0))
    for track in range(6):
        for d in range(len(sound)):
            masks = [0] * 6
            masks[track] = 1 << d
            cases.append((0, masks, 0))
    cases.extend((0, [0] * 6, 1 << d) for d in range(4))
    cases.extend((randomizer.getrandbits(6), [randomizer.getrandbits(13) for _ in range(6)],
                  randomizer.getrandbits(4)) for _ in range(64))
    watched = [0, False]

    def writes(u, access, address, size, value, data):
        if watched[1] and watched[0] <= address < watched[0] + 476:
            assert u.reg_read(mk.UC_M68K_REG_SR) & 0x700 == 0x700, 'ecriture sans masque IRQ'

    actual.uc.hook_add(UC_HOOK_MEM_WRITE, writes)
    count = 0
    for source in (SOURCE, 0x44740000):
        for index, (level_mask, sound_masks, fx_mask) in enumerate(cases):
            values = [randomizer.randrange(0x7f01) for _ in range(262)]
            levels = [randomizer.randrange(-65024, 65025) for _ in range(6)]
            sounds = [[randomizer.randrange(-65024, 65025) for _ in sound] for _ in range(6)]
            effects = [randomizer.randrange(-65024, 65025) for _ in fx]
            targets = values[:]
            for t in range(6):
                if level_mask & (1 << t):
                    targets[t] = min(0x7f00, max(0, values[t] + levels[t]))
                for d, p in enumerate(sound):
                    if sound_masks[t] & (1 << d):
                        slot = 7 + t * 33 + p['slot']
                        targets[slot] = parameter_value(p, values[slot] + sounds[t][d])
            for d, p in enumerate(fx):
                if fx_mask & (1 << d):
                    slot = 205 + p['slot']
                    targets[slot] = parameter_value(p, values[slot] + effects[d])
            initial = [randomizer.randrange(0x7f000001) for _ in range(238)]
            for r, e, words in ((native, ne, targets), (actual, ae, values)):
                r.uc.mem_write(source, struct.pack('>262H', *words))
                r.uc.mem_write(0x800011e8, struct.pack('>238I', *initial))
                r.uc.mem_write(0x8000100c, bytes(476))
                e.acc = [0] * 4
                e.macsr = 0x20
            actual.w(actual.s['per_initialized'], 1)
            actual.w(actual.s['per_level_mask'], level_mask)
            actual.w(actual.s['per_fx_mask'], fx_mask)
            actual.uc.mem_write(actual.s['per_level_audio'], b'\xa5' * 480)
            for t in range(6):
                actual.w(actual.s['per_level_sums'] + 4 * t, levels[t])
                actual.w(actual.s['per_sound_mask'] + 4 * t, sound_masks[t])
                for d, v in enumerate(sounds[t]):
                    actual.w(actual.s['per_sound_sums'] + 4 * (t * len(sound) + d), v)
            for d, v in enumerate(effects):
                actual.w(actual.s['per_fx_sums'] + 4 * d, v)
            preserved = {reg: randomizer.getrandbits(32) for reg in REGISTERS}
            for reg, v in preserved.items():
                actual.uc.reg_write(reg, v)
            actual.uc.reg_write(mk.UC_M68K_REG_SR, 0x2500)
            before = bytes(actual.uc.mem_read(source, 524))
            watched[:] = [source, True]
            result = actual.call('per_audio_levels', source)
            watched[1] = False
            native.call(0x40058474, source)
            assert result == 0x8000100c
            assert bytes(actual.uc.mem_read(source, 524)) == before
            assert actual.uc.reg_read(mk.UC_M68K_REG_SR) & 0xffe0 == 0x2500
            assert all(actual.uc.reg_read(reg) == v for reg, v in preserved.items())
            assert bytes(actual.uc.mem_read(actual.s['per_level_audio'] + 476, 4)) == b'\xa5' * 4
            for address, size in ((0x8000100c, 476), (0x800011e8, 952)):
                assert bytes(actual.uc.mem_read(address, size)) == bytes(native.uc.mem_read(address, size)), (source, index, address)
            count += 1
            print('ok %d : source %08x, cibles/lissage/ABI/IRQ identiques' % (count, source))
    cost = {}
    builds = [('courant', patched, payload, manifest)]
    if args.previous_build:
        d = args.previous_build
        old = json.loads((d / 'manifest.json').read_text())
        assert old['stock_main_sha256'] == gen.STOCK_SHA and old['cpu'] == '54418'
        builds.append(('precedent', (d / 'mainos.bin').read_bytes(), (d / 'payload.bin').read_bytes(), old))
    for label, image, data, m in builds:
        r, e = rig(image, data, m, decoded)
        r.w(r.s['per_initialized'], 1)
        r.w(r.s['per_level_mask'], 0x38)
        for t, v in enumerate((60, 100, 46), 3):
            r.w(r.s['per_level_sums'] + 4 * t, v * 256)
        executed = [0]

        def tick(u, pc, size, user):
            if gen.RUNTIME <= pc < 0x42340000:
                executed[0] += 1

        r.uc.hook_add(UC_HOOK_CODE, tick)
        for _ in range(32):
            r.call('per_audio_levels', SOURCE)
        cost[label] = executed[0] / 32
    report = dict(cases=count, mismatches=0, overlay_instructions_per_call=cost,
                  scope='Lissage natif EMAC ; sources SRAM/fallback et ABI/IRQ ; observation du motif substituee ; pas de DSP, de MMC ni de cycles physiques')
    (out / 'audio-validation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False))


def parameter_value(p, value):
    value = min(p['maximum'], max(p['minimum'], value))
    if p['step'] == 256:
        value = min(p['maximum'], (value + 128) & ~255)
    return value


if __name__ == '__main__':
    main()
