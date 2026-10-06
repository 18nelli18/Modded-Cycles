# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Lachlan Fysh
# Original authored source selected for review. re/tools/coldfire_emu/lfo2_ui_config_bank.py; lines 1-593.
# Unresolved integration bindings: see DEPENDENCIES.json.
"""Host-side two-bank LFO configuration and bounded snapshot handoff.

This is a prototype adapter, not firmware, persistence, or physical
concurrency evidence. LFO1 reads/writes are delegated to the installed stock
adapter. LFO2 owns a separate configuration record. Audio phase is deliberately
stored by :class:`AudioPhaseBank`, outside configuration and publication.

The native SPEED/UI encoding join is not established. SPEED writes through
either bank delegate to the stock adapter; the shared LFO2 speed adopts a
signed native C+0x02 value only when that adapter explicitly proves it.
``set_native_speed`` is the explicit entry point for an already-decoded value.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
import threading
from typing import Callable

from .lfo35_native_rate_cpu import literal_increment, s32
from .pre_b_fixture import PHASE_PERIOD


TRACK_COUNT = 6
INSTANCE_IDS = (1, 2)
CONTROLS = (
    "speed", "multiplier", "fade", "destination", "waveform",
    "start_phase", "trig_mode", "depth",
)
SYNC_MULTIPLIER_MAX = 11
MAX_MULTIPLIER = 23
LFO2_DEPTH_MIN_COMPACT_UNITS = -1024
LFO2_DEPTH_MAX_COMPACT_UNITS = 1024
LFO2_DESTINATIONS = (0, 10)  # NONE, PITCH
LFO2_WAVEFORMS = (0, 1)     # SQUARE, TRIANGLE
FREE_RATE_SCALAR = 0x3840
GUEST_PHASE_MODULUS = 1 << 32
_S32_MIN, _S32_MAX = -(1 << 31), (1 << 31) - 1
_S16_MIN, _S16_MAX = -(1 << 15), (1 << 15) - 1


def _target(track_id: int, instance_id: int | None = None,
            control: str | None = None) -> None:
    if type(track_id) is not int or not 0 <= track_id < TRACK_COUNT:
        raise ValueError("track_id must be an integer in 0..5")
    if instance_id is not None and (
            type(instance_id) is not int or instance_id not in INSTANCE_IDS):
        raise ValueError("instance_id must be exactly 1 or 2")
    if control is not None and (type(control) is not str or control not in CONTROLS):
        raise ValueError(f"control must be one of {', '.join(CONTROLS)}")


def _native_scalar(value: int) -> int:
    """Accept a signed scalar or its uint32 stack representation, then sign it."""
    if type(value) is not int or not _S32_MIN <= value <= 0xFFFFFFFF:
        raise ValueError("native_rate_scalar must be a signed32 or uint32 word")
    return s32(value)


def native_increment_to_guest_u32(increment: int) -> int:
    """Map one native-period increment to a nearest Q0.32 phase increment.

    The source phase wraps at ``0x5265c000``; the guest sidecar wraps at
    ``2**32``. The ratio is therefore converted as
    ``round_away(increment * 2**32 / 0x5265c000)``. Inputs outside the original
    one-correction interval are rejected. Negative results are encoded as a
    uint32 two's-complement increment, matching the guest ``add.l`` operation.
    This preserves normalized phase as closely as an integer Q0.32 step allows;
    it does not assert physical cadence.
    """
    if type(increment) is not int or abs(increment) >= PHASE_PERIOD:
        raise ValueError("native increment must satisfy abs(I) < 0x5265c000")
    numerator = increment * GUEST_PHASE_MODULUS
    half = PHASE_PERIOD // 2
    if numerator >= 0:
        rounded = (numerator + half) // PHASE_PERIOD
    else:
        rounded = -((-numerator + half) // PHASE_PERIOD)
    if not -(GUEST_PHASE_MODULUS - 1) <= rounded <= GUEST_PHASE_MODULUS - 1:
        raise AssertionError("bounded native increment escaped signed Q0.32 range")
    return rounded & 0xFFFFFFFF


def _signed_u32(value: int) -> int:
    value &= 0xFFFFFFFF
    return value - GUEST_PHASE_MODULUS if value & 0x80000000 else value


def _freeze_snapshot_value(value: object) -> object:
    """Recursively copy common UI scalar/container values into immutables."""
    if value is None or type(value) in (bool, int, float, str, bytes):
        return value
    if type(value) is tuple:
        return tuple(_freeze_snapshot_value(item) for item in value)
    if type(value) is list:
        return tuple(_freeze_snapshot_value(item) for item in value)
    if type(value) is dict:
        frozen = [(_freeze_snapshot_value(key), _freeze_snapshot_value(item))
                  for key, item in value.items()]
        return tuple(sorted(frozen, key=lambda pair: repr(pair[0])))
    if type(value) is set or type(value) is frozenset:
        return frozenset(_freeze_snapshot_value(item) for item in value)
    raise TypeError(f"snapshot value {type(value).__name__} is not freezeable")


def map_native_rate(native_speed: int | None, multiplier: int,
                    native_rate_scalar: int) -> RateMapping:
    """Evaluate #35's native equation and its bounded guest-phase conversion.

    ``multiplier`` is the native signed field before the literal clamp to
    0..23. The returned step is in routine invocations, not wall time.
    """
    if type(multiplier) is not int:
        raise ValueError("multiplier must be an integer native field")
    scalar = _native_scalar(native_rate_scalar)
    effective_multiplier = max(0, min(MAX_MULTIPLIER, multiplier))
    scalar_used = (scalar if effective_multiplier <= SYNC_MULTIPLIER_MAX
                   else FREE_RATE_SCALAR)
    if native_speed is None:
        return RateMapping("MAPPING_UNRESOLVED_NATIVE_SPEED",
                           effective_multiplier, scalar_used, None, None)
    if type(native_speed) is not int or not _S16_MIN <= native_speed <= _S16_MAX:
        raise ValueError("native_speed must be a signed 16-bit C+0x02 value")
    increment = literal_increment(native_speed, effective_multiplier, scalar_used)
    if abs(increment) >= PHASE_PERIOD:
        return RateMapping("OUTSIDE_NATIVE_ONE_CORRECTION_BOUND",
                           effective_multiplier, scalar_used, increment, None)
    return RateMapping("READY_NATIVE_INVOCATION_UNITS", effective_multiplier,
                       scalar_used, increment,
                       native_increment_to_guest_u32(increment))


@dataclass(frozen=True)
class Lfo1Value:
    """A value returned by the original LFO1 getter/setter adapter.

    ``raw_value`` and ``formatted_value`` are passed through unchanged.
    ``native_value`` must be supplied only when the stock adapter has actually
    decoded the value into the native field's units. The bank never guesses.
    """

    raw_value: object
    native_value: object | None = None
    formatted_value: str | None = None
    status: str = "DELEGATED"

    def __post_init__(self):
        if self.formatted_value is not None and type(self.formatted_value) is not str:
            raise TypeError("formatted_value must be a string or None")


@dataclass(frozen=True)
class Lfo1Adapter:
    read_control: Callable[[int, str], Lfo1Value]
    apply_write: Callable[[int, str, object, str, object], Lfo1Value]


@dataclass(frozen=True)
class Readback:
    track_id: int
    instance_id: int
    control: str
    raw_value: object | None
    native_value: object | None
    formatted_value: str | None
    generation: int
    status: str
    source: str | None = None
    event_id: object | None = None


@dataclass(frozen=True)
class Lfo2Configuration:
    """Complete bank-owned LFO2 configuration; no volatile phase is present."""

    multiplier: int = 0
    fade: int = 0
    destination: int = 0
    waveform: int = 0
    start_phase: int = 0
    trig_mode: int = 0
    depth: int = 0


@dataclass(frozen=True)
class PublishedLfo2:
    instance_id: int
    speed: int | None
    speed_raw_value: object | None
    speed_formatted_value: str | None
    multiplier: int
    fade: int
    destination: int
    waveform: int
    start_phase: int
    trig_mode: int
    depth: int


@dataclass(frozen=True)
class RateMapping:
    status: str
    effective_multiplier: int
    scalar_used: int | None
    native_increment: int | None
    guest_phase_increment_u32: int | None
    native_phase_period: int = PHASE_PERIOD
    guest_phase_modulus: int = GUEST_PHASE_MODULUS
    conversion: str = "round-away(I*2^32/0x5265c000), signed delta encoded uint32"


@dataclass(frozen=True)
class PublishedTrackSnapshot:
    """A complete immutable snapshot of this prototype's track-owned bank."""

    track_id: int
    generation: int
    config_generation: int
    linked_native_speed: int | None
    native_rate_scalar: int
    lfo2: PublishedLfo2
    rate: RateMapping


