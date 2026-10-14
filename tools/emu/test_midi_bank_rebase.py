#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Source chargeur MIDI : vrai LEA/JSR/décompresseur, ancien départ rejeté.

--cycles OS1.13.syx --base JSON --tweak JSON
Arrêt avant MOVEC CACR : cette frontière matérielle n'est pas simulée. Les
instructions du chargeur et le décompresseur ColdFire s'exécutent réellement.
"""
import argparse
import copy
import json
import pathlib

from unicorn import UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE, m68k_const as mk
from test_midi_bank_reclaim import load
from test_seq_gen_menu import STACK, STOP
from test_sdvintage import main_os_from_syx
from gen_midi_bank_rebase import generate


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cycles', required=True)
    p.add_argument('--base', required=True)
    p.add_argument('--tweak', required=True)
    a = p.parse_args()
    base = json.loads(pathlib.Path(a.base).read_text())
    tweak = json.loads(pathlib.Path(a.tweak).read_text())
    meta = tweak['midi_payload_rebase']
    source, old_source = int(meta['source'], 16), int(meta['old_source'], 16)
    assert generate(base, source) == tweak
    old_ap, ap = base['append'], tweak['append']
    assert old_ap['parts'] == ap['parts'] and old_ap['compressed_hex'] == ap['compressed_hex']
    original = copy.deepcopy(base)
    changed = copy.deepcopy(tweak)
    for x in (original, changed):
        x.pop('midi_payload_rebase', None)
        x.pop('status', None)
        x.pop('description', None)
    changed['append']['at'] = original['append']['at']
    changed['symbols']['ML_PAYLOAD_SRC'] = original['symbols']['ML_PAYLOAD_SRC']
    operand = int(meta['operand'], 16)
    import build
    old_w = next(w for w in original['writes'] if build.BASE + w['off'] == operand - 2)
    new_w = next(w for w in changed['writes'] if build.BASE + w['off'] == operand - 2)
    assert old_w['old'] == new_w['old']
    assert old_w['new'][:4] == new_w['new'][:4] and old_w['new'][12:] == new_w['new'][12:]
    new_w['new'] = old_w['new']
    assert original == changed
    print('ok : un opérande LEA + métadonnées seulement ; code/données RAM, flux compressé, clear et symboles musicaux identiques')
    # Refuser un chargeur inattendu, un alias ambigu et une référence cachée.
    cases = []
    bad = copy.deepcopy(base)
    bad_w = next(w for w in bad['writes'] if build.BASE + w['off'] == operand - 2)
    bad_w['new'] = '43f9' + bad_w['new'][4:]
    cases.append(bad)
    bad = copy.deepcopy(base)
    bad['symbols']['ambiguous_payload_source'] = hex(old_source)
    cases.append(bad)
    bad = copy.deepcopy(base)
    tail = bytes.fromhex(bad['append']['parts'][0]['hex'])
    bad['append']['parts'][0]['hex'] = (tail[:-4] + old_source.to_bytes(4, 'big')).hex()
    cases.append(bad)
    for malformed in cases:
        try:
            generate(malformed, source)
        except AssertionError:
            pass
        else:
            raise AssertionError('recette ambiguë acceptée')
    print('ok : opcode chargeur, alias et référence source supplémentaire refusés')

    stock = main_os_from_syx(a.cycles)
    dest = int(ap['dest'], 16)
    raw = bytes.fromhex(ap['parts'][0]['hex'])
    packed = bytes.fromhex(ap['compressed_hex'])
    fs_lo, fs_hi = 0x401a7750, 0x401ab750
    for recipe, expected, full in ((base, old_source, False), (tweak, source, True)):
        r = load(stock, recipe)
        r.u.mem_write(source, packed)
        r.u.mem_write(dest, bytes(len(raw)))
        r.u.mem_write(fs_lo, bytes(fs_hi - fs_lo))
        r.w32(STACK, STOP)
        r.u.reg_write(mk.UC_M68K_REG_A7, STACK)
        reads = []

        def read(u, access, address, size, value, data):
            if not reads:
                reads.append(address)
                if not full:
                    u.emu_stop()

        def forbidden(*args):
            raise AssertionError('écriture dans le tampon nul filesystem')

        r.u.hook_add(UC_HOOK_MEM_READ, read, begin=min(source, old_source), end=max(source, old_source) + len(packed) - 1)
        r.u.hook_add(UC_HOOK_MEM_WRITE, forbidden, begin=fs_lo, end=fs_hi - 1)
        stop = int(meta['cache_control'], 16)
        assert bytes(r.u.mem_read(stop, 4)).hex() == '4e7b0002'
        r.u.emu_start(r.s['ml_boot_copy'], stop, count=10000000)
        assert reads == [expected], reads
        if full:
            assert r.u.reg_read(mk.UC_M68K_REG_PC) == stop
            assert r.u.reg_read(mk.UC_M68K_REG_A7) == STACK
            assert bytes(r.u.mem_read(dest, len(raw))) == raw
            assert r.u.reg_read(mk.UC_M68K_REG_A0) == source + len(packed)
        assert bytes(r.u.mem_read(fs_lo, fs_hi - fs_lo)) == bytes(fs_hi - fs_lo)
    print('ok : ancien chargeur lit ancien départ ; chargeur réadressé lit nouveau départ et décompresse exactement58336 octets')
    print('ok : tampon filesystem401a7750..401ab750 jamais écrit, clear inchangé ; frontière CACR matérielle non exécutée')


if __name__ == '__main__':
    main()
