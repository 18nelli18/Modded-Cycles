# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Lachlan Fysh
# Original authored source selected for review. re/tools/lfo_reference.py; lines 1-52.
# Unresolved integration bindings: see DEPENDENCIES.json.
"""Original host-side reference for the documented stock LFO rate domain."""

from __future__ import annotations

from dataclasses import dataclass

_POWERS_OF_TWO = tuple(1 << exponent for exponent in range(12))


@dataclass(frozen=True)
class MultiplierSpec:
    index: int
    label: str
    synchronized: bool
    factor: int


def multiplier_spec(index: int) -> MultiplierSpec:
    """Return one of the 24 documented CC103 multiplier states."""

    if not isinstance(index, int) or not 0 <= index < 24:
        raise ValueError("CC103 multiplier index must be an integer in 0..23")
    synchronized = index < 12
    factor = _POWERS_OF_TWO[index % 12]
    prefix = "x" if synchronized else ""
    label = f"{prefix}{factor:g}".replace("2048", "2K").replace("1024", "1K")
    return MultiplierSpec(index, label, synchronized, factor)


def period_whole_notes(
    index: int, speed_magnitude: int = 1
) -> float:
    """Return the documented positive-speed period in whole notes.

    The manual's period table uses positive SPD magnitudes. This helper does
    not model the front-panel bipolar direction or an unobserved DSP phase
    accumulator.
    """

    if not isinstance(speed_magnitude, int) or not 1 <= speed_magnitude <= 64:
        raise ValueError("speed magnitude must be an integer in 1..64")
    return 128.0 / (speed_magnitude * multiplier_spec(index).factor)


def period_seconds(index: int, bpm: float, speed_magnitude: int = 1) -> float:
    """Return the product-level period using sync or fixed-120 BPM semantics."""

    if not isinstance(bpm, (int, float)) or bpm <= 0:
        raise ValueError("BPM must be positive")
    spec = multiplier_spec(index)
    base_bpm = bpm if spec.synchronized else 120.0
    return period_whole_notes(index, speed_magnitude) * 4.0 * 60.0 / base_bpm
