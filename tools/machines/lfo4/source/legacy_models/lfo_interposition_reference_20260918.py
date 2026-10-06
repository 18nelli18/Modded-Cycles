# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Lachlan Fysh
# Original authored source selected for review. re/tools/lfo_interposition_reference_20260918.py; lines 1-74.
# Unresolved integration bindings: see DEPENDENCIES.json.
"""Host-side contract model for post-conditioning LFO2 injection.

The model represents the proposed wrapper around FUN_40056e24.  The stock
compact conditioner runs first; a bounded PITCH delta is then applied to one
compact halfword.  It contains no firmware data and does not claim the native
PITCH domain until a runtime capture supplies it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, MutableSequence, Sequence


PITCH_DESTINATION = 10
COMPACT_BASE = 0x8000100C
COMPACT_PITCH_OFFSET = 0x22
COMPACT_REGION_STRIDE = 0x42
REGION_COUNT = 6


@dataclass(frozen=True)
class LfoState:
    active: bool = False
    destination: int = PITCH_DESTINATION
    delta: int = 0


def pitch_index(region: int) -> int:
    if not 0 <= region < REGION_COUNT:
        raise ValueError("region must be in 0..5")
    return COMPACT_PITCH_OFFSET + COMPACT_REGION_STRIDE * region


def interpose_compact(
    compact: MutableSequence[int],
    region: int,
    lfos: Sequence[LfoState],
    stock_conditioner: Callable[[MutableSequence[int]], object],
    native_domain: tuple[int, int] | None = None,
) -> object:
    """Run stock conditioning, then apply summed post-conditioning deltas.

    ``stock_conditioner`` is expected to rebuild the compact workspace on
    every invocation.  That makes repeated calls test the real non-accumulation
    invariant rather than relying on restoration of an input record.  The
    optional domain is deliberately explicit: no 0..0x7fff PITCH assumption is
    made by this model.
    """

    index = pitch_index(region)
    result = stock_conditioner(compact)
    active = [
        state for state in lfos
        if state.active and state.destination == PITCH_DESTINATION
        and state.delta != 0
    ]
    if not active:
        return result

    base = compact[index]
    effective = base + sum(state.delta for state in active)
    if native_domain is not None:
        lower, upper = native_domain
        if lower > upper:
            raise ValueError("native domain must be ordered")
        effective = max(lower, min(upper, effective))
    compact[index] = effective
    return result


# Retain the old symbol only as a diagnostic compatibility alias.  New callers
# must use interpose_compact so the post-conditioning contract is explicit.
interpose_pitch = interpose_compact