@dataclass(frozen=True)
class AudioPhase:
    """One audio-owned volatile uint32 phase word, separate from UI config."""

    phase_u32: int = 0

    def __post_init__(self):
        if type(self.phase_u32) is not int or not 0 <= self.phase_u32 < GUEST_PHASE_MODULUS:
            raise ValueError("phase_u32 must be an unsigned 32-bit phase")


class AudioPhaseBank:
    """Single-audio-owner phase storage for six regions.

    UI reads, selection, and configuration writes do not receive this object.
    ``advance`` is intended for the owning audio path only; it uses the guest
    bank's modulo-2**32 addition, not the stock 0x5265c000 modulus.
    """

    def __init__(self, phases: tuple[int, ...] | None = None):
        values = (0,) * TRACK_COUNT if phases is None else tuple(phases)
        if len(values) != TRACK_COUNT:
            raise ValueError("exactly six audio phase words are required")
        self._phases = [AudioPhase(value) for value in values]

    def read_audio_owned(self, track_id: int) -> AudioPhase:
        _target(track_id)
        return self._phases[track_id]

    def advance(self, track_id: int, increment_u32: int) -> AudioPhase:
        _target(track_id)
        if type(increment_u32) is not int or not 0 <= increment_u32 < GUEST_PHASE_MODULUS:
            raise ValueError("increment_u32 must be an unsigned 32-bit word")
        phase = (self._phases[track_id].phase_u32 + increment_u32) & 0xFFFFFFFF
        self._phases[track_id] = AudioPhase(phase)
        return self._phases[track_id]


