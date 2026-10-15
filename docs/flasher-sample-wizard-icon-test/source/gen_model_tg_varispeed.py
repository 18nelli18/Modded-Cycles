#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Delta Slice varispeed roterodamus/Model-TG 0c567d8, adresses TG conservées.

--cycles OS officiel --base TG.json --elf base/_b.elf --output candidat.json
[--check]. Base MIT 70b39dd et correctifs de ce fork conservés. Un masque
35x35 pour les helpers ; table dans pitch_thr TG devenu inutilisé. Le
préfixe TG reste zéro : c'est le tampon de création de chunks du filesystem.
"""
import argparse
import copy
import json
import pathlib
import re
import shutil
import struct
import subprocess
import tempfile

import build
import sprites
from gen_seq_gen import symbols, main_os_from_syx, STOCK

ROOT = pathlib.Path(__file__).resolve().parents[1]
PIN = '0c567d8c9e3d0c61837e1d91ac2f5c747ea9763f'
MASK = 0x401542F8


def generate(base, elf, stock, cross=None, mask=MASK):
    cross = cross or next((c for c in ('m68k-elf-', 'm68k-linux-gnu-') if shutil.which(c + 'as')), 'm68k-elf-')
    s = symbols(cross, pathlib.Path(elf))
    t = copy.deepcopy(base)
    assert t['id'] in ('model-tg', 'model-tg-st') and len(t['append']['parts']) == 1
    part = t['append']['parts'][0]
    dest = int(part['dest'], 16)
    raw = bytearray.fromhex(part['hex'])
    assert raw[:0x1610] == bytes(0x1610) and s['blob_start'] == dest + 0x1610
    assert raw[s['live_note'] - dest:s['live_note'] - dest + 8] == bytes([52]) * 8
    assert sprites.MASKS[mask][0] >= 280
    # Contrats sur le code MIT de TG, jamais sur des routines extraites d'Elektron.
    select = s['sv_lv'] - dest
    pattern = b'\x22\x42\x61\x00'
    select = raw.find(pattern, select, select + 80)
    assert select >= 0
    assert dest + select + 4 + struct.unpack('>h', raw[select + 4:select + 6])[0] == s['slice_from_pitch']
    gate = raw.find(bytes.fromhex('0c8000000002'), s['sv_noslice'] - dest, s['sv_defstep'] - dest) + 6
    assert gate >= 6 and raw[gate] == 0x67 and raw[gate + 2:gate + 8].hex() == '2042222800e8'
    assert dest + gate + 2 + struct.unpack('>b', raw[gate + 1:gate + 2])[0] == s['sv_defstep']
    seq = raw.find(bytes.fromhex('4a2b77cb67'), s['sq_go'] - dest, s['sq_plen'] - dest)
    assert seq >= 0
    assert dest + seq + 6 + struct.unpack('>b', raw[seq + 5:seq + 6])[0] == s['sq_plen']
    off = raw.find(b'\x41\xf9' + struct.pack('>I', s['live_note']),
                   s['note_off_hook'] - dest, s['note_off_hook'] - dest + 64)
    assert off >= 0 and raw[off + 6:off + 10].hex() == '11835800'
    # Ce tableau n'est lu que par slice_from_pitch, appelé uniquement au
    # raccord select. Vérifier les instructions/références du propre ELF TG.
    dis = subprocess.check_output([cross + 'objdump', '-d', str(elf)], text=True)
    callers = [row for row in dis.splitlines() if re.search(r'\b(?:bsr\w*|jsr|jmp)\s', row)
               and '<slice_from_pitch>' in row]
    readers = [row for row in dis.splitlines() if '<pitch_thr>' in row and ':\t' in row]
    assert len(callers) == len(readers) == 1, (callers, readers)
    assert raw.count(struct.pack('>I', s['pitch_thr'])) == 0
    reader = s['slice_from_pitch'] + 6 - dest
    assert raw[reader:reader + 2] == b'\x41\xfa'
    assert dest + reader + 2 + struct.unpack('>h', raw[reader + 2:reader + 4])[0] == s['pitch_thr']
    assert s['slice_pending'] - s['pitch_thr'] == 192
    defs = {k: s[k] for k in ['live_note', 'slice_pending', 'sv_defstep', 'sv_havestep', 'sq_plen']}
    defs.update(tgsv_select_return=dest + select + 6, tgsv_speed_return=dest + gate + 8,
                tgsv_seq_return=dest + seq + 6)
    with tempfile.TemporaryDirectory() as tmp:
        p = pathlib.Path(tmp)
        subprocess.run([cross + 'as', '-march=cfv4e', '-o', str(p / 'v.o'),
                        str(ROOT / 'tools/machines/model_tg_varispeed/varispeed.s')], check=True)
        script = '\n'.join(k + ' = ' + hex(v) + ';' for k, v in defs.items())
        script += '\nSECTIONS { .text ' + hex(mask) + ' : { *(.text*) }'
        script += ' .table ' + hex(s['pitch_thr']) + ' : { *(.rodata.tgsv_pitch_ctr) } }'
        (p / 'link.ld').write_text(script)
        subprocess.run([cross + 'ld', '-T', str(p / 'link.ld'), '-e', 'tgsv_select',
                        '-o', str(p / 'v.elf'), str(p / 'v.o')], check=True)
        ns = symbols(cross, p / 'v.elf')
        parts = []
        for section in ('.text', '.table'):
            out = p / (section[1:] + '.bin')
            subprocess.run([cross + 'objcopy', '-O', 'binary', '-j', section, str(p / 'v.elf'), str(out)], check=True)
            parts.append(out.read_bytes())
        code, table = parts
    assert len(code) <= sprites.MASKS[mask][0] and len(table) == 192, (len(code), len(table))
    for at, length, name in [(select, 6, 'tgsv_select'), (gate, 8, 'tgsv_speed_gate'), (seq, 6, 'tgsv_seq')]:
        raw[at:at + length] = b'\x4e\xf9' + struct.pack('>I', ns[name]) + b'\x4e\x71' * ((length - 6) // 2)
    raw[off:off + 10] = b'\x4e\x71' * 5
    table_at = s['pitch_thr'] - dest
    raw[table_at:table_at + 192] = table
    assert raw[:0x1610] == bytes(0x1610)
    part['hex'] = raw.hex()
    t['writes'].extend([{'off': mask - build.BASE,
                         'old': stock[mask - build.BASE:mask - build.BASE + len(code)].hex(), 'new': code.hex()},
                        sprites.redirect_write(mask)])
    t['symbols'].update({k: hex(v) for k, v in ns.items() if k.startswith('tgsv_')})
    t['roterodamus_commit'] = PIN
    t['status'] = 'experimental'
    t['description'] = ['Model-TG avec le Slice varispeed de roterodamus, commit ' + PIN[:7] + '.',
                        'En Slice, les notes sélectionnent la tranche et PITCH règle sa vitesse/hauteur. '
                        'Les adresses des autres fonctions TG restent inchangées.']
    t['varispeed_patch_sites'] = [dict(at=hex(dest + a), size=n)
                                for a, n in [(select, 6), (gate, 8), (seq, 6), (off, 10)]]
    t['varispeed_table'] = dict(at=hex(s['pitch_thr']), size=192)
    t['varispeed_mask'] = dict(at=hex(mask), size=sprites.MASKS[mask][0], used=len(code))
    build.apply_writes(stock, [t])
    return t


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cycles', required=True)
    p.add_argument('--base', required=True)
    p.add_argument('--elf', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--cross')
    p.add_argument('--mask', type=lambda v: int(v, 0), default=MASK)
    p.add_argument('--check', action='store_true')
    a = p.parse_args()
    stock = main_os_from_syx(a.cycles)
    assert build.sha(stock) == STOCK, "MAIN OS 1.13 officiel requis"
    t = generate(json.loads(pathlib.Path(a.base).read_text()), a.elf, stock, a.cross, a.mask)
    text = json.dumps(t, ensure_ascii=False, indent=1) + '\n'
    out = pathlib.Path(a.output)
    if a.check:
        assert out.read_text() == text
    else:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text)
    print('ok : varispeed Slice, ' + str(t['varispeed_mask']['used']) + ' octets dans un masque, '
          'ancienne table TG réutilisée, préfixe filesystem zéro conservé')


if __name__ == '__main__':
    main()
