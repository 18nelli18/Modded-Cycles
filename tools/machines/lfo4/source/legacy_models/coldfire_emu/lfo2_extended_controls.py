# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Lachlan Fysh
# Original authored source selected for review. re/tools/coldfire_emu/lfo2_extended_controls.py; lines 1-390.
# Unresolved integration bindings: see DEPENDENCIES.json.
"""Explicit-input LFO2 control model for controls beyond the guest proof.

This module is deliberately separate from native UI routing and the shared
DSP/backend.  Its configured SPEED input is an already-decoded signed C+0x02
value supplied by the shared LFO1/LFO2 configured-speed owner; it is not an
effective or p-locked speed.  Multiplier, signed depth, and waveform are
independent LFO2 config.  Audio phase remains in ``AudioPhaseBank``.

Depth units are compact PITCH-code units: adding +1 changes the compact
``C[r]+0x14`` halfword by one code when the waveform is at +1.  This is not a
semitone, MIDI-note, or calibrated audible-pitch claim.  The model bounds depth
to +/-1024 codes and clamps the final PITCH sum to the already-proven compact
proof domain 0..0x7fff.  Only PITCH is modeled.

The extended signed-depth/triangle controls map to the emulator-only wrapper
record contract. ``project_guest_runner_config`` remains deliberately pinned
to the stock DEPTH edit adapter's current track-0/square/depth-0-or-1 subset;
the separate published-bank output demo carries extended controls through the
broader original-CPU output runner.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from enum import IntEnum
import threading

from .lfo2_ui_config_bank import (
    AudioPhaseBank,
    LFO2_DEPTH_MAX_COMPACT_UNITS,
    LFO2_DEPTH_MIN_COMPACT_UNITS,
    GUEST_PHASE_MODULUS,
    MAX_MULTIPLIER,
    PublishedTrackSnapshot,
    RateMapping,
    map_native_rate,
)
from lfo_bank_reference import ACTIVE, ExtraLfo


TRACK_COUNT = 6
# Explicit prototype arithmetic envelope, not a recovered stock/native limit.
DEPTH_MIN_COMPACT_UNITS = LFO2_DEPTH_MIN_COMPACT_UNITS
DEPTH_MAX_COMPACT_UNITS = LFO2_DEPTH_MAX_COMPACT_UNITS
PITCH_MIN_COMPACT_CODE = 0
PITCH_MAX_COMPACT_CODE = 0x7FFF
PITCH_DESTINATION = 10
Q15_POSITIVE_ONE = 0x7FFF
Q15_SCALE = 1 << 15
SQUARE = 0
TRIANGLE = 1


class Waveform(IntEnum):
    SQUARE = SQUARE
    TRIANGLE = TRIANGLE


def _track(track_id: int) -> None:
    if type(track_id) is not int or not 0 <= track_id < TRACK_COUNT:
        raise ValueError("track_id must be an integer in 0..5")


def _signed_speed(value: int) -> None:
    if type(value) is not int or not -0x8000 <= value <= 0x7FFF:
        raise ValueError("configured native SPEED must be signed C+0x02 in -32768..32767")


def _trunc_div(numerator: int, denominator: int) -> int:
    """Integer division rounded toward zero, independent of Python floor rules."""
    if denominator <= 0:
        raise ValueError("denominator must be positive")
    return (numerator // denominator if numerator >= 0
            else -((-numerator) // denominator))


def stock_depth_raw_to_compact_units(raw_depth: int) -> int:
    """Map the stock DEPTH field into this prototype's signed compact units.

    Literal formatter evidence says stock descriptor-36 displays
    ``(raw_depth - 0x4000) / 0x100``. This project mapping deliberately treats
    one displayed DEPTH unit as one compact PITCH-code step per wrapper
    invocation; it does **not** claim that stock firmware uses that DSP scale
    or that a code step is a semitone. Fractional displayed values truncate
    toward zero because compact C stores an integer halfword; e.g. 0.5 can
    change the stored/editor value yet quantize to a zero compact contribution.
    """
    if type(raw_depth) is not int or not 0 <= raw_depth <= 0x7F00:
        raise ValueError("stock DEPTH raw value must be an integer in 0..0x7f00")
    centered_q8_8 = raw_depth - 0x4000
    return _trunc_div(centered_q8_8, 0x100)


@dataclass(frozen=True)
class Lfo2ControlConfig:
    multiplier_code: int = 0
    depth_compact_units: int = 0
    waveform: Waveform = Waveform.SQUARE
    destination_code: int = PITCH_DESTINATION


@dataclass(frozen=True)
class TrackControlSnapshot:
    track_id: int
    generation: int
    configured_speed_native: int | None
    config: Lfo2ControlConfig


@dataclass(frozen=True)
class MappedTrackControls:
    track_id: int
    generation: int
    configured_speed_native: int | None
    config: Lfo2ControlConfig
    rate: RateMapping


def map_published_track_snapshot(
        snapshot: PublishedTrackSnapshot) -> MappedTrackControls:
    """Convert one immutable bank publication into the control-model view.

    This is a host/emulator handoff: it consumes a complete acquired snapshot
    without re-reading mutable UI draft state. It does not establish MCU
    atomicity, cache coherency, or real-time memory ordering.
    """
    if not isinstance(snapshot, PublishedTrackSnapshot):
        raise TypeError("snapshot must be PublishedTrackSnapshot")
    lfo2 = snapshot.lfo2
    if lfo2.instance_id != 2:
        raise ValueError("published snapshot does not describe LFO2")
    if type(lfo2.multiplier) is not int or not 0 <= lfo2.multiplier <= MAX_MULTIPLIER:
        raise ValueError("published multiplier is outside 0..23")
    if (type(lfo2.depth) is not int or not DEPTH_MIN_COMPACT_UNITS <= lfo2.depth <=
            DEPTH_MAX_COMPACT_UNITS):
        raise ValueError("published depth is outside signed compact-code bounds")
    if type(lfo2.waveform) is not int or lfo2.waveform not in (SQUARE, TRIANGLE):
        raise ValueError("published waveform is not square or triangle")
    if type(lfo2.destination) is not int or lfo2.destination not in (0, PITCH_DESTINATION):
        raise ValueError("published destination is outside NONE/PITCH prototype")
    config = Lfo2ControlConfig(
        multiplier_code=lfo2.multiplier,
        depth_compact_units=lfo2.depth,
        waveform=Waveform(lfo2.waveform),
        destination_code=lfo2.destination,
    )
    return MappedTrackControls(
        snapshot.track_id, snapshot.config_generation,
        snapshot.linked_native_speed, config, snapshot.rate)


@dataclass(frozen=True)
class PitchEvaluation:
    phase_before_u32: int
    phase_after_u32: int
    waveform_q15: int
    depth_compact_units: int
    delta_compact_units: int
    base_pitch_code: int
    unclamped_pitch_code: int
    effective_pitch_code: int
    decision: str


class Lfo2ExtendedControlModel:
    """Six independent config banks driven by explicitly supplied base SPEED.

    This is not the native editor/BankPort adapter.  It supplies the eventual
    config contract while native selected-track routing is incomplete.  Calls
    to ``edit`` never touch phase; phase storage is a separate object owned by
    the audio-side caller.
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._configs = [Lfo2ControlConfig() for _ in range(TRACK_COUNT)]
        self._speeds: list[int | None] = [None] * TRACK_COUNT
        self._generations = [0] * TRACK_COUNT

    def set_linked_configured_speed(self, track_id: int,
                                    native_speed: int | None) -> TrackControlSnapshot:
        """Supply shared configured SPEED already decoded by its stock owner."""
        _track(track_id)
        if native_speed is not None:
            _signed_speed(native_speed)
        with self._lock:
            if self._speeds[track_id] != native_speed:
                self._speeds[track_id] = native_speed
                self._generations[track_id] += 1
            return self._snapshot_locked(track_id)

    def edit(self, track_id: int, control: str, value: object) -> TrackControlSnapshot:
        """Edit only LFO2 MUL, signed PITCH depth, or square/triangle shape."""
        _track(track_id)
        if type(control) is not str or control not in (
                "multiplier", "depth", "waveform"):
            raise ValueError("supported controls are multiplier, depth, waveform")
        if control == "multiplier":
            if type(value) is not int or not 0 <= value <= MAX_MULTIPLIER:
                raise ValueError("multiplier code must be an integer in 0..23")
        elif control == "depth":
            if (type(value) is not int or
                    not DEPTH_MIN_COMPACT_UNITS <= value <= DEPTH_MAX_COMPACT_UNITS):
                raise ValueError("depth must be signed compact PITCH units in -1024..1024")
        else:
            if type(value) is not int or value not in (SQUARE, TRIANGLE):
                raise ValueError("waveform code must be square=0 or triangle=1")
        with self._lock:
            if control == "multiplier":
                candidate = replace(self._configs[track_id], multiplier_code=value)
            elif control == "depth":
                candidate = replace(self._configs[track_id], depth_compact_units=value)
            else:
                candidate = replace(self._configs[track_id], waveform=Waveform(value))
            if self._configs[track_id] != candidate:
                self._configs[track_id] = candidate
                self._generations[track_id] += 1
            return self._snapshot_locked(track_id)

    def read(self, track_id: int) -> TrackControlSnapshot:
        _track(track_id)
        with self._lock:
            return self._snapshot_locked(track_id)

    def map(self, track_id: int, native_rate_scalar: int) -> MappedTrackControls:
        """Map linked configured SPEED and independent MUL via the stock equation."""
        snapshot = self.read(track_id)
        rate = map_native_rate(snapshot.configured_speed_native,
                               snapshot.config.multiplier_code,
                               native_rate_scalar)
        return MappedTrackControls(
            snapshot.track_id, snapshot.generation,
            snapshot.configured_speed_native, snapshot.config, rate)

    def _snapshot_locked(self, track_id: int) -> TrackControlSnapshot:
        return TrackControlSnapshot(
            track_id, self._generations[track_id], self._speeds[track_id],
            self._configs[track_id])


