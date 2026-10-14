#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Réadresser seulement la source flash du chargeur MIDI après compression amont.

--base JSON --payload-source VA --output JSON [--check]
L'image RAM, son flux compressé, les symboles musicaux et le clear restent
identiques. Un unique LEA absolu du chargeur est accepté, tous autres usages de
l'ancienne source font échouer l'adaptateur.
"""
import argparse
import copy
import hashlib
import json
import pathlib
import struct

import build


def occurrences(data, value):
    needle = struct.pack('>I', value)
    return [i for i in range(len(data) - 3) if data[i:i + 4] == needle]


def generate(base, source):
    t = copy.deepcopy(base)
    assert t['id'] == 'midi-bank-bundle' and t['ram_only_rollback']
    assert t['midi_tempo_native'] and 'midi_reclaim' in t
    s = {k: int(v, 16) for k, v in t['symbols'].items()}
    ap = t['append']
    assert len(ap['parts']) == 1 and ap['compress'] == 'aplib'
    old_source = int(ap['at'], 16)
    dest = int(ap['dest'], 16)
    raw = bytes.fromhex(ap['parts'][0]['hex'])
    packed = bytes.fromhex(ap['compressed_hex'])
    assert s['ML_PAYLOAD_SRC'] == old_source
    assert dest == int(ap['parts'][0]['dest'], 16) == 0x401bf8c0
    assert len(raw) == ap['size'] == 58336
    assert dest + len(raw) <= source < build.END_LIMIT
    assert source + len(packed) <= build.END_LIMIT, ('flash hors limite', hex(source), len(packed))
    assert source != old_source, 'la nouvelle source doit différer de la précédente'
    loader = s['ml_boot_copy']
    matches = [w for w in t['writes'] if build.BASE + w['off'] == loader]
    assert len(matches) == 1
    wr = matches[0]
    code = bytes.fromhex(wr['new'])
    assert len(code) == 54
    assert code[:12] == b'\x41\xf9' + struct.pack('>I', old_source) + b'\x43\xf9' + struct.pack('>I', dest)
    assert code[20:26] == b'\x4e\xb9' + struct.pack('>I', s['ml_depack'])
    assert code[-6:] == b'\x4e\xf9' + struct.pack('>I', s['ml_boot_clear'])
    # Scanner à l'octet, pas seulement les opérandes alignés : aucune autre
    # référence de données ou de code ne doit être corrigée implicitement.
    refs = []
    for w in t['writes']:
        refs += [build.BASE + w['off'] + i for i in occurrences(bytes.fromhex(w['new']), old_source)]
    refs += [dest + i for i in occurrences(raw, old_source)]
    assert refs == [loader + 2], ('source flash utilisée ailleurs', [hex(x) for x in refs])
    aliases = [name for name, value in s.items() if value == old_source]
    assert aliases == ['ML_PAYLOAD_SRC'], ('alias source inattendu', aliases)
    wr['new'] = (code[:2] + struct.pack('>I', source) + code[6:]).hex()
    ap['at'] = hex(source)
    t['symbols']['ML_PAYLOAD_SRC'] = hex(source)
    t['status'] = 'experimental'
    t['description'].append('Source flash réadressée par tools/gen_midi_bank_rebase.py ; image RAM et sauvegarde MIDI inchangées, note 75.')
    t['midi_payload_rebase'] = {
        'base_recipe_sha256': hashlib.sha256(json.dumps(base, sort_keys=True).encode()).hexdigest(),
        'old_source': hex(old_source), 'source': hex(source), 'operand': hex(loader + 2),
        'raw_sha256': hashlib.sha256(raw).hexdigest(), 'packed_sha256': hashlib.sha256(packed).hexdigest(),
        'cache_control': hex(loader + 42),
    }
    return t


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base', required=True)
    p.add_argument('--payload-source', type=lambda v: int(v, 0), required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--check', action='store_true')
    a = p.parse_args()
    t = generate(json.loads(pathlib.Path(a.base).read_text()), a.payload_source)
    text = json.dumps(t, ensure_ascii=False, indent=1) + '\n'
    out = pathlib.Path(a.output)
    if a.check:
        assert out.read_text() == text
    else:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text)
    m = t['midi_payload_rebase']
    print('ok : source flash', m['old_source'], '->', m['source'], '; unique LEA vérifié ; payload RAM/compressé et clear identiques')


if __name__ == '__main__':
    main()
