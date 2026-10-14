#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Récupérer vingt masques MIDI en réutilisant son stockage disque désactivé.

Chaque fragment entier conserve ses branches PC locales. Seuls les opérandes
absolus vérifiés JMP/JSR/MOVE immédiat/LEA sont réadressés. Le chargeur et le
décompresseur restent natifs : ils s'exécutent avant la copie du payload.
Les adresses musicales, le menu TEMPO et le format RAM ne changent pas.

--base JSON --output JSON [--cross m68k-elf-] [--check]
"""
import argparse
import copy
import hashlib
import json
import pathlib
import re
import struct
import subprocess
import tempfile

import aplib_dense
import build
import sprites

BASE = build.BASE
DEAD = ((0x401c34b4, 0x401c4818), (0x401c4984, 0x401c5624),
        (0x401c56b0, 0x401c5ce8))
ABS_OPS = {0x4ef9: 'jmp', 0x4eb9: 'jsr', 0x203c: 'callback', 0x41f9: 'table'}
DISK_HOOKS = {0x4000f762, 0x4000f850, 0x4008b24a, 0x4008b3f6}


def inside(address, intervals=DEAD):
    return any(lo <= address < hi for lo, hi in intervals)


def disassemble(cross, data, address):
    with tempfile.NamedTemporaryFile() as f:
        f.write(data)
        f.flush()
        return subprocess.check_output([cross + 'objdump', '-D', '-b', 'binary',
                                       '-m', 'm68k', '--adjust-vma=' + str(address), f.name], text=True)


def relative_targets(cross, data, address):
    """Lister les branches/adressages relatifs décodés par les binutils."""
    targets = []
    for line in disassemble(cross, data, address).splitlines():
        parts = line.split('\t')
        if len(parts) < 3:
            continue
        instruction = parts[-1].strip()
        relative = '%pc@' in instruction or re.match(
            r'^(?:bra|bsr|bhi|bls|bcc|bcs|beq|bne|bvc|bvs|bpl|bmi|bge|blt|bgt|ble)[bswl]?\s', instruction)
        if relative:
            match = re.search(r'0x([0-9a-f]+)', instruction)
            assert match, ('PC non décodé', line)
            target = int(match.group(1), 16)
            origin = int(parts[0].rstrip(':'), 16)
            targets.append((origin, target, line))
    return targets


def verify_local_pc(cross, data, address):
    """Toute branche relative détectée doit rester dans le fragment entier."""
    targets = relative_targets(cross, data, address)
    for _, target, line in targets:
        assert address <= target < address + len(data), ('PC externe', line)
    return len(targets)


def generate(base, cross='m68k-elf-'):
    t = copy.deepcopy(base)
    assert t['id'] == 'midi-bank-bundle' and t['ram_only_rollback'] and t['midi_tempo_native']
    s = {k: int(v, 16) for k, v in t['symbols'].items()}
    ap = t['append']
    assert len(ap['parts']) == 1 and ap['compress'] == 'aplib'
    part = ap['parts'][0]
    dest = int(part['dest'], 16)
    old_raw = bytes.fromhex(part['hex'])
    assert dest == 0x401bf8c0 and len(old_raw) == 58336 == ap['size']
    assert not DISK_HOOKS & {BASE + w['off'] for w in t['writes']}
    for name in ('ml_store_service', 'ml_store_bootstrap', 'ml_store_save_notice'):
        assert old_raw[s[name] - dest:s[name] - dest + 2] == b'\x4e\x75'
    for origin, target, line in relative_targets(cross, old_raw, dest):
        assert not (inside(target) and not inside(origin)), ('entrée relative stockage vivante', line)
    # Aucun appel musical n'entre dans ces corps, sauf le service public inerte.
    for at, data in [(dest, old_raw)] + [(BASE + w['off'], bytes.fromhex(w['new'])) for w in t['writes']]:
        for i in range(0, len(data) - 3, 2):
            target = struct.unpack_from('>I', data, i)[0]
            if inside(target) and not inside(at + i):
                assert target == s['ml_store_service'] and data[i - 2:i] == b'\x4e\xb9', ('appel stockage vivant', hex(at + i), hex(target))
    fragments = [(BASE + w['off'], bytes.fromhex(w['new'])) for w in t['writes']
                 if BASE + w['off'] in sprites.MASKS
                 and BASE + w['off'] not in (s['ml_boot_copy'], s['ml_depack'])]
    assert len(fragments) == 20 and sum(len(data) for _, data in fragments) == 3706
    pc_count = sum(verify_local_pc(cross, data, at) for at, data in fragments)
    # Garder un RTS à l'entrée de chaque ancienne fonction, même non appelée.
    entries = sorted({v for k, v in s.items() if inside(v) and k.startswith(('ml_store_', 'ml_record_'))})
    lo, hi = DEAD[0]
    bounds = sorted({v for v in entries if lo <= v < hi} | {hi})
    assert bounds[0] == lo
    spans = [((a + 5) & ~3, b) for a, b in zip(bounds, bounds[1:])]
    mapping = []
    for old, data in sorted(fragments, key=lambda x: (-len(x[1]), x[0])):
        fits = [q for q in spans if q[1] - q[0] >= len(data)]
        assert fits, ('corps stockage trop petits', hex(old), len(data))
        span = min(fits, key=lambda q: (q[1] - q[0], q[0]))
        spans.remove(span)
        new = span[0]
        tail = (new + len(data) + 3) & ~3
        if span[1] > tail:
            spans.append((tail, span[1]))
        mapping.append((old, new, len(data)))

    def relocate(value):
        for old, new, size in mapping:
            if old <= value < old + size:
                return new + value - old
        return value

    references = []

    def patch(data, address):
        result = bytearray(data)
        for i in range(0, len(data) - 3, 2):
            old = struct.unpack_from('>I', data, i)[0]
            new = relocate(old)
            if old != new:
                assert i >= 2
                opcode = struct.unpack_from('>H', data, i - 2)[0]
                assert opcode in ABS_OPS, ('opérande non approuvé', hex(address + i), hex(opcode), hex(old))
                result[i:i + 4] = struct.pack('>I', new)
                references.append({'operand': hex(address + i), 'old': hex(old), 'new': hex(new), 'kind': ABS_OPS[opcode]})
        return bytes(result)

    raw = bytearray(old_raw)
    for lo, hi in DEAD:
        raw[lo - dest:hi - dest] = bytes(hi - lo)
    for at in entries:
        raw[at - dest:at - dest + 2] = b'\x4e\x75'
    raw = bytearray(patch(bytes(raw), dest))
    for old, new, size in mapping:
        data = next(data for at, data in fragments if at == old)
        raw[new - dest:new - dest + size] = patch(data, old)
    removed = {old for old, _, _ in mapping}
    redirect_offsets = {sprites.redirect_write(old)['off'] for old in removed}
    assert len(redirect_offsets) == 20
    for old in removed:
        redirect = sprites.redirect_write(old)
        matches = [w for w in t['writes'] if w['off'] == redirect['off']]
        assert len(matches) == 1 and matches[0] == redirect, ('redirect partagé/non standard', hex(old))
    kept = []
    for w in t['writes']:
        at = BASE + w['off']
        if at in removed or w['off'] in redirect_offsets:
            continue
        w['new'] = patch(bytes.fromhex(w['new']), at).hex()
        kept.append(w)
    assert len(kept) == len(t['writes']) - 40
    t['writes'] = kept
    for name, value in s.items():
        t['symbols'][name] = hex(relocate(value))
    assert len(references) == 131, ('raccords absolus inattendus', len(references))
    part['hex'] = raw.hex()
    packed = min((aplib_dense.pack(bytes(raw), depth=d) for d in (32, 128, 512)), key=len)
    assert len(packed) <= len(bytes.fromhex(ap['compressed_hex'])), 'restitution masque augmente image flash'
    previous_packed = len(bytes.fromhex(ap['compressed_hex']))
    ap['compressed_hex'] = packed.hex()
    t['status'] = 'experimental'
    t['description'].append('Placement expérimental récupéré par tools/gen_midi_bank_reclaim.py ; note 75, sauvegarde MIDI toujours désactivée.')
    free_spans = []
    for lo, hi in DEAD:
        cursor = lo
        blockers = sorted([(at, at + 2) for at in entries if lo <= at < hi]
                          + [(at, at + size) for _, at, size in mapping if lo <= at < hi])
        for start, end in blockers + [(hi, hi)]:
            begin = (cursor + 3) & ~3
            if begin < start:
                free_spans.append([hex(begin), hex(start)])
            cursor = max(cursor, end)
    t['midi_reclaim'] = {
        'base_recipe_sha256': hashlib.sha256(json.dumps(base, sort_keys=True).encode()).hexdigest(),
        'mapping': [{'old': hex(old), 'new': hex(new), 'size': size, 'capacity': sprites.MASKS[old][0]} for old, new, size in mapping],
        'dead_ranges': [[hex(lo), hex(hi)] for lo, hi in DEAD],
        'inert_entries': [hex(at) for at in entries], 'references': references,
        'local_pc_references': pc_count, 'freed_capacity': sum(sprites.MASKS[old][0] for old in removed),
        'old_packed_size': previous_packed, 'packed_size': len(packed),
        'free_spans': free_spans,
    }
    return t


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--cross', default='m68k-elf-')
    p.add_argument('--check', action='store_true')
    a = p.parse_args()
    t = generate(json.loads(pathlib.Path(a.base).read_text()), a.cross)
    text = json.dumps(t, ensure_ascii=False, indent=1) + '\n'
    out = pathlib.Path(a.output)
    if a.check:
        assert out.read_text() == text
    else:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text)
    meta = t['midi_reclaim']
    print('ok : vingt masques libérés,', meta['freed_capacity'], 'octets ; 131 opérandes absolus vérifiés,',
          meta['local_pc_references'], 'branches PC locales ; flash', meta['old_packed_size'], '->', meta['packed_size'])


if __name__ == '__main__':
    main()