def waveform_q15(phase_u32: int, waveform: Waveform | int) -> int:
    """Return signed Q1.15-ish square/triangle sample at a Q0.32 phase.

    Square starts negative and switches positive at half-cycle, matching the
    existing guest proof polarity. Triangle samples phase[31:16] as four
    contiguous linear quadrants: 0 at phase 0, +peak at quarter-cycle, 0 at
    half-cycle, -peak at three-quarter-cycle, then back to 0. Endpoints match
    the candidate guest arithmetic (+32767/-32768); no cadence or analog
    waveform claim is made.
    """
    if type(phase_u32) is not int or not 0 <= phase_u32 < GUEST_PHASE_MODULUS:
        raise ValueError("phase_u32 must be an unsigned 32-bit phase")
    # Numeric equality alone is not enough here: bool and float values compare
    # equal to 0/1 in Python, but a waveform selector is a discrete config code.
    if (not (type(waveform) is int or isinstance(waveform, Waveform)) or
            waveform not in (SQUARE, TRIANGLE)):
        raise ValueError("waveform must be square=0 or triangle=1")
    if waveform == SQUARE:
        return -Q15_POSITIVE_ONE if phase_u32 < 0x80000000 else Q15_POSITIVE_ONE
    coordinate = phase_u32 >> 16
    quadrant, fraction = coordinate >> 14, coordinate & 0x3FFF
    twice = fraction * 2
    if quadrant == 0:
        return twice
    if quadrant == 1:
        return Q15_POSITIVE_ONE - twice
    if quadrant == 2:
        return -twice
    return -0x8000 + twice


