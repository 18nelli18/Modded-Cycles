# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Lachlan Fysh
# Original authored source selected for review. re/tools/coldfire_emu/live_profile_candidate/native_adapter/safe_enum/model.py; lines 1-30.
# Unresolved integration bindings: see DEPENDENCIES.json.
"""Independent offline specification, not guest instruction execution."""
from dataclasses import dataclass

@dataclass(frozen=True)
class Result:
    count: int
    status: int

def enumerate_into(extra, buffer, capacity, words, lookup, flags, protected):
    # Caller supplies retained spans; native admission is a separate callout.
    if type(buffer) is not int or not 0 < buffer < 2**32 or buffer % 4:
        return Result(0,14)
    if type(capacity) is not int or capacity < 33:
        return Result(0,13)
    if capacity > 0x3fffffff or buffer+4*capacity >= 2**32:
        return Result(0,14)
    first, status = lookup(extra,0)
    if status:
        return Result(0,status)
    if any(buffer < start+size and start < buffer+4*capacity for start,size in protected):
        return Result(0,15)
    count = 0
    for ordinal in range(33):
        descriptor,status = (first,0) if ordinal==0 else lookup(extra,ordinal)
        if status:
            return Result(0,status)
        if descriptor and flags(descriptor) & 0x600 == 0x600:
            words[count] = descriptor
            count += 1
    return Result(count,0)
