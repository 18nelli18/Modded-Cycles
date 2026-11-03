"""Compile le vrai C ColdFire : depart selectionne, repetitions, STOP et LOOP.

python tools/emu/test_song_cursor367.py --output ../controls367/proof/song
"""
import argparse
import json
import os
from pathlib import Path
import struct
import subprocess
from unicorn import Uc, UC_ARCH_M68K, UC_MODE_BIG_ENDIAN
from unicorn import m68k_const as mk

ROOT = Path(__file__).resolve().parents[2]
CROSS = 'H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-'
CODE, DATA, STACK, STOP = 0x100000, 0x200000, 0x30f000, 0x10f000


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    os.environ['PATH'] = str(Path(CROSS).parent) + os.pathsep + os.environ.get('PATH', '')
    obj, elf, blob = (args.output / name for name in ('song.o', 'song.elf', 'song.bin'))

    def run(tool, *values):
        return subprocess.check_output([CROSS + tool + '.exe', *map(str, values)], text=True)

    run('gcc', '-mcpu=54418', '-Os', '-ffreestanding', '-fno-builtin', '-fno-pic',
        '-Wall', '-Wextra', '-Werror', '-c', ROOT / 'tools/machines/song/song.c', '-o', obj)
    run('ld', '-Ttext', hex(CODE), '-e', 'song_compile_from', '-o', elf, obj)
    run('objcopy', '-O', 'binary', elf, blob)
    symbols = {p[2]: int(p[0], 16) for line in run('nm', elf).splitlines()
               if len(p := line.split()) == 3}
    u = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
    for address in (CODE, DATA, 0x300000):
        u.mem_map(address, 0x10000)
    u.mem_write(CODE, blob.read_bytes())
    out, mapping = DATA + 1024, DATA + 2048
    cases = 0
    rows = [(4, 2, 3, 0), (9, 1, 5, 0), (95, 3, 63, 0), (0, 1, 0, 0)]
    for loop in (0, 1):
        for start in range(len(rows)):
            u.mem_write(DATA, struct.pack('>II', len(rows), loop) + b''.join(bytes(r) for r in rows))
            ordered = list(range(start, len(rows))) + (list(range(start)) if loop else [])
            expected = [i for i in ordered for _ in range(rows[i][1])]
            u.mem_write(out, b'\xa5' * 520)
            u.mem_write(mapping, b'\xa5' * 72)
            argv = [DATA, out, mapping, 0x41000000, 0x42000000, start]
            u.mem_write(STACK, struct.pack('>7I', STOP, *argv))
            u.reg_write(mk.UC_M68K_REG_A7, STACK)
            u.emu_start(symbols['song_compile_from'], STOP, count=100000)
            assert u.reg_read(mk.UC_M68K_REG_PC) == STOP
            assert u.reg_read(mk.UC_M68K_REG_D0) == len(expected)
            assert list(u.mem_read(mapping, len(expected))) == expected
            for n, index in enumerate(expected):
                assert bytes(u.mem_read(out + 8*n, 8)) == struct.pack(
                    '>II', 0x41000000 + 0x77f6 * rows[index][0],
                    0x42000000 + 0x1bb6 * rows[index][0])
            assert bytes(u.mem_read(out + 8*len(expected), 8)) == b'\xa5' * 8
            assert bytes(u.mem_read(mapping + len(expected), 8)) == b'\xa5' * 8
            cases += 1
    # Un curseur invalide ne produit aucune chaine partielle.
    before = bytes(u.mem_read(out, 520))
    u.mem_write(STACK, struct.pack('>7I', STOP, DATA, out, mapping, 0x41000000, 0x42000000, 4))
    u.reg_write(mk.UC_M68K_REG_A7, STACK)
    u.emu_start(symbols['song_compile_from'], STOP, count=100000)
    assert u.reg_read(mk.UC_M68K_REG_D0) == 0 and bytes(u.mem_read(out, 520)) == before
    result = dict(cases=cases, selected_row_first=True, loop_keeps_all_rows=True,
                  stop_ends_at_last_row=True, repeats_and_row_mapping=True,
                  guard_bytes_unchanged=True, hardware_tested=False)
    (args.output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print('PASS selected-row Song compiler, STOP/LOOP, repeats, mappings and guards')


if __name__ == '__main__':
    main()
