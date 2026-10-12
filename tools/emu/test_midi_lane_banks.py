#!/usr/bin/env python3
"""Note 57 : prototype de résolution des 96 banques, sans publication firmware.

Exécute le code ColdFire ; objets actifs synthétiques suivant le format OS.
Ne prouve ni changement natif complet, ni sauvegarde, ni sortie MIDI.
"""
import argparse
import pathlib
import struct
import subprocess
import tempfile
from test_seq_gen_menu import Rig
from test_sdvintage import main_os_from_syx
from test_midi_lane_page import load


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--cycles', required=True)
    args = ap.parse_args()
    root = pathlib.Path(__file__).resolve().parents[2]
    cross = str(root.parent / 'toolchain/bin/m68k-elf-')
    rig = Rig(main_os_from_syx(args.cycles), {'writes': []},
              {'writes': [], 'symbols': {}})
    load(rig)
    with tempfile.TemporaryDirectory() as temp:
        p = pathlib.Path(temp)
        subprocess.run([cross+'as', '-march=cfv4e', '-o', str(p/'bank.o'),
                        str(root/'tools/machines/midi_lanes/banks.s')], check=True)
        subprocess.run([cross+'ld', '-Ttext=0x930f0000', '-e', 'ml_bank_for',
                        '--defsym=ml_stop='+hex(rig.s['ml_stop']),
                        '-o', str(p/'bank.elf'), str(p/'bank.o')], check=True)
        subprocess.run([cross+'objcopy', '-O', 'binary', str(p/'bank.elf'),
                        str(p/'bank.bin')], check=True)
        rig.u.mem_write(0x930f0000, (p/'bank.bin').read_bytes())
        rig.s.update({line.split()[2]: int(line.split()[0], 16)
                 for line in subprocess.check_output(
                     [cross+'nm', str(p/'bank.elf')], text=True).splitlines()
                 if len(line.split()) == 3})
    base = 0x93090000
    image = bytes((i // 1584) for i in range(96 * 1584))
    rig.u.mem_write(base, image)
    for index in range(96):
        pointer = rig.call('ml_bank_for', base, index)
        assert pointer == base + 1584 * index
        assert bytes(rig.u.mem_read(pointer, 1584)) == bytes([index])*1584
    for index in (96, 65536, 0xffffffff):
        assert rig.call('ml_bank_for', base, index) == 0
    assert rig.call('ml_bank_for', 0, 0) == 0
    assert bytes(rig.u.mem_read(base, len(image))) == image
    print('ok : 96 banques distinctes, indices invalides refusés, données intactes')
    # Les vrais setters du prototype doivent modifier uniquement la banque visée.
    for index in (0, 1, 95):
        bank = rig.call('ml_bank_for', base, index)
        assert rig.call('ml_init', bank) == 1
        assert rig.call('ml_edit', bank, 5, 15, 0, 36+index % 48) == 1
        assert rig.call('ml_edit', bank, 5, 15, 1, 80+index % 40) == 1
        assert rig.call('ml_edit', bank, 5, 15, 3, 1) == 1
    snapshot = bytes(rig.u.mem_read(base, len(image)))
    for index in (0, 1, 95, 1, 0, 95, 0):
        bank = rig.call('ml_bank_for', base, index)
        step = bytes(rig.u.mem_read(bank+5*264+8+15*4, 4))
        assert step[0] == 36+index % 48
        assert step[1] == 80+index % 40 and step[3] == 1
    assert bytes(rig.u.mem_read(base, len(image))) == snapshot
    print('ok : édition réelle note/vélocité/trig sur A/B/96, retour sans mélange')
    for pointer in (0x93010000, 0x93020000):
        rig.w32(0x40a7887c, pointer)
        for index in (0, 1, 95, 96, 0xffffffff, 6, 0):
            rig.u.mem_write(pointer+30706, struct.pack('>I', index))
            expected = index if index < 96 else 0xffffffff
            assert rig.call('ml_active_pattern_id') == expected
    rig.w32(0x40a7887c, 0)
    assert rig.call('ml_active_pattern_id') == 0xffffffff
    print('ok : identité active relue, remplacement objet, bornes et singleton nul')
    runtime, clock, slot = 0x93070000, 0x93071000, 0x93072000
    bank_a, bank_b = base, base+1584
    for full in (False, True):
        rig.u.mem_write(runtime, bytes(320))
        rig.u.mem_write(clock, bytes(52))
        rig.w32(slot, bank_a)
        # Six notes tenues ; file contenant encore leurs note-on.
        for lane in range(6):
            assert rig.call('ml_edit', bank_a, lane, 0, 3, 1) == 1
            assert rig.call('ml_edit', bank_b, lane, 0, 0, 72+lane) == 1
            assert rig.call('ml_edit', bank_b, lane, 0, 3, 1) == 1
        assert rig.call('ml_clock', runtime, bank_a, clock, 100, 1) == 6
        if full:
            # Saturation à 58 paquets + six places réservées aux note-off.
            while rig.r32(runtime) < 58:
                count, tail = rig.r32(runtime), rig.r32(runtime+8)
                rig.w32(runtime+16+tail*4, 0x963c6404)
                rig.w32(runtime+8, (tail+1)&63)
                rig.w32(runtime, count+1)
        before = bytes(rig.u.mem_read(base, len(image)))
        assert rig.call('ml_bank_activate', slot, runtime, clock, bank_b) == 1
        assert rig.r32(slot) == bank_b
        assert bytes(rig.u.mem_read(clock, 52)) == bytes(52)
        assert rig.r32(runtime+12) == 0
        assert rig.r32(runtime) <= 64
        old_count = rig.r32(runtime)
        if not full:
            assert rig.call('ml_clock', runtime, bank_b, clock, 200, 1) == 6
        packets = []
        while rig.r32(runtime):
            packets.append(rig.call('ml_take', runtime))
        assert packets and all(p >> 28 == 8 for p in packets[:old_count])
        assert {p >> 24 for p in packets[:old_count]} == set(range(0x86, 0x8c))
        if not full:
            ons = packets[old_count:]
            assert len(ons) == 6 and all(p >> 28 == 9 for p in ons)
            assert [(p >> 16)&127 for p in ons] == list(range(72, 78))
        assert bytes(rig.u.mem_read(base, len(image))) == before
        rig.u.mem_write(clock, bytes([17])*52)
        assert rig.call('ml_bank_activate', slot, runtime, clock, bank_b) == 0
        assert rig.call('ml_bank_activate', slot, runtime, clock, 0) == 0
        assert bytes(rig.u.mem_read(clock, 52)) == bytes([17])*52
    print('ok : changement atomique, anciens note-on annulés, note-off avant nouveau bank, saturation, phase remise à zéro')


if __name__ == '__main__':
    main()
