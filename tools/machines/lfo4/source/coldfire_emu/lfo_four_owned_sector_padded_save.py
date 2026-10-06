# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Lachlan Fysh
# Original authored source selected for review. re/tools/coldfire_emu/lfo_four_owned_sector_padded_save.py; lines 1-96.
# Unresolved integration bindings: see DEPENDENCIES.json.
"""Derive sector-owned save buffers without changing logical LF4S geometry.

Reassemble both complete accepted save callers, widening only their malloc,
zero and (cache caller) pre-zero extent check to the rounded sector length.
The checked writer gate must use that same transmitted count. Every original
codec/entry and every caller offset stays unchanged. No allocation-class slack
is borrowed: all bytes sent by the proposed writer are explicitly requested
and zeroed. This is guest composition, not native DMA/cache qualification.
"""
from dataclasses import replace
import hashlib

from . import lfo_four_owned_cache_save as cache

owned, C, native = cache.accepted, cache.C, cache.native
MAXIMUM = cache.MAXIMUM
BUFFER_BYTES = (MAXIMUM+511) & ~511


def owned_source(text):
    if text.count(' pea MAXIMUM\n') != 2:
        raise ValueError('exact malloc and zero source operands required')
    return text.replace(' pea MAXIMUM\n', ' pea BUFFER_BYTES\n')


def cache_source(text):
    if text.count(' pea MAXIMUM\n') != 2 or \
            text.count(' cmpal #(ARENA_END-MAXIMUM),%a4\n') != 1:
        raise ValueError('exact cache malloc/zero/extent operands required')
    if text.count('.text\n') != 1:
        raise ValueError('single cache source body required')
    return text.replace('.text\n', f'.equ BUFFER_BYTES,{BUFFER_BYTES:#x}\n.text\n').replace(
        ' pea MAXIMUM\n', ' pea BUFFER_BYTES\n').replace(
        ' cmpal #(ARENA_END-MAXIMUM),%a4\n',
        ' cmpal #(ARENA_END-BUFFER_BYTES),%a4\n')


def _header(ps, layout):
    constants = dict(CONTEXT_BYTES=layout.size, MAXIMUM=MAXIMUM, STOCK_BYTES=owned.STOCK_BYTES,
        WIRE_MAX=owned.WIRE_MAX, ARENA=native.heap.ARENA, ARENA_END=native.heap.ARENA_END,
        ROOT=C.production.BACKING, ROOT_BINDER=C.production.BINDER,
        OWNER_SLOT=native.owned.SLOT, VERIFY_CURRENT=C.PERSISTENCE+ps['verify_current'],
        OWNED_CODEC_SAVE=C.PERSISTENCE+ps['owned_save'], BUFFER_BYTES=BUFFER_BYTES)
    return ''.join(f'.equ {n},{v:#x}\n' for n,v in constants.items())


def apply(joined, ps, layout, slot):
    """Only five exact original instruction operands may differ; no overlays."""
    from . import lfo_four_named_write_length_gate as gate
    from .lfo_four_named_read_length_gate import _assemble
    old = dict(joined.components)[C.PERSISTENCE]
    gate._caller(old, ps, layout)
    gate._cache_caller(old, ps, layout, slot)
    text = _header(ps, layout)+owned_source(owned.SOURCE.read_text())
    cached = cache_source(cache.source(ps, layout, slot))
    result, changes = bytearray(old), []
    for prefix, source, expected_count in (('save_owned', text, 2),
                                         ('save_owned_cache', cached, 3)):
        code, symbols = _assemble(source)
        start = ps[prefix]
        original = old[start:start+len(code)]
        for name, offset in symbols.items():
            if name != '.text' and ps.get(name) != start+offset:
                raise ValueError('padded caller changes entry/layout: '+name)
        before = gate._instructions(original, C.PERSISTENCE+start)
        after = gate._instructions(code, C.PERSISTENCE+start)
        if len(before) != len(after):
            raise ValueError('padded caller changes instruction count')
        modified = []
        for (pc,a,_), (next_pc,b,_) in zip(before, after):
            if pc != next_pc or len(a) != len(b):
                raise ValueError('padded caller changes instruction layout')
            if a == b:
                continue
            valid = (a == b'\x48\x79'+MAXIMUM.to_bytes(4,'big') and
                     b == b'\x48\x79'+BUFFER_BYTES.to_bytes(4,'big')) or (
                     prefix == 'save_owned_cache' and
                     a == b'\xb9\xfc'+(native.heap.ARENA_END-MAXIMUM).to_bytes(4,'big') and
                     b == b'\xb9\xfc'+(native.heap.ARENA_END-BUFFER_BYTES).to_bytes(4,'big'))
            if not valid:
                raise ValueError(f'unexpected padded save change at {pc:#x}')
            modified.append(dict(pc=hex(pc), before=a.hex(), after=b.hex(), caller=prefix))
        if len(modified) != expected_count:
            raise ValueError('exact five padding operand changes required')
        changes.extend(modified)
        result[start:start+len(code)] = code
    proposed = replace(joined, components=tuple((a, bytes(result) if a==C.PERSISTENCE else b)
                                                for a,b in joined.components))
    C.manifest(proposed, ps, layout, slot)
    return proposed, dict(serialized_bytes=MAXIMUM, requested_bytes=BUFFER_BYTES,
        initialized_bytes=BUFFER_BYTES, transmitted_bytes=BUFFER_BYTES,
        padding_bytes=BUFFER_BYTES-MAXIMUM, allocator_class_bytes=0x400000,
        additional_executable_bytes=0, additional_mutable_bytes=0,
        old_component_sha256=hashlib.sha256(old).hexdigest(),
        new_component_sha256=hashlib.sha256(bytes(result)).hexdigest(), changes=changes,
        native_DMA_cache_qualified=False, physical_headroom_qualified=False)