@dataclass
class _TrackDraft:
    native_speed: int | None = None
    speed_raw_value: object | None = None
    speed_formatted_value: str | None = None
    config: Lfo2Configuration = Lfo2Configuration()
    config_generation: int = 0
    published_generation: int = 0
    selected_instance: int = 1


class Lfo2ConfigBank:
    """BankPort implementation with one-writer immutable snapshot publication.

    Control-side methods serialize draft mutations. ``publish_block_boundary``
    prepares and atomically replaces a whole frozen snapshot. The audio-side
    ``acquire_block_snapshot`` is exactly one reference load: no lock, retry,
    sequence loop, wait, or partial generation. This models an atomic pointer
    handoff in CPython; it is not a hardware memory-order/cache proof.
    """

    def __init__(self, lfo1_adapter: Lfo1Adapter | None = None):
        self._adapter = lfo1_adapter
        self._writer_lock = threading.RLock()
        self._tracks = [_TrackDraft() for _ in range(TRACK_COUNT)]
        self._published: list[PublishedTrackSnapshot | None] = [None] * TRACK_COUNT

    def install_lfo1_adapter(self, adapter: Lfo1Adapter | None) -> None:
        if adapter is not None and not isinstance(adapter, Lfo1Adapter):
            raise TypeError("adapter must be Lfo1Adapter or None")
        with self._writer_lock:
            self._adapter = adapter

    def selected_instance(self, track_id: int) -> int:
        _target(track_id)
        with self._writer_lock:
            return self._tracks[track_id].selected_instance

    def select_instance(self, track_id: int, instance_id: int) -> None:
        _target(track_id, instance_id)
        with self._writer_lock:
            # View state only: never touches either bank config or audio phase.
            self._tracks[track_id].selected_instance = instance_id

    def _read_lfo1(self, track_id: int, control: str) -> Readback:
        adapter = self._adapter
        if adapter is None:
            return Readback(track_id, 1, control, None, None, None,
                            self._tracks[track_id].config_generation,
                            "LFO1_ADAPTER_UNAVAILABLE")
        value = adapter.read_control(track_id, control)
        if not isinstance(value, Lfo1Value):
            raise TypeError("LFO1 getter must return Lfo1Value")
        return Readback(track_id, 1, control, value.raw_value,
                        value.native_value, value.formatted_value,
                        self._tracks[track_id].config_generation,
                        value.status)

    def read_control(self, track_id: int, instance_id: int, control: str) -> Readback:
        _target(track_id, instance_id, control)
        if instance_id == 1:
            return self._read_lfo1(track_id, control)
        if control == "speed":
            # SPEED is the deliberately shared control. Read its stock source
            # and formatter, while reporting mapping unresolved unless the
            # adapter has actually supplied native C+0x02.
            stock = self._read_lfo1(track_id, "speed")
            with self._writer_lock:
                track = self._tracks[track_id]
                if stock.status == "LFO1_ADAPTER_UNAVAILABLE":
                    raw, formatted = track.speed_raw_value, track.speed_formatted_value
                    native = track.native_speed
                else:
                    raw, formatted = stock.raw_value, stock.formatted_value
                    native = (stock.native_value
                              if type(stock.native_value) is int and
                              _S16_MIN <= stock.native_value <= _S16_MAX
                              else (track.native_speed
                                    if stock.raw_value == track.speed_raw_value
                                    else None))
                status = ("NATIVE_CONFIGURED" if native is not None
                          else "MAPPING_UNRESOLVED")
                return Readback(track_id, 2, "speed", raw, native,
                                formatted, track.config_generation,
                                status)
        with self._writer_lock:
            track = self._tracks[track_id]
            config = track.config
            value = getattr(config, control)
            if control in ("depth", "destination", "multiplier", "waveform"):
                status = "PROTOTYPE_SUPPORTED"
            else:
                status = "UNIMPLEMENTED_DEFAULT"
            return Readback(track_id, 2, control, value, value, None,
                            track.config_generation, status)

    def _write_lfo2(self, track_id: int, control: str, raw_value: object,
                    source: str, event_id: object) -> Readback:
        with self._writer_lock:
            track = self._tracks[track_id]
            config = track.config
            current = (track.native_speed if control == "speed"
                       else getattr(config, control))
            if control == "speed":
                return Readback(track_id, 2, control, current, current, None,
                                track.config_generation, "MAPPING_UNRESOLVED",
                                source, event_id)
            if control not in ("depth", "destination", "multiplier", "waveform"):
                return Readback(track_id, 2, control, current, current, None,
                                track.config_generation, "UNSUPPORTED",
                                source, event_id)
            if type(raw_value) is not int:
                return Readback(track_id, 2, control, current, current, None,
                                track.config_generation, "REJECTED_NATIVE_VALUE",
                                source, event_id)
            if control == "depth":
                valid = (LFO2_DEPTH_MIN_COMPACT_UNITS <= raw_value <=
                         LFO2_DEPTH_MAX_COMPACT_UNITS)
            elif control == "destination":
                valid = raw_value in LFO2_DESTINATIONS
            elif control == "multiplier":
                valid = 0 <= raw_value <= MAX_MULTIPLIER
            else:
                valid = raw_value in LFO2_WAVEFORMS
            if not valid:
                return Readback(track_id, 2, control, current, current, None,
                                track.config_generation, "REJECTED_NATIVE_VALUE",
                                source, event_id)
            if current != raw_value:
                track.config = replace(config, **{control: raw_value})
                track.config_generation += 1
            return Readback(track_id, 2, control, raw_value, raw_value, None,
                            track.config_generation, "APPLIED",
                            source, event_id)

    @staticmethod
    def _adapter_result(track_id: int, control: str, generation: int,
                        source: str, event_id: object,
                        value: Lfo1Value) -> Readback:
        return Readback(track_id, 1, control, value.raw_value,
                        value.native_value, value.formatted_value,
                        generation, value.status, source, event_id)

    def _write_lfo1(self, track_id: int, control: str, raw_value: object,
                    source: str, event_id: object,
                    result_instance_id: int = 1) -> Readback:
        adapter = self._adapter
        with self._writer_lock:
            generation = self._tracks[track_id].config_generation
        if adapter is None:
            if control == "speed" and result_instance_id == 2:
                return Readback(track_id, 2, control, None, None, None,
                                generation, "MAPPING_UNRESOLVED", source, event_id)
            return Readback(track_id, 1, control, None, None, None,
                            generation, "LFO1_ADAPTER_UNAVAILABLE", source, event_id)
        value = adapter.apply_write(track_id, control, raw_value, source, event_id)
        if not isinstance(value, Lfo1Value):
            raise TypeError("LFO1 setter must return Lfo1Value")
        if control == "speed" and value.status in ("APPLIED", "DELEGATED"):
            # The stock setter remains authoritative. Link only when its adapter
            # explicitly returns the already-decoded native C+0x02 value.
            with self._writer_lock:
                track = self._tracks[track_id]
                changed = False
                if track.speed_raw_value != value.raw_value:
                    track.speed_raw_value = value.raw_value
                    changed = True
                if track.speed_formatted_value != value.formatted_value:
                    track.speed_formatted_value = value.formatted_value
                    changed = True
                native_is_proven = (type(value.native_value) is int and
                                    _S16_MIN <= value.native_value <= _S16_MAX)
                linked_native = value.native_value if native_is_proven else None
                if track.native_speed != linked_native:
                    track.native_speed = linked_native
                    changed = True
                if changed:
                    track.config_generation += 1
                generation = track.config_generation
            status = (value.status if native_is_proven
                      else "DELEGATED_MAPPING_UNRESOLVED")
            return Readback(track_id, result_instance_id, control,
                            value.raw_value, value.native_value,
                            value.formatted_value, generation, status,
                            source, event_id)
        return self._adapter_result(track_id, control, generation, source,
                                    event_id, value)

    def apply_ui_write(self, track_id: int, instance_id: int, control: str,
                       raw_value: object, event_id: object) -> Readback:
        _target(track_id, instance_id, control)
        with self._writer_lock:
            if self._tracks[track_id].selected_instance != instance_id:
                track = self._tracks[track_id]
                current = (track.native_speed if instance_id == 2 and control == "speed"
                           else (getattr(track.config, control)
                                 if instance_id == 2 and control != "speed" else None))
                return Readback(track_id, instance_id, control, current, current, None,
                                track.config_generation, "STALE_UI_TARGET", "ui", event_id)
        if instance_id == 1:
            return self._write_lfo1(track_id, control, raw_value, "ui", event_id)
        if control == "speed":
            return self._write_lfo1(track_id, control, raw_value, "ui", event_id,
                                    result_instance_id=2)
        return self._write_lfo2(track_id, control, raw_value, "ui", event_id)

    def apply_external_write(self, track_id: int, instance_id: int, control: str,
                             raw_value: object, source: str,
                             event_id: object) -> Readback:
        _target(track_id, instance_id, control)
        if type(source) is not str or not source:
            raise ValueError("source must be a nonempty string")
        # External MIDI/lock routing always uses the supplied instance_id;
        # selected_instance is intentionally not consulted.
        if instance_id == 1:
            return self._write_lfo1(track_id, control, raw_value, source, event_id)
        if control == "speed":
            return self._write_lfo1(track_id, control, raw_value, source, event_id,
                                    result_instance_id=2)
        return self._write_lfo2(track_id, control, raw_value, source, event_id)

    def set_native_speed(self, track_id: int, native_speed: int) -> Readback:
        """Set an already-decoded shared signed C+0x02 speed value.

        This is not a UI conversion and does not call or mutate the stock LFO1
        object. Normal integration calls it with the native value yielded by
        the delegated stock setter/owner path. The linked value is then used by
        LFO2's literal #35 rate calculation.
        """
        _target(track_id)
        if type(native_speed) is not int or not _S16_MIN <= native_speed <= _S16_MAX:
            raise ValueError("native_speed must be a signed 16-bit C+0x02 value")
        with self._writer_lock:
            track = self._tracks[track_id]
            if track.native_speed != native_speed:
                track.native_speed = native_speed
                track.config_generation += 1
            generation = track.config_generation
        return Readback(track_id, 2, "speed", native_speed, native_speed, None,
                        generation, "NATIVE_SPEED_SET", "native", None)

    def _build_snapshot(self, track_id: int, track: _TrackDraft,
                        scalar: int, generation: int) -> PublishedTrackSnapshot:
        config = track.config
        published_lfo = PublishedLfo2(
            instance_id=2, speed=track.native_speed,
            speed_raw_value=_freeze_snapshot_value(track.speed_raw_value),
            speed_formatted_value=_freeze_snapshot_value(track.speed_formatted_value),
            multiplier=config.multiplier, fade=config.fade,
            destination=config.destination, waveform=config.waveform,
            start_phase=config.start_phase, trig_mode=config.trig_mode,
            depth=config.depth,
        )
        rate = map_native_rate(track.native_speed, config.multiplier, scalar)
        return PublishedTrackSnapshot(
            track_id=track_id, generation=generation,
            config_generation=track.config_generation,
            linked_native_speed=track.native_speed,
            native_rate_scalar=scalar,
            lfo2=published_lfo, rate=rate,
        )

    def publish_block_boundary(self, track_id: int,
                               native_rate_scalar: int) -> PublishedTrackSnapshot:
        """Publish one whole snapshot before a block; call off the audio path.

        The audio owner subsequently calls ``acquire_block_snapshot`` once at
        its block boundary. The native scalar is pinned input only for sync
        multiplier codes 0..11; free-family entries always use literal 0x3840.
        """
        _target(track_id)
        scalar = _native_scalar(native_rate_scalar)
        with self._writer_lock:
            track = self._tracks[track_id]
            next_generation = track.published_generation + 1
            snapshot = self._build_snapshot(track_id, track, scalar, next_generation)
            track.published_generation = next_generation
            # Single atomic reference replacement of the complete immutable
            # generation. No field-by-field publication is visible to readers.
            self._published[track_id] = snapshot
            return snapshot

    def acquire_block_snapshot(self, track_id: int) -> PublishedTrackSnapshot | None:
        """One lock-free reference read for the audio owner at block start."""
        _target(track_id)
        return self._published[track_id]


