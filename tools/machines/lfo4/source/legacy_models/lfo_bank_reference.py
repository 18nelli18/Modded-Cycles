# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Lachlan Fysh
# Original authored source selected for review. re/tools/lfo_bank_reference.py; lines 1-194.
# Unresolved integration bindings: see DEPENDENCIES.json.
"""Original, host-only indexed extra-LFO proof contract (not stock firmware).

Consumes a freshly rebuilt *byte* workspace after stock conditioning/event
modulation. No stock-LFO simulation, device state, firmware or table data.
Extra instances are indexed; stock LFO1 is outside this bank. This is a
bounded square/triangle PITCH guest contract, not the final eight-control
product implementation.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from fractions import Fraction
import struct

from dsp_reference.coordinate_abi import (
    COMPACT_RECORDS_END_OFFSET, REGION_COUNT, region_slot_offset,
)

PHASE_MODULUS = 1 << 32
PITCH_SLOT = 10
RECORD_BYTES = 16
ACTIVE = 1
SQUARE = 0
# These compact-code bounds and waveform codes are the emulator-only guest
# contract.  They do not assert the stock firmware's native LFO semantics.
TRIANGLE = 1
DEPTH_MIN, DEPTH_MAX = -1024, 1024
# Only the q=10 stock event writer's nonnegative domain is established. This
# is a proof guard, not a claim that all stock PITCH inputs occupy that domain.
PROOF_PITCH_MIN, PROOF_PITCH_MAX = 0, 0x7FFF
_RECORD = struct.Struct(">IIhBBH2x")


def _integer(value, lower, upper, name):
    if type(value) is not int or not lower <= value <= upper:
        raise ValueError(f"{name} must be an integer in {lower}..{upper}")


def _waveform_q15(phase_u32: int, waveform: int) -> int:
    """Sample the guest's square/triangle wave at phase-after, upper16 only."""
    if waveform == SQUARE:
        return -0x7FFF if phase_u32 < PHASE_MODULUS // 2 else 0x7FFF
    coordinate = phase_u32 >> 16
    quadrant, fraction = coordinate >> 14, coordinate & 0x3FFF
    twice = fraction * 2
    if quadrant == 0:
        return twice
    if quadrant == 1:
        return 0x7FFF - twice
    if quadrant == 2:
        return -twice
    return -0x8000 + twice


