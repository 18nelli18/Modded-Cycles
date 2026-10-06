# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Lachlan Fysh
# Original authored source selected for review. re/tools/coldfire_emu/lfo_four_owned_temporary_incoming.py; lines 1-109.
# Unresolved integration bindings: see DEPENDENCIES.json.
"""BUILD-ONLY allocator-owned temporary read preparation; no CPU evidence.

temporary_prepare(manager, live_ctx, slot0..96) returns the same owned handle
as lean_prepare. Slot96 aliases fixed mode2: the caller must exclude that
route as well as Project/UI/cache/publication/teardown and allocator observers
through preparation and release. The original named reader/validator and
PRIVATE_DECODE operate on actual allocations, with no publication or switch.
Declared source/allocator/ABI prerequisites remain those of owned incoming.
No length probe, installation, metadata seed, new codec or persistent state.
"""
from dataclasses import replace
from pathlib import Path
import hashlib
import re

from . import lfo_four_owned_incoming_lean as lean

owned, native, C = lean.accepted, lean.native, lean.C
STOCK_BYTES, WIRE_MAX, MAXIMUM = lean.STOCK_BYTES, lean.WIRE_MAX, lean.MAXIMUM
WRAPPER_FRAME_BYTES = 44  # Saved A6 + 40-byte MOVEM; no local storage.
CALLER_SOURCE_SHA256 = 'e8221f4236b9438d4aee469e6fdd6266ed08aa56edc04f35d9414f3b4f09d249'
LEAN_MODULE_SHA256 = '87056ff82ba85859c43ecfd8c4e07b79cbb025688c98ac004ffd4bcc2f033ada'
LEAN_BODY_SHA256 = '1ff9777b8aa0f1fc6bd150ed0ef95589185b5dc7edf1d31d40fbb4157b4191d6'


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _transform(authored):
    """Exactly one unsigned-bound change and a complete label rename."""
    guard = ' cmpil #96,%d0\n bcc lean_refused\n'
    if authored.count(guard) != 1:
        raise ValueError('complete lean slot admission changed')
    authored = authored.replace(guard, ' cmpil #96,%d0\n bhi lean_refused\n', 1)
    return re.sub(r'\blean_[a-z_]+\b', lambda m: 'temporary_' + m[0][5:], authored)


def source(ps, layout, slot):
    """Derive the whole pinned lean source, including its constant header."""
    if _sha(owned.SOURCE.read_bytes()) != CALLER_SOURCE_SHA256:
        raise ValueError('complete incoming source changed; explicit review required')
    if _sha(Path(lean.__file__).read_bytes()) != LEAN_MODULE_SHA256:
        raise ValueError('complete lean derivation changed; explicit review required')
    if (layout.size, owned.HANDLE_BYTES, STOCK_BYTES, WIRE_MAX, MAXIMUM) != (
            698992, 32, 0x210404, 349468, 2513184):
        raise ValueError('incoming allocation/size contract changed')
    for name in ('verify_current', 'create', 'incoming_load', 'incoming_padding_zero'):
        if type(ps.get(name)) is not int or ps[name] < 0:
            raise ValueError('complete incoming target symbols required: ' + name)
    authored = lean.source(ps, layout, slot)
    if _sha(authored[authored.index('lean_prepare:\n'):].encode()) != LEAN_BODY_SHA256:
        raise ValueError('complete lean source body changed')
    return _transform(authored)


def append(joined, ps, layout, slot):
    """Append to a complete supplied composition, preserving all prior bytes.

    The full incoming body proves the unchanged release contract: bounds,
    alignment, magic LFIN and state1, followed by freeing context/buffer/handle;
    no slot restriction. Reassembly checks its every label, including release.
    The legacy writer may be padded; no writer or whole-prefix pin is imposed.
    Assembler input is stdin; no assembly source is created or modified.
    """
    from . import lfo_four_named_read_length_gate as gate
    components = dict(joined.components)
    if len(components) != len(joined.components) or C.PERSISTENCE not in components:
        raise ValueError('unique supplied incoming code component required')
    if any(name.startswith('temporary_') for name in ps):
        raise ValueError('temporary operation already appended')
    old = components[C.PERSISTENCE]
    gate._caller(old, ps, layout, slot)
    gate._caller(old, ps, layout, slot, is_lean=True)
    code, offsets = gate._assemble(source(ps, layout, slot))
    if offsets.get('temporary_prepare') != 0 or len(old) & 1:
        raise ValueError('temporary append entry moved or prefix unaligned')
    symbols = dict(ps, **{name: len(old) + offset for name, offset in offsets.items()
                         if name.startswith('temporary_')})
    complete = old + code
    gate._caller(complete, symbols, layout, slot, is_temporary=True)
    result = replace(joined, components=tuple(
        (address, complete if address == C.PERSISTENCE else payload)
        for address, payload in joined.components))
    C.manifest(result, symbols, layout, slot)  # Existing component overlap check.
    return result, symbols, layout, slot


def manifest(joined, ps, layout, slot):
    from . import lfo_four_named_read_length_gate as gate
    identity = gate._caller(dict(joined.components)[C.PERSISTENCE], ps, layout, slot,
                            is_temporary=True)
    gate._caller(dict(joined.components)[C.PERSISTENCE], ps, layout, slot)
    return dict(build_only=True, guest_executed=False, installed=False,
        physical_placement_qualified=False, frame_provenance_proven=False,
        temporary_prepare_entry=hex(identity['entry']), caller=identity,
        temporary_release_entry=hex(C.PERSISTENCE + ps['incoming_release']),
        release_contract_reassembled=True, release_accepts_slot96=True,
        slot_range=[0, 96], slot96_fixed_mode_alias=2,
        extra_mutable_bytes=0, wrapper_frame_bytes=WRAPPER_FRAME_BYTES,
        allocation_requests=[owned.HANDLE_BYTES, MAXIMUM, layout.size],
        allocation_classes=[32, 0x400000, 0x100000],
        memory_schedule=lean.memory_schedule(), requested_zeroed_bytes=MAXIMUM,
        private_context_published=False, Project_switch=False,
        temporary_allocator_exclusion_required=True,
        ownership_prerequisites='authentic original calloc/malloc lifetime; '
            'original callees preserve A4/A6; constructor-backed owner/live context; '
            'serialized Project/UI/cache/publication/teardown/allocator and fixed mode2',
        read_length_gate_required=True, native_partial_read_copies_requested_bytes=True)
