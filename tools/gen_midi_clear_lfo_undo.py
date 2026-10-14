#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prototype B clear/Undo : adapters isolés, extension du payload RAM existant.

--base JSON --output JSON [--cross m68k-elf-] [--check]
Ne change ni sources banque existantes, ni pages ; neuf blocs déjà réservés.
Code et snapshot privés après l'ancien RAW, tous symboles musicaux conservés.
"""
import argparse
import copy
import hashlib
import json
import pathlib
import struct
import subprocess
import tempfile

import aplib_cost
import build

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'tools/machines/midi_lanes/clear_lfo_undo.s'
LIMIT = 0x401ce400  # La plage suivante est réservée à l'adaptateur A indépendant.
BINDINGS = ('ml_repeat_clip', 'ml_pattern', 'mlp_track', 'mlcc_context', 'mlcc_cfg_owner',
            'mlcc_settings', 'mlccp_track', 'mlccp_confirm_cancel', 'mlcc_lane_cancel',
            'mlcc_triggers', 'mlcc_refresh', 'mlp_redraw', 'ml_repeat_clip_prepare',
            'mlcc_lane_put', 'mlp_clip_undo_op', 'mlp_clip_undo_lane')


def symbols(cross, elf):
    result = {}
    for line in subprocess.check_output([cross + 'nm', '--defined-only', str(elf)], text=True).splitlines():
        fields = line.split()
        if len(fields) == 3:
            result[fields[2]] = int(fields[0], 16)
    return result


def compile_adapter(s, start, cross):
    with tempfile.TemporaryDirectory() as tmp:
        p = pathlib.Path(tmp)
        obj, elf, binary = p / 'clear.o', p / 'clear.elf', p / 'clear.bin'
        subprocess.run([cross + 'as', '-march=cfv4e', '-o', str(obj), str(SOURCE)], check=True)
        bindings = '\n'.join('B_' + name + ' = ' + hex(s[name]) + ';' for name in BINDINGS)
        (p / 'link.ld').write_text(bindings + f'\nSECTIONS {{ .adapter {start:#x} : {{ *(.text*) *(.rodata*) *(.data*) *(.bss*) . = ALIGN(16); }} }}\n')
        subprocess.run([cross + 'ld', '--orphan-handling=error', '-T', str(p / 'link.ld'),
                        '-e', 'mclf_op', '-o', str(elf), str(obj)], check=True)
        subprocess.run([cross + 'objcopy', '-O', 'binary', '--only-section=.adapter', str(elf), str(binary)], check=True)
        return binary.read_bytes(), symbols(cross, elf)


def generate(base, cross='m68k-elf-', dynamic=False):
    t = copy.deepcopy(base)
    assert t['id'] == 'midi-bank-bundle'
    if not dynamic:assert t['ram_only_rollback'] and t['midi_tempo_native']
    assert not {0x4000f762,0x4000f850,0x4008b24a,0x4008b3f6} & {build.BASE+w['off'] for w in t['writes']}
    assert 'b_clear_lfo_undo' not in t
    s = {k: int(v, 16) for k, v in t['symbols'].items()}
    ap = t['append']
    assert len(ap['parts']) == 1 and ap['compress'] == 'aplib'
    part = ap['parts'][0]
    dest = int(part['dest'], 16)
    before = bytes.fromhex(part['hex'])
    start = dest + len(before)
    assert start == s['ML_BANK_END']
    if not dynamic:assert start==0x401cdca0 and len(before)==s['ML_BANK_SIZE']==58336
    code, own = compile_adapter(s, start, cross)
    end = start + len(code)
    if not dynamic:assert end <= LIMIT, ('réserve B pleine', len(code), hex(end), hex(LIMIT))
    # Les neuf blocs TG retirés sont déjà réservés par la recette matérielle.
    bound = next(w for w in t['writes'] if build.BASE + w['off'] == 0x400792f2)
    blocks = (int(bound['new'], 16) - 0x401eb750) // 20
    if not dynamic:assert blocks == 9 and end <= s['ML_TG_START'] + blocks * 16384
    else:
        blocks=max(blocks,(end-s['ML_TG_START']+16383)//16384)
        for at,val in [(0x400792f2,0x401eb750+20*blocks),(0x400792bc,0x401eb750+20*(blocks+1)+16)]:
            row=next(w for w in t['writes'] if build.BASE+w['off']==at);row['new']=struct.pack('>I',val).hex()
        t['cache_blocks']=blocks
    raw = bytearray(before + code)
    edits = []

    def patch_call(start_name, stop_name, target_name, replacement, count):
        lo, hi = s[start_name], s[stop_name]
        old = b'\x4e\xb9' + struct.pack('>I', s[target_name])
        sites = [at for at in range(lo, hi, 2) if bytes(raw[at - dest:at - dest + 6]) == old]
        assert len(sites) == count, (target_name, [hex(at) for at in sites])
        new = b'\x4e\xb9' + struct.pack('>I', own[replacement])
        for at in sites:
            raw[at - dest:at - dest + 6] = new
            edits.append({'at': hex(at), 'old': old.hex(), 'new': new.hex(), 'role': replacement})

    patch_call('mlp_clip_key', 'mlp_track_setup_open', 'ml_repeat_clip', 'mclf_op', 5)
    patch_call('mlp_clip_key', 'mlp_track_setup_open', 'mlp_redraw', 'mclf_redraw', 2 if dynamic else 1)
    patch_call('mlp_clip_key', 'mlp_track_setup_open', 'ml_repeat_clip_prepare', 'mclf_prepare', 1)
    patch_call('ml_ui_drain', 'ml_key', 'mlcc_refresh', 'mclf_refresh', 1)
    patch_call('mlcc_audio', 'mlcc_ready', 'mlcc_lane_put', 'mclf_emit', 1)
    # Le clear natif doit conserver également l'extension après copie au boot.
    at = s['ml_boot_skip']
    old = b'\x20\x7c' + struct.pack('>I', start)
    new = b'\x20\x7c' + struct.pack('>I', end)
    assert bytes(raw[at - dest:at - dest + 6]) == old
    raw[at - dest:at - dest + 6] = new
    edits.append({'at': hex(at), 'old': old.hex(), 'new': new.hex(), 'role': 'boot_end'})
    # Cette fonction propre se trouve dans un fragment natif, éventuellement
    # réadressé par reclaim. Chercher sa plage, pas une adresse de masque figée.
    at = s['mlp_clip_invalidate']
    expected = b'\x42\xb9' + struct.pack('>I', s['mlp_clip_undo_op'])
    if dest <= at < start:
        assert bytes(raw[at - dest:at - dest + 6]) == expected
        old = expected
        new = b'\x4e\xf9' + struct.pack('>I', own['mclf_invalidate'])
        raw[at - dest:at - dest + 6] = new
    else:
        owners = [w for w in t['writes'] if build.BASE + w['off'] <= at < build.BASE + w['off'] + len(bytes.fromhex(w['new']))]
        assert len(owners) == 1
        w = owners[0]
        data = bytearray.fromhex(w['new'])
        index = at - build.BASE - w['off']
        assert bytes(data[index:index + 6]) == expected
        old = expected
        new = b'\x4e\xf9' + struct.pack('>I', own['mclf_invalidate'])
        data[index:index + 6] = new
        w['new'] = data.hex()
    edits.append({'at': hex(at), 'old': old.hex(), 'new': new.hex(), 'role': 'invalidate'})
    packed = aplib_cost.pack(bytes(raw), depth=512, lazy=True)
    assert int(ap['at'], 16) + len(packed) <= build.END_LIMIT, ('flash plein', len(packed), hex(int(ap['at'], 16)))
    part['hex'] = raw.hex()
    ap['size'] = len(raw)
    ap['compressed_hex'] = packed.hex()
    t['symbols'].update({name: hex(value) for name, value in own.items() if name.startswith('mclf_')})
    t['symbols']['ML_BANK_END'] = hex(end)
    t['symbols']['ML_BANK_SIZE'] = hex(len(raw))
    if 'midi_payload_rebase' in t:
        t['midi_payload_rebase']['raw_sha256'] = hashlib.sha256(raw).hexdigest()
        t['midi_payload_rebase']['packed_sha256'] = hashlib.sha256(packed).hexdigest()
    t['status'] = 'experimental'
    t.setdefault('description',[]).append('Prototype B : FUNC+PLAY clear/Undo inclut les deux LFO MIDI, tools/gen_midi_clear_lfo_undo.py ; aucune sauvegarde disque.')
    t['b_clear_lfo_undo'] = {
        'base_recipe_sha256': hashlib.sha256(json.dumps(base, sort_keys=True).encode()).hexdigest(),
        'adapter_start': hex(start), 'adapter_end': hex(end), 'adapter_size': len(code),
        'a_reserved_start': hex(end if dynamic else LIMIT), 'edits': edits, 'packed_size': len(packed),
        'flash_margin': build.END_LIMIT - int(ap['at'], 16) - len(packed),
    }
    return t


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--cross', default='m68k-elf-')
    p.add_argument('--check', action='store_true')
    p.add_argument('--dynamic',action='store_true')
    a = p.parse_args()
    t = generate(json.loads(pathlib.Path(a.base).read_text()), a.cross,a.dynamic)
    text = json.dumps(t, ensure_ascii=False, indent=1) + '\n'
    out = pathlib.Path(a.output)
    if a.check:
        assert out.read_text() == text
    else:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text)
    m = t['b_clear_lfo_undo']
    print('ok : prototype B isolé', m['adapter_start'], '..', m['adapter_end'], m['adapter_size'],
          'octets ; payload', m['packed_size'], '; marge flash', m['flash_margin'])


if __name__ == '__main__':
    main()
