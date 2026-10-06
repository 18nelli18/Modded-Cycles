# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Lachlan Fysh
# Original authored source selected for review. re/tools/coldfire_emu/lfo_four_publication_contract.py; lines 1-44.
# Unresolved integration bindings: see DEPENDENCIES.json.
"""Join-only comparison: private snapshots must include preceding publications.

These functions check/compute expectations. They never supply a DSP result to
the emulator. Numerical reference outputs must come from original CPU code.
"""
WORK_BYTES = 476


def expected_private_input(live, controls):
    if type(live) is not bytes or len(live) != WORK_BYTES:
        raise ValueError("complete live W required")
    if len(controls) != 6 or any(type(c) is not bytes or len(c) != 16 for c in controls):
        raise ValueError("six independent native control rows required")
    result = bytearray(live)
    for track,control in enumerate(controls):
        offset = 16+66*track
        result[offset:offset+16] = control
    return bytes(result)


def advance_expected_publication(live, private_input, original_output):
    if any(type(w) is not bytes or len(w) != WORK_BYTES for w in (live,private_input,original_output)):
        raise ValueError("complete workspace witnesses required")
    result = bytearray(live)
    for track in range(6):
        destination = private_input[22+66*track]
        if destination == 0:
            continue
        if not 10 <= destination <= 22:
            raise ValueError("non-product destination")
        depth = int.from_bytes(private_input[30+66*track:32+66*track], "big")
        if depth == 0x4000:
            continue  # Native zero delta may still clamp an unrelated base.
        offset = 14+66*track+2*destination
        result[offset:offset+2] = original_output[offset:offset+2]
    return bytes(result)


def compare_snapshot(live,controls,captured):
    expected = expected_private_input(live,controls)
    if captured != expected:
        first = next((i for i,(a,b) in enumerate(zip(expected,captured)) if a != b),None)
        raise AssertionError(("private snapshot lost preceding publication",first))
    return expected
