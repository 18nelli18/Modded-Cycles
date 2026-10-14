#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Déplacement MIDI : contrats binaires, décompression réelle, relais et chance.

--cycles OS1.13.syx --base recette-main.json --tweak recette-reclaim.json
Le writer MIDI physique reste simulé ; les vrais fragments ColdFire s'exécutent.
"""
import argparse
import json
import pathlib
import random
import struct

from unicorn import UC_HOOK_CODE, m68k_const as mk
from test_seq_gen_menu import Rig, STACK, STOP
from test_sdvintage import main_os_from_syx
from gen_midi_bank_reclaim import DEAD, DISK_HOOKS, inside
import build


def load(stock, tweak):
    r = Rig(stock, {'writes': []}, {'writes': [], 'symbols': {}})
    r.s = {k: int(v, 16) for k, v in tweak['symbols'].items()}
    for w in tweak['writes']:
        r.u.mem_write(build.BASE + w['off'], bytes.fromhex(w['new']))
    for part in tweak['append']['parts']:
        r.u.mem_write(int(part['dest'], 16), bytes.fromhex(part['hex']))
    return r


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cycles', required=True)
    p.add_argument('--base', required=True)
    p.add_argument('--tweak', required=True)
    a = p.parse_args()
    old = json.loads(pathlib.Path(a.base).read_text())
    new = json.loads(pathlib.Path(a.tweak).read_text())
    meta = new['midi_reclaim']
    mapping = [(int(m['old'], 16), int(m['new'], 16), m['size']) for m in meta['mapping']]
    original = bytes.fromhex(old['append']['parts'][0]['hex'])
    final = bytes.fromhex(new['append']['parts'][0]['hex'])
    dest = int(new['append']['dest'], 16)

    def relocate(value):
        for lo, hi, size in mapping:
            if lo <= value < lo + size:
                return hi + value - lo
        return value

    # Bytes hors corps inertes : seuls les quatre octets des opérandes changent.
    allowed = {i for lo, hi in DEAD for i in range(lo - dest, hi - dest)}
    for row in meta['references']:
        at = int(row['operand'], 16)
        if dest <= at < dest + len(final):
            allowed.update(range(at - dest, at - dest + 4))
    assert len(original) == len(final)
    assert {i for i, (before, after) in enumerate(zip(original, final)) if before != after} <= allowed
    for name, value in old['symbols'].items():
        assert int(new['symbols'][name], 16) == relocate(int(value, 16)), name
    for name in ('ml_boot_copy', 'ml_depack', 'ml_store_bank_init', 'ml_audio_lfo_init', 'ml_audio_lfo_sync',
                 'mllr_mode', 'ml_tempo_present', 'ml_tempo_toggle', 'ml_tempo_bank_guard'):
        assert new['symbols'][name] == old['symbols'][name], name
    for at in meta['inert_entries']:
        offset = int(at, 16) - dest
        assert final[offset:offset + 2] == b'\x4e\x75'
    assert len(mapping) == 20 and meta['freed_capacity'] == 3900
    assert meta['packed_size'] <= meta['old_packed_size']
    assert not DISK_HOOKS & {build.BASE + w['off'] for w in new['writes']}
    old_ranges = [(lo, lo + size) for lo, _, size in mapping]
    for at, data in [(dest, final)] + [(build.BASE + w['off'], bytes.fromhex(w['new'])) for w in new['writes']]:
        for i in range(0, len(data) - 3, 2):
            value = struct.unpack_from('>I', data, i)[0]
            assert not inside(value, old_ranges), (hex(at + i), hex(value))
    print('ok : vingt masques/3900 octets libres, adresses musicales et TEMPO conservées, zéro référence aux anciens fragments, disque inerte')

    stock = main_os_from_syx(a.cycles)
    r = load(stock, new)
    # Le vrai décompresseur reste hors payload et produit exactement son image.
    packed = bytes.fromhex(new['append']['compressed_hex'])
    source, target = 0x93100000, 0x93110000
    r.u.mem_write(source, packed)
    r.u.reg_write(mk.UC_M68K_REG_A0, source)
    r.u.reg_write(mk.UC_M68K_REG_A1, target)
    r.w32(STACK, STOP)
    r.u.reg_write(mk.UC_M68K_REG_A7, STACK)
    r.u.emu_start(r.s['ml_depack'], STOP, count=10000000)
    assert r.u.reg_read(mk.UC_M68K_REG_PC) == STOP
    assert r.u.reg_read(mk.UC_M68K_REG_A7) == STACK + 4
    assert bytes(r.u.mem_read(target, len(final))) == final
    print('ok : décompression ColdFire réelle complète, chargeur/décompresseur natifs inchangés')

    # Comparaison stock de notre mod avant/après : mêmes fonctions de condition.
    before = load(stock, old)
    rng = random.Random(20261013)
    for _ in range(500):
        args = (rng.randrange(12), rng.randrange(102), rng.randrange(10), rng.randrange(10),
                rng.randrange(2), rng.randrange(2), rng.randrange(2), rng.randrange(101))
        assert before.call('ml_condition_eval', *args) == r.call('ml_condition_eval', *args), args
    print('ok : 500 conditions/ratios/chance exécutés avant/après, résultats identiques')

    ctx = 0x93060000
    sent = []

    def send(args):
        assert not r.u.reg_read(mk.UC_M68K_REG_SR) & 0x700
        sent.append(bytes(r.u.mem_read(args[1], args[0])))
        return 0

    r.stubs[0x40001100] = send
    r.u.hook_add(UC_HOOK_CODE, r.stub, begin=0x40001100, end=0x40001100)

    def reset():
        r.u.mem_write(ctx, bytes(8256))
        sent.clear()

    def feed(data):
        for byte in data:
            r.u.reg_write(mk.UC_M68K_REG_SR, 0x2400)
            r.call('mm_feed', ctx, byte)
            assert r.u.reg_read(mk.UC_M68K_REG_SR) & 0x2700 == 0x2400

    def drain():
        r.u.reg_write(mk.UC_M68K_REG_SR, 0x2000)
        return r.call('mm_service', ctx, 8)

    for status in range(0x80, 0xf0):
        reset()
        size = 1 if status >> 4 in (0xc, 0xd) else 2
        feed([status, *range(size), *range(10, 10 + size)])
        assert drain() == 2
        assert sent == [bytes([status, *range(size)]), bytes([status, *range(10, 10 + size)])]
    reset()
    feed([0xb6, 74])
    assert drain() == 0
    sent.append(b'\x86\x3c\x00')
    feed([100, 74, 90])
    assert drain() == 2
    assert sent == [b'\x86\x3c\x00', b'\xb6\x4a\x64', b'\xb6\x4a\x5a']
    reset()
    data = bytes([0xf0] + [1] * 1022 + [0xf7])
    feed(data)
    assert drain() == 1 and sent == [data]
    print('ok : relais déplacé, tous types/canaux/running status, CC fragmenté + Note Off et SysEx1024 inchangés')
    print('Limite : writer physique simulé ; la sélection intégrée ChordKeys nécessite ses preuves puis un test matériel.')


if __name__ == '__main__':
    main()