def _round_away(numerator: int, denominator: int) -> int:
    """Nearest integer, with exact half cases rounded away from zero."""
    magnitude = (abs(numerator) + denominator // 2) // denominator
    return -magnitude if numerator < 0 else magnitude


@dataclass(frozen=True)
class ExtraLfo:
    """Proposed 16-byte volatile record; not a discovered stock RAM layout.

    +00 phase u32; +04 increment u32; +08 signed depth s16 (-1024..1024);
    +0a destination u8 (NONE=0/PITCH=10); +0b waveform u8 (square=0,
    triangle=1);
    +0c flags u16 (ACTIVE=1); +0e..0f reserved zero.
    Enabled zero-depth/NONE sources still advance. Disabled sources freeze.
    Phase advances modulo 2**32 before waveform sampling. Square uses exact
    signed depth; triangle scales its signed Q15 sample by depth and rounds to
    nearest/ties-away. Other future flag bits are rejected.
    """

    phase: int = 0
    increment: int = 0
    depth: int = 0
    destination: int = 0
    waveform: int = SQUARE
    flags: int = 0

    def __post_init__(self):
        _integer(self.phase, 0, PHASE_MODULUS - 1, "phase")
        _integer(self.increment, 0, PHASE_MODULUS - 1, "increment")
        _integer(self.depth, DEPTH_MIN, DEPTH_MAX, "compact depth")
        _integer(self.waveform, SQUARE, TRIANGLE, "waveform")
        _integer(self.flags, 0, ACTIVE, "flags")
        _integer(self.destination, 0, PITCH_SLOT, "destination")
        if self.destination not in (0, PITCH_SLOT):
            raise ValueError("proof destination must be NONE or PITCH")

    def to_bytes(self) -> bytes:
        return _RECORD.pack(self.phase, self.increment, self.depth,
                            self.destination, self.waveform, self.flags)

    @classmethod
    def from_bytes(cls, raw: bytes) -> ExtraLfo:
        if type(raw) is not bytes or len(raw) != RECORD_BYTES or any(raw[14:]):
            raise ValueError("exactly 16 bytes with zero reserved bytes required")
        return cls(*_RECORD.unpack(raw))

    def tick(self) -> tuple[int, ExtraLfo]:
        if not self.flags & ACTIVE:
            return 0, self
        phase = (self.phase + self.increment) % PHASE_MODULUS
        if self.waveform == SQUARE:
            delta = self.depth if phase >= PHASE_MODULUS // 2 else -self.depth
        else:
            sample = _waveform_q15(phase, self.waveform)
            delta = _round_away(sample * self.depth, 1 << 15)
        if self.destination != PITCH_SLOT:
            delta = 0
        return delta, replace(self, phase=phase)


@dataclass(frozen=True)
class PitchChange:
    region: int
    byte_offset: int
    base: int
    summed_delta: int
    effective: int
    decision: str


@dataclass(frozen=True)
class BankResult:
    workspace: bytes
    state: tuple[tuple[ExtraLfo, ...], ...]
    changes: tuple[PitchChange, ...]


def zero_bank(extra_instances: int = 1) -> tuple[tuple[ExtraLfo, ...], ...]:
    """Six region rows; extra index 0 is proposed LFO2, not stock LFO1."""
    _integer(extra_instances, 1, 7, "extra instance count")
    return tuple(tuple(ExtraLfo() for _ in range(extra_instances))
                 for _ in range(REGION_COUNT))


def apply_bank(stock_workspace: bytes, bank) -> BankResult:
    """Sum from one immutable stock base, clamp once, write PITCH only.

    Must be given this invocation's newly stock-built workspace, never the
    previous result. This pure function cannot prove caller provenance or
    actual stock rebuilding. Tests explicitly exercise the correct ordering.
    Unsupported negative stock codes are preserved, not silently clamped.
    All input validation precedes computation; input bytes/state never mutate.
    No interpretation of one native code as semitones/MIDI units is made.
    """
    if type(stock_workspace) is not bytes or len(stock_workspace) < COMPACT_RECORDS_END_OFFSET:
        raise ValueError("immutable complete compact byte workspace required")
    rows = tuple(tuple(row) for row in bank)
    if len(rows) != REGION_COUNT:
        raise ValueError("exactly six region rows required")
    count = len(rows[0])
    _integer(count, 1, 7, "extra instance count")
    if any(len(row) != count or any(type(s) is not ExtraLfo for s in row) for row in rows):
        raise ValueError("rectangular six-region ExtraLfo bank required")
    effective = bytearray(stock_workspace)
    next_rows, changes = [], []
    for region, row in enumerate(rows):
        ticks = tuple(source.tick() for source in row)
        next_rows.append(tuple(state for _, state in ticks))
        total = sum(delta for delta, _ in ticks)
        offset = region_slot_offset(region, PITCH_SLOT)
        base = int.from_bytes(stock_workspace[offset:offset + 2], "big", signed=True)
        value, decision = base, "ZERO_CONTRIBUTION"
        if total and not PROOF_PITCH_MIN <= base <= PROOF_PITCH_MAX:
            decision = "SKIP_UNPROVEN_BASE_DOMAIN"
        elif total:
            value = min(PROOF_PITCH_MAX, max(PROOF_PITCH_MIN, base + total))
            decision = "CLAMPED" if value != base + total else "APPLIED"
            effective[offset:offset + 2] = value.to_bytes(2, "big", signed=True)
        changes.append(PitchChange(region, offset, base, total, value, decision))
    return BankResult(bytes(effective), tuple(next_rows), tuple(changes))


def extra_state_bytes(total_instances: int) -> int:
    """Additional proposed records only: total count includes untouched LFO1."""
    _integer(total_instances, 2, 8, "total instance count")
    return REGION_COUNT * (total_instances - 1) * RECORD_BYTES


def nominal_rate(increment: int, *, updates_per_second: Fraction) -> Fraction:
    """Conditional host phase rate; caller must supply a justified cadence.

    Does not recover stock Speed/Multiplier mappings, actual firmware update
    rate, or audio alias behavior. Zero increment explicitly yields zero.
    """
    _integer(increment, 0, PHASE_MODULUS - 1, "increment")
    if not isinstance(updates_per_second, Fraction) or updates_per_second <= 0:
        raise ValueError("positive exact Fraction cadence required")
    return updates_per_second * increment / PHASE_MODULUS
