# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Lachlan Fysh
# Original authored source selected for review. re/tools/coldfire_emu/lfo_four_pending_state_contract.py; lines 1-118.
# Unresolved integration bindings: see DEPENDENCIES.json.
"""Optional pending-worker snapshot; no installation or Runtime mutation.

The parent may call snapshot(r) ONLY for pending.execute's before/after pair.
Without that explicit hook, the existing whole-byte r.snapshot() contract stays
strict. This helper calls it unchanged and excludes exactly canonical PAYLOAD's
first 48 bytes from the pending context comparison, never its remaining 32.

The existing four-key comparison also checks root/Project and the same tracked
CTX allocation through live_context's composite digest. Raw context hash and
scratch hex remain evidence, not comparison keys. All reads require the parent's
existing synchronous exclusion; allocator tracking is not physical proof.

The integration separately captures progress at pre-JSR P, including the
16-byte copied object; writer W must satisfy W=P-144 and progress=P+40=W+184
with all 16 object bytes unchanged. That observation does not expand this mask.
"""
import hashlib
import json

from .test_lfo2_owned_heap_setup import ARENA, ARENA_END


SCRATCH_BYTES = 48
CANONICAL_LAYOUT = dict(capacity=6720, table=32, stage=349472,
                        payload=698912, size=698992, row_bytes=52,
                        wire_max=349468, table_bytes=349440)
COMPARISON_KEYS = ('owner', 'live_context', 'context_slot', 'publication')
STRICT_KEYS = (*COMPARISON_KEYS, 'logical_stock', 'real_Project')


def _require(condition, message):
    if not condition:
        raise ValueError('pending state contract: ' + message)


def validate_layout(layout):
    """Refuse any drift before computing an excluded byte range."""
    fields = {name: getattr(layout, name, None) for name in CANONICAL_LAYOUT}
    _require(all(type(value) is int for value in fields.values()),
             'canonical integer Layout fields required')
    _require(fields == CANONICAL_LAYOUT, 'canonical full Layout required')
    capacity, row = fields['capacity'], fields['row_bytes']
    _require(fields['table_bytes'] == capacity * row and
             fields['stage'] == fields['table'] + fields['table_bytes'] and
             fields['payload'] == fields['stage'] + fields['table_bytes'] and
             fields['wire_max'] == 28 + fields['table_bytes'] and
             fields['size'] == fields['payload'] + 80 and
             fields['payload'] + SCRATCH_BYTES == fields['size'] - 32,
             'payload/table/tail bounds')
    return fields


def _allocation(r, size):
    pointer = r.ctx
    _require(type(pointer) is int and pointer % 16 == 0 and
             ARENA <= pointer <= ARENA_END - size, 'CTX pointer/extent')
    record = r.live.get(pointer)
    _require(isinstance(record, dict), 'CTX missing live allocation')
    _require(type(record.get('requested_bytes')) is int and
             record['requested_bytes'] == size, 'CTX requested extent')
    _require(record.get('returned') is True and
             record.get('released', False) is False, 'CTX allocation lifetime')
    extent = record.get('class_bytes')
    _require(type(extent) is int and extent >= size and
             pointer + extent <= ARENA_END, 'CTX allocator class extent')
    _require(pointer in r.pinned, 'CTX no longer retained/pinned')
    _require(record.get('pointer') == hex(pointer), 'CTX tracked malloc result')
    _require(type(record.get('return_pc')) is int and
             0 <= record['return_pc'] <= 0xffffffff and
             isinstance(record.get('phase'), str) and record['phase'],
             'CTX allocation provenance fields')
    # The tracer retains malloc dictionaries in allocations. Their identity
    # distinguishes a new lifetime at an old address without a new global or
    # a synthesized guest generation. Valid only within this retained runtime.
    _require(any(item is record for item in r.allocations),
             'CTX record absent from tracked allocation history')
    return dict(pointer=hex(pointer), record_id=id(record),
                requested_bytes=size, class_bytes=extent,
                return_pc=hex(record['return_pc']), phase=record['phase'])


def snapshot(r):
    """Return JSON-safe hashes/evidence for the optional pending-only hook.

    live_context combines the context-minus-48 digest, strict root/Project
    hashes and tracked allocation identity. Comparing COMPARISON_KEYS therefore
    rejects every strict-state mutation, including root/Project and ABA reuse.
    context_semantic_sha256 describes context bytes alone; raw_context_sha256
    and gather_scratch deliberately differ after a legitimate gather.
    """
    layout = validate_layout(r.layout)
    allocation = _allocation(r, layout['size'])
    strict = r.snapshot()
    _require(isinstance(strict, dict) and all(name in strict for name in STRICT_KEYS),
             'complete strict Runtime snapshot required')
    _require(all(isinstance(strict[name], str) and len(strict[name]) == 64 and
                 all(char in '0123456789abcdef' for char in strict[name])
                 for name in STRICT_KEYS), 'strict SHA256 fields required')
    raw = r.cpu.read(r.ctx, layout['size'])
    _require(isinstance(raw, bytes) and len(raw) == layout['size'],
             'short/non-byte CTX read')
    raw_hash = hashlib.sha256(raw).hexdigest()
    _require(raw_hash == strict['live_context'], 'CTX changed during snapshot')
    start, end = layout['payload'], layout['payload'] + SCRATCH_BYTES
    semantic = hashlib.sha256(raw[:start] + raw[end:]).hexdigest()
    comparison = dict(context=semantic, allocation=allocation,
                      logical_stock=strict['logical_stock'], real_Project=strict['real_Project'])
    digest = hashlib.sha256(json.dumps(comparison, sort_keys=True,
                                      separators=(',', ':')).encode()).hexdigest()
    return dict(strict, live_context=digest, context_semantic_sha256=semantic,
                pending_state_contract='canonical_full_context_minus_gather48_v1',
                context_layout=layout,
                raw_context_sha256=raw_hash, context_allocation=allocation,
                gather_scratch=dict(offset=start, end_exclusive=end, bytes=SCRATCH_BYTES,
                                    address=hex(r.ctx + start), hex=raw[start:end].hex(),
                                    sha256=hashlib.sha256(raw[start:end]).hexdigest(),
                                    remaining_strict_tail_bytes=32,
                                    whole_80_byte_tail_unused_proven=False))