_DEFAULT_BANK = Lfo2ConfigBank()


def install_lfo1_adapter(adapter: Lfo1Adapter | None) -> None:
    _DEFAULT_BANK.install_lfo1_adapter(adapter)


def read_control(track_id: int, instance_id: int, control: str) -> Readback:
    return _DEFAULT_BANK.read_control(track_id, instance_id, control)


def apply_ui_write(track_id: int, instance_id: int, control: str,
                   raw_value: object, event_id: object) -> Readback:
    return _DEFAULT_BANK.apply_ui_write(track_id, instance_id, control,
                                         raw_value, event_id)


def apply_external_write(track_id: int, instance_id: int, control: str,
                         raw_value: object, source: str,
                         event_id: object) -> Readback:
    return _DEFAULT_BANK.apply_external_write(track_id, instance_id, control,
                                              raw_value, source, event_id)


def select_instance(track_id: int, instance_id: int) -> None:
    _DEFAULT_BANK.select_instance(track_id, instance_id)


def publish_block_boundary(track_id: int,
                           native_rate_scalar: int) -> PublishedTrackSnapshot:
    return _DEFAULT_BANK.publish_block_boundary(track_id, native_rate_scalar)


def acquire_block_snapshot(track_id: int) -> PublishedTrackSnapshot | None:
    return _DEFAULT_BANK.acquire_block_snapshot(track_id)


def set_native_speed(track_id: int, native_speed: int) -> Readback:
    return _DEFAULT_BANK.set_native_speed(track_id, native_speed)


def default_bank_for_testing() -> Lfo2ConfigBank:
    """Return the module's BankPort for callers that need isolated adapters."""
    return _DEFAULT_BANK