def _round_away(numerator: int, denominator: int) -> int:
    """Round a signed ratio to nearest, with exact halves away from zero."""
    if denominator <= 0:
        raise ValueError("denominator must be positive")
    magnitude = (abs(numerator) + denominator // 2) // denominator
    return -magnitude if numerator < 0 else magnitude


def evaluate_pitch_step(mapped: MappedTrackControls, phase_before_u32: int,
                        base_pitch_code: int) -> PitchEvaluation:
    """Evaluate one reference-model update; does not mutate persistent phase.

    Operation order is explicit: advance modulo 2^32; sample waveform; apply
    exact signed square depth or Q15 triangle scaling with symmetric
    nearest-integer/ties-away quantization; add to the immutable base; clamp
    the final compact code once. A depth of zero is exactly neutral while the
    phase still advances, like the existing enabled-neutral guest contract.
    """
    if not isinstance(mapped, MappedTrackControls):
        raise TypeError("mapped must be MappedTrackControls")
    if type(phase_before_u32) is not int or not 0 <= phase_before_u32 < GUEST_PHASE_MODULUS:
        raise ValueError("phase_before_u32 must be an unsigned 32-bit phase")
    if type(base_pitch_code) is not int or not (
            PITCH_MIN_COMPACT_CODE <= base_pitch_code <= PITCH_MAX_COMPACT_CODE):
        raise ValueError("base PITCH must be in the proven compact proof domain 0..32767")
    increment = mapped.rate.guest_phase_increment_u32
    if increment is None:
        raise ValueError(f"cannot evaluate unresolved rate: {mapped.rate.status}")
    phase_after = (phase_before_u32 + increment) & 0xFFFFFFFF
    depth = mapped.config.depth_compact_units
    q15 = waveform_q15(phase_after, mapped.config.waveform)
    if mapped.config.waveform == Waveform.SQUARE:
        # Preserve the guest proof's exact bipolar square mapping, including
        # depth values smaller than the Q15 denominator.
        delta = depth if phase_after >= 0x80000000 else -depth
    else:
        # Symmetric nearest-integer quantization makes ±1 depth at the two
        # triangle peaks produce +1/-1 rather than a one-sided truncation bias.
        delta = _round_away(q15 * depth, Q15_SCALE)
    unclamped = base_pitch_code + delta
    effective = min(PITCH_MAX_COMPACT_CODE,
                    max(PITCH_MIN_COMPACT_CODE, unclamped))
    decision = ("NEUTRAL" if delta == 0 else
                "CLAMPED" if effective != unclamped else "APPLIED")
    return PitchEvaluation(phase_before_u32, phase_after, q15, depth,
                           delta, base_pitch_code, unclamped, effective, decision)


def project_guest_runner_config(mapped: MappedTrackControls,
                                phase_bank: AudioPhaseBank) -> dict | None:
    """Project the current native DEPTH editor subset into runner settings.

    ``None`` means not accepted by the persistent integration runner, whose
    native-DEPTH edit adapter admits any of the six regions, square waveform
    and depth 0/1. The output runner also accepts extended signed/triangle
    records, projected separately through :func:`project_guest_wrapper_record`.
    This helper does not execute either path.
    """
    if not isinstance(mapped, MappedTrackControls):
        raise TypeError("mapped must be MappedTrackControls")
    if not isinstance(phase_bank, AudioPhaseBank):
        raise TypeError("phase_bank must be AudioPhaseBank")
    config = mapped.config
    if (type(mapped.track_id) is not int or not 0 <= mapped.track_id < 6 or
            mapped.rate.guest_phase_increment_u32 is None or
            config.destination_code != PITCH_DESTINATION or
            not isinstance(config.waveform, Waveform) or
            config.waveform is not Waveform.SQUARE or
            type(config.depth_compact_units) is not int or
            config.depth_compact_units not in (0, 1)):
        return None
    return {
        "instances": 1,
        "region": mapped.track_id,
        "phase": phase_bank.read_audio_owned(mapped.track_id).phase_u32,
        "increment": mapped.rate.guest_phase_increment_u32,
        "depth": config.depth_compact_units,
        "destination": PITCH_DESTINATION,
        "waveform": SQUARE,
        "cancel_second": False,
        "initially_enabled": True,
        "disable_at": 1,
    }


def project_guest_wrapper_record(mapped: MappedTrackControls,
                                 phase_bank: AudioPhaseBank, *,
                                 active: bool = True) -> ExtraLfo | None:
    """Project one track's explicit controls into the emulator sidecar record.

    This is a host-side record builder, not execution or MCU-safe publication.
    The record is accepted by the original-CPU proof wrapper: signed compact
    PITCH-code depth in +/-1024, square/triangle waveform, and PITCH destination
    only. A missing rate mapping returns ``None`` rather than inventing an
    increment. Phase is read but never advanced or reset here.
    """
    if not isinstance(mapped, MappedTrackControls):
        raise TypeError("mapped must be MappedTrackControls")
    if not isinstance(phase_bank, AudioPhaseBank):
        raise TypeError("phase_bank must be AudioPhaseBank")
    if type(active) is not bool:
        raise ValueError("active must be bool")
    increment = mapped.rate.guest_phase_increment_u32
    if increment is None:
        return None
    config = mapped.config
    if (config.destination_code != PITCH_DESTINATION or
            not isinstance(config.waveform, Waveform) or
            type(config.depth_compact_units) is not int or
            not DEPTH_MIN_COMPACT_UNITS <= config.depth_compact_units <=
            DEPTH_MAX_COMPACT_UNITS):
        return None
    return ExtraLfo(
        phase=phase_bank.read_audio_owned(mapped.track_id).phase_u32,
        increment=increment,
        depth=config.depth_compact_units,
        destination=config.destination_code,
        waveform=int(config.waveform),
        flags=ACTIVE if active else 0,
    )
